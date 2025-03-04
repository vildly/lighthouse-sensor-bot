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
    Faithfulness as faithfulness,
    ResponseRelevancy as answer_relevancy,
    # context_relevancy,
    LLMContextRecall as context_recall,
    LLMContextPrecisionWithoutReference as context_precision,
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


def custom_evaluate(dataset, metrics):
    """Custom evaluation function to bypass RAGAS validation issues."""
    from ragas.evaluation import score_dataset
    
    # Skip the validation step and directly call the scoring function
    results = {}
    for metric in metrics:
        try:
            metric_results = score_dataset(dataset, metric)
            results.update(metric_results)
        except Exception as e:
            print(f"Error evaluating {metric.__class__.__name__}: {e}")
    
    return results


def run_ragas_evaluation(test_cases_df):
    """Run RAGAS evaluation on the test cases."""
    # Initialize the LLM for evaluation
    llm = ChatOpenAI(
        model="gpt-3.5-turbo",
        temperature=0,
        api_key=openai_api_key
    )
    
    # Create a LangchainLLMWrapper
    from ragas.llms import LangchainLLMWrapper
    evaluator_llm = LangchainLLMWrapper(llm)
    
    # Prepare dataset in the format expected by RAGAS
    dataset_items = []
    
    for _, row in test_cases_df.iterrows():
        question = str(row['query'])
        ground_truth = str(row['ground_truth'])
        
        # Query the agent
        answer, context = query_agent(question)
        if answer is None:
            continue
        
        # Format context properly
        formatted_context = [str(c) for c in (context if context else ["No context provided"])]
        
        # Add to dataset
        dataset_items.append({
            "user_input": question,
            "retrieved_contexts": formatted_context,
            "response": answer,
            "reference": ground_truth
        })
    
    # Create EvaluationDataset
    from ragas import EvaluationDataset
    evaluation_dataset = EvaluationDataset.from_list(dataset_items)
    
    # Import the metrics
    from ragas.metrics import LLMContextRecall, Faithfulness, FactualCorrectness
    
    # Run evaluation
    results = evaluate(
        dataset=evaluation_dataset,
        metrics=[LLMContextRecall(), Faithfulness(), FactualCorrectness()],
        llm=evaluator_llm
    )
    
    return results, dataset_items


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
    
    # Convert results to DataFrame
    metrics_df = results.to_pandas()
    
    # Save the metrics DataFrame
    metrics_df.to_csv(metrics_path, index=False)
    
    # Save detailed results with questions, answers, and scores
    detailed_path = os.path.join(timestamped_dir, "detailed_results.csv")
    
    # Create a DataFrame with the detailed results
    detailed_df = pd.DataFrame([
        {
            "question": item["user_input"],
            "ground_truth": item["reference"],
            "answer": item["response"]
        }
        for item in data
    ])
    
    # Save detailed results
    detailed_df.to_csv(detailed_path, index=False)
    
    # Save a text summary file with the same timestamp
    text_summary_path = os.path.join(timestamped_dir, f"{timestamp}.txt")
    with open(text_summary_path, 'w') as f:
        f.write(f"RAGAS Evaluation Results\n")
        f.write(f"======================\n\n")
        f.write(f"Timestamp: {timestamp}\n\n")
        f.write(f"Summary Metrics:\n")
        
        # Get the metrics from the results object directly
        # This assumes results has a get_scores() method or similar
        try:
            # Try to access scores directly from the results object
            if hasattr(results, 'scores'):
                for metric, score in results.scores.items():
                    f.write(f"{metric}: {score:.4f}\n")
            elif hasattr(results, 'get_scores'):
                scores = results.get_scores()
                for metric, score in scores.items():
                    f.write(f"{metric}: {score:.4f}\n")
            else:
                # Fallback: just write the DataFrame as is
                f.write(f"Metrics DataFrame:\n{metrics_df.to_string()}\n")
        except Exception as e:
            f.write(f"Error getting scores: {e}\n")
            f.write(f"Metrics DataFrame:\n{metrics_df.to_string()}\n")
        
        f.write(f"\nEvaluated {len(data)} questions\n")
    
    print(f"Results saved to {timestamped_dir}")
    print(f"- Summary metrics: {metrics_path}")
    print(f"- Detailed results: {detailed_path}")
    print(f"- Text summary: {text_summary_path}")
    
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
    
    metrics_df = results.to_pandas()
    for column in metrics_df.columns:
        if pd.api.types.is_numeric_dtype(metrics_df[column]):
            print(f"{column}: {metrics_df[column].mean():.4f}")
        else:
            print(f"{column}: (non-numeric)")


if __name__ == "__main__":
    main()
