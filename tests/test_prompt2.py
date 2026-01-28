"""
Test script for Vector Store implementation (Prompt 2).
"""

import sys
import os
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def test_vector_store_initialization():
    """Test vector store initialization."""
    try:
        from tools.vector_store import PolicyVectorStore
        
        store = PolicyVectorStore()
        store.initialize_db()
        
        stats = store.get_stats()
        assert stats['initialized'] == True
        
        print("✓ Vector store initialization successful")
        return True, store
    except Exception as e:
        print(f"✗ Vector store initialization failed: {e}")
        return False, None


def test_load_policies(store):
    """Test loading policies from file."""
    try:
        policy_file = Path(__file__).parent.parent / "policies" / "sample_policies.txt"
        
        if not policy_file.exists():
            print(f"✗ Policy file not found: {policy_file}")
            return False
        
        # Reset collection for clean test
        store.reset_collection()
        
        # Load policies
        stats = store.load_policies_from_file(str(policy_file))
        
        assert stats['total_chunks'] > 0
        assert stats['collection_count'] > 0
        
        print(f"✓ Loaded policies successfully")
        print(f"  - Total chunks: {stats['total_chunks']}")
        print(f"  - Collection count: {stats['collection_count']}")
        
        return True
    except Exception as e:
        print(f"✗ Policy loading failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_query_policies(store):
    """Test querying policies."""
    try:
        # Test query for different review rules
        test_rules = [
            "IDENTITY_VERIFICATION",
            "INCOME_VALIDATION",
            "FRAUD_CHECK",
            "HIGH_RISK_PROFILE"
        ]
        
        all_passed = True
        
        for rule in test_rules:
            results = store.query_policy(rule, top_k=3)
            
            if not results:
                print(f"✗ No results for {rule}")
                all_passed = False
            else:
                print(f"✓ Query for '{rule}' returned {len(results)} results")
                
                # Show top result
                top_result = results[0]
                print(f"  - Similarity: {top_result['similarity']:.3f}")
                print(f"  - Review Rule: {top_result['metadata'].get('review_rule')}")
        
        return all_passed
    except Exception as e:
        print(f"✗ Policy query failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_list_policies(store):
    """Test listing all policies."""
    try:
        policies = store.list_all_policies()
        
        expected_policies = [
            "FRAUD_CHECK",
            "HIGH_RISK_PROFILE",
            "IDENTITY_VERIFICATION",
            "INCOME_VALIDATION"
        ]
        
        print(f"✓ Found {len(policies)} policies:")
        for policy in policies:
            print(f"  - {policy}")
        
        # Check if expected policies are present
        for expected in expected_policies:
            if expected not in policies:
                print(f"✗ Expected policy not found: {expected}")
                return False
        
        return True
    except Exception as e:
        print(f"✗ List policies failed: {e}")
        return False


def test_get_policy_by_rule(store):
    """Test getting complete policy by rule."""
    try:
        policy = store.get_policy_by_rule("IDENTITY_VERIFICATION")
        
        if not policy:
            print("✗ Failed to retrieve policy")
            return False
        
        # Check if policy contains expected content
        assert "SSN" in policy or "identity" in policy.lower()
        
        print("✓ Retrieved complete policy document")
        print(f"  - Length: {len(policy)} characters")
        
        return True
    except Exception as e:
        print(f"✗ Get policy by rule failed: {e}")
        return False


def main():
    """Run all verification tests for Prompt 2."""
    print("=" * 60)
    print("PROMPT 2 VERIFICATION: Vector Store & Policy Management")
    print("=" * 60)
    print()
    
    # Check for OpenAI API key
    from config import settings
    if not settings.openai_api_key or settings.openai_api_key == "your_openai_api_key_here":
        print("⚠️  WARNING: OpenAI API key not set in .env file")
        print("   Please add your API key to continue")
        print("   (This test requires OpenAI embeddings)")
        return 1
    
    tests = []
    store = None
    
    # Test 1: Initialization
    print("Testing: Vector Store Initialization")
    print("-" * 60)
    success, store = test_vector_store_initialization()
    tests.append(("Vector Store Initialization", success))
    print()
    
    if not success or not store:
        print("❌ Cannot proceed without successful initialization")
        return 1
    
    # Test 2: Load Policies
    print("Testing: Load Policies from File")
    print("-" * 60)
    success = test_load_policies(store)
    tests.append(("Load Policies", success))
    print()
    
    if not success:
        print("❌ Cannot proceed without loaded policies")
        return 1
    
    # Test 3: Query Policies
    print("Testing: Query Policies")
    print("-" * 60)
    success = test_query_policies(store)
    tests.append(("Query Policies", success))
    print()
    
    # Test 4: List Policies
    print("Testing: List All Policies")
    print("-" * 60)
    success = test_list_policies(store)
    tests.append(("List Policies", success))
    print()
    
    # Test 5: Get Policy by Rule
    print("Testing: Get Policy by Rule")
    print("-" * 60)
    success = test_get_policy_by_rule(store)
    tests.append(("Get Policy by Rule", success))
    print()
    
    # Summary
    print("=" * 60)
    print("SUMMARY")
    print("=" * 60)
    passed = sum(1 for _, success in tests if success)
    total = len(tests)
    
    for test_name, success in tests:
        status = "✓" if success else "✗"
        print(f"{status} {test_name}")
    
    print(f"\nTests passed: {passed}/{total}")
    
    if passed == total:
        print("\n✅ Prompt 2 completed successfully!")
        print("\nNext steps:")
        print("  • Proceed to Prompt 2a: Policy Executor (Structured Rules)")
        print("  • Vector store is ready for policy retrieval")
        return 0
    else:
        print("\n❌ Some tests failed. Please review the errors above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
