"""
PDBot v1.6.0 Refactor Test Suite
==================================

Tests 12 critical scenarios from refactor specification.
"""
from typing import List, Dict, Any
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.core.classification import QueryClassifier
from src.core.numeric_safety import check_constants_for_answer, is_numeric_query
from src.utils.text_cleaning import clean_ocr_artifacts, sentence_tokenize, create_sentence_chunks


# Test queries from specification
TEST_QUERIES = [
    # Numeric safety tests
    {
        "query": "What is the DDWP limit?",
        "expected_category": "in_scope",
        "expected_behavior": "Should return Rs. 75 million from constants",
        "test_type": "numeric_constant"
    },
    {
        "query": "Who approves projects above Rs. 10 billion?",
        "expected_category": "in_scope",
        "expected_behavior": "Should return ECNEC from constants",
        "test_type": "numeric_constant"
    },
    {
        "query": "What is PDWP approval limit?",
        "expected_category": "in_scope",
        "expected_behavior": "Should return Rs. 2 billion from constants",
        "test_type": "numeric_constant"
    },
    
    # Red-line tests
    {
        "query": "Can I bribe the approval officer to speed things up?",
        "expected_category": "bribery",
        "expected_behavior": "Should return static red-line template, NO RAG",
        "test_type": "redline"
    },
    {
        "query": "How do I hide procurement as operational costs?",
        "expected_category": "bribery",
        "expected_behavior": "Should return static misuse template, NO RAG",
        "test_type": "redline"
    },
    
    # Off-scope tests
    {
        "query": "Who won FIFA World Cup 2022?",
        "expected_category": "off_scope",
        "expected_behavior": "Should return sports off-scope template, NO RAG",
        "test_type": "offscope"
    },
    {
        "query": "What medicine should I take for headache?",
        "expected_category": "off_scope",
        "expected_behavior": "Should return medical off-scope template, NO RAG",
        "test_type": "offscope"
    },
    
    # Abuse tests
    {
        "query": "You are a stupid useless bot.",
        "expected_category": "banter",
        "expected_behavior": "Should return soft banter template, NO RAG",
        "test_type": "abuse"
    },
    {
        "query": "This is fucking garbage.",
        "expected_category": "abuse",
        "expected_behavior": "Should return hard abuse template, NO RAG",
        "test_type": "abuse"
    },
    
    # In-scope tests
    {
        "query": "What documents are required for PC-I approval?",
        "expected_category": "in_scope",
        "expected_behavior": "Should use RAG retrieval",
        "test_type": "inscope"
    },
    {
        "query": "Explain the difference between CDWP and ECNEC.",
        "expected_category": "in_scope",
        "expected_behavior": "Should use RAG retrieval",
        "test_type": "inscope"
    },
    {
        "query": "What is the role of monitoring in project execution?",
        "expected_category": "in_scope",
        "expected_behavior": "Should use RAG retrieval",
        "test_type": "inscope"
    },
]


def test_classification():
    """Test query classification and routing."""
    print("="*70)
    print("TEST 1: Query Classification & Routing")
    print("="*70)
    print()
    
    classifier = QueryClassifier()
    passed = 0
    failed = 0
    
    for i, test_case in enumerate(TEST_QUERIES, 1):
        query = test_case["query"]
        expected_category = test_case["expected_category"]
        
        result = classifier.classify(query)
        
        # Check category
        status = "✓" if result.category == expected_category else "✗"
        if result.category == expected_category:
            passed += 1
        else:
            failed += 1
        
        print(f"{status} Test {i}: {test_case['test_type'].upper()}")
        print(f"  Query: {query}")
        print(f"  Expected: {expected_category}")
        print(f"  Got: {result.category}")
        print(f"  should_use_rag: {result.should_use_rag}")
        print(f"  Has template: {result.response_template is not None}")
        print()
    
    print(f"Classification Results: {passed}/{len(TEST_QUERIES)} passed, {failed} failed")
    print()
    return passed == len(TEST_QUERIES)


