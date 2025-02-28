import pandas as pd
import json
from flask import Flask, request, jsonify  # Assuming you're using Flask
# ... (ragas imports if needed, but likely not directly for this part)
import requests # to send requests to your API

app = Flask(__name__)  # If you're running this in the same file as your Flask app

# --- 1. Load Test Cases ---
try:
    test_cases = pd.read_csv("data/ragas/test_cases.csv")  # Make sure the path is correct
except FileNotFoundError:
    print("Error: test_cases.csv not found. Please create the file.")
    exit() # or handle the error appropriately


def evaluate_numerical_answer(ground_truth, rag_output, threshold=0.05):
    try:
        gt_value = float(ground_truth)
        rag_value = float(rag_output)
        if gt_value == 0:  # Avoid division by zero
            percentage_error = float('inf') if rag_value != 0 else 0.0
        else:
            percentage_error = abs(gt_value - rag_value) / gt_value
        return percentage_error, percentage_error <= threshold
    except ValueError:
        return None, False


def run_test_case(query, ground_truth):
    # --- 2. Call your Flask API ---
    api_url = "http://127.0.0.1:5000/query"  # Replace with your API endpoint
    try:
        response = requests.post(api_url, json={"question": query}) # send json payload to your API
        response.raise_for_status() # Raise an exception for bad status codes (4xx or 5xx)
        agent_response = response.json().get('response') # assumes your API returns {"response": "the response"}
        if agent_response is None:
             print(f"Error: No 'response' key found in the API response for query: {query}")
             return None, None, None, False

    except requests.exceptions.RequestException as e:
        print(f"Error calling API for query: {query}: {e}")
        return None, None, None, False
    except json.JSONDecodeError as e:
        print(f"Error decoding JSON response for query: {query}: {e}")
        return None, None, None, False

    # --- 3. Evaluate ---
    percentage_error, pass_fail = evaluate_numerical_answer(ground_truth, agent_response)

    return agent_response, percentage_error, pass_fail, True


# --- 4. Run Tests and Store Results ---
results = []
for index, row in test_cases.iterrows():
    query = row['query']
    ground_truth = row['ground_truth']

    agent_response, percentage_error, pass_fail, api_call_success = run_test_case(query, ground_truth)

    results.append({
        "query": query,
        "ground_truth": ground_truth,
        "agent_response": agent_response,
        "percentage_error": percentage_error,
        "pass_fail": pass_fail,
        "api_call_success": api_call_success
    })


# --- 5. Output Results (Example: CSV) ---
results_df = pd.DataFrame(results)
results_df.to_csv("data/ragas/test_results.csv", index=False)
print("Test results saved to test_results.csv")