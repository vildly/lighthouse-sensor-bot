import pandas as pd
import requests
import json
import re
from typing import List, Dict, Any, Callable, Union, Optional
import os
import numpy as np
from datetime import datetime

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
from ragas.metrics.base import Metric

# Custom metric for numerical accuracy
class NumericalAccuracy(Metric):
    """Custom metric to evaluate numerical accuracy of answers."""
    
    def __init__(self, threshold: float = 0.05):
        self.threshold = threshold
        super().__init__(
            name="numerical_accuracy",
            definition="Measures the accuracy of numerical values in the answer compared to ground truth",
        )
    
    def _extract_numbers(self, text: str) -> List[float]:
        """Extract numbers from text."""
        # Remove commas in numbers and find all numbers in the text
        text = re.sub(r'(\d),(\d)', r'\1\2', text)
        return [float(x) for x in re.findall(r'\b\d+\.?\d*\b', text)]
    
    def _compute_error(self, pred: float, gt: float) -> float:
        """Compute relative error between prediction and ground truth."""
        if gt == 0:
            return float('inf') if pred != 0 else 0.0
        return abs(pred - gt) / abs(gt)
    
    def _score_sample(self, 
                     question: str, 
                     answer: str, 
                     ground_truth: str) -> float:
        """Score a single sample."""
        # Extract numbers from answer and ground truth
        answer_nums = self._extract_numbers(answer)
        gt_nums = self._extract_numbers(ground_truth)
        
        # If no numbers in either, return 0.5 (neutral score)
        if not answer_nums or not gt_nums:
            return 0.5
        
        # Match numbers and compute errors
        errors = []
        for gt_num in gt_nums:
            if answer_nums:
                # Find closest number in answer
                closest_num = min(answer_nums, key=lambda x: abs(x - gt_num))
                error = self._compute_error(closest_num, gt_num)
                errors.append(error)
        
        # Compute average error and convert to score (0-1)
        if not errors:
            return 0.5
        
        avg_error = np.mean(errors)
        score = max(0, 1 - min(avg_error / self.threshold, 1))
        return score
    
    def score(self, 
             question: List[str], 
             answer: List[str], 
             ground_truth: List[str]) -> Dict[str, List[float]]:
        """Score multiple samples."""
        scores = []
        for q, a, gt in zip(question, answer, ground_truth):
            scores.append(self._score_sample(q, a, gt))
        
        return {"numerical_accuracy": scores}

# Custom metric for temporal accuracy
class TemporalAccuracy(Metric):
    """Custom metric to evaluate temporal accuracy of answers."""
    
    def __init__(self):
        super().__init__(
            name="temporal_accuracy",
            definition="Measures the accuracy of temporal information in the answer",
        )
    
    def _extract_dates(self, text: str) -> List[str]:
        """Extract dates from text."""
        # Simple date patterns (can be expanded)
        date_patterns = [
            r'\b\d{1,2}/\d{1,2}/\d{2,4}\b',  # MM/DD/YYYY
            r'\b\d{1,2}-\d{1,2}-\d{2,4}\b',  # MM-DD-YYYY
            r'\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]* \d{1,2},? \d{4}\b',  # Month DD, YYYY
            r'\b\d{1,2} (?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]* \d{4}\b',  # DD Month YYYY
        ]
        
        dates = []
        for pattern in date_patterns:
            dates.extend(re.findall(pattern, text, re.IGNORECASE))
        
        return dates
    
    def _score_sample(self, 
                     question: str, 
                     answer: str, 
                     ground_truth: str) -> float:
        """Score a single sample."""
        # Extract dates
        answer_dates = self._extract_dates(answer)
        gt_dates = self._extract_dates(ground_truth)
        
        # If no dates in either, return 0.5 (neutral score)
        if not answer_dates or not gt_dates:
            return 0.5
        
        # Check if any dates match
        matches = 0
        for gt_date in gt_dates:
            if any(gt_date.lower() in a_date.lower() or a_date.lower() in gt_date.lower() for a_date in answer_dates):
                matches += 1
        
        # Compute score
        if not gt_dates:
            return 0.5
        
        score = matches / len(gt_dates)
        return score
    
    def score(self, 
             question: List[str], 
             answer: List[str], 
             ground_truth: List[str]) -> Dict[str, List[float]]:
        """Score multiple samples."""
        scores = []
        for q, a, gt in zip(question, answer, ground_truth):
            scores.append(self._score_sample(q, a, gt))
        
        return {"temporal_accuracy": scores}

