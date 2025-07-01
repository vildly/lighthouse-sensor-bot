#!/usr/bin/env python3
"""
API-based Evaluation Test Runner
Uses the local backend API to run evaluation tests
"""

import argparse
import requests
import json
import sys
from typing import Optional

def run_evaluation_via_api(
    model_id: str,
    number_of_runs: int = 1,
    max_retries: int = 3,
    test_selection: str = None,
    api_base_url: str = "http://localhost:5001"
) -> dict:
    """Run evaluation tests via the API endpoint"""
    
    print(f"�� Running evaluation test via API")
    print(f"   Model: {model_id}")
    print(f"   Runs: {number_of_runs}")
    print(f"   Max retries: {max_retries}")
    if test_selection:
        print(f"   Test selection: {test_selection}")
    print(f"   API URL: {api_base_url}/api/evaluate")
    
    # Prepare the payload
    payload = {
        "model_id": model_id,
        "number_of_runs": number_of_runs,
        "max_retries": max_retries
    }
    
    # Add test_selection if provided
    if test_selection:
        payload["test_selection"] = test_selection
    
    print(f"\n📤 Sending payload: {json.dumps(payload, indent=2)}")
    
    try:
        # Make the API request
        response = requests.post(
            f"{api_base_url}/api/evaluate",
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=300  # 5 minute timeout
        )
        
        print(f"\n📥 Response status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Evaluation completed successfully!")
            
            # Display results summary
            if "summary" in result:
                summary = result["summary"]
                print(f"\n📊 Results Summary:")
                print(f"   Total tests: {summary.get('total_tests', 'N/A')}")
                print(f"   Successful: {summary.get('successful_tests', 'N/A')}")
                print(f"   Failed: {summary.get('failed_tests', 'N/A')}")
                print(f"   Total retries: {summary.get('total_retries', 'N/A')}")
            
            # Display metrics if available
            if "metrics" in result:
                metrics = result["metrics"]
                print(f"\n📈 Average Metrics:")
                for metric, value in metrics.items():
                    if isinstance(value, (int, float)):
                        print(f"   {metric}: {value:.3f}")
                    else:
                        print(f"   {metric}: {value}")
            
            print(f"\n💡 View detailed results: python view_test_results.py")
            
        else:
            print(f"❌ Error: {response.status_code}")
            try:
                error_data = response.json()
                print(f"Error details: {json.dumps(error_data, indent=2)}")
            except:
                print(f"Error response: {response.text}")
        
    except requests.exceptions.ConnectionError:
        print(f"❌ Connection error. Is the backend running on {api_base_url}?")
        print(f"💡 Try: cd backend && python app.py")
        return None
    except requests.exceptions.Timeout:
        print(f"❌ Request timed out after 5 minutes")
        return None
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return None

def display_results(results: dict):
    """Display results from the API response"""
    if results is None:
        print("❌ No results to display")
        return
        
    if "error" in results:
        print(f"\n❌ Error: {results['error']}")
        return
    
    print(f"\n📊 Evaluation Results:")
    print("=" * 50)
    
    # Display summary info
    if "message" in results:
        print(f"📝 Status: {results['message']}")
    
    if "model_id" in results:
        print(f"🤖 Model: {results['model_id']}")
    
    if "total_tests" in results:
        print(f"📋 Tests completed: {results['total_tests']}")
    
    if "successful_tests" in results:
        print(f"✅ Successful: {results['successful_tests']}")
    
    if "failed_tests" in results:
        print(f"❌ Failed: {results['failed_tests']}")
    
    # Display metrics if available
    if "metrics" in results:
        print(f"\n📈 Average Metrics:")
        metrics = results["metrics"]
        if "avg_factual_correctness" in metrics:
            print(f"   • Factual Correctness: {metrics['avg_factual_correctness']:.3f}")
        if "avg_semantic_similarity" in metrics:
            print(f"   • Semantic Similarity: {metrics['avg_semantic_similarity']:.3f}")
        if "avg_faithfulness" in metrics:
            print(f"   • Faithfulness: {metrics['avg_faithfulness']:.3f}")
        if "avg_context_recall" in metrics:
            print(f"   • Context Recall: {metrics['avg_context_recall']:.3f}")
    
    # Display test results if available
    if "test_results" in results:
        print(f"\n📝 Individual Test Results:")
        for i, test_result in enumerate(results["test_results"], 1):
            print(f"   Test {i}: {test_result.get('status', 'unknown')}")
    
    print(f"\n💡 Tip: Use 'python view_test_results.py' to see detailed results")

def list_available_models(api_base_url: str = "http://localhost:5001"):
    """List available models from the API"""
    
    print("🔍 Checking available models...")
    
    # We can check via the test endpoint or make a simple query
    try:
        # Test if backend is running
        response = requests.get(f"{api_base_url}/api/test", timeout=10)
        if response.status_code == 200:
            print("✅ Backend is running")
            print("\n📋 Suggested models to try:")
            print("   • openai/gpt-4o-2024-11-20")
            print("   • google/gemini-2.5-flash-preview")
            print("   • anthropic/claude-3.7-sonnet")
            print("   • meta-llama/llama-3.1-8b-instruct")
            print("\n💡 These models should be available in your database")
        else:
            print("❌ Backend not responding properly")
            
    except Exception as e:
        print(f"❌ Error checking backend: {e}")
        print("   Make sure the backend is running with: docker-compose up -d")

def main():
    parser = argparse.ArgumentParser(
        description="Run evaluation tests via the local API",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python run_evaluation_api.py --model "openai/gpt-4o-2024-11-20"
  python run_evaluation_api.py --model "google/gemini-2.5-flash-preview" --runs 2
  python run_evaluation_api.py --model "anthropic/claude-3.7-sonnet" --retries 5
  python run_evaluation_api.py --list-models
        """
    )
    
    parser.add_argument(
        "--model",
        type=str,
        default="openai/gpt-4o-2024-11-20",
        help="Model ID to test (default: openai/gpt-4o-2024-11-20)"
    )
    
    parser.add_argument(
        "--tests",
        type=str,
        help="Test selection (e.g., '1', '1,3,5', '1-3', '1,3,7-10')"
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
        help="Maximum retry attempts (default: 3)"
    )
    
    parser.add_argument(
        "--api-url",
        type=str,
        default="http://localhost:5001",
        help="Backend API base URL (default: http://localhost:5001)"
    )
    
    parser.add_argument(
        "--list-models",
        action="store_true",
        help="List suggested models and check backend status"
    )
    
    args = parser.parse_args()
    
    if args.list_models:
        list_available_models(args.api_url)
        return
    
    # Run the evaluation
    results = run_evaluation_via_api(
        model_id=args.model,
        number_of_runs=args.runs,
        max_retries=args.retries,
        test_selection=args.tests,
        api_base_url=args.api_url
    )
    
    # Display results
    display_results(results)

if __name__ == "__main__":
    main() 