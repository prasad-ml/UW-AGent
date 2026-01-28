"""
Demo script for Policy Executor (Prompt 2a).
Demonstrates generating and using structured rules.
"""

import sys
import os
from pathlib import Path
import json

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tools.vector_store import PolicyVectorStore
from tools.policy_executor import PolicyExecutor
from config import settings


def main():
    """Demo the Policy Executor functionality."""
    
    print("=" * 70)
    print("POLICY EXECUTOR DEMO - Structured Rules Generation")
    print("=" * 70)
    print()
    
    # Check for API key
    if not settings.openai_api_key or settings.openai_api_key == "your_openai_api_key_here":
        print("❌ OpenAI API key not configured")
        print("   Please add your API key to the .env file")
        return 1
    
    print("✓ OpenAI API key configured")
    print()
    
    try:
        # Step 1: Initialize Vector Store
        print("1. Initializing Vector Store...")
        vector_store = PolicyVectorStore()
        vector_store.initialize_db()
        print("   ✓ Vector store initialized")
        print()
        
        # Step 2: Load Policies
        print("2. Loading policies...")
        policy_file = Path("policies/sample_policies.txt")
        
        # Reset for clean demo
        vector_store.reset_collection()
        stats = vector_store.load_policies_from_file(str(policy_file))
        print(f"   ✓ Loaded {stats['total_policies']} policies")
        print(f"   ✓ Created {stats['total_chunks']} chunks")
        print()
        
        # Step 3: Initialize Policy Executor
        print("3. Initializing Policy Executor...")
        executor = PolicyExecutor()
        executor.initialize(vector_store)
        print("   ✓ Policy Executor initialized")
        print()
        
        # Step 4: Generate Structured Rules
        print("4. Generating structured rules (this may take a minute)...")
        print("   Using LLM to parse and structure policies...")
        
        structured_rules = executor.generate_structured_rules()
        print(f"   ✓ Generated {len(structured_rules)} structured rules")
        print()
        
        # Step 5: Display Generated Rules
        print("5. Generated Rules Summary:")
        for rule_name in structured_rules.keys():
            rule = executor.get_rule(rule_name)
            print(f"\n   📋 {rule_name}")
            print(f"      Risk Level: {rule.risk_level}")
            print(f"      Required Agents: {', '.join(rule.required_agents)}")
            print(f"      Number of Checks: {len(rule.checks)}")
            print(f"      Min Confidence: {rule.decision_criteria.min_confidence}")
            
            # Show checks
            if rule.checks:
                print(f"      Checks:")
                for check in rule.checks[:3]:  # Show first 3
                    print(f"        • {check.name}: {check.description[:50]}...")
        print()
        
        # Step 6: Save Rules to JSON
        print("6. Saving structured rules to JSON...")
        rules_path = settings.structured_rules_path
        executor.save_rules(rules_path)
        print(f"   ✓ Saved to: {rules_path}")
        
        # Check file size
        if Path(rules_path).exists():
            file_size = Path(rules_path).stat().st_size
            print(f"   ✓ File size: {file_size:,} bytes")
        print()
        
        # Step 7: Test Loading Rules
        print("7. Testing rule loading (simulating runtime)...")
        new_executor = PolicyExecutor()
        loaded_rules = new_executor.load_rules(rules_path)
        print(f"   ✓ Loaded {len(loaded_rules)} rules")
        print(f"   ✓ No vector DB or LLM needed - instant lookup!")
        print()
        
        # Step 8: Demonstrate Fast Lookup
        print("8. Demonstrating fast rule lookup:")
        
        test_rules = ["IDENTITY_VERIFICATION", "FRAUD_CHECK"]
        for review_rule in test_rules:
            workflow = new_executor.get_workflow_config(review_rule)
            criteria = new_executor.get_decision_criteria(review_rule)
            
            if workflow:
                print(f"\n   📌 {review_rule}")
                print(f"      Agents: {workflow['required_agents']}")
                print(f"      Checks: {len(workflow['checks'])}")
                print(f"      Timeout: {workflow['workflow_config']['timeout_seconds']}s")
                print(f"      Parallel: {workflow['workflow_config']['parallel_execution']}")
                print(f"      Min Confidence: {criteria['min_confidence']}")
        print()
        
        # Step 9: Show Stats
        print("9. Policy Executor Statistics:")
        stats = new_executor.get_stats()
        print(f"   Total Rules: {stats['total_rules']}")
        print(f"   Total Checks: {stats['total_checks']}")
        print(f"   Risk Distribution: {stats['risk_level_distribution']}")
        print()
        
        # Step 10: Show JSON Sample
        print("10. Sample Structured Rule (JSON):")
        sample_rule = "IDENTITY_VERIFICATION"
        rule_data = structured_rules.get(sample_rule)
        if rule_data:
            print(json.dumps(rule_data, indent=2)[:500] + "...")
        print()
        
        print("=" * 70)
        print("✅ Policy Executor Demo Completed Successfully!")
        print("=" * 70)
        print()
        print("📊 PERFORMANCE BENEFITS:")
        print("   • No vector DB queries needed at runtime")
        print("   • No LLM API calls during application processing")
        print("   • Instant rule lookup from JSON (< 1ms)")
        print("   • Cost: $0 per application (after initial setup)")
        print("   • Consistency: 100% identical rule application")
        print()
        print("🎯 NEXT STEPS:")
        print("   • Orchestrator will load these rules directly")
        print("   • Rules can be version controlled")
        print("   • Update policies → regenerate rules → deploy")
        print()
        
        return 0
        
    except Exception as e:
        print(f"❌ Error during demo: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
