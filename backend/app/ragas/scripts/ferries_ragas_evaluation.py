import pandas as pd
import requests
import json
from typing import List, Dict, Any
import os
import time
from dotenv import load_dotenv
import datetime
import numpy as np


load_dotenv()


openai_api_key = os.getenv("OPENAI_API_KEY")
if not openai_api_key:
    raise ValueError("OPENAI_API_KEY environment variable not set. Please set it before running this script.")

# RAGAS imports
from ragas.metrics import (
    faithfulness,
    answer_relevancy,
    context_relevancy,
    context_recall,
    context_precision
)
from ragas.metrics.critique import harmfulness
from datasets import Dataset
from ragas import evaluate
from langchain_openai import ChatOpenAI
import langchain

# Configure langchain to use the OpenAI API key
langchain.openai_api_key = openai_api_key

def load_test_cases(file_path="app/ragas/test_cases/ferries_test_cases.csv"):
    """Load test cases from CSV file."""
    try:
        return pd.read_csv(file_path)
    except FileNotFoundError:
        print(f"Error: {file_path} not found.")
        return None

def query_agent(question: str, api_url="http://127.0.0.1:5000/api/query"):
    """Send a query to the agent API and get the response."""
    try:
        print(f"Querying agent with question: {question}")
        response = requests.post(
            api_url, 
            json={"question": question, "source_file": "ferries.json"},
            timeout=30
        )
        response.raise_for_status()
        
        # Check if response contains expected fields
        response_data = response.json()
        if 'response' not in response_data:
            print(f"Warning: API response missing 'response' field. Full response: {response_data}")
            return None, []
            
        print(f"Received response: {response_data.get('response')[:50]}...")
        # Add a small delay to avoid overwhelming the server
        time.sleep(1)
        return response_data.get('response'), response_data.get('context', [])
    except requests.exceptions.Timeout:
        print(f"Error: API request timed out after 30 seconds for question: {question}")
        return None, []
    except requests.exceptions.RequestException as e:
        print(f"Error calling API: {e}")
        return None, []
    except json.JSONDecodeError as e:
        print(f"Error decoding JSON response: {e}")
        return None, []
    except Exception as e:
        print(f"Unexpected error: {e}")
        return None, []

def run_ragas_evaluation(test_cases_df):
    """Run RAGAS evaluation on the test cases."""
    questions = []
    answers = []
    contexts = []
    ground_truths = []
    
    # Process each test case
    for _, row in test_cases_df.iterrows():
        question = str(row['query'])
        ground_truth = str(row['ground_truth'])
        
        # Query the agent
        answer, context = query_agent(question)
        if answer is None:
            continue
            
        # Append to lists
        questions.append(question)
        answers.append(str(answer))
        contexts.append([str(c) for c in (context if context else ["No context provided"])])
        ground_truths.append(ground_truth)
    
    # Create dataset for RAGAS
    data = {
        "question": questions,
        "answer": answers,
        "contexts": contexts,
        "ground_truth": ground_truths
    }
    
    # Convert to RAGAS dataset format
    dataset = Dataset.from_dict(data)
    
    # Define metrics to evaluate
    metrics = [
        faithfulness,
        answer_relevancy,
        context_relevancy,
        context_recall,
        context_precision,
        harmfulness
    ]
    
    # Run evaluation
    results = evaluate(dataset, metrics)
    
    return results, data

def save_results(results, data, output_dir="output"):
    """Save RAGAS evaluation results to a timestamped folder within the output directory."""
    # Create a timestamp for the folder name
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Create the timestamped folder path
    timestamped_dir = os.path.join(output_dir, timestamp)
    
    # Create the directory if it doesn't exist
    os.makedirs(timestamped_dir, exist_ok=True)
    
    # Save metrics summary
    metrics_path = os.path.join(timestamped_dir, "metrics_summary.csv")
    metrics_df = pd.DataFrame({
        metric: [scores.mean() if hasattr(scores, 'mean') else np.mean(scores) if isinstance(scores, list) else scores] 
        for metric, scores in results.items() 
        if metric not in ["question", "answer", "contexts", "ground_truth"]
    })
    metrics_df.to_csv(metrics_path, index=False)
    
    # Save detailed results with questions, answers, and scores
    detailed_path = os.path.join(timestamped_dir, "detailed_results.csv")
    detailed_df = pd.DataFrame({
        "question": data["question"],
        "ground_truth": data["ground_truth"],
        "answer": data["answer"]
    })
    
    # Add metrics
    for metric, scores in results.items():
        if isinstance(scores, list) and all(isinstance(x, (int, float)) for x in scores):
            detailed_df[metric] = scores
    
    detailed_df.to_csv(detailed_path, index=False)
    
    print(f"Results saved to {timestamped_dir}")
    print(f"- Summary metrics: {metrics_path}")
    print(f"- Detailed results: {detailed_path}")
    
    return metrics_df, detailed_df

def main():
    # Load test cases
    test_cases_df = load_test_cases()
    if test_cases_df is None:
        return
    
    # Run RAGAS evaluation
    results, data = run_ragas_evaluation(test_cases_df)
    
    # Save results
    metrics_df, detailed_df = save_results(results, data)
    
    # Print summary
    print("\nRAGAS Evaluation Summary:")
    for metric, scores in results.items():
        if isinstance(scores, list) and all(isinstance(x, (int, float)) for x in scores):
            print(f"{metric}: {np.mean(scores):.4f}")

if __name__ == "__main__":
    main() 