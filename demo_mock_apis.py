"""
Demo script for Mock APIs and Agent Routing.

Demonstrates:
1. Mock API functionality with different test scenarios
2. Agent routing based on review rules
3. Integration between structured rules and routing logic
"""

import json
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from tools.mock_apis import (
    check_identity,
    verify_income,
    check_ofac,
    check_fraud_indicators,
    get_credit_bureau_data,
    get_test_ssns
)
from tools.agent_router import ReviewRuleRouter, get_agent_execution_plan

# PolicyExecutor will be created in future prompts
try:
    from tools.policy_executor import PolicyExecutor
    HAS_POLICY_EXECUTOR = True
except ImportError:
    HAS_POLICY_EXECUTOR = False
    PolicyExecutor = None


def demo_mock_apis():
    """Demonstrate all mock API functions with different scenarios."""
    print("=" * 80)
    print("DEMO 1: MOCK API TESTING")
    print("=" * 80)
    
    test_ssns = get_test_ssns()
    
    # Scenario 1: Valid low-risk applicant
    print("\n" + "─" * 80)
    print("Scenario 1: Valid Low-Risk Applicant (SSN: 111-22-3333)")
    print("─" * 80)
    
    ssn = test_ssns["valid_low_risk"][0]
    
    print("\n📋 Identity Check:")
    identity_result = check_identity(ssn, "John Doe", "123 Main St, New York, NY 10001")
    print(f"  ✓ SSN Valid: {identity_result['ssn_valid']}")
    print(f"  ✓ Name Match: {identity_result['name_match']}")
    print(f"  ✓ Identity Theft Flags: {identity_result['identity_theft_flags']}")
    print(f"  ✓ Confidence Score: {identity_result['confidence_score']}")
    print(f"  ✓ All Checks Passed: {all(identity_result['checks_passed'].values())}")
    
    print("\n💰 Income Verification:")
    income_result = verify_income(ssn, 85000, "Tech Corp Inc", total_debt_payments=2500)
    print(f"  ✓ Income Match: {income_result['income_match']}")
    print(f"  ✓ Verified Income: ${income_result['verified_income']:,}")
    print(f"  ✓ Employment Stable: {income_result['employment_stable']}")
    print(f"  ✓ DTI Ratio: {income_result['dti_ratio']:.1%}")
    print(f"  ✓ DTI Within Limit: {income_result['dti_within_limit']}")
    print(f"  ✓ Confidence Score: {income_result['confidence_score']}")
    
    print("\n🚨 OFAC Screening:")
    ofac_result = check_ofac(ssn, "John Doe")
    print(f"  ✓ On OFAC List: {ofac_result['on_ofac_list']}")
    print(f"  ✓ Screening Passed: {ofac_result['screening_passed']}")
    print(f"  ✓ Confidence Score: {ofac_result['confidence_score']}")
    
    print("\n🔍 Fraud Indicators:")
    fraud_result = check_fraud_indicators(ssn, device_id="device-abc123", ip_address="192.168.1.1", application_count_30d=1)
    print(f"  ✓ Fraud Indicators: {fraud_result['fraud_indicators'] or 'None'}")
    print(f"  ✓ Fraud Risk Score: {fraud_result['fraud_risk_score']:.2f}")
    print(f"  ✓ Credit Inquiries (30d): {fraud_result['details']['credit_inquiries']['count_30d']}")
    print(f"  ✓ Screening Passed: {fraud_result['screening_passed']}")
    print(f"  ✓ Confidence Score: {fraud_result['confidence_score']}")
    
    print("\n📊 Credit Bureau Data:")
    credit_result = get_credit_bureau_data(ssn)
    if credit_result['success']:
        print(f"  ✓ Credit Score: {credit_result['credit_score']}")
        print(f"  ✓ Total Accounts: {credit_result['summary']['total_accounts']}")
        print(f"  ✓ Utilization Ratio: {credit_result['summary']['utilization_ratio']:.1%}")
        print(f"  ✓ Delinquencies: {credit_result['summary']['delinquencies']}")
        print(f"  ✓ Payment History: {credit_result['summary']['payment_history_pct']:.1%}")
    
    # Scenario 2: Suspicious high-risk applicant
    print("\n" + "─" * 80)
    print("Scenario 2: Suspicious High-Risk Applicant (SSN: 333-44-5555)")
    print("─" * 80)
    
    ssn = test_ssns["suspicious_high_risk"][0]
    
    print("\n📋 Identity Check:")
    identity_result = check_identity(ssn, "Bob Johnson", "789 Elm St, Chicago, IL 60601")
    print(f"  ✗ SSN Valid: {identity_result['ssn_valid']}")
    print(f"  ✗ Identity Theft Flags: {identity_result['identity_theft_flags']}")
    print(f"  ✗ Address History (months): {identity_result['address_history_months']}")
    print(f"  ✗ Confidence Score: {identity_result['confidence_score']}")
    
    print("\n💰 Income Verification:")
    income_result = verify_income(ssn, 45000, total_debt_payments=3000)
    print(f"  ✗ Income Verified: {income_result.get('income_verified', False)}")
    print(f"  ✗ Employment Stable: {income_result['employment_stable']}")
    print(f"  ✗ Documentation Complete: {income_result['documentation_complete']}")
    if income_result.get('dti_ratio'):
        print(f"  ✗ DTI Ratio: {income_result['dti_ratio']:.1%}")
    
    print("\n🔍 Fraud Indicators:")
    fraud_result = check_fraud_indicators(ssn, device_id="device-xyz789", ip_address="192.168.1.100", application_count_30d=5)
    print(f"  ✗ Fraud Indicators: {fraud_result['fraud_indicators']}")
    print(f"  ✗ Fraud Risk Score: {fraud_result['fraud_risk_score']:.2f}")
    print(f"  ✗ Application Velocity Flag: {fraud_result['details']['application_velocity']['velocity_flag']}")
    print(f"  ✗ Screening Passed: {fraud_result['screening_passed']}")
    
    # Scenario 3: OFAC match (critical failure)
    print("\n" + "─" * 80)
    print("Scenario 3: OFAC Match - Critical Failure (SSN: 444-55-6666)")
    print("─" * 80)
    
    ssn = test_ssns["ofac_match"][0]
    
    print("\n🚨 OFAC Screening:")
    ofac_result = check_ofac(ssn, "Sanctioned Person")
    print(f"  ✗ On OFAC List: {ofac_result['on_ofac_list']}")
    print(f"  ✗ Match Type: {ofac_result['match_type']}")
    print(f"  ✗ Screening Passed: {ofac_result['screening_passed']}")
    print(f"  ✗ Confidence Score: {ofac_result['confidence_score']}")
    print(f"  ⚠️  CRITICAL: Zero-tolerance violation - automatic denial")


