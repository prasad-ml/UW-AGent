"""
Test script for Policy Executor (Prompt 2a).
"""

import sys
import os
from pathlib import Path
import json

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def test_policy_executor_import():
    """Test importing PolicyExecutor."""
    try:
        from tools.policy_executor import PolicyExecutor, StructuredRule, CheckConfig
        print("✓ PolicyExecutor imports successful")
        return True
    except Exception as e:
        print(f"✗ PolicyExecutor import failed: {e}")
        return False


def test_pydantic_models():
    """Test Pydantic models."""
    try:
        from tools.policy_executor import CheckConfig, DecisionCriteria, WorkflowConfig, StructuredRule
        
        # Test CheckConfig
        check = CheckConfig(
            name="test_check",
            description="Test check",
            tool="test_tool",
            required=True
        )
        assert check.name == "test_check"
        
        # Test DecisionCriteria
        criteria = DecisionCriteria(
            approval_condition="all_pass",
            min_confidence=0.9
        )
        assert criteria.min_confidence == 0.9
        
        # Test WorkflowConfig
        workflow = WorkflowConfig(
            parallel_execution=True,
            timeout_seconds=45
        )
        assert workflow.timeout_seconds == 45
        
        # Test StructuredRule
        rule = StructuredRule(
            description="Test rule",
            risk_level="HIGH",
            required_agents=["identity"],
            checks=[check],
            decision_criteria=criteria,
            workflow_config=workflow
        )
        assert rule.risk_level == "HIGH"
        assert len(rule.checks) == 1
        
        print("✓ All Pydantic models working correctly")
        return True
    except Exception as e:
        print(f"✗ Pydantic model test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_generate_and_save_rules():
    """Test generating and saving structured rules."""
    try:
        from tools.vector_store import PolicyVectorStore
        from tools.policy_executor import PolicyExecutor
        from config import settings
        
        # Check API key
        if not settings.openai_api_key or settings.openai_api_key == "your_openai_api_key_here":
            print("⚠️  Skipping generation test - API key not configured")
            return True
        
        # Initialize vector store
        vector_store = PolicyVectorStore()
        vector_store.initialize_db()
        
        # Load policies
        policy_file = Path(__file__).parent.parent / "policies" / "sample_policies.txt"
        vector_store.reset_collection()
        vector_store.load_policies_from_file(str(policy_file))
        
        # Initialize executor
        executor = PolicyExecutor()
        executor.initialize(vector_store)
        
        # Generate rules
        print("  Generating structured rules...")
        rules = executor.generate_structured_rules()
        
        assert len(rules) > 0, "No rules generated"
        print(f"✓ Generated {len(rules)} structured rules")
        
        # Save rules
        test_rules_path = "policies/test_structured_rules.json"
        executor.save_rules(test_rules_path)
        
        assert Path(test_rules_path).exists(), "Rules file not created"
        print(f"✓ Saved rules to {test_rules_path}")
        
        # Clean up
        Path(test_rules_path).unlink()
        
        return True
    except Exception as e:
        print(f"✗ Generate and save test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_load_rules():
    """Test loading rules from JSON."""
    try:
        from tools.policy_executor import PolicyExecutor
        
        # Create sample rules file
        sample_rules = {
            "TEST_RULE": {
                "description": "Test rule",
                "risk_level": "MEDIUM",
                "required_agents": ["test"],
                "checks": [
                    {
                        "name": "test_check",
                        "description": "Test",
                        "tool": "test_tool",
                        "required": True,
                        "threshold": None,
                        "zero_tolerance": False
                    }
                ],
                "decision_criteria": {
                    "approval_condition": "all_pass",
                    "min_confidence": 0.8,
                    "dti_threshold": None,
                    "zero_tolerance_checks": [],
                    "requires_manual_signoff": False
                },
                "workflow_config": {
                    "parallel_execution": False,
                    "timeout_seconds": 30,
                    "retry_on_failure": False,
                    "cascade_mode": False
                }
            }
        }
        
        # Save to temp file
        test_file = "policies/test_load_rules.json"
        Path(test_file).parent.mkdir(exist_ok=True)
        with open(test_file, 'w') as f:
            json.dump(sample_rules, f)
        
        # Load rules
        executor = PolicyExecutor()
        loaded = executor.load_rules(test_file)
        
        assert len(loaded) == 1, "Failed to load rules"
        assert "TEST_RULE" in loaded, "Rule not found"
        
        print("✓ Successfully loaded rules from JSON")
        
        # Test getters
        workflow = executor.get_workflow_config("TEST_RULE")
        assert workflow is not None, "Failed to get workflow config"
        
        criteria = executor.get_decision_criteria("TEST_RULE")
        assert criteria is not None, "Failed to get decision criteria"
        
        print("✓ Rule getters working correctly")
        
        # Clean up
        Path(test_file).unlink()
        
        return True
    except Exception as e:
        print(f"✗ Load rules test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all tests for Prompt 2a."""
    print("=" * 60)
    print("PROMPT 2a VERIFICATION: Policy Executor")
    print("=" * 60)
    print()
    
    tests = [
        ("Policy Executor Import", test_policy_executor_import),
        ("Pydantic Models", test_pydantic_models),
        ("Load Rules from JSON", test_load_rules),
        ("Generate and Save Rules", test_generate_and_save_rules),
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"Testing: {test_name}")
        print("-" * 60)
        success = test_func()
        results.append((test_name, success))
        print()
    
    # Summary
    print("=" * 60)
    print("SUMMARY")
    print("=" * 60)
    passed = sum(1 for _, success in results if success)
    total = len(results)
    
    for test_name, success in results:
        status = "✓" if success else "✗"
        print(f"{status} {test_name}")
    
    print(f"\nTests passed: {passed}/{total}")
    
    if passed == total:
        print("\n✅ Prompt 2a completed successfully!")
        print("\nNext steps:")
        print("  • Proceed to Prompt 3: Mock Tools & APIs")
        print("  • Policy Executor ready for orchestrator integration")
        return 0
    else:
        print("\n❌ Some tests failed. Please review the errors above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