def load_test_cases(file_path="data/ragas/test_cases.csv"):
    """Load test cases from CSV file."""
    try:
        return pd.read_csv(file_path)
    except FileNotFoundError:
        print(f"Error: {file_path} not found.")
        return None

def query_agent(question: str, api_url="http://127.0.0.1:5000/api/query"):
    """Send a query to the agent API and get the response."""
    try:
        response = requests.post(api_url, json={"question": question, "source_file": "ferry_trips_data.csv"})
        response.raise_for_status()
        return response.json().get('response'), response.json().get('context', [])
    except requests.exceptions.RequestException as e:
        print(f"Error calling API: {e}")
        return None, []
    except json.JSONDecodeError as e:
        print(f"Error decoding JSON response: {e}")
        return None, []

def run_ragas_evaluation(test_cases_df):
    """Run RAGAS evaluation on the test cases."""
    questions = []
    answers = []
    contexts = []
    ground_truths = []
    
    # Process each test case
    for _, row in test_cases_df.iterrows():
        question = row['query']
        ground_truth = row['ground_truth']
        
        # Query the agent
        answer, context = query_agent(question)
        if answer is None:
            continue
            
        # Append to lists
        questions.append(question)
        answers.append(answer)
        contexts.append(context if context else ["No context provided"])
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
    
    # Define standard metrics
    standard_metrics = [
        faithfulness,
        answer_relevancy,
        context_relevancy,
        context_recall,
        context_precision,
        harmfulness
    ]
    
    # Define custom metrics
    custom_metrics = [
        NumericalAccuracy(),
        TemporalAccuracy()
    ]
    
    # Run evaluation with standard metrics
    standard_results = evaluate(dataset, standard_metrics)
    
    # Run evaluation with custom metrics
    custom_results = evaluate(dataset, custom_metrics)
    
    # Combine results
    results = {**standard_results, **custom_results}
    
    return results, data

def save_results(results, data, output_dir="data/ragas"):
    """Save RAGAS evaluation results."""
    # Create timestamp for filenames
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Ensure directory exists
    os.makedirs(output_dir, exist_ok=True)
    
    # Save metrics results
    metrics_df = pd.DataFrame()
    for metric, scores in results.items():
        if isinstance(scores, list) and all(isinstance(x, (int, float)) for x in scores):
            metrics_df[metric] = scores
    
    metrics_df.to_csv(f"{output_dir}/metrics_{timestamp}.csv", index=False)
    
    # Save detailed results with questions, answers, and scores
    detailed_df = pd.DataFrame({
        "question": data["question"],
        "ground_truth": data["ground_truth"],
        "answer": data["answer"]
    })
    
    # Add metrics
    for metric, scores in results.items():
        if isinstance(scores, list) and all(isinstance(x, (int, float)) for x in scores):
            detailed_df[metric] = scores
    
    detailed_df.to_csv(f"{output_dir}/detailed_results_{timestamp}.csv", index=False)
    
    print(f"Results saved to {output_dir}/metrics_{timestamp}.csv and {output_dir}/detailed_results_{timestamp}.csv")
    
    return metrics_df, detailed_df