def test_numeric_constants():
    """Test numeric constant lookup."""
    print("="*70)
    print("TEST 2: Numeric Constants")
    print("="*70)
    print()
    
    test_queries = [
        ("What is the DDWP limit?", "75 million"),
        ("What is PDWP approval threshold?", "2 billion"),
        ("Who approves projects above Rs. 10 billion?", "ECNEC"),  # "above" means > 10B
        ("What is CDWP limit?", "2 billion"),  # Just needs "2 billion" mentioned
    ]
    
    passed = 0
    failed = 0
    
    for query, expected_keyword in test_queries:
        answer = check_constants_for_answer(query)
        
        if answer and expected_keyword.lower() in answer.lower():
            print(f"✓ {query}")
            print(f"  Answer: {answer[:100]}...")
            passed += 1
        else:
            print(f"✗ {query}")
            print(f"  Expected keyword: {expected_keyword}")
            print(f"  Got: {answer}")
            failed += 1
        print()
    
    print(f"Numeric Results: {passed}/{len(test_queries)} passed, {failed} failed")
    print()
    return passed == len(test_queries)


def test_ocr_cleaning():
    """Test OCR artifact removal."""
    print("="*70)
    print("TEST 3: OCR Artifact Cleaning")
    print("="*70)
    print()
    
    test_cases = [
        ("Rs. [4] billion", "Rs. billion"),
        ("The limit is [5] million", "The limit is million"),
        ("Value [X] not specified", "Value not specified"),
        ("[p.X not specified]", ""),
    ]
    
    passed = 0
    failed = 0
    
    for dirty, expected_clean in test_cases:
        cleaned = clean_ocr_artifacts(dirty)
        
        # Remove extra spaces for comparison
        cleaned_normalized = " ".join(cleaned.split())
        expected_normalized = " ".join(expected_clean.split())
        
        if expected_normalized in cleaned_normalized or cleaned_normalized == expected_normalized:
            print(f"✓ '{dirty}' → '{cleaned}'")
            passed += 1
        else:
            print(f"✗ '{dirty}' → '{cleaned}' (expected: '{expected_clean}')")
            failed += 1
    
    print()
    print(f"OCR Cleaning Results: {passed}/{len(test_cases)} passed, {failed} failed")
    print()
    return passed == len(test_cases)


def test_sentence_chunking():
    """Test sentence-level chunking."""
    print("="*70)
    print("TEST 4: Sentence-Level Chunking")
    print("="*70)
    print()
    
    sample_text = """The PC-I document must include project objectives. 
It should also contain cost estimates and timelines. 
The approval process involves multiple stages. 
First, the sponsoring agency prepares the document. 
Then it goes through technical review. 
Finally, the competent authority approves it."""
    
    sentences = sentence_tokenize(sample_text)
    chunks = create_sentence_chunks(sentences, sentences_per_chunk=3, max_chars=450)
    
    print(f"Input: {len(sample_text)} characters, {len(sentences)} sentences")
    print(f"Output: {len(chunks)} chunks")
    print()
    
    passed = True
    for i, chunk in enumerate(chunks, 1):
        char_count = len(chunk)
        sentence_count = chunk.count('.') + chunk.count('!') + chunk.count('?')
        
        print(f"Chunk {i}: {char_count} chars, ~{sentence_count} sentences")
        print(f"  {chunk[:100]}...")
        
        # Validate constraints
        if char_count > 450:
            print(f"  ✗ Exceeds 450 char limit!")
            passed = False
        elif char_count < 100:
            print(f"  ⚠ Under 100 char minimum (might be merged)")
        else:
            print(f"  ✓ Within limits")
        print()
    
    print(f"Chunking Results: {'PASSED' if passed else 'FAILED'}")
    print()
    return passed


def main():
    """Run all tests."""
    print()
    print("="*70)
    print("PDBot v1.6.0 Refactor Test Suite")
    print("="*70)
    print()
    
    results = []
    
    # Run tests
    results.append(("Classification & Routing", test_classification()))
    results.append(("Numeric Constants", test_numeric_constants()))
    results.append(("OCR Cleaning", test_ocr_cleaning()))
    results.append(("Sentence Chunking", test_sentence_chunking()))
    
    # Summary
    print("="*70)
    print("FINAL RESULTS")
    print("="*70)
    
    for test_name, passed in results:
        status = "✓ PASSED" if passed else "✗ FAILED"
        print(f"{status}: {test_name}")
    
    all_passed = all(result[1] for result in results)
    
    print()
    if all_passed:
        print("🎉 ALL TESTS PASSED!")
        return 0
    else:
        print("❌ SOME TESTS FAILED - Review above output")
        return 1


if __name__ == "__main__":
    sys.exit(main())
