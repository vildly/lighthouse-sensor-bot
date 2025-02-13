import os
import math
from datetime import datetime

import pandas as pd
import requests
import numpy as np
from dotenv import load_dotenv
import pydeck as pdk
from pydeck.data_utils import compute_view
from sklearn.cluster import DBSCAN, KMeans, AgglomerativeClustering
from typing import List, Tuple


# Load environment variables from .env file
load_dotenv()

PONTOS_TOKEN = os.getenv("PONTOS_TOKEN")

R = 6371000  # Earth's radius in meters


if not PONTOS_TOKEN:
    raise Exception("PONTOS_TOKEN not found in environment variables")


def fetch_vessel_data(
    vessel_id, start_time, end_time, parameter_ids=["*"], time_bucket=None
):
    """
    Fetches historical vessel data from PONTOS-HUB through the REST API.
    Requires a specified time range and for specified parameters.

    Args:
        vessel_id (str): The unique identifier of the vessel.
        start_time (str): The start time for data fetching in ISO 8601 format (YYYY-MM-DDTHH:MM:SS).
        end_time (str): The end time for data fetching in ISO 8601 format (YYYY-MM-DDTHH:MM:SS).
        parameter_ids (list of str, optional): A list of parameter IDs to filter the data. Defaults to ['*'].
        time_bucket (str, optional): The time bucket for averaging the data. Valid options are:
            "5 seconds", "30 seconds", "1 minute", "5 minutes", "10 minutes". Defaults to None.

    Returns:
        dict: The response from the PONTOS-hub API containing the vessel data.
    """
    # Convert string dates to datetime objects
    start = datetime.fromisoformat(start_time)
    end = datetime.fromisoformat(end_time)

    if start >= end:
        raise ValueError("'start_time' must be before 'end_time'")

    if start < datetime.fromisoformat("2023-04-30T22:00:00"):
        raise ValueError(
            "'start_time' must be before 2023-04-30T22:00:00. PONTOS-hub does not contain data before this time."
        )

    # Choose appropriate view of vessel data view
    averaged_vessel_data_views = {
        "5 seconds": "vessel_data_5_seconds_average",
        "30 seconds": "vessel_data_30_seconds_average",
        "1 minute": "vessel_data_1_minute_average",
        "5 minutes": "vessel_data_5_minutes_average",
        "10 minutes": "vessel_data_10_minutes_average",
    }
    api_view = (
        "vessel_data"
        if time_bucket is None
        else averaged_vessel_data_views.get(time_bucket, None)
    )
    if api_view is None:
        valid_keys = ", ".join([key for key in averaged_vessel_data_views.keys()])
        raise ValueError(
            f"Invalid time_bucket '{time_bucket}'. Use one of the following: {valid_keys}"
        )

    # Construct the parameter_id filter
    parameter_id_filter = "".join(
        [f"parameter_id.ilike.*{param}*," for param in parameter_ids]
    )
    parameter_id_filter = parameter_id_filter[:-1]  # Remove the trailing comma

    # Format query string with the current time bounds
    query = f"or=({parameter_id_filter})" f"&vessel_id=eq.{vessel_id}"
    if api_view != "vessel_data":
        query += f"&bucket=gte.{start.isoformat()}&bucket=lt.{end.isoformat()}"
    else:
        query += f"&time=gte.{start.isoformat()}&time=lt.{end.isoformat()}&select=time,parameter_id,value::float"

    # Make the API request
    url = f"https://pontos.ri.se/api/{api_view}?{query}"
    headers = {"Authorization": f"Bearer {PONTOS_TOKEN}"}
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        try:
            return response.json()
        except:
            raise Exception("Failed to parse JSON response:", response.text, url)
    else:
        raise Exception(
            "Failed to retrieve data:", response.status_code, response.text, url
        )


