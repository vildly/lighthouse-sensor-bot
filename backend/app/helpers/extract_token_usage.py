def extract_token_usage(response):
    """Extract token usage from a RunResponse object."""
    token_usage = None
    if hasattr(response, 'metrics') and response.metrics:
        prompt_tokens = sum(response.metrics.get('prompt_tokens', [0]))
        completion_tokens = sum(response.metrics.get('completion_tokens', [0]))
        total_tokens = sum(response.metrics.get('total_tokens', [0]))
        
        token_usage = {
            'prompt_tokens': prompt_tokens,
            'completion_tokens': completion_tokens,
            'total_tokens': total_tokens
        }
    return token_usage