def generate_report(metrics_df, detailed_df, output_dir="data/ragas"):
    """Generate a human-readable report of the evaluation results."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_path = f"{output_dir}/report_{timestamp}.md"
    
    with open(report_path, "w") as f:
        f.write("# RAGAS Evaluation Report\n\n")
        f.write(f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        
        # Overall metrics
        f.write("## Overall Metrics\n\n")
        f.write("| Metric | Score |\n")
        f.write("|--------|-------|\n")
        
        for column in metrics_df.columns:
            avg_score = metrics_df[column].mean()
            f.write(f"| {column} | {avg_score:.4f} |\n")
        
        # Best and worst performing questions
        f.write("\n## Best Performing Questions\n\n")
        
        # Calculate average score across all metrics for each question
        detailed_df["avg_score"] = detailed_df.select_dtypes(include=[np.number]).mean(axis=1)
        
        # Get top 3 questions
        top_questions = detailed_df.sort_values("avg_score", ascending=False).head(3)
        
        for i, (_, row) in enumerate(top_questions.iterrows()):
            f.write(f"### {i+1}. Question: {row['question']}\n")
            f.write(f"- Ground Truth: {row['ground_truth']}\n")
            f.write(f"- Answer: {row['answer']}\n")
            f.write("- Scores:\n")
            
            for column in metrics_df.columns:
                f.write(f"  - {column}: {row[column]:.4f}\n")
            
            f.write("\n")
        
        # Worst performing questions
        f.write("\n## Worst Performing Questions\n\n")
        
        # Get bottom 3 questions
        bottom_questions = detailed_df.sort_values("avg_score", ascending=True).head(3)
        
        for i, (_, row) in enumerate(bottom_questions.iterrows()):
            f.write(f"### {i+1}. Question: {row['question']}\n")
            f.write(f"- Ground Truth: {row['ground_truth']}\n")
            f.write(f"- Answer: {row['answer']}\n")
            f.write("- Scores:\n")
            
            for column in metrics_df.columns:
                f.write(f"  - {column}: {row[column]:.4f}\n")
            
            f.write("\n")
        
        # Recommendations
        f.write("\n## Recommendations\n\n")
        
        # Find weakest metrics
        avg_scores = metrics_df.mean()
        weakest_metrics = avg_scores.sort_values().head(3)
        
        f.write("Based on the evaluation results, here are some recommendations for improvement:\n\n")
        
        for metric, score in weakest_metrics.items():
            if metric == "faithfulness" and score < 0.8:
                f.write("- **Improve Faithfulness**: The agent sometimes generates information not supported by the context. Consider adding more constraints to ensure answers are grounded in the provided context.\n\n")
            elif metric == "answer_relevancy" and score < 0.8:
                f.write("- **Improve Answer Relevancy**: Some answers are not directly addressing the questions. Consider fine-tuning the agent to focus more on the specific question being asked.\n\n")
            elif metric == "context_relevancy" and score < 0.8:
                f.write("- **Improve Context Relevancy**: The retrieved context is sometimes not relevant to the question. Consider improving the retrieval mechanism to fetch more relevant information.\n\n")
            elif metric == "context_recall" and score < 0.8:
                f.write("- **Improve Context Recall**: The context often misses important information needed to answer the question. Consider expanding the context window or improving the retrieval strategy.\n\n")
            elif metric == "context_precision" and score < 0.8:
                f.write("- **Improve Context Precision**: The context contains too much irrelevant information. Consider refining the retrieval to be more precise and focused.\n\n")
            elif metric == "numerical_accuracy" and score < 0.8:
                f.write("- **Improve Numerical Accuracy**: The agent struggles with numerical values. Consider adding specific training or constraints for handling numerical data accurately.\n\n")
            elif metric == "temporal_accuracy" and score < 0.8:
                f.write("- **Improve Temporal Accuracy**: The agent has issues with dates and temporal information. Consider adding specific handling for temporal data.\n\n")
    
    print(f"Report generated at {report_path}")
    return report_path

def main():
    # Load test cases
    test_cases_df = load_test_cases()
    if test_cases_df is None:
        return
    
    # Run RAGAS evaluation
    results, data = run_ragas_evaluation(test_cases_df)
    
    # Save results
    metrics_df, detailed_df = save_results(results, data)
    
    # Generate report
    generate_report(metrics_df, detailed_df)
    
    # Print summary
    print("\nRAGAS Evaluation Summary:")
    for metric, score in results.items():
        if isinstance(score, list) and all(isinstance(x, (int, float)) for x in score):
            print(f"{metric}: {np.mean(score):.4f}")

if __name__ == "__main__":
    main() 