def transform_vessel_data_to_dataframe(vessel_data):
    """
    Transforms vessel data into a Pandas DataFrame.

    Args:
        vessel_data (list of dict): A list of dictionaries containing vessel data returned by the PONTOS REST-API.

    Returns:
        pandas.DataFrame: A DataFrame where the index is the time, columns are parameter IDs, and values are the
                          corresponding data values. The DataFrame is pivoted to have 'parameter_id' as columns
                          and 'time' as rows.
    """

    # Convert the list of dictionaries into a DataFrame
    df = pd.DataFrame(vessel_data)

    # Convert the time related columns to datetime format
    if "avg_time" in df.columns:
        df.rename(columns={"avg_time": "time", "avg_value": "value"}, inplace=True)
        df["bucket"] = pd.to_datetime(df["bucket"])
    df["time"] = pd.to_datetime(df["time"], format="ISO8601")

    # Pivot the DataFrame to have parameter_ids as columns, time as rows
    pivot_df = df.pivot_table(
        index="time", columns="parameter_id", values="value", aggfunc="first"
    ).reset_index()

    # Rename index
    pivot_df.index.name = "id"

    return pivot_df


def get_trips_from_vessel_data(
    vessel_data,
    speed_threshold_kn=1.0,
    stop_time_threshold_min=1.0,
    lat="positioningsystem_latitude_deg_1",
    lon="positioningsystem_longitude_deg_1",
    sog="positioningsystem_sog_kn_1",
    time_zone="CET",
):
    """
    Processes vessel data to extract trips based on speed and stop time thresholds.

    Args:
        vessel_data (list): A list of dictionaries containing vessel data points.
        speed_threshold_kn (float, optional): The speed threshold in knots below which data points are considered stops. Defaults to 1.0 kn.
        stop_time_threshold_min (float, optional): The time threshold in minutes to consider a stop between trips. Defaults to 1.0 minute.
        lat (str, optional): The key for latitude in the vessel data. Defaults to "positioningsystem_latitude_deg_1".
        lon (str, optional): The key for longitude in the vessel data. Defaults to "positioningsystem_longitude_deg_1".
        sog (str, optional): The key for speed over ground in the vessel data. Defaults to "positioningsystem_sog_kn_1".
        time_zone (str, optional): The time zone to which the 'time' column should be converted. Defaults to 'CET'.

    Returns:
        list: A list of dictionaries, each representing a trip. Each dictionary contains:
            - "path": A list of tuples with latitude and longitude points.
            - "time": A list of ISO8601 formatted timestamps.
            - Other attributes from the vessel data excluding latitude, longitude, and time.
    """

    # Transform vessel data to a Dataframe
    df = transform_vessel_data_to_dataframe(vessel_data)

    # Return empty list if the DataFrame is missing the required columns
    if lat not in df.columns or lon not in df.columns or sog not in df.columns:
        return []

    # Drop data points where latitude, longitude, or speed over ground is NaN
    df = df.dropna(subset=[lat, lon, sog])

    # Drop data points where the speed is below 0.5 kn
    df = df.drop(df[df[sog] < speed_threshold_kn].index)

    # Add column with time between messages (dt)
    df["dt"] = df["time"].diff().dt.total_seconds()

    # Transform time to timezone and ISO8601 format strings
    df["time"] = df["time"].dt.tz_convert(time_zone).dt.strftime("%Y-%m-%dT%H:%M:%S")

    # Split data into trips at time gaps ( dt > stop_time_threshold_min)
    trips = []
    for group in np.split(df, np.where(df.dt > stop_time_threshold_min * 60)[0]):
        path = [(p[0], p[1]) for p in group[[lat, lon]].to_records(index=False)]
        attributes = group[group.columns.difference([lat, lon, "dt"])].to_dict(
            orient="list"
        )
        trips.append({"path": path, **attributes})

    # Remove trips with less than 2 points
    trips = [trip for trip in trips if len(trip["path"]) > 1]

    return trips