def demo_agent_routing():
    """Demonstrate agent routing logic for different review rules."""
    print("\n\n" + "=" * 80)
    print("DEMO 2: AGENT ROUTING")
    print("=" * 80)
    
    # Show routing for each review rule
    print("\n📍 Individual Review Rule Routing:")
    print("─" * 80)
    
    for rule in ReviewRuleRouter.get_all_review_rules():
        agents = ReviewRuleRouter.get_agent_names(rule)
        risk = ReviewRuleRouter.get_risk_level(rule)
        has_prereqs = ReviewRuleRouter.requires_prerequisites(rule)
        
        print(f"\n{rule} ({risk}):")
        print(f"  → Execution Order: {' → '.join(agents)}")
        
        if has_prereqs:
            prereqs = [a.value for a in ReviewRuleRouter.PREREQUISITES[rule]]
            print(f"  → Prerequisites: {', '.join(prereqs)} (must complete before primary agent)")
    
    # Show execution plan for multiple rules
    print("\n\n📋 Multi-Rule Execution Plan:")
    print("─" * 80)
    
    scenarios = [
        {
            "name": "Identity + Income Review",
            "rules": ["IDENTITY_VERIFICATION", "INCOME_VALIDATION"]
        },
        {
            "name": "Fraud Investigation",
            "rules": ["FRAUD_CHECK"]
        },
        {
            "name": "High-Risk Profile",
            "rules": ["HIGH_RISK_PROFILE"]
        },
        {
            "name": "Multiple Rules (Identity + Fraud)",
            "rules": ["IDENTITY_VERIFICATION", "FRAUD_CHECK"]
        },
    ]
    
    for scenario in scenarios:
        print(f"\n{scenario['name']}:")
        print(f"  Rules: {', '.join(scenario['rules'])}")
        
        plan = get_agent_execution_plan(scenario["rules"])
        print(f"  Execution Order: {' → '.join(plan['execution_order'])}")
        print(f"  Total Agents: {plan['total_agents']}")
        print(f"  Has Critical Rules: {plan['has_critical_rules']}")
        
        # Show rule details
        for detail in plan["rule_details"]:
            print(f"    • {detail['rule']} ({detail['risk_level']}): {', '.join(detail['agents'])}")


