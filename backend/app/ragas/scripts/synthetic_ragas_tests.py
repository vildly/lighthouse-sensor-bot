import pandas as pd
import json
from ragas import evaluate, EvaluationDataset
from ragas.metrics import LLMContextRecall, Faithfulness, SemanticSimilarity
# from ragas.dataset_schema import SingleTurnSample
from ragas.metrics._string import NonLLMStringSimilarity
from ragas.metrics import RougeScore
from ragas.metrics import StringPresence
from ragas.llms import LangchainLLMWrapper
from ragas.embeddings import LangchainEmbeddingsWrapper
# from langchain_openai import ChatOpenAI
from langchain_deepseek import ChatDeepSeek
from langchain_openai import OpenAIEmbeddings
import os
from dotenv import load_dotenv
from pathlib import Path
import datetime
import requests
from app.ragas.custom_metrics.LenientFactualCorrectness import LenientFactualCorrectness
from app.ragas.custom_metrics.bleu_score import BleuScore
import argparse
from typing import Callable, Optional

load_dotenv()
# this script is used to evaluate the performance of the agent on the synthetic dataset.
API_URL = os.getenv('API_URL')
RAGAS_APP_TOKEN = os.getenv('RAGAS_APP_TOKEN')

DEEPSEEK_API_KEY = os.getenv('DEEPSEEK_API_KEY')

# Initialize LLM and Embeddings wrappers

# evaluator_llm = LangchainLLMWrapper(ChatOpenAI(model="gpt-4o"))
evaluator_llm = LangchainLLMWrapper(ChatDeepSeek(model="deepseek-chat", temperature=0))
evaluator_embeddings = LangchainEmbeddingsWrapper(OpenAIEmbeddings())

def run_test_case(query, ground_truth, llm_model_id):
    """Run a single test case through the API"""
    api_url = f"{API_URL}/api/query"
    try:
        response = requests.post(api_url, json={
            "question": query,
            "source_file": "ferry_trips_data.csv",
            "llm_model_id": llm_model_id
        })
        response.raise_for_status()
        
        response_data = response.json()
        agent_response = response_data.get('content')
        full_response = response_data.get('full_response')
        sql_queries = response_data.get('sql_queries', [])
        
        if agent_response is None:
            print(f"Error: No 'content' key found in the API response for query: {query}")
            return None, None, False
            
        # Format contexts including SQL queries and full response
        contexts = []
        for sql in sql_queries:
            contexts.append(f"SQL Query: {sql}")
        contexts.append(f"Agent Reasoning and Response: {full_response}")
        
        return agent_response, contexts, True
        
    except requests.exceptions.RequestException as e:
        print(f"Error calling API for query: {query}: {e}")
        return None, None, False
    except json.JSONDecodeError as e:
        print(f"Error decoding JSON response for query: {query}: {e}")
        return None, None, False

def load_synthetic_test_cases():
    """Load synthetic test cases from JSON file"""
    test_cases_path = Path("app/ragas/test_cases/synthetic_test_cases.json")
    try:
        with open(test_cases_path, "r") as f:
            test_cases = json.load(f)
        return test_cases
    except FileNotFoundError:
        print(f"Error: {test_cases_path} not found.")
        return None
    except json.JSONDecodeError:
        print(f"Error: Invalid JSON format in {test_cases_path}.")
        return None

def run_synthetic_evaluation(llm_model_id, progress_callback: Optional[Callable] = None):
    """Run evaluation using the synthetic test cases"""
    # Load synthetic test cases
    test_cases = load_synthetic_test_cases()
    if test_cases is None:
        return
    
    results = []
    
    # After loading test cases, report progress
    if progress_callback:
        progress_callback(1, 8, "Loading test cases")
    
    # Process each test case
    for test_case in test_cases:
        query = test_case['user_input']
        ground_truth = test_case['reference']
        response, context, api_call_success = run_test_case(query, ground_truth, llm_model_id)
        
        if api_call_success:
            results.append({
                "user_input": query,
                "reference": ground_truth,
                "response": response,
                "context": context,
                "reference_contexts": test_case['reference_contexts'],
                "api_call_success": api_call_success
            })
    
    # After each major step, report progress
    # For example, after running test cases:
    if progress_callback:
        progress_callback(3, 8, "Processing test results")
    
    # Create results DataFrame for RAGAS evaluation
    results_df = pd.DataFrame(results)
    
    # Prepare data for RAGAS evaluation
    ragas_data = pd.DataFrame({
        "user_input": results_df['user_input'],
        "reference": results_df['reference'],
        "response": results_df['response'],
        "retrieved_contexts": results_df['reference_contexts']
    })
    
    # Create EvaluationDataset
    eval_dataset = EvaluationDataset.from_pandas(ragas_data)
    
    # Define metrics
    metrics = [
        LenientFactualCorrectness(),
        SemanticSimilarity(embeddings=evaluator_embeddings),
        LLMContextRecall(llm=evaluator_llm),
        Faithfulness(llm=evaluator_llm),
        BleuScore(),
        NonLLMStringSimilarity(),
        RougeScore(),
        StringPresence()
    ]
    
    # Before RAGAS evaluation
    if progress_callback:
        progress_callback(5, 8, "Running RAGAS evaluation")
    
    # Run evaluation
    ragas_results = evaluate(eval_dataset, metrics, llm=evaluator_llm)
    
    if progress_callback:
        progress_callback(7, 8, "Finalizing results")
    
    ragas_results.upload()
    
    return ragas_results, results_df

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Run synthetic RAGAS evaluation with a specific LLM model')
    parser.add_argument('--model_id', type=str, required=True, 
                        help='The LLM model ID to use for testing (required)')
    args = parser.parse_args()
    
    print(f"Running synthetic evaluation with model: {args.model_id}")
    run_synthetic_evaluation(llm_model_id=args.model_id) 