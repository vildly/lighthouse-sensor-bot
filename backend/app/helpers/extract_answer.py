import re

def extract_answer_for_evaluation(response):
    """Extract the answer from the model's response for evaluation purposes."""
    
    # Remove any "Agent Reasoning and Response:" prefix first
    if "Agent Reasoning and Response:" in response:
        response = response.split("Agent Reasoning and Response:")[1].strip()
    
    # Clean up the response by removing LaTeX formatting and artifacts
    cleaned_response = response
    
    # Remove thinking blocks
    cleaned_response = re.sub(r'<thinking>.*?</thinking>', '', cleaned_response, flags=re.DOTALL)
    
    # Remove running commands but keep their context
    cleaned_response = re.sub(r'Running: [^\n]+\n?', '', cleaned_response)
    
    # Remove LaTeX formatting artifacts
    cleaned_response = re.sub(r'\\text\{[^}]*\}', '', cleaned_response)  # Remove \text{...}
    cleaned_response = re.sub(r'\\[a-zA-Z]+\{[^}]*\}', '', cleaned_response)  # Remove other LaTeX commands
    cleaned_response = re.sub(r'\$[^$]*\$', '', cleaned_response)  # Remove inline math
    cleaned_response = re.sub(r'\[[^\]]*\\[^\]]*\]', '', cleaned_response)  # Remove LaTeX brackets with commands
    cleaned_response = re.sub(r'\\times|\\cdot|\\approx|\\geq|\\leq', '', cleaned_response)  # Remove LaTeX operators
    
    # Remove orphaned LaTeX artifacts like "10 , \text{SEK} ]"
    cleaned_response = re.sub(r'\d+\s*,\s*\\text\{[^}]*\}\s*\]', '', cleaned_response)
    cleaned_response = re.sub(r'^\d+\s*,\s*[^a-zA-Z]*$', '', cleaned_response, flags=re.MULTILINE)
    
    # Look for conclusion patterns - prioritize "In conclusion" statements
    conclusion_patterns = [
        r"In conclusion,\s*([^.]*\.)",
        r"Therefore,\s*([^.]*\.)",
        r"The (?:answer|result) is\s*([^.]*\.)",
        r"Based on (?:the )?(?:analysis|data|calculations?),\s*([^.]*\.)",
    ]
    
    for pattern in conclusion_patterns:
        matches = re.findall(pattern, cleaned_response, re.DOTALL | re.IGNORECASE)
        if matches:
            final_answer = matches[-1].strip()
            # Clean up any remaining artifacts
            final_answer = re.sub(r'^\s*[,\]\}\)]+\s*', '', final_answer)  # Remove leading punctuation
            final_answer = re.sub(r'\s+', ' ', final_answer)  # Normalize whitespace
            if len(final_answer) > 10 and any(char.isdigit() for char in final_answer):
                return f"In conclusion, {final_answer}"
    
    # Look for sentences that end with specific units or values
    value_patterns = [
        r"([^.]*(?:\d+(?:,\d{3})*(?:\.\d+)?)\s*(?:SEK|EUR|USD|liters?|nautical miles?|knots?|km/h|mph|hours?|minutes?|ferries?|vessels?)[^.]*)\.\s*$",
        r"([^.]*is\s*(?:\d+(?:,\d{3})*(?:\.\d+)?)[^.]*)\.\s*$",
    ]
    
    for pattern in value_patterns:
        matches = re.findall(pattern, cleaned_response, re.DOTALL | re.IGNORECASE)
        if matches:
            final_answer = matches[-1].strip()
            # Clean up any remaining artifacts
            final_answer = re.sub(r'^\s*[,\]\}\)]+\s*', '', final_answer)
            final_answer = re.sub(r'\s+', ' ', final_answer)
            if len(final_answer) > 10:
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
    ]
    
    for pattern in patterns:
        matches = re.findall(pattern, cleaned_response, re.DOTALL | re.IGNORECASE | re.MULTILINE)
        if matches:
            clean_answer = matches[-1].strip()  # Use the last match
            if clean_answer and len(clean_answer) > 20:  # Ensure it's substantial
                # Clean up the answer
                clean_answer = re.sub(r"^###\s*.*?\n", "", clean_answer, flags=re.MULTILINE)
                clean_answer = re.sub(r"^\*\*.*?\*\*\s*\n", "", clean_answer, flags=re.MULTILINE)
                clean_answer = re.sub(r'^\s*[,\]\}\)]+\s*', '', clean_answer)
                clean_answer = re.sub(r'\s+', ' ', clean_answer)
                return clean_answer.strip()
    
    # Extract the LAST meaningful sentence from the response
    # Split into sentences and work backwards
    sentences = re.split(r'[.!?]+', cleaned_response)
    
    for sentence in reversed(sentences):
        sentence = sentence.strip()
        
        # Skip empty sentences, headers, and artifacts
        if (not sentence or 
            len(sentence) < 15 or
            sentence.startswith('#') or 
            sentence.startswith('Query:') or 
            sentence.startswith('Question:') or
            sentence.startswith('Response:') or
            sentence.startswith('Model:') or
            re.match(r'^\d+\s*,?\s*$', sentence) or  # Skip pure numbers
            '\\' in sentence):  # Skip sentences with LaTeX
            continue
        
        # If we find a sentence with meaningful content, return it
        if (any(char.isdigit() for char in sentence) or 
            any(word in sentence.lower() for word in ['total', 'average', 'approximately', 'about', 'conclusion', 'result'])):
            return sentence.strip()
    
    # If all extraction fails, return empty string to differentiate from full response
    return ""


