import pandas as pd
import json
import requests
from ragas import evaluate, EvaluationDataset
from ragas.metrics import AspectCritic, LLMContextRecall, Faithfulness, FactualCorrectness, SemanticSimilarity
from ragas.llms import LangchainLLMWrapper
from ragas.embeddings import LangchainEmbeddingsWrapper
from langchain_openai import ChatOpenAI
from langchain_deepseek import ChatDeepSeek
from langchain_openai import OpenAIEmbeddings
import os
from dotenv import load_dotenv
from pathlib import Path
import datetime
import argparse
from app.ragas.custom_metrics.LenientFactualCorrectness import LenientFactualCorrectness

load_dotenv()

API_URL = os.getenv('API_URL')
RAGAS_APP_TOKEN = os.getenv('RAGAS_APP_TOKEN')

# Initialize LLM and Embeddings wrappers
# evaluator_llm = LangchainLLMWrapper(ChatOpenAI(model="gpt-4o"))
evaluator_llm = LangchainLLMWrapper(ChatDeepSeek(model="deepseek-chat", temperature=0))
evaluator_embeddings = LangchainEmbeddingsWrapper(OpenAIEmbeddings())

def run_test_case(query, ground_truth, llm_model_id):
    api_url = f"{API_URL}/api/query"
    try:
        response = requests.post(api_url, json={
            "question": query,
            "source_file": "ferry_trips_data.csv",
            "llm_model_id": llm_model_id
        })
        response.raise_for_status()
        
        response_data = response.json()
        agent_response = response_data.get('content')  # This is already the clean response
        full_response = response_data.get('full_response')  # This contains the full context
        sql_queries = response_data.get('sql_queries', [])
        
        if agent_response is None:
            print(f"Error: No 'content' key found in the API response for query: {query}")
            return None, None, True
            
        # Format the complete context with reasoning and SQL
        contexts = []
        for sql in sql_queries:
            contexts.append(f"SQL Query: {sql}")
        
        # Add the complete agent response as context
        contexts.append(f"Agent Reasoning and Response: {full_response}")
        
        return agent_response, contexts, True
        
    except requests.exceptions.RequestException as e:
        print(f"Error calling API for query: {query}: {e}")
        return None, None, False
    except json.JSONDecodeError as e:
        print(f"Error decoding JSON response for query: {query}: {e}")
        return None, None, False

def run_evaluation(llm_model_id):
    # Load test cases from JSON file
    test_cases_path = Path("app/ragas/test_cases/test_cases.json")
    try:
        with open(test_cases_path, "r") as f:
            test_cases_list = json.load(f)
    except FileNotFoundError:
        print(f"Error: {test_cases_path} not found.")
        return
    except json.JSONDecodeError:
        print(f"Error: Invalid JSON format in {test_cases_path}.")
        return

    results = []

    for test_case in test_cases_list:
        query = test_case['user_input']
        ground_truth = test_case.get('reference')
        response, context, api_call_success = run_test_case(query, ground_truth, llm_model_id)
        results.append({
            "user_input": query,
            "reference": ground_truth,
            "response": response,
            "context": context,
            "api_call_success": api_call_success
        })

    results_df = pd.DataFrame(results)

    # RAGAS Evaluation
    ragas_data = pd.DataFrame({
        "user_input": results_df['user_input'],
        "reference": results_df['reference'],
        "response": results_df['response'],
        "retrieved_contexts": results_df['context'].apply(lambda x: x if isinstance(x, list) else [])
    })

    # Create EvaluationDataset
    eval_dataset = EvaluationDataset.from_pandas(ragas_data)

    # Define metrics including context recall
    metrics = [
        LenientFactualCorrectness(),
        SemanticSimilarity(embeddings=evaluator_embeddings),
        LLMContextRecall(llm=evaluator_llm),
        Faithfulness(llm=evaluator_llm)
    ]

    print(ragas_data[['user_input', 'response', 'reference']])

    ragas_results = evaluate(eval_dataset, metrics, llm=evaluator_llm)

    ragas_results.upload()

    # Add RAGAS metrics to results_df
    for metric_name, scores in ragas_results.to_pandas().items():
        if metric_name != 'hash':
            results_df[metric_name] = scores

    # Save results
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    
    cwd = Path(__file__).parent.parent.parent.parent.resolve()  # Go up to root directory
    output_dir = cwd.joinpath("output")

    # Create timestamped directory within output that includes model ID
    timestamped_dir = output_dir.joinpath(f"ragas_{timestamp}_{llm_model_id.replace('/', '_')}")
    timestamped_dir.mkdir(exist_ok=True)

    # Save results using timestamped paths
    results_df.to_csv(timestamped_dir.joinpath("test_results.csv"), index=False)
    print(f"Test results saved to {timestamped_dir}/test_results.csv")

    # Save metrics summary
    metrics_df = ragas_results.to_pandas()
    metrics_df.to_csv(timestamped_dir.joinpath("metrics_summary.csv"), index=False)

    print(f"Results saved in directory: {timestamped_dir}")
    print("\nRAGAS Results:")
    print(ragas_results)
    
    return ragas_results, results_df

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Run RAGAS evaluation with a specific LLM model')
    parser.add_argument('--model_id', type=str, required=True, 
                        help='The LLM model ID to use for testing (required)')
    args = parser.parse_args()
    
    print(f"Running evaluation with model: {args.model_id}")
    run_evaluation(llm_model_id=args.model_id)