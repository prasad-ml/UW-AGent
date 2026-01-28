"""
Test suite for Prompt 3: Mock Tools & APIs

Tests:
1. Mock API imports and basic functionality
2. Agent routing logic
3. Structured rules integration
4. Fraud check cascade behavior
"""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

import unittest
from tools.mock_apis import (
    check_identity,
    verify_income,
    check_ofac,
    check_fraud_indicators,
    get_credit_bureau_data,
    get_test_ssns
)
from tools.agent_router import (
    ReviewRuleRouter,
    AgentType,
    get_agent_execution_plan
)

# PolicyExecutor will be created in future prompts
try:
    from tools.policy_executor import PolicyExecutor
    HAS_POLICY_EXECUTOR = True
except ImportError:
    HAS_POLICY_EXECUTOR = False
    PolicyExecutor = None


class TestMockAPIs(unittest.TestCase):
    """Test mock API functions."""
    
    def setUp(self):
        """Set up test data."""
        self.test_ssns = get_test_ssns()
        self.valid_ssn = self.test_ssns["valid_low_risk"][0]
        self.suspicious_ssn = self.test_ssns["suspicious_high_risk"][0]
        self.ofac_ssn = self.test_ssns["ofac_match"][0]
    
    def test_check_identity_valid(self):
        """Test identity check with valid SSN."""
        result = check_identity(self.valid_ssn, "John Doe", "123 Main St")
        
        self.assertTrue(result["success"])
        self.assertTrue(result["ssn_valid"])
        self.assertFalse(result["identity_theft_flags"])
        self.assertGreater(result["confidence_score"], 0.8)
        self.assertIn("checks_passed", result)
        self.assertTrue(result["checks_passed"]["ssn_validation"])
    
    def test_check_identity_suspicious(self):
        """Test identity check with suspicious SSN."""
        result = check_identity(self.suspicious_ssn, "Bob Johnson", "789 Elm St")
        
        self.assertTrue(result["success"])
        self.assertFalse(result["ssn_valid"])
        self.assertTrue(result["identity_theft_flags"])
        self.assertLess(result["confidence_score"], 0.5)
    
    def test_verify_income_valid(self):
        """Test income verification with valid SSN."""
        result = verify_income(self.valid_ssn, 85000, "Tech Corp Inc", total_debt_payments=2500)
        
        self.assertTrue(result["success"])
        self.assertTrue(result["income_match"])
        self.assertTrue(result["employment_stable"])
        self.assertIsNotNone(result["dti_ratio"])
        self.assertLess(result["dti_ratio"], 0.43)
        self.assertTrue(result["dti_within_limit"])
    
    def test_verify_income_suspicious(self):
        """Test income verification with suspicious SSN."""
        result = verify_income(self.suspicious_ssn, 45000, total_debt_payments=3000)
        
        self.assertTrue(result["success"])
        self.assertFalse(result["employment_stable"])
        self.assertFalse(result["documentation_complete"])
    
    def test_check_ofac_clean(self):
        """Test OFAC check with clean SSN."""
        result = check_ofac(self.valid_ssn, "John Doe")
        
        self.assertTrue(result["success"])
        self.assertFalse(result["on_ofac_list"])
        self.assertTrue(result["screening_passed"])
        self.assertEqual(result["confidence_score"], 1.0)
    
    def test_check_ofac_match(self):
        """Test OFAC check with matched SSN."""
        result = check_ofac(self.ofac_ssn, "Sanctioned Person")
        
        self.assertTrue(result["success"])
        self.assertTrue(result["on_ofac_list"])
        self.assertFalse(result["screening_passed"])
        self.assertEqual(result["confidence_score"], 0.0)
    
    def test_check_fraud_indicators_low_risk(self):
        """Test fraud check with low-risk applicant."""
        result = check_fraud_indicators(
            self.valid_ssn,
            device_id="device-123",
            ip_address="192.168.1.1",
            application_count_30d=1
        )
        
        self.assertTrue(result["success"])
        self.assertEqual(len(result["fraud_indicators"]), 0)
        self.assertTrue(result["screening_passed"])
        self.assertGreater(result["confidence_score"], 0.7)
    
    def test_check_fraud_indicators_high_risk(self):
        """Test fraud check with high-risk applicant."""
        result = check_fraud_indicators(
            self.suspicious_ssn,
            device_id="device-xyz",
            ip_address="192.168.1.100",
            application_count_30d=5
        )
        
        self.assertTrue(result["success"])
        self.assertGreater(len(result["fraud_indicators"]), 0)
        self.assertFalse(result["screening_passed"])
    
    def test_get_credit_bureau_data_valid(self):
        """Test credit bureau data retrieval."""
        result = get_credit_bureau_data(self.valid_ssn)
        
        self.assertTrue(result["success"])
        self.assertIn("credit_score", result)
        self.assertGreater(result["credit_score"], 600)
        self.assertIn("summary", result)
        self.assertIn("tradelines", result)
    
    def test_get_credit_bureau_data_not_found(self):
        """Test credit bureau data with unknown SSN."""
        result = get_credit_bureau_data("999-99-9999")
        
        self.assertFalse(result["success"])
        self.assertIn("error", result)
        self.assertTrue(result.get("thin_file", False))