def demo_structured_rules_integration():
    """Demonstrate integration with structured rules."""
    print("\n\n" + "=" * 80)
    print("DEMO 3: STRUCTURED RULES + ROUTING INTEGRATION")
    print("=" * 80)
    
    if not HAS_POLICY_EXECUTOR:
        print("\n⚠️  PolicyExecutor not yet implemented - skipping this demo")
        print("   This will be available after Prompt 2a completion")
        return
    
    # Load structured rules
    print("\n📁 Loading Structured Rules...")
    executor = PolicyExecutor()
    
    try:
        executor.load_rules("./policies/structured_rules.json")
        print("  ✓ Loaded successfully")
        
        stats = executor.get_stats()
        print(f"  ✓ Total Rules: {stats['total_rules']}")
        print(f"  ✓ Total Checks: {stats['total_checks']}")
        print(f"  ✓ Risk Distribution: {stats['risk_distribution']}")
        
    except Exception as e:
        print(f"  ✗ Error loading rules: {e}")
        return
    
    # Validate routing matches structured rules
    print("\n✅ Validating Routing Configuration:")
    print("─" * 80)
    
    validation = ReviewRuleRouter.validate_structured_rules(executor.rules)
    
    all_valid = True
    for rule_name, warnings in validation.items():
        if warnings:
            all_valid = False
            print(f"\n⚠️  {rule_name}:")
            for warning in warnings:
                print(f"    - {warning}")
        else:
            agents = ReviewRuleRouter.get_agent_names(rule_name, include_prerequisites=False)
            print(f"  ✓ {rule_name}: {', '.join(agents)}")
    
    if all_valid:
        print("\n✓ All structured rules match routing configuration!")
    
    # Show workflow for each rule
    print("\n\n📋 Complete Workflow Configurations:")
    print("─" * 80)
    
    for rule_name in executor.list_rules():
        rule = executor.get_rule(rule_name)
        workflow = executor.get_workflow_config(rule_name)
        criteria = executor.get_decision_criteria(rule_name)
        
        print(f"\n{rule_name}:")
        print(f"  Risk Level: {rule.risk_level}")
        print(f"  Required Agents: {', '.join(rule.required_agents)}")
        print(f"  Total Checks: {len(rule.checks)}")
        print(f"  Parallel Execution: {workflow.parallel_execution}")
        print(f"  Timeout: {workflow.timeout_seconds}s")
        print(f"  Min Confidence: {criteria.min_confidence}")
        print(f"  Requires Manual Signoff: {criteria.requires_manual_signoff}")
        
        # Show check breakdown
        if rule.checks:
            print(f"  Checks:")
            for check in rule.checks:
                status = "✓" if check.required else "○"
                zt = " [ZERO TOLERANCE]" if check.zero_tolerance else ""
                print(f"    {status} {check.name} → {check.tool}{zt}")


