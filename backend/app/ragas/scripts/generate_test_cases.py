import pandas as pd
import json
import os
import random
from typing import List, Dict, Any

def load_ferry_data(file_path="data/ferries.json"):
    """Load ferry data from JSON file."""
    try:
        with open(file_path, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"Error: {file_path} not found.")
        return None
    except json.JSONDecodeError:
        print(f"Error: {file_path} is not valid JSON.")
        return None

def load_trips_data(file_path="data/ferry_trips_data.csv"):
    """Load ferry trips data from CSV file."""
    try:
        return pd.read_csv(file_path)
    except FileNotFoundError:
        print(f"Error: {file_path} not found.")
        return None

def generate_test_cases(ferry_data, trips_data, num_cases=10):
    """Generate test cases based on ferry and trips data."""
    test_cases = []
    
    # Example question templates
    templates = [
        ("What is the passenger capacity of {ferry_name}?", "{capacity} passengers"),
        ("How many trips did {ferry_name} make in total?", "{trip_count} trips"),
        ("What is the average fuel consumption of {ferry_name}?", "{fuel_consumption} liters per nautical mile"),
        ("Which route does {ferry_name} primarily serve?", "Route {route}"),
        ("What is the top speed of {ferry_name}?", "{speed} knots"),
        ("When was {ferry_name} built?", "{year}"),
        ("How many crew members are required for {ferry_name}?", "{crew_count} crew members"),
        ("What is the maintenance schedule for {ferry_name}?", "Every {maintenance_interval} months"),
        ("What is the total distance traveled by {ferry_name} in kilometers?", "{distance} km"),
        ("What is the average trip duration for {ferry_name}?", "{duration} minutes"),
        ("What was the total fuel consumption for all ferries in 2023?", "{total_fuel} liters"),
        ("How many passengers were transported in total during summer 2023?", "{passenger_count} passengers"),
        ("What is the average occupancy rate for {ferry_name}?", "{occupancy_rate}%"),
        ("Which ferry had the most maintenance days in 2023?", "{ferry_name} with {maintenance_days} days"),
        ("What was the busiest month for ferry traffic in 2023?", "{month} with {trip_count} trips")
    ]
    
    # Generate test cases
    for i in range(min(num_cases, len(templates))):
        if ferry_data and len(ferry_data) > 0:
            ferry = random.choice(ferry_data)
            template, answer_template = templates[i]
            
            # Fill in the template with ferry data
            query = template.format(ferry_name=ferry.get("name", "Unknown Ferry"))
            
            # Generate a plausible ground truth answer
            if "{capacity}" in answer_template:
                ground_truth = answer_template.format(capacity=ferry.get("capacity", random.randint(100, 500)))
            elif "{trip_count}" in answer_template:
                ground_truth = answer_template.format(trip_count=random.randint(50, 200))
            elif "{fuel_consumption}" in answer_template:
                ground_truth = answer_template.format(fuel_consumption=round(random.uniform(5, 20), 1))
            elif "{route}" in answer_template:
                ground_truth = answer_template.format(route=random.choice(["A", "B", "C", "D"]))
            elif "{speed}" in answer_template:
                ground_truth = answer_template.format(speed=random.randint(15, 35))
            elif "{year}" in answer_template:
                ground_truth = answer_template.format(year=random.randint(1990, 2020))
            elif "{crew_count}" in answer_template:
                ground_truth = answer_template.format(crew_count=random.randint(3, 12))
            elif "{maintenance_interval}" in answer_template:
                ground_truth = answer_template.format(maintenance_interval=random.choice([3, 6, 12]))
            elif "{distance}" in answer_template:
                ground_truth = answer_template.format(distance=random.randint(5000, 50000))
            elif "{duration}" in answer_template:
                ground_truth = answer_template.format(duration=random.randint(20, 90))
            elif "{total_fuel}" in answer_template:
                ground_truth = answer_template.format(total_fuel=random.randint(500000, 2000000))
            elif "{passenger_count}" in answer_template:
                ground_truth = answer_template.format(passenger_count=random.randint(100000, 500000))
            elif "{occupancy_rate}" in answer_template:
                ground_truth = answer_template.format(occupancy_rate=random.randint(60, 95))
            elif "{maintenance_days}" in answer_template:
                ground_truth = answer_template.format(ferry_name=ferry.get("name", "Unknown Ferry"), maintenance_days=random.randint(10, 45))
            elif "{month}" in answer_template:
                ground_truth = answer_template.format(month=random.choice(["July", "August", "June"]), trip_count=random.randint(500, 1500))
            else:
                ground_truth = "Unknown"
            
            test_cases.append({"query": query, "ground_truth": ground_truth})
    
    return test_cases

def save_test_cases(test_cases, output_path="data/ragas/generated_test_cases.csv"):
    """Save generated test cases to CSV."""
    # Convert to DataFrame
    test_cases_df = pd.DataFrame(test_cases)
    
    # Save to CSV
    test_cases_df.to_csv(output_path, index=False)
    print(f"Generated {len(test_cases)} test cases saved to {output_path}")

def main():
    # Load data
    ferry_data = load_ferry_data()
    trips_data = load_trips_data()
    
    # Generate test cases
    test_cases = generate_test_cases(ferry_data, trips_data, num_cases=20)
    
    # Save test cases
    save_test_cases(test_cases)
    
    # Print example
    print("\nExample test cases:")
    for i, case in enumerate(test_cases[:3]):
        print(f"{i+1}. Query: {case['query']}")
        print(f"   Ground Truth: {case['ground_truth']}")
        print()

if __name__ == "__main__":
    main() 