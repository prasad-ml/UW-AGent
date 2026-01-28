"""
Verification script for Prompt 1 completion.
Tests that all components are properly set up.
"""

import sys
import os
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_imports():
    """Test that all modules can be imported."""
    try:
        from models import CreditApplication, UnderwritingDecision, AgentFinding
        from models import RiskLevel, DecisionStatus, FindingStatus
        from config import settings
        print("✓ All imports successful")
        return True
    except ImportError as e:
        print(f"✗ Import error: {e}")
        return False

def test_models():
    """Test Pydantic models."""
    try:
        from models import (
            CreditApplication, UnderwritingDecision, AgentFinding,
            RiskLevel, DecisionStatus, FindingStatus
        )
        
        # Test CreditApplication
        app = CreditApplication(
            application_id="APP-TEST-001",
            customer_name="John Doe",
            ssn="123-45-6789",
            annual_income=75000.0,
            credit_score=720,
            review_rules=["IDENTITY_VERIFICATION", "FRAUD_CHECK"]
        )
        assert app.application_id == "APP-TEST-001"
        
        # Test AgentFinding
        finding = AgentFinding(
            agent_name="TestAgent",
            check_type="TEST_CHECK",
            status=FindingStatus.PASS,
            risk_level=RiskLevel.LOW,
            confidence=0.95,
            reasoning="Test passed",
            details={"test": True}
        )
        assert finding.confidence == 0.95
        
        # Test UnderwritingDecision
        decision = UnderwritingDecision(
            application_id="APP-TEST-001",
            decision=DecisionStatus.APPROVED,
            confidence_score=0.92,
            reasoning="All checks passed",
            rules_applied=["IDENTITY_VERIFICATION"]
        )
        decision.add_finding(finding)
        assert len(decision.findings) == 1
        assert decision.all_checks_passed() == True
        assert decision.has_critical_failures() == False
        
        print("✓ All models working correctly")
        return True
    except Exception as e:
        print(f"✗ Model test error: {e}")
        return False

def test_config():
    """Test configuration."""
    try:
        from config import settings
        
        assert settings.app_name == "UW-Agent"
        assert settings.app_version == "0.1.0"
        assert settings.openai_model == "gpt-4"
        
        openai_config = settings.get_openai_config()
        assert "api_key" in openai_config
        assert "model" in openai_config
        
        chroma_config = settings.get_chroma_config()
        assert "persist_directory" in chroma_config
        assert "collection_name" in chroma_config
        
        print("✓ Configuration working correctly")
        return True
    except Exception as e:
        print(f"✗ Configuration test error: {e}")
        return False

def test_project_structure():
    """Test that project structure exists."""
    import os
    
    required_dirs = [
        "config",
        "models",
        "agents",
        "tools",
        "policies",
        "tests"
    ]
    
    required_files = [
        "main.py",
        "requirements.txt",
        ".env.example",
        ".gitignore",
        "README.md"
    ]
    
    all_exist = True
    
    for dir_name in required_dirs:
        if not os.path.isdir(dir_name):
            print(f"✗ Missing directory: {dir_name}")
            all_exist = False
    
    for file_name in required_files:
        if not os.path.isfile(file_name):
            print(f"✗ Missing file: {file_name}")
            all_exist = False
    
    if all_exist:
        print("✓ Project structure complete")
    
    return all_exist

def main():
    """Run all verification tests."""
    print("=" * 60)
    print("PROMPT 1 VERIFICATION: Project Setup & Base Structure")
    print("=" * 60)
    print()
    
    tests = [
        ("Project Structure", test_project_structure),
        ("Module Imports", test_imports),
        ("Pydantic Models", test_models),
        ("Configuration", test_config),
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\nTesting: {test_name}")
        print("-" * 60)
        results.append(test_func())
    
    print()
    print("=" * 60)
    print("SUMMARY")
    print("=" * 60)
    passed = sum(results)
    total = len(results)
    
    print(f"Tests passed: {passed}/{total}")
    
    if passed == total:
        print("\n✅ Prompt 1 completed successfully!")
        print("\nNext steps:")
        print("  • Proceed to Prompt 2: Vector Store & Policy Management")
        print("  • All base components are ready for development")
        return 0
    else:
        print("\n❌ Some tests failed. Please review the errors above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
