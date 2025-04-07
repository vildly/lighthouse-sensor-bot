import re

def extract_answer_for_evaluation(response):
    """Extract the answer from the model's response for evaluation purposes."""
    
    # Extract the answer section using regex - get the LAST answer section
    answer_sections = re.findall(
        r"## Answer\s*(.*?)(?=\s*##|$)", response, re.DOTALL
    )
    if answer_sections:
        clean_answer = answer_sections[-1].strip()  # Use the last answer section
    else:
        # Check if there's an "Agent Reasoning and Response:" prefix
        if "Agent Reasoning and Response:" in response:
            response = response.split("Agent Reasoning and Response:")[1].strip()
        
        # Try to find any section that looks like an answer
        answer_match = re.search(r"(?:###|##)\s*(?:Answer|Key Details.*?)\s*(.*?)(?=\s*(?:###|##)|$)", response, re.DOTALL)
        if answer_match:
            clean_answer = answer_match.group(1).strip()
        else:
            # Fallback: Split on the Analysis section header to get just the answer
            parts = response.split("## Analysis")
            clean_answer = parts[-1].strip() if len(parts) > 1 else response.strip()
    
    # Remove any remaining markdown headers
    clean_answer = re.sub(r"^###\s*.*?\n", "", clean_answer, flags=re.MULTILINE)
    
    # If we still don't have a clean answer, use the original response
    if not clean_answer or clean_answer.isspace():
        clean_answer = response
    
    return clean_answer