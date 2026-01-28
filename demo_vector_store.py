"""
Demo script to show PolicyVectorStore functionality.
This demo requires an OpenAI API key to be set in .env file.
"""

import sys
import os
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tools.vector_store import PolicyVectorStore
from config import settings


def main():
    """Demo the vector store functionality."""
    
    print("=" * 70)
    print("POLICY VECTOR STORE DEMO")
    print("=" * 70)
    print()
    
    # Check for API key
    if not settings.openai_api_key or settings.openai_api_key == "your_openai_api_key_here":
        print("⚠️  OpenAI API key not configured")
        print("   To run this demo, add your API key to the .env file:")
        print("   OPENAI_API_KEY=your_actual_api_key")
        print()
        print("📝 However, we can still demonstrate the structure:")
        print()
        
        # Show policy file structure
        policy_file = Path(__file__).parent / "policies" / "sample_policies.txt"
        if not policy_file.exists():
            policy_file = Path("policies/sample_policies.txt")
        
        with open(policy_file, 'r') as f:
            content = f.read()
        
        print(f"✓ Policy file loaded: {len(content)} characters")
        print(f"✓ Contains {content.count('REVIEW_RULE:')} review rules")
        print()
        print("Review rules defined:")
        for line in content.split('\n'):
            if line.startswith('REVIEW_RULE:'):
                rule = line.replace('REVIEW_RULE:', '').strip()
                print(f"  • {rule}")
        print()
        
        # Show what would happen with API key
        print("With an OpenAI API key configured, the vector store would:")
        print("  1. Initialize ChromaDB with persistent storage")
        print("  2. Generate embeddings for each policy section")
        print("  3. Store embeddings in ChromaDB")
        print("  4. Enable semantic search: query_policy('FRAUD_CHECK')")
        print("  5. Return most relevant policy sections")
        print()
        print("Example usage:")
        print("  store = PolicyVectorStore()")
        print("  store.initialize_db()")
        print("  store.load_policies_from_file('policies/sample_policies.txt')")
        print("  results = store.query_policy('IDENTITY_VERIFICATION')")
        print()
        
        return 0
    
    # If API key is set, run full demo
    try:
        print("✓ OpenAI API key configured")
        print()
        
        # Initialize vector store
        print("1. Initializing PolicyVectorStore...")
        store = PolicyVectorStore()
        store.initialize_db()
        print(f"   ✓ ChromaDB initialized at: {store.persist_directory}")
        print()
        
        # Load policies
        print("2. Loading policies from file...")
        policy_file = Path(__file__).parent / "policies" / "sample_policies.txt"
        if not policy_file.exists():
            policy_file = Path("policies/sample_policies.txt")
        
        # Reset for clean demo
        store.reset_collection()
        
        stats = store.load_policies_from_file(str(policy_file))
        print(f"   ✓ Loaded {stats['total_policies']} policies")
        print(f"   ✓ Created {stats['total_chunks']} chunks")
        print(f"   ✓ Collection now has {stats['collection_count']} documents")
        print()
        
        # List all policies
        print("3. Available review rules:")
        policies = store.list_all_policies()
        for policy in policies:
            print(f"   • {policy}")
        print()
        
        # Query examples
        print("4. Query examples:")
        print()
        
        test_queries = [
            "IDENTITY_VERIFICATION",
            "FRAUD_CHECK",
            "income verification"
        ]
        
        for query in test_queries:
            print(f"   Query: '{query}'")
            results = store.query_policy(query, top_k=2)
            
            for idx, result in enumerate(results, 1):
                print(f"   Result {idx}:")
                print(f"     - Review Rule: {result['metadata'].get('review_rule')}")
                print(f"     - Similarity: {result['similarity']:.3f}")
                print(f"     - Snippet: {result['document'][:100]}...")
            print()
        
        # Get complete policy
        print("5. Retrieving complete policy:")
        policy = store.get_policy_by_rule("FRAUD_CHECK")
        if policy:
            print(f"   ✓ Retrieved FRAUD_CHECK policy ({len(policy)} chars)")
            print(f"   Preview: {policy[:200]}...")
        print()
        
        # Show stats
        print("6. Vector Store Statistics:")
        stats = store.get_stats()
        for key, value in stats.items():
            if key != 'policies':
                print(f"   • {key}: {value}")
        print()
        
        print("=" * 70)
        print("✅ Demo completed successfully!")
        print("=" * 70)
        
        return 0
        
    except Exception as e:
        print(f"❌ Error during demo: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
