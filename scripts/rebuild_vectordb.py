"""
Refactored RAG Ingestion Script for PDBot v1.6.0
================================================

CRITICAL FIXES IMPLEMENTED:
1. ✅ Sentence-level chunking (2-3 sentences per chunk, 350-450 chars)
2. ✅ OCR artifact cleaning BEFORE embedding
3. ✅ Improved metadata (page, section, type)
4. ✅ Rebuild vector DB from scratch

Usage:
    python rebuild_vectordb.py --pdf_path path/to/manual.pdf [--collection_name pnd_manual_v2]
"""

import os
import sys
import argparse
from typing import List, Dict, Any
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from utils.text_cleaning import (
    clean_ocr_artifacts,
    sentence_tokenize,
    create_sentence_chunks,
    clean_chunk_for_embedding,
)

# Qdrant imports
try:
    from qdrant_client import QdrantClient
    from qdrant_client.http.models import Distance, VectorParams, PointStruct
    QDRANT_AVAILABLE = True
except ImportError:
    print("ERROR: qdrant-client not installed. Run: pip install qdrant-client")
    sys.exit(1)

# Sentence transformers
try:
    from sentence_transformers import SentenceTransformer
    SENT_TRANSFORMERS_AVAILABLE = True
except ImportError:
    print("ERROR: sentence-transformers not installed. Run: pip install sentence-transformers")
    sys.exit(1)

# PDF reading
try:
    from pypdf import PdfReader
    PYPDF_AVAILABLE = True
except ImportError:
    try:
        import PyPDF2  # type: ignore
        PdfReader = PyPDF2.PdfReader  # type: ignore
        PYPDF_AVAILABLE = True
    except ImportError:
        print("ERROR: PDF library not installed. Run: pip install pypdf")
        sys.exit(1)


def extract_pages_from_pdf(pdf_path: str) -> List[str]:
    """
    Extract text from each page of PDF.
    
    Args:
        pdf_path: Path to PDF file
        
    Returns:
        List of page text strings
    """
    reader = PdfReader(pdf_path)
    pages = []
    
    print(f"Extracting text from {len(reader.pages)} pages...")
    
    for i, page in enumerate(reader.pages, 1):
        try:
            text = page.extract_text()
            if text:
                pages.append(text)
            else:
                pages.append("")
        except Exception as e:
            print(f"  Warning: Failed to extract page {i}: {e}")
            pages.append("")
        
        if i % 50 == 0:
            print(f"  Processed {i}/{len(reader.pages)} pages...")
    
    print(f"✓ Extracted {len(pages)} pages")
    return pages


def classify_chunk_type(text: str, page_num: int) -> str:
    """
    Classify chunk type for metadata.
    
    Returns: "main_manual", "annexure", "checklist", "table", or "appendix"
    """
    text_lower = text.lower()
    
    # Annexure detection
    if any(keyword in text_lower for keyword in ["annexure", "annex ", "appendix"]):
        return "annexure"
    
    # Checklist detection
    if any(keyword in text_lower for keyword in ["n/a yes no", "checklist", "s. no.", "inclusion of"]):
        return "checklist"
    
    # Table detection (high number density)
    words = text.split()
    if len(words) > 10:
        number_count = sum(1 for w in words if w.isdigit())
        if number_count / len(words) > 0.2:
            return "table"
    
    # Appendix detection
    if "appendix" in text_lower and page_num > 80:
        return "appendix"
    
    return "main_manual"


def process_page_into_chunks(page_text: str, page_num: int) -> List[Dict[str, Any]]:
    """
    Process a single page into sentence-level chunks with metadata.
    
    Pipeline:
    1. Clean OCR artifacts from raw page text
    2. Split into sentences
    3. Group into 2-3 sentence chunks
    4. Clean each chunk
    5. Classify and add metadata
    
    Args:
        page_text: Raw page text
        page_num: Page number (1-indexed)
        
    Returns:
        List of chunk dictionaries with text and metadata
    """
    # Step 1: Clean OCR from entire page
    page_clean = clean_ocr_artifacts(page_text)
    
    # Step 2: Split into sentences
    sentences = sentence_tokenize(page_clean)
    
    if not sentences:
        return []
    
    # Step 3: Group into 2-3 sentence chunks
    chunk_texts = create_sentence_chunks(
        sentences,
        sentences_per_chunk=3,
        max_chars=450,
        min_chars=100
    )
    
    # Step 4: Process each chunk
    chunks = []
    for chunk_text in chunk_texts:
        # Final cleaning
        chunk_clean = clean_chunk_for_embedding(chunk_text)
        
        if not chunk_clean or len(chunk_clean) < 100:
            continue  # Skip too-short chunks
        
        # Classify chunk type
        chunk_type = classify_chunk_type(chunk_clean, page_num)
        
        # Create chunk metadata
        chunk_data = {
            "text": chunk_clean,
            "page": page_num,
            "type": chunk_type,
            "is_annexure": chunk_type == "annexure",
            "is_checklist": chunk_type == "checklist",
            "is_table": chunk_type == "table",
        }
        
        chunks.append(chunk_data)
    
    return chunks