class TestAgentRouting(unittest.TestCase):
    """Test agent routing logic."""
    
    def test_identity_verification_routing(self):
        """Test routing for IDENTITY_VERIFICATION."""
        agents = ReviewRuleRouter.get_required_agents("IDENTITY_VERIFICATION")
        
        self.assertEqual(len(agents), 1)
        self.assertEqual(agents[0], AgentType.IDENTITY)
    
    def test_income_validation_routing(self):
        """Test routing for INCOME_VALIDATION."""
        agents = ReviewRuleRouter.get_required_agents("INCOME_VALIDATION")
        
        self.assertEqual(len(agents), 1)
        self.assertEqual(agents[0], AgentType.INCOME)
    
    def test_fraud_check_routing_with_prerequisites(self):
        """Test routing for FRAUD_CHECK includes prerequisites."""
        agents = ReviewRuleRouter.get_required_agents("FRAUD_CHECK", include_prerequisites=True)
        
        # Should include Identity, Income, then Fraud
        self.assertEqual(len(agents), 3)
        self.assertEqual(agents[0], AgentType.IDENTITY)
        self.assertEqual(agents[1], AgentType.INCOME)
        self.assertEqual(agents[2], AgentType.FRAUD)
    
    def test_fraud_check_routing_without_prerequisites(self):
        """Test routing for FRAUD_CHECK without prerequisites."""
        agents = ReviewRuleRouter.get_required_agents("FRAUD_CHECK", include_prerequisites=False)
        
        # Should only include Fraud agent
        self.assertEqual(len(agents), 1)
        self.assertEqual(agents[0], AgentType.FRAUD)
    
    def test_high_risk_profile_routing(self):
        """Test routing for HIGH_RISK_PROFILE."""
        agents = ReviewRuleRouter.get_required_agents("HIGH_RISK_PROFILE")
        
        # Should include all three agents
        self.assertEqual(len(agents), 3)
        self.assertIn(AgentType.IDENTITY, agents)
        self.assertIn(AgentType.INCOME, agents)
        self.assertIn(AgentType.FRAUD, agents)
    
    def test_risk_levels(self):
        """Test risk level classification."""
        self.assertEqual(ReviewRuleRouter.get_risk_level("IDENTITY_VERIFICATION"), "HIGH")
        self.assertEqual(ReviewRuleRouter.get_risk_level("INCOME_VALIDATION"), "MEDIUM")
        self.assertEqual(ReviewRuleRouter.get_risk_level("FRAUD_CHECK"), "CRITICAL")
        self.assertEqual(ReviewRuleRouter.get_risk_level("HIGH_RISK_PROFILE"), "HIGH")
    
    def test_critical_rule_detection(self):
        """Test critical rule detection."""
        self.assertTrue(ReviewRuleRouter.is_critical_rule("FRAUD_CHECK"))
        self.assertFalse(ReviewRuleRouter.is_critical_rule("INCOME_VALIDATION"))
    
    def test_agent_name_strings(self):
        """Test agent name string conversion."""
        names = ReviewRuleRouter.get_agent_names("FRAUD_CHECK")
        
        self.assertIsInstance(names, list)
        self.assertEqual(names, ["identity", "income", "fraud"])
    
    def test_execution_plan_single_rule(self):
        """Test execution plan for single rule."""
        plan = get_agent_execution_plan(["IDENTITY_VERIFICATION"])
        
        self.assertEqual(plan["total_agents"], 1)
        self.assertEqual(plan["execution_order"], ["identity"])
        self.assertEqual(len(plan["rule_details"]), 1)
    
    def test_execution_plan_multiple_rules(self):
        """Test execution plan for multiple rules."""
        plan = get_agent_execution_plan(["IDENTITY_VERIFICATION", "INCOME_VALIDATION"])
        
        self.assertEqual(plan["total_agents"], 2)
        self.assertIn("identity", plan["execution_order"])
        self.assertIn("income", plan["execution_order"])
        self.assertEqual(len(plan["rule_details"]), 2)
    
    def test_execution_plan_with_fraud(self):
        """Test execution plan including fraud check."""
        plan = get_agent_execution_plan(["FRAUD_CHECK"])
        
        # Should include all three agents due to prerequisites
        self.assertEqual(plan["total_agents"], 3)
        self.assertEqual(plan["execution_order"], ["identity", "income", "fraud"])
        self.assertTrue(plan["has_critical_rules"])
    
    def test_execution_plan_deduplication(self):
        """Test that execution plan deduplicates agents."""
        plan = get_agent_execution_plan(["IDENTITY_VERIFICATION", "FRAUD_CHECK"])
        
        # Identity should not be duplicated
        self.assertEqual(plan["execution_order"].count("identity"), 1)
        # Should have all three agents
        self.assertEqual(plan["total_agents"], 3)
    
    def test_routing_summary(self):
        """Test routing summary generation."""
        summary = ReviewRuleRouter.get_routing_summary()
        
        self.assertIsInstance(summary, dict)
        self.assertEqual(len(summary), 4)  # 4 review rules
        
        # Check FRAUD_CHECK has prerequisites
        fraud_summary = summary["FRAUD_CHECK"]
        self.assertEqual(len(fraud_summary["prerequisites"]), 2)
        self.assertIn("identity", fraud_summary["prerequisites"])
        self.assertIn("income", fraud_summary["prerequisites"])