def demo_fraud_check_cascade():
    """Demonstrate FRAUD_CHECK triggering Identity and Income checks."""
    print("\n\n" + "=" * 80)
    print("DEMO 4: FRAUD_CHECK CASCADE BEHAVIOR")
    print("=" * 80)
    
    print("\n🔍 When FRAUD_CHECK is triggered:")
    print("─" * 80)
    
    # Show the cascade
    fraud_agents = ReviewRuleRouter.get_agent_names("FRAUD_CHECK", include_prerequisites=True)
    fraud_agents_only = ReviewRuleRouter.get_agent_names("FRAUD_CHECK", include_prerequisites=False)
    
    print(f"\nPrimary Agent: {', '.join(fraud_agents_only)}")
    print(f"Full Execution Order: {' → '.join(fraud_agents)}")
    print("\n📌 Key Points:")
    print("  1. Identity Agent runs FIRST to verify applicant authenticity")
    print("  2. Income Agent runs SECOND to ensure financial capacity")
    print("  3. Fraud Agent runs LAST to check fraud indicators")
    print("  4. If Identity or Income fails, Fraud check may be skipped (optional)")
    
    # Simulate a fraud check scenario
    print("\n\n📝 Simulated Fraud Investigation:")
    print("─" * 80)
    
    test_ssn = "333-44-5555"  # Suspicious applicant
    
    print(f"\nProcessing SSN: {test_ssn}")
    print("\nStep 1: Identity Verification")
    identity_result = check_identity(test_ssn, "Bob Johnson", "789 Elm St")
    identity_passed = all(identity_result['checks_passed'].values())
    print(f"  Result: {'✓ PASSED' if identity_passed else '✗ FAILED'}")
    print(f"  Confidence: {identity_result['confidence_score']}")
    
    print("\nStep 2: Income Validation")
    income_result = verify_income(test_ssn, 45000, total_debt_payments=3000)
    income_passed = all(income_result['checks_passed'].values())
    print(f"  Result: {'✓ PASSED' if income_passed else '✗ FAILED'}")
    print(f"  Confidence: {income_result['confidence_score']}")
    
    print("\nStep 3: Fraud Indicators")
    fraud_result = check_fraud_indicators(test_ssn, application_count_30d=5)
    fraud_passed = fraud_result['screening_passed']
    print(f"  Result: {'✓ PASSED' if fraud_passed else '✗ FAILED'}")
    print(f"  Fraud Risk Score: {fraud_result['fraud_risk_score']}")
    print(f"  Indicators: {fraud_result['fraud_indicators']}")
    
    print("\nFinal Decision:")
    all_passed = identity_passed and income_passed and fraud_passed
    if all_passed:
        print("  ✓ APPROVED - All checks passed")
    else:
        reasons = []
        if not identity_passed:
            reasons.append("Identity verification failed")
        if not income_passed:
            reasons.append("Income validation failed")
        if not fraud_passed:
            reasons.append("Fraud indicators detected")
        print(f"  ✗ DENIED - {', '.join(reasons)}")


if __name__ == "__main__":
    # Run all demos
    demo_mock_apis()
    demo_agent_routing()
    demo_structured_rules_integration()
    demo_fraud_check_cascade()
    
    print("\n\n" + "=" * 80)
    print("✅ DEMO COMPLETE")
    print("=" * 80)
    print("\nKey Takeaways:")
    print("  • Mock APIs provide realistic responses with confidence scores")
    print("  • Routing logic maps review rules to appropriate agents")
    print("  • FRAUD_CHECK cascades to Identity + Income verification")
    print("  • HIGH_RISK_PROFILE invokes all three agents")
    print("  • Structured rules integrate seamlessly with routing")
    print("  • OFAC matches trigger zero-tolerance denials")
