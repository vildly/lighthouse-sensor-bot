#!/usr/bin/env python3
"""
Standalone script to run evaluation tests without the frontend.
Allows specifying which tests to run using slice notation or specific indices.

Usage:
    python run_evaluation_tests.py                    # Run all tests
    python run_evaluation_tests.py --tests 0:5        # Run tests 0-4 (slice notation)
    python run_evaluation_tests.py --tests 1,2,3      # Run specific test numbers
    python run_evaluation_tests.py --model gpt-4      # Use specific model
    python run_evaluation_tests.py --runs 3           # Run each test 3 times
    python run_evaluation_tests.py --retries 5        # Max 5 retries per test
"""

import sys
import json
import argparse
from pathlib import Path
import pandas as pd
from typing import List, Dict, Any, Optional

# Add the current directory to the path so we can import app modules
sys.path.append(str(Path(__file__).parent))

from app.ragas.scripts.test_run_manager import execute_test_runs
from app.ragas.scripts.synthetic_ragas_tests import load_synthetic_test_cases


def parse_test_selection(test_selection: str) -> List[int]:
    """
    Parse test selection string into list of test indices.
    
    Args:
        test_selection: String like "0:5", "1,2,3", "all", etc.
    
    Returns:
        List of test indices to run
    """
    if not test_selection or test_selection.lower() == "all":
        return []  # Empty list means all tests
    
    if ":" in test_selection:
        # Slice notation like "0:5" or "1:10:2"
        parts = test_selection.split(":")
        if len(parts) == 2:
            start, end = int(parts[0]), int(parts[1])
            return list(range(start, end))
        elif len(parts) == 3:
            start, end, step = int(parts[0]), int(parts[1]), int(parts[2])
            return list(range(start, end, step))
        else:
            raise ValueError(f"Invalid slice notation: {test_selection}")
    
    elif "," in test_selection:
        # Comma-separated list like "1,2,3"
        return [int(x.strip()) for x in test_selection.split(",")]
    
    else:
        # Single test number
        return [int(test_selection)]


def filter_test_cases(test_cases: List[Dict[str, Any]], test_indices: List[int]) -> List[Dict[str, Any]]:
    """
    Filter test cases based on test indices.
    
    Args:
        test_cases: Full list of test cases
        test_indices: List of test indices to include (1-based)
    
    Returns:
        Filtered list of test cases
    """
    if not test_indices:
        return test_cases  # Return all if no specific indices
    
    filtered_cases = []
    for idx in test_indices:
        # Convert 1-based test numbers to 0-based array indices
        array_idx = idx - 1 if idx > 0 else idx
        
        if 0 <= array_idx < len(test_cases):
            test_case = test_cases[array_idx].copy()
            # Ensure the test_no reflects the original test number
            test_case["test_no"] = idx if idx > 0 else test_cases[array_idx]["test_no"]
            filtered_cases.append(test_case)
        else:
            print(f"Warning: Test index {idx} is out of range (1-{len(test_cases)})")
    
    return filtered_cases