class TestStructuredRulesIntegration(unittest.TestCase):
    """Test integration with structured rules."""
    
    def setUp(self):
        """Load structured rules."""
        if not HAS_POLICY_EXECUTOR:
            self.skipTest("PolicyExecutor not yet implemented")
        
        self.executor = PolicyExecutor()
        try:
            self.executor.load_rules("./policies/structured_rules.json")
        except FileNotFoundError:
            self.skipTest("structured_rules.json not found")
    
    def test_structured_rules_loaded(self):
        """Test that structured rules are loaded."""
        self.assertIsNotNone(self.executor.rules)
        self.assertGreater(len(self.executor.rules), 0)
    
    def test_routing_validation(self):
        """Test that routing matches structured rules."""
        validation = ReviewRuleRouter.validate_structured_rules(self.executor.rules)
        
        # Count warnings
        total_warnings = sum(len(warnings) for warnings in validation.values())
        
        # Should have no validation warnings
        self.assertEqual(total_warnings, 0, 
                        f"Routing validation failed: {validation}")
    
    def test_required_agents_match(self):
        """Test that required_agents field matches routing."""
        for rule_name in self.executor.list_rules():
            rule = self.executor.get_rule(rule_name)
            expected_agents = set(ReviewRuleRouter.get_agent_names(
                rule_name, include_prerequisites=False
            ))
            actual_agents = set(rule.required_agents)
            
            self.assertEqual(
                actual_agents, expected_agents,
                f"Agent mismatch for {rule_name}: expected {expected_agents}, got {actual_agents}"
            )
    
    def test_risk_levels_match(self):
        """Test that risk levels match between routing and structured rules."""
        for rule_name in self.executor.list_rules():
            rule = self.executor.get_rule(rule_name)
            expected_risk = ReviewRuleRouter.get_risk_level(rule_name)
            
            self.assertEqual(
                rule.risk_level, expected_risk,
                f"Risk level mismatch for {rule_name}"
            )


