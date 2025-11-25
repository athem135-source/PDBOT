"""
PDBot v1.7.0 - Quick Validation Test Suite
===========================================

Run this after starting Streamlit app to validate all fixes.

Test Categories:
1. Over-answering fixed (≤80 words)
2. Citation spam fixed (≤3 sources)
3. Dynamic retrieval (no hardcoding)
4. Garbage filtering (no tables/annexures)
5. Classification regression (red-line/off-scope)

Usage:
    python test_v1.7.0.py
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

# Test queries
TEST_QUERIES = {
    "over_answering": [
        ("What is the DDWP approval limit?", "DDWP", 80),
        ("What is included in PC-I?", "PC-I", 80),
        ("Define umbrella project.", "umbrella", 80),
        ("What is the role of ECNEC?", "ECNEC", 80),
    ],
    "citation_spam": [
        ("What documents are required for PC-I approval?", 3),
        ("What is the PDWP limit?", 3),
        ("How is land acquisition handled?", 3),
    ],
    "dynamic_retrieval": [
        ("What is the DDWP limit?", "must retrieve from RAG, not hardcoded"),
        ("Who approves projects above Rs. 10 billion?", "must retrieve from RAG"),
        ("What is CDWP threshold?", "must retrieve from RAG"),
    ],
    "garbage_filtering": [
        ("What is ECNEC composition?", ["NO climate tables", "NO iPAS", "NO annexures"]),
        ("What is PC-I purpose?", ["NO notifications", "NO list of figures"]),
    ],
    "classification": [
        ("Can I bribe the officer?", "static template, NO RAG"),
        ("Who won FIFA 2022?", "off-scope, NO RAG"),
        ("How to make biryani?", "off-scope, NO RAG"),
        ("You are stupid.", "banter, NO RAG"),
    ],
}


def count_words(text: str) -> int:
    """Count words in text."""
    return len(text.split())


def count_citations(text: str) -> int:
    """Count number of citations in format '[1] Manual...'"""
    import re
    return len(re.findall(r'\[\d+\]\s+Manual', text))


def test_over_answering():
    """Test that answers are ≤80 words."""
    print("\n" + "="*70)
    print("TEST 1: Over-Answering Fixed (≤80 words)")
    print("="*70)
    
    for query, expected_keyword, max_words in TEST_QUERIES["over_answering"]:
        print(f"\nQuery: {query}")
        print(f"Expected: Contains '{expected_keyword}', ≤{max_words} words")
        print("⚠️  MANUAL TEST REQUIRED - Run in Streamlit app")
        print("   Check: Word count, no extra paragraphs")


def test_citation_spam():
    """Test that citations are ≤3 sources."""
    print("\n" + "="*70)
    print("TEST 2: Citation Spam Fixed (≤3 sources)")
    print("="*70)
    
    for query, max_citations in TEST_QUERIES["citation_spam"]:
        print(f"\nQuery: {query}")
        print(f"Expected: ≤{max_citations} citations in 'Sources:' section")
        print("⚠️  MANUAL TEST REQUIRED - Run in Streamlit app")
        print("   Check: Count [1], [2], [3]... should stop at [3]")


def test_dynamic_retrieval():
    """Test that values come from RAG, not hardcoded."""
    print("\n" + "="*70)
    print("TEST 3: Dynamic Retrieval (No Hardcoding)")
    print("="*70)
    
    for query, expected_behavior in TEST_QUERIES["dynamic_retrieval"]:
        print(f"\nQuery: {query}")
        print(f"Expected: {expected_behavior}")
        print("⚠️  MANUAL TEST REQUIRED - Run in Streamlit app")
        print("   Check: Answer should vary based on retrieved chunks")
        print("   Should NOT be instant (hardcoded) response")


def test_garbage_filtering():
    """Test that garbage chunks are filtered out."""
    print("\n" + "="*70)
    print("TEST 4: Garbage Filtering (No Tables/Annexures)")
    print("="*70)
    
    for query, forbidden_content in TEST_QUERIES["garbage_filtering"]:
        print(f"\nQuery: {query}")
        print(f"Expected: {', '.join(forbidden_content)}")
        print("⚠️  MANUAL TEST REQUIRED - Run in Streamlit app")
        print("   Check: Answer should NOT contain any forbidden content")


def test_classification():
    """Test classification routing (regression test)."""
    print("\n" + "="*70)
    print("TEST 5: Classification (Regression)")
    print("="*70)
    
    for query, expected_behavior in TEST_QUERIES["classification"]:
        print(f"\nQuery: {query}")
        print(f"Expected: {expected_behavior}")
        print("⚠️  MANUAL TEST REQUIRED - Run in Streamlit app")
        print("   Check: Should return template immediately, no retrieval delay")


def print_summary():
    """Print test summary and instructions."""
    print("\n" + "="*70)
    print("TEST SUMMARY")
    print("="*70)
    
    print("\n📊 Total Test Queries: 18")
    print("   - Over-answering: 4 queries")
    print("   - Citation spam: 3 queries")
    print("   - Dynamic retrieval: 3 queries")
    print("   - Garbage filtering: 2 queries")
    print("   - Classification: 4 queries")
    
    print("\n🎯 Success Criteria:")
    print("   ✅ ALL answers ≤80 words")
    print("   ✅ ALL citations ≤3 sources")
    print("   ✅ NO hardcoded values (retrieval delay present)")
    print("   ✅ NO garbage content (tables, annexures, iPAS)")
    print("   ✅ Red-line/off-scope return templates instantly")
    
    print("\n🚀 How to Test:")
    print("   1. Start Streamlit: streamlit run .\\src\\app.py")
    print("   2. For each query above, paste into chat")
    print("   3. Validate answer meets criteria")
    print("   4. Record results in REFACTOR_v1.7.0_SUMMARY.md")
    
    print("\n📝 Record Results:")
    print("   Update 'Test Result' column in REFACTOR_v1.7.0_SUMMARY.md")
    print("   - ✅ PASS: Meets criteria")
    print("   - ❌ FAIL: Document issue")
    print("   - ⚠️  PARTIAL: Note deviation")


if __name__ == "__main__":
    print("\n" + "="*70)
    print("PDBot v1.7.0 - VALIDATION TEST SUITE")
    print("="*70)
    print("\n⚠️  This is a MANUAL test guide.")
    print("   Tests must be run in Streamlit app (http://localhost:8501)")
    print("   This script provides test queries and validation criteria.")
    
    test_over_answering()
    test_citation_spam()
    test_dynamic_retrieval()
    test_garbage_filtering()
    test_classification()
    print_summary()
    
    print("\n✅ Test guide generated successfully!")
    print("   Start Streamlit and begin testing.\n")