def is_ferry_related_question(question: str) -> bool:
    """
    Validate if a question is related to ferry/maritime operations data.
    
    Args:
        question: The user's question
        
    Returns:
        bool: True if question appears to be ferry-related, False otherwise
    """
    if not question or len(question.strip()) < 3:
        return False
    
    question_lower = question.lower().strip()
    
    # Ferry/Maritime related keywords - if found, question is likely relevant
    ferry_keywords = [
        'ferry', 'ferries', 'vessel', 'ship', 'boat', 'maritime', 'marine',
        'fragancia', 'jupiter', 'merkurius', 'nina', 'yxlan',  # Original 5 ferries
        'skidbladner', 'marie', 'capella', 'linda', 'sedna', 'ebba brahe',  # Additional 6 ferries
        'fuel', 'consumption', 'efficiency', 'speed', 'route', 'trip', 'voyage',
        'passenger', 'vehicle', 'cargo', 'load', 'capacity', 'terminal',
        'nautical', 'knots', 'distance', 'outbound', 'inbound', 'departure',
        'arrival', 'schedule', 'timetable', 'operations', 'traffic',
        'ljusteröleden', 'furusundsleden', 'blidoleden', 'vaxholm',  # Route names
        'färjerederiet', 'pontos'  # Company/system names
    ]
    
    # Check if question contains ferry-related keywords
    if any(keyword in question_lower for keyword in ferry_keywords):
        return True
    
    # Data analysis keywords that might be relevant in context
    data_keywords = [
        'analyze', 'analysis', 'compare', 'comparison', 'average', 'total',
        'count', 'how many', 'which', 'what', 'when', 'where', 'trend',
        'pattern', 'correlation', 'efficiency', 'performance', 'statistics',
        'data', 'database', 'table', 'record', 'metric'
    ]
    
    # If question has data analysis terms, it might be relevant - be more permissive
    if any(keyword in question_lower for keyword in data_keywords):
        # But exclude obvious off-topic questions
        off_topic_indicators = [
            'weather', 'temperature', 'rain', 'snow', 'wind',
            'fish', 'animal', 'bird', 'plant', 'tree',
            'time', 'clock', 'date', 'calendar', 'today', 'tomorrow', 'yesterday',
            'food', 'recipe', 'cooking', 'restaurant',
            'movie', 'music', 'game', 'sport', 'football', 'soccer',
            'politics', 'government', 'election', 'president',
            'health', 'medicine', 'doctor', 'hospital',
            'school', 'university', 'education', 'student',
            'programming', 'software', 'computer', 'internet', 'website',
            'finance', 'money', 'bank', 'stock', 'investment',
            'car', 'automobile', 'truck', 'plane', 'airplane', 'train',
            'space', 'planet', 'star', 'universe', 'astronomy'
        ]
        
        if any(indicator in question_lower for indicator in off_topic_indicators):
            return False
        
        return True
    
    # If no ferry keywords and no data analysis context, likely off-topic
    return False