class TestFraudCheckCascade(unittest.TestCase):
    """Test FRAUD_CHECK cascade behavior."""
    
    def test_fraud_check_triggers_identity(self):
        """Test that FRAUD_CHECK triggers identity verification."""
        agents = ReviewRuleRouter.get_required_agents("FRAUD_CHECK")
        
        self.assertIn(AgentType.IDENTITY, agents)
    
    def test_fraud_check_triggers_income(self):
        """Test that FRAUD_CHECK triggers income validation."""
        agents = ReviewRuleRouter.get_required_agents("FRAUD_CHECK")
        
        self.assertIn(AgentType.INCOME, agents)
    
    def test_fraud_check_execution_order(self):
        """Test FRAUD_CHECK agent execution order."""
        agents = ReviewRuleRouter.get_required_agents("FRAUD_CHECK")
        
        # Identity should come before Fraud
        identity_idx = agents.index(AgentType.IDENTITY)
        fraud_idx = agents.index(AgentType.FRAUD)
        self.assertLess(identity_idx, fraud_idx)
        
        # Income should come before Fraud
        income_idx = agents.index(AgentType.INCOME)
        self.assertLess(income_idx, fraud_idx)
    
    def test_fraud_scenario_integration(self):
        """Test complete fraud scenario with all three checks."""
        test_ssn = "111-22-3333"
        
        # Step 1: Identity
        identity_result = check_identity(test_ssn, "John Doe", "123 Main St")
        self.assertTrue(identity_result["success"])
        
        # Step 2: Income
        income_result = verify_income(test_ssn, 85000, total_debt_payments=2500)
        self.assertTrue(income_result["success"])
        
        # Step 3: Fraud
        fraud_result = check_fraud_indicators(test_ssn, application_count_30d=1)
        self.assertTrue(fraud_result["success"])
        
        # All should pass for this valid applicant
        identity_passed = all(identity_result["checks_passed"].values())
        income_passed = all(income_result["checks_passed"].values())
        fraud_passed = fraud_result["screening_passed"]
        
        self.assertTrue(identity_passed)
        self.assertTrue(income_passed)
        self.assertTrue(fraud_passed)


def run_tests():
    """Run all tests and display results."""
    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    suite.addTests(loader.loadTestsFromTestCase(TestMockAPIs))
    suite.addTests(loader.loadTestsFromTestCase(TestAgentRouting))
    suite.addTests(loader.loadTestsFromTestCase(TestStructuredRulesIntegration))
    suite.addTests(loader.loadTestsFromTestCase(TestFraudCheckCascade))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Print summary
    print("\n" + "=" * 70)
    print("TEST SUMMARY")
    print("=" * 70)
    print(f"Tests Run: {result.testsRun}")
    print(f"Successes: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print(f"Skipped: {len(result.skipped)}")
    
    if result.wasSuccessful():
        print("\n✅ ALL TESTS PASSED!")
    else:
        print("\n❌ SOME TESTS FAILED")
    
    return result.wasSuccessful()


if __name__ == "__main__":
    import sys
    success = run_tests()
    sys.exit(0 if success else 1)
