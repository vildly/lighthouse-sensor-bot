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
    raise ValueError(
        "OPENAI_API_KEY environment variable not set. Please set it before running this script."
    )

# RAGAS imports
from ragas.metrics import (
    Faithfulness,
    ResponseRelevancy,
    # context_relevancy,
    LLMContextRecall,
    LLMContextPrecisionWithoutReference,
)
from ragas.metrics import AspectCritic
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
            timeout=30,
        )
        response.raise_for_status()

        # Check if response contains expected fields
        response_data = response.json()
        if "response" not in response_data:
            print(
                f"Warning: API response missing 'response' field. Full response: {response_data}"
            )
            return None, []

        print(f"Received response: {response_data.get('response')[:50]}...")
        # Add a small delay to avoid overwhelming the server
        time.sleep(1)
        return response_data.get("response"), response_data.get("context", [])
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
        answer, context_list = query_agent(question)
        if answer is None:
            continue
            
        # Format context properly for RAGAS
        # RAGAS expects a list of strings for the context
        formatted_context = [str(c) for c in (context_list if context_list else ["No context provided"])]
        
        # Append to lists
        questions.append(question)
        answers.append(str(answer))
        contexts.append(formatted_context)
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
    
    # Define metrics to evaluate individually to handle potential errors
    try:
        faithfulness_result = evaluate(dataset, [Faithfulness])
    except Exception as e:
        print(f"Error evaluating faithfulness: {e}")
        faithfulness_result = {"faithfulness": [0.0] * len(questions)}
    
    try:
        answer_relevancy_result = evaluate(dataset, [ResponseRelevancy])
    except Exception as e:
        print(f"Error evaluating answer_relevancy: {e}")
        answer_relevancy_result = {"answer_relevancy": [0.0] * len(questions)}
    
    try:
        context_relevancy_result = evaluate(dataset, [LLMContextRecall])
    except Exception as e:
        print(f"Error evaluating context_relevancy: {e}")
        context_relevancy_result = {"context_relevancy": [0.0] * len(questions)}
    
    try:
        context_recall_result = evaluate(dataset, [LLMContextRecall])
    except Exception as e:
        print(f"Error evaluating context_recall: {e}")
        context_recall_result = {"context_recall": [0.0] * len(questions)}
    
    try:
        context_precision_result = evaluate(dataset, [LLMContextPrecisionWithoutReference])
    except Exception as e:
        print(f"Error evaluating context_precision: {e}")
        context_precision_result = {"context_precision": [0.0] * len(questions)}
    
    try:
        harmfulness_result = evaluate(dataset, [AspectCritic])
    except Exception as e:
        print(f"Error evaluating harmfulness: {e}")
        harmfulness_result = {"harmfulness": [0.0] * len(questions)}
    
    # Combine all results
    results = {
        **faithfulness_result,
        **answer_relevancy_result,
        **context_relevancy_result,
        **context_recall_result,
        **context_precision_result,
        **harmfulness_result
    }
    
    return results, data


def save_results(results, data, output_dir="output"):
    """Save RAGAS evaluation results to a timestamped folder within the output directory."""
    # Create a timestamp for the folder name
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")

    # Create the timestamped folder path
    timestamped_dir = os.path.join(output_dir, timestamp)

    # Create the directory if it doesn't exist
    os.makedirs(timestamped_dir, exist_ok=True)

    # Save detailed results with questions, answers, and scores
    detailed_path = os.path.join(timestamped_dir, "detailed_results.csv")
    detailed_df = pd.DataFrame(
        {
            "question": data["question"],
            "ground_truth": data["ground_truth"],
            "answer": data["answer"],
        }
    )

    # Add metrics
    for metric, scores in results.items():
        if isinstance(scores, list) and all(
            isinstance(x, (int, float)) for x in scores
        ):
            detailed_df[metric] = scores

    detailed_df.to_csv(detailed_path, index=False)

    print(f"Results saved to {timestamped_dir}")
    print(f"- Summary metrics: {detailed_path}")

    return detailed_df


def main():
    # Load test cases
    test_cases_df = load_test_cases()
    if test_cases_df is None:
        return

    # Run RAGAS evaluation
    results, data = run_ragas_evaluation(test_cases_df)

    # Save results
    detailed_df = save_results(results, data)

    # Print summary
    print("\nRAGAS Evaluation Summary:")
    for metric, scores in results.items():
        if isinstance(scores, list) and all(
            isinstance(x, (int, float)) for x in scores
        ):
            print(f"{metric}: {np.mean(scores):.4f}")


if __name__ == "__main__":
    main()