CLUSTER_COLORS = [
    (31, 119, 180),
    (255, 127, 14),
    (44, 160, 44),
    (214, 39, 40),
    (148, 103, 189),
    (140, 86, 75),
    (227, 119, 194),
    (127, 127, 127),
    (188, 189, 34),
    (23, 190, 207),
    (230, 25, 75),
    (60, 180, 75),
    (245, 130, 49),
    (145, 30, 180),
    (70, 240, 240),
    (240, 50, 230),
    (188, 246, 12),
    (250, 190, 190),
    (0, 128, 128),
    (230, 190, 255),
    (154, 99, 36),
    (255, 250, 200),
    (128, 0, 0),
    (170, 255, 195),
    (128, 128, 0),
    (255, 216, 177),
    (0, 0, 128),
    (169, 169, 169),
    (255, 255, 255),
    (0, 0, 0),
]


def get_cluster_colors(labels):
    return [
        CLUSTER_COLORS[label] if label != -1 else [255.0, 255.0, 255.0]
        for label in labels
    ]


def flip_coordinates_order(path):
    """Flip the order of the coordinates in a path"""
    return [(p[1], p[0]) for p in path]


def make_paths_layer(paths, colors=None, opacity=0.95):
    if colors is None:
        colors = [CLUSTER_COLORS[i % len(CLUSTER_COLORS)] for i in range(len(paths))]
    paths_pdk = [
        {"path": flip_coordinates_order(path), "color": color}
        for path, color in zip(paths, colors)
    ]
    return pdk.Layer(
        "PathLayer",
        paths_pdk,
        get_color="color",
        opacity=opacity,
        width_min_pixels=5,
        rounded=True,
    )


def plot_paths(paths, colors=None):
    """
    Plots a series of paths on a map using the pydeck library.

    Args:
        paths (list of list of tuples): A list of paths, where each path is a list of (latitude, longitude) tuples.
        colors (list of tuples, optional): A list of RGB color tuples corresponding to each path. Defaults to None.

    Returns:
        pydeck.Deck: A pydeck Deck object representing the plotted paths.
    """
    layer = make_paths_layer(paths, colors=colors)
    points = [point for path in paths for point in flip_coordinates_order(path)]
    view_state = compute_view(points)
    r = pdk.Deck(layers=[layer], initial_view_state=view_state)
    return r


def haversine(point_1, point_2):
    """
    Calculate the great-circle distance between two points on the Earth using the Haversine formula.

    Args:
        point_1 (tuple): A tuple containing the latitude and longitude of the first point (in decimal degrees)
        point_2 (tuple): A tuple containing the latitude and longitude of the second point (in decimal degrees)

    Returns:
        float: The great-circle distance between the two points in meters
    """
    lat1, lon1 = point_1
    lat2, lon2 = point_2

    lat1_rad = math.radians(lat1)
    lon1_rad = math.radians(lon1)
    lat2_rad = math.radians(lat2)
    lon2_rad = math.radians(lon2)

    dlat = lat2_rad - lat1_rad
    dlon = lon2_rad - lon1_rad

    a = (math.sin(dlat / 2) ** 2) + math.cos(lat1_rad) * math.cos(lat2_rad) * (
        math.sin(dlon / 2) ** 2
    )
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    return R * c


def bearing(point_1, point_2):
    """
    Calculate the initial bearing from one point to another on the Earth's surface.

    Parameters:
    point_1 (tuple): A tuple containing the latitude and longitude of the first point (in decimal degrees)
    point_2 (tuple): A tuple containing the latitude and longitude of the second point (in decimal degrees)

    Returns:
    float: The initial bearing from the first point to the second point in degrees (0-360)
    """
    lat1, lon1 = point_1
    lat2, lon2 = point_2

    lat1_rad = math.radians(lat1)
    lon1_rad = math.radians(lon1)
    lat2_rad = math.radians(lat2)
    lon2_rad = math.radians(lon2)

    dlon = lon2_rad - lon1_rad
    y = math.sin(dlon) * math.cos(lat2_rad)
    x = math.cos(lat1_rad) * math.sin(lat2_rad) - math.sin(lat1_rad) * math.cos(
        lat2_rad
    ) * math.cos(dlon)

    initial_bearing_rad = math.atan2(y, x)

    # Convert radians to degrees and normalize the result to the range [0, 360)
    initial_bearing_deg = (math.degrees(initial_bearing_rad) + 360) % 360

    return initial_bearing_deg


