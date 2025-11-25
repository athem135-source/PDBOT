"""Test if sentence-transformers imports correctly."""
import sys
import warnings
warnings.filterwarnings("ignore")

print("Testing sentence-transformers import...")
try:
    from sentence_transformers import SentenceTransformer
    print("✅ SentenceTransformer imported successfully")
    print(f"   Class type: {type(SentenceTransformer)}")
    print(f"   Available: {SentenceTransformer is not None}")
except ImportError as e:
    print(f"❌ ImportError: {e}")
    sys.exit(1)
except Exception as e:
    print(f"⚠️ Exception during import: {e}")
    print(f"   Exception type: {type(e)}")
    # Check if it actually imported despite exception
    try:
        print(f"   SentenceTransformer in globals: {'SentenceTransformer' in globals()}")
        if 'SentenceTransformer' in globals():
            print("   ✅ Import succeeded despite exception")
    except:
        pass
    sys.exit(1)

print("\nTesting model initialization...")
try:
    model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')
    print(f"✅ Model initialized: {model}")
    dim = model.get_sentence_embedding_dimension()
    print(f"   Embedding dimension: {dim}")
except Exception as e:
    print(f"❌ Model initialization failed: {e}")
    sys.exit(1)

print("\n✅ All tests passed!")
