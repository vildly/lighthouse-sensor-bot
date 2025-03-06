import pandas as pd
import json
import requests
from ragas import evaluate, EvaluationDataset
from ragas.metrics import AspectCritic
from ragas.llms import LangchainLLMWrapper
from ragas.embeddings import LangchainEmbeddingsWrapper
from langchain_openai import ChatOpenAI
from langchain_openai import OpenAIEmbeddings


### Define ragas metrics
from ragas.metrics import LLMContextRecall, Faithfulness, FactualCorrectness, SemanticSimilarity

# Initialize LLM and Embeddings wrappers
evaluator_llm = LangchainLLMWrapper(ChatOpenAI(model="gpt-4o"))
evaluator_embeddings = LangchainEmbeddingsWrapper(OpenAIEmbeddings())

def run_test_case(query, ground_truth=None):
    api_url = "http://127.0.0.1:5000/query"
    try:
        response = requests.post(api_url, json={"question": query})
        response.raise_for_status()
        agent_response = response.json().get('response')
        if agent_response is None:
            print(f"Error: No 'response' key found in the API response for query: {query}")
            return None, True
    except requests.exceptions.RequestException as e:
        print(f"Error calling API for query: {query}: {e}")
        return None, False
    except json.JSONDecodeError as e:
        print(f"Error decoding JSON response for query: {query}: {e}")
        return None, False
    return agent_response, True

# Load test cases from JSON file
try:
    with open("data/ragas/test_cases.json", "r") as f:
        test_cases_list = json.load(f)
except FileNotFoundError:
    print("Error: test_cases.json not found.")
    exit()
except json.JSONDecodeError:
    print("Error: Invalid JSON format in test_cases.json.")
    exit()

results = []

for test_case in test_cases_list:
    query = test_case['user_input']
    ground_truth = test_case.get('reference')
    agent_response, api_call_success = run_test_case(query, ground_truth)
    results.append({
        "user_input": query,
        "reference": ground_truth,
        "agent_response": agent_response,
        "api_call_success": api_call_success
    })

results_df = pd.DataFrame(results)

# RAGAS Evaluation
ragas_data = pd.DataFrame(test_cases_list)
ragas_data['response'] = results_df['agent_response']

# Ensure 'reference' column exists for RAGAS evaluation
if 'reference' not in ragas_data.columns:
    ragas_data['reference'] = None

# Create EvaluationDataset
eval_dataset = EvaluationDataset.from_pandas(ragas_data)

metrics=[FactualCorrectness(), SemanticSimilarity(embeddings=evaluator_embeddings)]

ragas_results = evaluate(eval_dataset, metrics, llm=evaluator_llm)

# Add RAGAS metrics to results_df
for metric_name, scores in ragas_results.to_pandas().items():
    if metric_name != 'hash':
        results_df[metric_name] = scores


results_df.to_csv("data/ragas/test_results.csv", index=False)
print("Test results saved to test_results.csv")
print(ragas_results)