def cross_track_distance(start_point, end_point, point):
    """
    Calculate the cross-track distance between a point and a rhumb line on the surface of the Earth.

    Parameters:
    start_point (tuple): A tuple containing the latitude and longitude of the starting point of the rhumb line (in decimal degrees)
    end_point (tuple): A tuple containing the latitude and longitude of the ending point of the rhumb line (in decimal degrees)
    point (tuple): A tuple containing the latitude and longitude of the point to calculate cross-track distance for (in decimal degrees)

    Returns:
    float: The cross-track distance between the point and the rhumb line in kilometers
    """

    d13 = haversine(start_point, point) / R
    bearing13 = math.radians(bearing(start_point, end_point))
    bearing12 = math.radians(bearing(start_point, point))

    return math.asin(math.sin(d13) * math.sin(bearing13 - bearing12)) * R


def douglas_peucker(path, epsilon):
    """
    Simplify a path using the Douglas-Peucker algorithm with cross-track distance.

    Parameters:
    path (list): A list of tuples containing the latitude and longitude of the path in the trajectory (in decimal degrees)
    epsilon (float): The tolerance value used to determine if a point should be kept in the simplified trajectory (in meters)

    Returns:
    list: A list of tuples containing the simplified trajectory path
    """
    dist_max = 0
    index = 0
    for i in range(1, len(path) - 1):
        dist = abs(cross_track_distance(path[0], path[-1], path[i]))
        if dist > dist_max:
            index = i
            dist_max = dist

    if dist_max > epsilon:
        rec_results_1 = douglas_peucker(path[: index + 1], epsilon)
        rec_results_2 = douglas_peucker(path[index:], epsilon)
        results = rec_results_1[:-1] + rec_results_2
    else:
        results = [path[0], path[-1]]
    return results


def frechet_distance(path_1, path_2):
    """
    Calculate the discrete Fréchet distance between two paths using cross-track distance.

    Parameters:
    path_1 (list): A list of tuples containing the latitude and longitude of the points in the first path (in decimal degrees)
    path_2 (list): A list of tuples containing the latitude and longitude of the points in the second path (in decimal degrees)

    Returns:
    float: The discrete Fréchet distance between the two paths
    """
    len_path_1 = len(path_1)
    len_path_2 = len(path_2)

    if len_path_1 == 0 or len_path_2 == 0:
        raise ValueError("Paths must not be empty")

    memo = np.full((len_path_1, len_path_2), -1.0)

    def recursive_frechet(i, j):
        if memo[i][j] != -1.0:
            return memo[i][j]

        if i == 0 and j == 0:
            memo[i][j] = haversine(path_1[0], path_2[0])
        elif i > 0 and j == 0:
            memo[i][j] = max(
                recursive_frechet(i - 1, 0), haversine(path_1[i], path_2[0])
            )
        elif i == 0 and j > 0:
            memo[i][j] = max(
                recursive_frechet(0, j - 1), haversine(path_1[0], path_2[j])
            )
        elif i > 0 and j > 0:
            memo[i][j] = max(
                min(
                    recursive_frechet(i - 1, j),
                    recursive_frechet(i - 1, j - 1),
                    recursive_frechet(i, j - 1),
                ),
                haversine(path_1[i], path_2[j]),
            )
        else:
            memo[i][j] = float("inf")
        return memo[i][j]

    return recursive_frechet(len_path_1 - 1, len_path_2 - 1)


