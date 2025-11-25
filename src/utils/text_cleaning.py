"""
Text Cleaning Utilities for PDBot
==================================
Removes OCR artifacts, normalizes text, and prepares content for embedding.
"""

import re
from typing import List

def clean_ocr_artifacts(text: str) -> str:
    """
    Remove OCR garbage from text BEFORE embedding.
    
    Fixes:
    - Rs. [4] → Rs.
    - [5] billion → billion
    - [X] → removed
    - Multiple spaces → single space
    
    Args:
        text: Raw text with potential OCR artifacts
        
    Returns:
        Cleaned text ready for embedding
    """
    if not text:
        return ""
    
    # Remove Rs. [digit] patterns
    text = re.sub(r"Rs\.\s*\[\d+\]", "Rs.", text)
    
    # Remove standalone [digit] patterns
    text = re.sub(r"\[\d+\]", "", text)
    
    # Remove [X] patterns
    text = re.sub(r"\[X\]", "", text)
    
    # Remove [p.X] artifacts
    text = re.sub(r"\[p\.\s*\d+\]", "", text)
    
    # Remove [p.X not specified] artifacts
    text = re.sub(r"\[p\.\s*X\s+not\s+specified\]", "", text, flags=re.IGNORECASE)
    
    # Normalize multiple spaces to single space
    text = re.sub(r" +", " ", text)
    
    # Remove leading/trailing whitespace
    text = text.strip()
    
    return text


def sentence_tokenize(text: str) -> List[str]:
    """
    Split text into sentences using NLTK punkt tokenizer.
    Fallback to simple regex if NLTK unavailable.
    
    Args:
        text: Text to split into sentences
        
    Returns:
        List of sentence strings
    """
    try:
        import nltk
        # Try to use punkt tokenizer if available
        try:
            sentences = nltk.sent_tokenize(text)
            return sentences
        except LookupError:
            # Download punkt if not available
            try:
                nltk.download('punkt', quiet=True)
                nltk.download('punkt_tab', quiet=True)
                sentences = nltk.sent_tokenize(text)
                return sentences
            except Exception:
                # Fall through to regex fallback
                pass
    except ImportError:
        pass
    
    # Fallback: Simple regex-based sentence splitting
    # Split on period, exclamation, question mark followed by space and capital letter
    sentences = re.split(r'(?<=[.!?])\s+(?=[A-Z])', text)
    return [s.strip() for s in sentences if s.strip()]


def create_sentence_chunks(sentences: List[str], sentences_per_chunk: int = 3, 
                          max_chars: int = 450, min_chars: int = 100) -> List[str]:
    """
    Group sentences into chunks of 2-3 sentences each.
    
    Args:
        sentences: List of sentence strings
        sentences_per_chunk: Target number of sentences per chunk (default: 3)
        max_chars: Maximum characters per chunk (default: 450)
        min_chars: Minimum characters per chunk to avoid tiny fragments (default: 100)
        
    Returns:
        List of chunk strings
    """
    chunks = []
    i = 0
    
    while i < len(sentences):
        # Start with target number of sentences
        chunk_sentences = []
        chunk_text = ""
        
        # Try to build a chunk
        for j in range(sentences_per_chunk):
            if i + j >= len(sentences):
                break
                
            candidate = sentences[i + j]
            potential_chunk = chunk_text + " " + candidate if chunk_text else candidate
            
            # Check if adding this sentence exceeds max_chars
            if len(potential_chunk) > max_chars and chunk_text:
                # Don't add this sentence, chunk is complete
                break
            
            chunk_sentences.append(candidate)
            chunk_text = potential_chunk
        
        # Only add chunk if it meets minimum size
        if chunk_text and len(chunk_text) >= min_chars:
            chunks.append(chunk_text.strip())
        elif chunk_text:
            # If too small and not last chunk, try to merge with next
            if i + len(chunk_sentences) < len(sentences):
                next_sent = sentences[i + len(chunk_sentences)]
                merged = chunk_text + " " + next_sent
                if len(merged) <= max_chars:
                    chunks.append(merged.strip())
                    chunk_sentences.append(next_sent)
                else:
                    # Can't merge, add as is
                    chunks.append(chunk_text.strip())
            else:
                # Last chunk, add as is
                chunks.append(chunk_text.strip())
        
        # Move to next unprocessed sentence
        i += max(1, len(chunk_sentences))
    
    return chunks


def normalize_whitespace(text: str) -> str:
    """
    Normalize whitespace in text.
    
    Args:
        text: Text with irregular whitespace
        
    Returns:
        Text with normalized whitespace
    """
    # Replace tabs and multiple spaces with single space
    text = re.sub(r'[\t ]+', ' ', text)
    
    # Replace multiple newlines with double newline (paragraph break)
    text = re.sub(r'\n{3,}', '\n\n', text)
    
    # Remove leading/trailing whitespace from each line
    lines = [line.strip() for line in text.split('\n')]
    text = '\n'.join(lines)
    
    return text.strip()


def clean_chunk_for_embedding(text: str) -> str:
    """
    Complete cleaning pipeline for a text chunk before embedding.
    
    Pipeline:
    1. Remove OCR artifacts
    2. Normalize whitespace
    3. Final cleanup
    
    Args:
        text: Raw chunk text
        
    Returns:
        Cleaned text ready for embedding
    """
    # Step 1: OCR artifacts
    text = clean_ocr_artifacts(text)
    
    # Step 2: Whitespace
    text = normalize_whitespace(text)
    
    # Step 3: Final cleanup
    text = text.strip()
    
    return text