def run_evaluation_tests(
    model_id: str = "gpt-4o-mini",
    number_of_runs: int = 1,
    max_retries: int = 3,
    test_selection: Optional[str] = None
) -> None:
    """
    Run evaluation tests with specified parameters.
    
    Args:
        model_id: LLM model to test
        number_of_runs: Number of runs per test
        max_retries: Maximum retry attempts
        test_selection: Which tests to run (slice notation or comma-separated)
    """
    print(f"🚀 Starting evaluation tests for model: {model_id}")
    print(f"   Runs per test: {number_of_runs}")
    print(f"   Max retries: {max_retries}")
    
    try:
        # Load all test cases
        all_test_cases = load_synthetic_test_cases()
        print(f"📋 Loaded {len(all_test_cases)} total test cases")
        
        # Filter test cases based on selection
        if test_selection:
            test_indices = parse_test_selection(test_selection)
            test_cases = filter_test_cases(all_test_cases, test_indices)
            print(f"🎯 Selected {len(test_cases)} test cases: {test_selection}")
            
            if not test_cases:
                print("❌ No valid test cases selected. Exiting.")
                return
        else:
            test_cases = all_test_cases
            print("🎯 Running all test cases")
        
        # Convert to DataFrame for the test runner
        test_data = pd.DataFrame(test_cases)
        
        print(f"\n📊 Test cases to run:")
        for i, test_case in enumerate(test_cases):
            print(f"   {test_case['test_no']}: {test_case['query'][:80]}...")
        
        print(f"\n🔄 Starting test execution...")
        
        # Run the tests
        combined_ragas_results, results_df = execute_test_runs(
            model_id=model_id,
            number_of_runs=number_of_runs,
            max_retries=max_retries,
            progress_callback=None,  # No frontend progress callback
            test_data=test_data
        )
        
        if results_df is not None and not results_df.empty:
            print(f"\n✅ Tests completed successfully!")
            print(f"📈 Results summary:")
            print(f"   Total test runs: {len(results_df)}")
            
            # Calculate success rate
            successful_runs = len(results_df[results_df['api_call_success'] == True])
            ragas_evaluated = len(results_df[results_df['ragas_evaluated'] == True])
            
            print(f"   Successful API calls: {successful_runs}/{len(results_df)} ({successful_runs/len(results_df)*100:.1f}%)")
            print(f"   RAGAS evaluated: {ragas_evaluated}/{len(results_df)} ({ragas_evaluated/len(results_df)*100:.1f}%)")
            
            # Show metric averages if available
            if ragas_evaluated > 0:
                metrics = ['factual_correctness', 'semantic_similarity', 'context_recall', 'faithfulness']
                print(f"\n📊 Average metrics:")
                for metric in metrics:
                    if metric in results_df.columns:
                        avg_value = results_df[metric].dropna().mean()
                        if not pd.isna(avg_value):
                            print(f"   {metric}: {avg_value:.3f}")
            
            print(f"\n💾 Results saved to database tables:")
            print(f"   - query_result")
            print(f"   - query_evaluation") 
            print(f"   - evaluation_metrics")
            print(f"   - run_attempt_history")
            
        else:
            print("❌ No results returned from test execution")
            
    except Exception as e:
        print(f"❌ Error running evaluation tests: {e}")
        import traceback
        traceback.print_exc()


def main():
    """Main entry point for the script."""
    parser = argparse.ArgumentParser(
        description="Run evaluation tests without frontend",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python run_evaluation_tests.py                    # Run all tests
  python run_evaluation_tests.py --tests 0:5        # Run first 5 tests
  python run_evaluation_tests.py --tests 1,2,3      # Run tests 1, 2, and 3
  python run_evaluation_tests.py --tests 10:15      # Run tests 10-14
  python run_evaluation_tests.py --model gpt-4      # Use different model
  python run_evaluation_tests.py --runs 3           # Run each test 3 times
        """
    )
    
    parser.add_argument(
        "--model", 
        default="gpt-4o-mini",
        help="LLM model ID to test (default: gpt-4o-mini)"
    )
    
    parser.add_argument(
        "--tests",
        default=None,
        help="Which tests to run. Use slice notation (0:5) or comma-separated (1,2,3). Default: all tests"
    )
    
    parser.add_argument(
        "--runs",
        type=int,
        default=1,
        help="Number of runs per test (default: 1)"
    )
    
    parser.add_argument(
        "--retries",
        type=int,
        default=3,
        help="Maximum retry attempts per test (default: 3)"
    )
    
    parser.add_argument(
        "--list-tests",
        action="store_true",
        help="List all available tests and exit"
    )
    
    args = parser.parse_args()
    
    if args.list_tests:
        try:
            test_cases = load_synthetic_test_cases()
            print(f"📋 Available test cases ({len(test_cases)} total):")
            for i, test_case in enumerate(test_cases, 1):
                print(f"   {i}: {test_case['query']}")
        except Exception as e:
            print(f"❌ Error loading test cases: {e}")
        return
    
    # Run the evaluation tests
    run_evaluation_tests(
        model_id=args.model,
        number_of_runs=args.runs,
        max_retries=args.retries,
        test_selection=args.tests
    )


if __name__ == "__main__":
    main() 