def cluster_paths(
    paths: List[List[Tuple[float, float]]],
    alpha: float = 0.3,
    eps: float = 100,
    min_samples: int = 2,
    epsilon: float = 10,
) -> List[int]:
    """
    Cluster paths based on their Fréchet distance and direction similarity.

    Arguments:
        paths: A list of paths, where each path is a list of (x, y) coordinate tuples.
        alpha: The weight of the angular difference in the distance calculation, ranging from 0 to 1.
        eps: The maximum distance between two samples for them to be considered as in the same cluster.
        min_samples: The number of samples in a neighborhood for a point to be considered as a core point.
        epsilon: The threshold cross-track distance used to determine if a point should be kept in path simplification step (Douglas-Peucker algorithm).

    Returns:
        A list of cluster labels for each path. Noise points are given the label -1.
    """

    # Simplify the paths
    simplified_paths = [douglas_peucker(path, epsilon) for path in paths]

    # Compute path directions
    path_directions = [
        np.arctan2(path[-1][1] - path[0][1], path[-1][0] - path[0][0])
        for path in simplified_paths
    ]

    # Compute pairwise distances between all pairs of trajectories using the Fréchet distance
    distance_matrix = np.zeros([len(simplified_paths), len(simplified_paths)])
    for i, i_path in enumerate(simplified_paths):
        for j, j_path in enumerate(simplified_paths):
            if i == j:
                distance_matrix[i, j] = 0
            else:
                fr_dist = frechet_distance(i_path, j_path)
                angular_diff = angular_diff = np.abs(
                    path_directions[i] - path_directions[j]
                )
                distance_matrix[i, j] = (1 - alpha) * fr_dist + alpha * angular_diff

    # Apply DBSCAN clustering to group similar trajectories together
    clustering = DBSCAN(eps=eps, min_samples=min_samples, metric="precomputed")
    labels = clustering.fit_predict(distance_matrix)

    return labels


def generate_representative_path(
    paths: List[List[Tuple[float, float]]], epsilon: float = 10
) -> List[Tuple[float, float]]:
    """Generate representative path

    Generates a path representative of a group of similar paths by
    simplyfing each of the given paths then clustering the points
    of the simplified paths. The simplification is done with the
    Douglas-Peucker algorithm and the clustering with Agglomerative
    Clustering.

    Arguments:
    ----------

        paths: list
            List of similar paths where a path is list of (lat, lon) tuples.

        epsilon: float
            The threshold cross-track distance used to determine if
            a point should be kept in path simplification step
            (Douglas-Peucker algorithm).

    Returns:
    --------

        list
            The representative path as a list of (lat, lon) tuples.

    """
    # Find the representative waypoints.
    s_paths = [douglas_peucker(path, epsilon) for path in paths]
    n_waypoints = (
        int(np.ceil(sum([len(s_path) for s_path in s_paths]) / len(s_paths))) + 1
    )
    agglomerative_clustering = AgglomerativeClustering(n_clusters=n_waypoints)

    # Add the index as a third element in the input points for the Agglomerative Clustering algorithm
    points = np.array(
        [
            (point[0], point[1], index)
            for sublist in s_paths
            for index, point in enumerate(sublist)
        ]
    )
    points_np = np.array(points)[
        :, :2
    ]  # Exclude the index from the numpy array for clustering
    agglomerative_clustering.fit(points_np)

    # Calculate cluster centers
    cluster_centers = []
    ref = np.array([(p[0], p[1]) for p in paths[0]])
    for cluster_id in np.unique(agglomerative_clustering.labels_):
        cluster_points = points[agglomerative_clustering.labels_ == cluster_id]
        cluster_center = cluster_points[:, :2].mean(axis=0)
        closest_point_idx = np.argmin(np.linalg.norm(ref - cluster_center, axis=1))
        cluster_centers.append(
            (cluster_center[0], cluster_center[1], closest_point_idx)
        )

    # Sort the cluster centers based on the third element (the index)
    ordered_cluster_centers = sorted(cluster_centers, key=lambda x: x[2])

    # Remove the index from the final output
    ordered_cluster_centers = [(p[0], p[1]) for p in ordered_cluster_centers]

    return ordered_cluster_centers
