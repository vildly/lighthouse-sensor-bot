import pandas as pd
import json
import requests
from ragas import evaluate, EvaluationDataset
from ragas.metrics import AspectCritic
from ragas.llms import LangchainLLMWrapper
from ragas.embeddings import LangchainEmbeddingsWrapper
from langchain_openai import ChatOpenAI
from langchain_openai import OpenAIEmbeddings
from ragas.dataset_schema import SingleTurnSample

import os
from dotenv import load_dotenv
from pathlib import Path
import datetime
import asyncio

load_dotenv()


API_URL = os.getenv("API_URL")
RAGAS_APP_TOKEN = os.getenv("RAGAS_APP_TOKEN")

### Define ragas metrics
from ragas.metrics import (
    LLMContextRecall,
    Faithfulness,
    FactualCorrectness,
    SemanticSimilarity,
)

# Initialize LLM and Embeddings wrappers
evaluator_llm = LangchainLLMWrapper(ChatOpenAI(model="gpt-4o"))
evaluator_embeddings = LangchainEmbeddingsWrapper(OpenAIEmbeddings())


def run_test_case(query, ground_truth=None):
    api_url = f"{API_URL}/api/query"
    try:
        response = requests.post(
            api_url, 
            json={
                "question": query, 
                "source_file": "ferry_trips_data.csv",
                "return_context": True  # Request context data
            }
        )
        response.raise_for_status()
        data = response.json()
        agent_response = data.get("response")
        context = data.get("context", [])  # Get the actual data context
        if agent_response is None:
            print(f"Error: No 'response' key found in the API response for query: {query}")
            return None, None, True
    except requests.exceptions.RequestException as e:
        print(f"Error calling API for query: {query}: {e}")
        return None, None, False
    except json.JSONDecodeError as e:
        print(f"Error decoding JSON response for query: {query}: {e}")
        return None, None, False
    return agent_response, context, True


# Load test cases from JSON file
test_cases_path = Path("app/ragas/test_cases/test_cases.json")
try:
    with open(test_cases_path, "r") as f:
        test_cases_list = json.load(f)
except FileNotFoundError:
    print(f"Error: {test_cases_path} not found.")
    exit()
except json.JSONDecodeError:
    print(f"Error: Invalid JSON format in {test_cases_path}.")
    exit()

results = []

for test_case in test_cases_list:
    query = test_case["user_input"]
    ground_truth = test_case.get("reference")
    agent_response, context, api_call_success = run_test_case(query, ground_truth)
    results.append({
        "user_input": query,
        "reference": ground_truth,
        "agent_response": agent_response,
        "retrieved_contexts": context,
        "api_call_success": api_call_success,
    })

results_df = pd.DataFrame(results)

# RAGAS Evaluation
ragas_data = pd.DataFrame(test_cases_list)
ragas_data["response"] = results_df["agent_response"]
ragas_data["retrieved_contexts"] = results_df["retrieved_contexts"]

# Ensure 'reference' column exists for RAGAS evaluation
if "reference" not in ragas_data.columns:
    ragas_data["reference"] = None

# Create EvaluationDataset
eval_dataset = EvaluationDataset.from_pandas(ragas_data)

metrics = [
    FactualCorrectness(llm=evaluator_llm),
    SemanticSimilarity(embeddings=evaluator_embeddings),
    Faithfulness(llm=evaluator_llm)
]

async def evaluate_samples():
    scores = []
    for _, row in ragas_data.iterrows():
        sample = SingleTurnSample(
            user_input=row["user_input"],
            response=row["response"],
            reference=row["reference"],
            retrieved_contexts=row["retrieved_contexts"]
        )
        
        factual_score = await FactualCorrectness(llm=evaluator_llm).single_turn_ascore(sample)
        scores.append(factual_score)
    return scores

# Run the async evaluation
factual_scores = asyncio.run(evaluate_samples())
results_df["factual_correctness"] = factual_scores

ragas_results = evaluate(eval_dataset, metrics, llm=evaluator_llm)

ragas_results.upload()


# Add RAGAS metrics to results_df
for metric_name, scores in ragas_results.to_pandas().items():
    if metric_name != "hash":
        results_df[metric_name] = scores


cwd = Path(__file__).parent.parent.parent.parent.resolve()  # Go up to root directory
output_dir = cwd.joinpath("output")  # Use the same output directory as app.py

# Create timestamped directory within output
timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
timestamped_dir = output_dir.joinpath(f"ragas_{timestamp}")
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
