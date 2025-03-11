# RAGAS Evaluation for Lighthouse Sensor Bot

This README explains how to use the RAGAS (Retrieval Augmented Generation Assessment) framework to evaluate your agent's outputs.

## What is RAGAS?

RAGAS is an open-source framework for evaluating Retrieval Augmented Generation (RAG) systems. It provides a set of metrics to assess the quality of generated answers, including:

## Test Cases

Test cases are stored in CSV files with the following format:

```
query,ground_truth
What is the total fuel cost for route A in January 2024?,12345.67
...
```

Test cases are located in ./test_cases

## Running the Evaluation


These scripts will:
1. Load the test cases from the respective files
2. Query your agent API for each test case
3. Run RAGAS evaluation on the responses
4. Save the results to CSV files
5. Print a summary of the evaluation metrics

## Interpreting Results

RAGAS metrics are scored between 0 and 1, where higher is better:

- **Factual Correctness**
- **Context Relevancy**: 1.0 means the context is perfectly relevant to the question

- **Faithfulness**: 1.0 means the answer is completely faithful to the context
- **Answer Relevancy**: 1.0 means the answer is perfectly relevant to the question
- **Context Recall**: 1.0 means all necessary information is in the context
- **Context Precision**: 1.0 means the context contains only relevant information
- **Harmfulness**: 1.0 means the answer is completely safe (not harmful)