def rebuild_vectordb(
    pdf_path: str,
    collection_name: str = "pnd_manual_v2",
    embed_model: str = "sentence-transformers/all-MiniLM-L6-v2",
    qdrant_url: str = "http://localhost:6333"
) -> int:
    """
    Rebuild vector database from scratch with sentence-level chunking.
    
    Args:
        pdf_path: Path to PDF file
        collection_name: Qdrant collection name
        embed_model: HuggingFace embedding model name
        qdrant_url: Qdrant server URL
        
    Returns:
        Number of chunks ingested
    """
    print("="*70)
    print("PDBot Vector DB Rebuild - Sentence-Level Chunking")
    print("="*70)
    print()
    
    # Step 1: Extract pages
    print("STEP 1: Extracting pages from PDF...")
    pages = extract_pages_from_pdf(pdf_path)
    print()
    
    # Step 2: Process into chunks
    print("STEP 2: Processing pages into sentence-level chunks...")
    all_chunks: List[Dict[str, Any]] = []
    
    for page_num, page_text in enumerate(pages, 1):
        if not page_text.strip():
            continue
        
        chunks = process_page_into_chunks(page_text, page_num)
        all_chunks.extend(chunks)
        
        if page_num % 20 == 0:
            print(f"  Processed {page_num}/{len(pages)} pages, {len(all_chunks)} chunks so far...")
    
    print(f"✓ Created {len(all_chunks)} sentence-level chunks")
    print()
    
    # Statistics
    type_counts: Dict[str, int] = {}
    for chunk in all_chunks:
        chunk_type = chunk["type"]
        type_counts[chunk_type] = type_counts.get(chunk_type, 0) + 1
    
    print("Chunk distribution:")
    for chunk_type, count in sorted(type_counts.items()):
        print(f"  {chunk_type:15s}: {count:4d} chunks")
    print()
    
    # Step 3: Initialize embedding model
    print("STEP 3: Loading embedding model...")
    print(f"  Model: {embed_model}")
    embedder = SentenceTransformer(embed_model)
    embedding_dim = int(embedder.get_sentence_embedding_dimension() or 384)  # type: ignore
    print(f"  Dimension: {embedding_dim}")
    print()
    
    # Step 4: Connect to Qdrant
    print("STEP 4: Connecting to Qdrant...")
    print(f"  URL: {qdrant_url}")
    print(f"  Collection: {collection_name}")
    
    client = QdrantClient(url=qdrant_url)
    
    # Delete old collection if exists
    try:
        client.delete_collection(collection_name)
        print(f"  ✓ Deleted old collection")
    except Exception:
        pass
    
    # Create new collection
    client.recreate_collection(
        collection_name,
        vectors_config=VectorParams(size=embedding_dim, distance=Distance.COSINE)
    )
    print(f"  ✓ Created new collection")
    print()
    
    # Step 5: Embed and upload chunks
    print("STEP 5: Embedding and uploading chunks...")
    
    batch_size = 100
    points: List[PointStruct] = []
    
    for idx, chunk in enumerate(all_chunks, 1):
        # Embed text
        vec = embedder.encode([chunk["text"]], normalize_embeddings=True)[0]
        
        # Create point
        point = PointStruct(
            id=idx,
            vector=vec.tolist(),
            payload={
                "text": chunk["text"],
                "page": chunk["page"],
                "type": chunk["type"],
                "is_annexure": chunk["is_annexure"],
                "is_checklist": chunk["is_checklist"],
                "is_table": chunk["is_table"],
            }
        )
        
        points.append(point)
        
        # Upload in batches
        if len(points) >= batch_size:
            client.upsert(collection_name, points)
            print(f"  Uploaded batch: {idx - len(points) + 1} to {idx}")
            points = []
    
    # Upload remaining points
    if points:
        client.upsert(collection_name, points)
        print(f"  Uploaded final batch: {len(all_chunks) - len(points) + 1} to {len(all_chunks)}")
    
    print()
    print(f"✓ Ingested {len(all_chunks)} chunks successfully!")
    print()
    print("="*70)
    print("Vector DB rebuild complete!")
    print("="*70)
    
    return len(all_chunks)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Rebuild PDBot vector database with sentence-level chunking")
    parser.add_argument("--pdf_path", type=str, required=True, help="Path to PDF manual")
    parser.add_argument("--collection_name", type=str, default="pnd_manual_v2", help="Qdrant collection name")
    parser.add_argument("--embed_model", type=str, default="sentence-transformers/all-MiniLM-L6-v2", help="Embedding model")
    parser.add_argument("--qdrant_url", type=str, default="http://localhost:6333", help="Qdrant URL")
    
    args = parser.parse_args()
    
    # Validate PDF exists
    if not os.path.exists(args.pdf_path):
        print(f"ERROR: PDF file not found: {args.pdf_path}")
        sys.exit(1)
    
    # Rebuild
    try:
        chunk_count = rebuild_vectordb(
            pdf_path=args.pdf_path,
            collection_name=args.collection_name,
            embed_model=args.embed_model,
            qdrant_url=args.qdrant_url
        )
        print(f"\nSuccess! Ingested {chunk_count} chunks.")
        print(f"\nUpdate your app configuration:")
        print(f'  PNDBOT_RAG_COLLECTION="{args.collection_name}"')
    except Exception as e:
        print(f"\nERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
