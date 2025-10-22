"""
Response filtering utilities for cleaning AI model outputs.
"""

import re


def clean_thinking_tags(response: str) -> str:
    """
    Remove <thinking> tags and their content from AI responses.
    
    Args:
        response (str): Raw response from AI model
        
    Returns:
        str: Cleaned response without thinking tags
    """
    if not response:
        return response
    
    # Remove <thinking>...</thinking> blocks (including multiline)
    cleaned = re.sub(r'<thinking>.*?</thinking>', '', response, flags=re.DOTALL | re.IGNORECASE)
    
    # Clean up any extra whitespace left behind
    cleaned = re.sub(r'\n\s*\n\s*\n', '\n\n', cleaned)  # Multiple newlines to double
    cleaned = cleaned.strip()
    
    return cleaned


def clean_xml_artifacts(response: str) -> str:
    """
    Remove common XML artifacts that might leak into responses.
    
    Args:
        response (str): Raw response from AI model
        
    Returns:
        str: Cleaned response without XML artifacts
    """
    if not response:
        return response
    
    # Remove various XML-like tags that might appear
    patterns = [
        r'<thinking>.*?</thinking>',
        r'<reasoning>.*?</reasoning>',
        r'<analysis>.*?</analysis>',
        r'<internal>.*?</internal>',
        r'<scratch>.*?</scratch>',
    ]
    
    cleaned = response
    for pattern in patterns:
        cleaned = re.sub(pattern, '', cleaned, flags=re.DOTALL | re.IGNORECASE)
    
    # Clean up whitespace
    cleaned = re.sub(r'\n\s*\n\s*\n', '\n\n', cleaned)
    cleaned = cleaned.strip()
    
    return cleaned


def clean_user_ids(response: str) -> str:
    """
    Remove user ID mentions from responses.
    
    Args:
        response (str): Raw response from AI model
        
    Returns:
        str: Cleaned response without user ID mentions
    """
    if not response:
        return response
    
    # Remove common user ID patterns
    patterns = [
        r'- \*\*User ID:\*\* [^\n]*\n?',  # - **User ID:** user_111
        r'User ID: [^\n]*\n?',            # User ID: user_111
        r'user_id: [^\n]*\n?',            # user_id: user_111
        r'User: [^\n]*\n?',               # User: user_111
    ]
    
    cleaned = response
    for pattern in patterns:
        cleaned = re.sub(pattern, '', cleaned, flags=re.IGNORECASE)
    
    return cleaned


def clean_response(response: str) -> str:
    """
    Main function to clean AI responses of unwanted artifacts.
    
    Args:
        response (str): Raw response from AI model
        
    Returns:
        str: Cleaned response ready for frontend
    """
    if not response:
        return response
    
    # Apply all cleaning functions
    cleaned = clean_thinking_tags(response)
    cleaned = clean_xml_artifacts(cleaned)
    cleaned = clean_user_ids(cleaned)
    
    # Final cleanup of extra whitespace
    cleaned = re.sub(r'\n\s*\n\s*\n', '\n\n', cleaned)
    cleaned = cleaned.strip()
    
    return cleaned