import pandas as pd
import json
from pathlib import Path

def convert_synthetic_to_json():
    # Read the CSV file
    df = pd.read_csv("data/ragas/testset_syntethic.csv")
    
    # Convert DataFrame to list of dictionaries
    test_cases = []
    for _, row in df.iterrows():
        # Convert string representation of list to actual list
        reference_contexts = eval(row['reference_contexts'])
        
        test_case = {
            "user_input": row['user_input'],
            "reference_contexts": reference_contexts,
            "reference": row['reference'],
            "synthesizer_name": row['synthesizer_name']
        }
        test_cases.append(test_case)
    
    # Create test_cases directory if it doesn't exist
    test_cases_dir = Path("app/ragas/test_cases")
    test_cases_dir.mkdir(parents=True, exist_ok=True)
    
    # Write to JSON file
    output_path = test_cases_dir / "synthetic_test_cases.json"
    with open(output_path, "w") as f:
        json.dump(test_cases, f, indent=2)
    
    print(f"Converted synthetic test cases to JSON: {output_path}")

if __name__ == "__main__":
    convert_synthetic_to_json() 