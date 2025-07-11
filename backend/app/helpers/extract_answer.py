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
    
    # PRIORITY 1: Extract entire content from CONCLUSION section
    conclusion_match = re.search(r'\bCONCLUSION\b\s*(.*?)(?=\n\s*\n|\n\s*[A-Z]{2,}|\Z)', cleaned_response, re.DOTALL | re.IGNORECASE)
    if conclusion_match:
        conclusion_content = conclusion_match.group(1).strip()
        if conclusion_content and len(conclusion_content) > 20:
            # Clean up the content
            conclusion_content = re.sub(r'\s+', ' ', conclusion_content)
            # Remove any leading/trailing punctuation artifacts
            conclusion_content = re.sub(r'^\s*[,\]\}\)]+\s*', '', conclusion_content)
            conclusion_content = re.sub(r'\s*[,\[\{\(]+\s*$', '', conclusion_content)
            if not conclusion_content.endswith('.'):
                conclusion_content += '.'
            return conclusion_content
    
    # PRIORITY 2: Extract entire content from RESPONSE section
    if "RESPONSE" in cleaned_response:
        # Find the RESPONSE section and extract all content after it
        response_split = re.split(r'\b(?:RESPONSE|Response)\b', cleaned_response, flags=re.IGNORECASE)
        if len(response_split) > 1:
            response_section = response_split[-1].strip()  # Get the last RESPONSE section
            
            # First try to find a CONCLUSION subsection within RESPONSE
            conclusion_in_response = re.search(r'\bCONCLUSION\b\s*(.*?)(?=\n\s*\n|\n\s*[A-Z]{2,}|\Z)', response_section, re.DOTALL | re.IGNORECASE)
            if conclusion_in_response:
                conclusion_content = conclusion_in_response.group(1).strip()
                if conclusion_content and len(conclusion_content) > 20:
                    conclusion_content = re.sub(r'\s+', ' ', conclusion_content)
                    conclusion_content = re.sub(r'^\s*[,\]\}\)]+\s*', '', conclusion_content)
                    if not conclusion_content.endswith('.'):
                        conclusion_content += '.'
                    return conclusion_content
            
            # Look for final conclusion patterns within the RESPONSE section
            conclusion_in_response_patterns = [
                r"(In conclusion[:\s]*[^.]*?(?:\d+(?:\.\d+)?)?[^.]*?)\.(?!\d)",
                r"(Based on (?:the )?(?:analysis|data|calculations?)[:\s]*[^.]*?(?:\d+(?:\.\d+)?)?[^.]*?)\.(?!\d)",
                r"(Therefore[:\s]*[^.]*?(?:\d+(?:\.\d+)?)?[^.]*?)\.(?!\d)",
                r"(The (?:answer|result) is[:\s]*[^.]*?(?:\d+(?:\.\d+)?)?[^.]*?)\.(?!\d)",
            ]
            
            # Try to find complete conclusion paragraphs instead of just sentences
            for pattern in conclusion_in_response_patterns:
                matches = re.findall(pattern, response_section, re.DOTALL | re.IGNORECASE)
                if matches:
                    # Look for the pattern that leads to the largest/most complete match
                    for match in reversed(matches):  # Start from the last match
                        conclusion_text = match.strip()
                        
                        # Try to extend backwards to get full paragraph context
                        # Find the position of this conclusion in the response_section
                        match_pos = response_section.rfind(conclusion_text)
                        if match_pos > 0:
                            # Look backwards to find the start of the paragraph
                            before_text = response_section[:match_pos].rstrip()
                            
                            # Find sentences that lead into this conclusion
                            sentences_before = re.findall(r'([^.!?]*[.!?])\s*$', before_text)
                            if sentences_before:
                                prev_sentence = sentences_before[-1].strip()
                                # If the previous sentence is substantial and related, include it
                                if (len(prev_sentence) > 20 and 
                                    any(word in prev_sentence.lower() for word in ['analysis', 'data', 'available', 'no', 'query', 'table', 'route'])):
                                    full_conclusion = f"{prev_sentence} {conclusion_text}."
                                    full_conclusion = re.sub(r'\s+', ' ', full_conclusion)
                                    return full_conclusion
                        
                        # If no good context found, return the conclusion with proper ending
                        conclusion_text = re.sub(r'\s+', ' ', conclusion_text)
                        if not conclusion_text.endswith('.'):
                            conclusion_text += '.'
                        return conclusion_text
            
            # If no conclusion patterns found, extract the LAST substantial paragraph from RESPONSE section
            # Split by double newlines to get paragraphs
            paragraphs = re.split(r'\n\s*\n', response_section)
            for paragraph in reversed(paragraphs):
                paragraph = paragraph.strip()
                # Skip empty paragraphs and ones that are just numbered lists without conclusions
                if (len(paragraph) > 50 and 
                    not re.match(r'^\d+\.\s', paragraph) and  # Skip numbered list items
                    any(word in paragraph.lower() for word in ['conclusion', 'analysis', 'data', 'therefore', 'based', 'result'])):
                    # Clean up the paragraph
                    paragraph = re.sub(r'\s+', ' ', paragraph)
                    if not paragraph.endswith('.'):
                        paragraph += '.'
                    return paragraph
    
    # Look for conclusion patterns - prioritize "In conclusion" and "Based on" statements
    # Updated patterns to properly capture decimal numbers
    conclusion_patterns = [
        r"In conclusion,\s*([^.]*?(?:\d+(?:\.\d+)?)[^.]*?)\.(?!\d)",  # Updated to not stop at decimal points
        r"Based on (?:the )?(?:analysis|data|calculations?),\s*([^.]*?(?:\d+(?:\.\d+)?)[^.]*?)\.(?!\d)",
        r"Therefore,\s*([^.]*?(?:\d+(?:\.\d+)?)[^.]*?)\.(?!\d)",
        r"The (?:answer|result) is\s*([^.]*?(?:\d+(?:\.\d+)?)[^.]*?)\.(?!\d)",
    ]
    
    for pattern in conclusion_patterns:
        matches = re.findall(pattern, cleaned_response, re.DOTALL | re.IGNORECASE)
        if matches:
            final_answer = matches[-1].strip()
            # Clean up any remaining artifacts
            final_answer = re.sub(r'^\s*[,\]\}\)]+\s*', '', final_answer)  # Remove leading punctuation
            final_answer = re.sub(r'\s+', ' ', final_answer)  # Normalize whitespace
            if len(final_answer) > 10 and any(char.isdigit() for char in final_answer):
                # Determine which conclusion phrase was matched
                if "In conclusion" in cleaned_response and "In conclusion" in pattern:
                    return f"In conclusion, {final_answer}."
                elif "Based on" in cleaned_response and "Based on" in pattern:
                    return f"Based on the analysis, {final_answer}."
        else:
                    return f"{final_answer}."
    
    # Look for sentences that end with specific units or decimal values
    value_patterns = [
        r"([^.]*?(?:\d+(?:,\d{3})*(?:\.\d+)?)\s*(?:SEK|EUR|USD|liters?|nautical miles?|knots?|km/h|mph|hours?|minutes?|ferries?|vessels?)[^.]*?)\.(?!\d)",
        r"([^.]*?is\s*(?:approximately\s*)?(?:\d+(?:,\d{3})*(?:\.\d+)?)[^.]*?)\.(?!\d)",
        r"([^.]*?(?:approximately|about)\s*(?:\d+(?:,\d{3})*(?:\.\d+)?)[^.]*?)\.(?!\d)",
    ]
    
    for pattern in value_patterns:
        matches = re.findall(pattern, cleaned_response, re.DOTALL | re.IGNORECASE)
        if matches:
            final_answer = matches[-1].strip()
            # Clean up any remaining artifacts
            final_answer = re.sub(r'^\s*[,\]\}\)]+\s*', '', final_answer)
            final_answer = re.sub(r'\s+', ' ', final_answer)
            if len(final_answer) > 10:
                return f"{final_answer}."
    
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
    # Split into sentences more carefully to preserve decimal numbers
    sentences = re.split(r'\.(?!\d)(?:\s|$)', cleaned_response)  # Don't split on decimal points
    
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
            # Ensure it ends with a period if it doesn't already
            if not sentence.endswith('.'):
                sentence += '.'
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