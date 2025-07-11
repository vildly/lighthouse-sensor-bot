import re

def extract_answer_for_evaluation(response):
    """Extract the answer from the model's response for evaluation purposes."""
    
    # Remove any "Agent Reasoning and Response:" prefix first
    if "Agent Reasoning and Response:" in response:
        response = response.split("Agent Reasoning and Response:")[1].strip()
    
    # First, try to find the VERY LAST sentence that looks like a final answer
    # This handles cases where the answer is just the last line after thinking blocks
    last_sentence_patterns = [
        # Look for final sentences with "is approximately", "is about", etc.
        r".*(?:is approximately|is about|equals?|totals?|average[^.]*is)\s+([^.]+)\.\s*$",
        # Look for sentences ending with units (nautical miles, knots, etc.)
        r".*(\d+(?:\.\d+)?\s*(?:nautical miles?|knots?|km/h|mph|hours?|minutes?)[^.]*)\.\s*$",
        # Look for any final sentence with numbers
        r".*(\d+(?:\.\d+)?[^.]*)\.\s*$",
    ]
    
    for pattern in last_sentence_patterns:
        matches = re.findall(pattern, response, re.DOTALL | re.IGNORECASE)
        if matches:
            final_answer = matches[-1].strip()
            # Ensure it's substantial and looks like an answer
            if len(final_answer) > 10 and any(char.isdigit() for char in final_answer):
                return final_answer
    
    # Try structured section patterns (for well-formatted responses)
    patterns = [
        # Look for "## Answer" section (most specific)
        r"## Answer\s*(.*?)(?=\s*##|$)",
        # Look for "### Answer" section
        r"### Answer\s*(.*?)(?=\s*###|$)", 
        # Look for "Answer:" at start of line
        r"^Answer:\s*(.*?)(?=\n\n|\n[A-Z]|\n#|$)",
        # Look for any section with "Answer" in header
        r"(?:###|##)\s*.*?Answer.*?\s*(.*?)(?=\s*(?:###|##)|$)",
        # Look for "Conclusion:" section (very common)
        r"(?:###|##)?\s*Conclusion:\s*(.*?)(?=\n\n|\n[A-Z]|\n#|$)",
        # Look for "Key findings:" or similar
        r"(?:Key findings?|Summary):\s*(.*?)(?=\n\n|\n[A-Z]|\n#|$)",
        # Look for content after "Based on the analysis:" 
        r"Based on (?:the )?(?:analysis|data):\s*(.*?)(?=\n\n|\n[A-Z]|\n#|$)",
    ]
    
    for pattern in patterns:
        matches = re.findall(pattern, response, re.DOTALL | re.IGNORECASE | re.MULTILINE)
        if matches:
            clean_answer = matches[-1].strip()  # Use the last match
            if clean_answer and len(clean_answer) > 20:  # Ensure it's substantial
                # Clean up the answer
                clean_answer = re.sub(r"^###\s*.*?\n", "", clean_answer, flags=re.MULTILINE)
                clean_answer = re.sub(r"^\*\*.*?\*\*\s*\n", "", clean_answer, flags=re.MULTILINE)
                return clean_answer.strip()
    
    # If no structured answer found, try to extract the main content
    # Split on common analysis headers and take the last substantial part
    analysis_headers = [
        "## Analysis", "### Analysis", "## Summary", "### Summary",
        "## Conclusion", "### Conclusion", "## Results", "### Results"
    ]
    
    for header in analysis_headers:
        if header in response:
            parts = response.split(header)
            if len(parts) > 1:
                potential_answer = parts[-1].strip()
                if len(potential_answer) > 50:  # Ensure it's substantial
                    # Clean up headers and return first paragraph or two
                    lines = potential_answer.split('\n')
                    clean_lines = []
                    for line in lines:
                        line = line.strip()
                        if line and not line.startswith('#') and not line.startswith('```'):
                            clean_lines.append(line)
                        if len('\n'.join(clean_lines)) > 200:  # Limit length
                            break
                    
                    if clean_lines:
                        return '\n'.join(clean_lines)
    
    # Extract the LAST substantial content (after all thinking/running blocks)
    # Clean up the response by removing thinking blocks and running commands
    cleaned_response = response
    
    # Remove thinking blocks
    cleaned_response = re.sub(r'<thinking>.*?</thinking>', '', cleaned_response, flags=re.DOTALL)
    
    # Remove running commands but keep their context
    cleaned_response = re.sub(r'Running: [^\n]+\n?', '', cleaned_response)
    
    # Split into lines and find the last substantial content
    lines = cleaned_response.strip().split('\n')
    substantial_lines = []
    
    # Process from the end to find the last meaningful content
    for line in reversed(lines):
        line = line.strip()
        
        # Skip empty lines, headers, and metadata
        if (not line or 
            line.startswith('#') or 
            line.startswith('Query:') or 
            line.startswith('Question:') or
            line.startswith('Response:') or
            line.startswith('Model:') or
            len(line) < 10):
            continue
        
        # Found substantial content
        substantial_lines.insert(0, line)
        
        # If we have a good answer (with numbers or key terms), return it
        if (len(' '.join(substantial_lines)) > 20 and 
            (any(char.isdigit() for char in line) or 
             any(word in line.lower() for word in ['average', 'speed', 'total', 'approximately', 'about']))):
            return ' '.join(substantial_lines)
        
        # Don't get too much content
        if len(substantial_lines) > 3:
            break
    
    # If we found substantial lines, return them
    if substantial_lines:
        return ' '.join(substantial_lines)
    
    # If all extraction fails, return empty string to differentiate from full response
    return ""