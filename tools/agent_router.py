"""
Agent routing logic based on review rules.

This module determines which agents should be invoked based on the review rule type.
Special handling for FRAUD_CHECK which requires Identity and Income verification first.
"""

from typing import List, Dict, Set
from enum import Enum


class AgentType(Enum):
    """Available agent types in the underwriting system."""
    IDENTITY = "identity"
    INCOME = "income"
    FRAUD = "fraud"


class ReviewRuleRouter:
    """
    Routes review rules to appropriate agents based on policy configuration.
    
    Routing Rules:
    - IDENTITY_VERIFICATION → Identity Agent
    - INCOME_VALIDATION → Income Agent
    - FRAUD_CHECK → Fraud Agent (+ Identity + Income as prerequisites)
    - HIGH_RISK_PROFILE → All Agents (Identity + Income + Fraud)
    """
    
    # Core routing map from review rules to primary agents
    ROUTING_MAP = {
        "IDENTITY_VERIFICATION": [AgentType.IDENTITY],
        "INCOME_VALIDATION": [AgentType.INCOME],
        "FRAUD_CHECK": [AgentType.FRAUD],
        "HIGH_RISK_PROFILE": [AgentType.IDENTITY, AgentType.INCOME, AgentType.FRAUD],
    }
    
    # Special prerequisites - agents that must run BEFORE the primary agent
    PREREQUISITES = {
        "FRAUD_CHECK": [AgentType.IDENTITY, AgentType.INCOME],
        # HIGH_RISK_PROFILE already includes all agents, no extra prerequisites
    }
    
    # Risk levels by review rule
    RISK_LEVELS = {
        "IDENTITY_VERIFICATION": "HIGH",
        "INCOME_VALIDATION": "MEDIUM",
        "FRAUD_CHECK": "CRITICAL",
        "HIGH_RISK_PROFILE": "HIGH",
    }
    
    @classmethod
    def get_required_agents(cls, review_rule: str, include_prerequisites: bool = True) -> List[AgentType]:
        """
        Get the list of agents required for a review rule.
        
        Args:
            review_rule: The review rule name (e.g., "FRAUD_CHECK")
            include_prerequisites: If True, includes prerequisite agents before primary agents
            
        Returns:
            List of AgentType in execution order
            
        Example:
            >>> ReviewRuleRouter.get_required_agents("FRAUD_CHECK")
            [AgentType.IDENTITY, AgentType.INCOME, AgentType.FRAUD]
            
            >>> ReviewRuleRouter.get_required_agents("FRAUD_CHECK", include_prerequisites=False)
            [AgentType.FRAUD]
        """
        if review_rule not in cls.ROUTING_MAP:
            raise ValueError(f"Unknown review rule: {review_rule}. Valid rules: {list(cls.ROUTING_MAP.keys())}")
        
        agents = []
        
        # Add prerequisites first (if enabled)
        if include_prerequisites and review_rule in cls.PREREQUISITES:
            for agent in cls.PREREQUISITES[review_rule]:
                if agent not in agents:
                    agents.append(agent)
        
        # Add primary agents
        for agent in cls.ROUTING_MAP[review_rule]:
            if agent not in agents:
                agents.append(agent)
        
        return agents
    
    @classmethod
    def get_agent_names(cls, review_rule: str, include_prerequisites: bool = True) -> List[str]:
        """
        Get the list of agent names (as strings) required for a review rule.
        
        Args:
            review_rule: The review rule name
            include_prerequisites: If True, includes prerequisite agents
            
        Returns:
            List of agent names as strings
            
        Example:
            >>> ReviewRuleRouter.get_agent_names("FRAUD_CHECK")
            ["identity", "income", "fraud"]
        """
        agents = cls.get_required_agents(review_rule, include_prerequisites)
        return [agent.value for agent in agents]
    
    @classmethod
    def requires_prerequisites(cls, review_rule: str) -> bool:
        """
        Check if a review rule requires prerequisite agents.
        
        Args:
            review_rule: The review rule name
            
        Returns:
            True if prerequisites are required
        """
        return review_rule in cls.PREREQUISITES
    
    @classmethod
    def get_risk_level(cls, review_rule: str) -> str:
        """
        Get the risk level for a review rule.
        
        Args:
            review_rule: The review rule name
            
        Returns:
            Risk level string (HIGH, MEDIUM, CRITICAL)
        """
        return cls.RISK_LEVELS.get(review_rule, "MEDIUM")
    
    @classmethod
    def is_critical_rule(cls, review_rule: str) -> bool:
        """
        Check if a review rule is CRITICAL (highest priority).
        
        Args:
            review_rule: The review rule name
            
        Returns:
            True if CRITICAL risk level
        """
        return cls.get_risk_level(review_rule) == "CRITICAL"
    
    @classmethod
    def get_all_review_rules(cls) -> List[str]:
        """
        Get list of all supported review rules.
        
        Returns:
            List of review rule names
        """
        return list(cls.ROUTING_MAP.keys())
    
    @classmethod
    def get_routing_summary(cls) -> Dict[str, Dict]:
        """
        Get a complete summary of all routing configurations.
        
        Returns:
            Dict with routing details for each review rule
        """
        summary = {}
        for rule in cls.get_all_review_rules():
            summary[rule] = {
                "primary_agents": [a.value for a in cls.ROUTING_MAP[rule]],
                "prerequisites": [a.value for a in cls.PREREQUISITES.get(rule, [])],
                "execution_order": cls.get_agent_names(rule, include_prerequisites=True),
                "risk_level": cls.get_risk_level(rule),
                "is_critical": cls.is_critical_rule(rule),
            }
        return summary
    
    @classmethod
    def validate_structured_rules(cls, structured_rules: Dict) -> Dict[str, List[str]]:
        """
        Validate that structured rules match the routing configuration.
        
        Args:
            structured_rules: Dict loaded from structured_rules.json
            
        Returns:
            Dict with validation results (warnings for each rule)
        """
        validation_results = {}
        
        for rule_name, rule_config in structured_rules.items():
            warnings = []
            
            # Check if rule is recognized
            if rule_name not in cls.ROUTING_MAP:
                warnings.append(f"Unknown review rule: {rule_name}")
                validation_results[rule_name] = warnings
                continue
            
            # Check required_agents field
            if "required_agents" not in rule_config:
                warnings.append("Missing 'required_agents' field")
            else:
                configured_agents = set(rule_config["required_agents"])
                expected_agents = set(cls.get_agent_names(rule_name, include_prerequisites=False))
                
                if configured_agents != expected_agents:
                    warnings.append(
                        f"Agent mismatch - Expected: {expected_agents}, Got: {configured_agents}"
                    )
            
            # Check risk level
            if "risk_level" in rule_config:
                if rule_config["risk_level"] != cls.get_risk_level(rule_name):
                    warnings.append(
                        f"Risk level mismatch - Expected: {cls.get_risk_level(rule_name)}, "
                        f"Got: {rule_config['risk_level']}"
                    )
            
            validation_results[rule_name] = warnings
        
        return validation_results


def get_agent_execution_plan(review_rules: List[str]) -> Dict:
    """
    Create an execution plan for multiple review rules.
    
    Handles:
    - Deduplication of agents across multiple rules
    - Correct execution order with prerequisites
    - Priority ordering (CRITICAL first)
    
    Args:
        review_rules: List of review rule names to execute
        
    Returns:
        Dict with execution plan including agent order and rule details
        
    Example:
        >>> plan = get_agent_execution_plan(["INCOME_VALIDATION", "FRAUD_CHECK"])
        >>> print(plan["execution_order"])
        ["identity", "income", "fraud"]
    """
    # Sort rules by priority (CRITICAL > HIGH > MEDIUM)
    priority_order = {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2}
    sorted_rules = sorted(
        review_rules,
        key=lambda r: priority_order.get(ReviewRuleRouter.get_risk_level(r), 3)
    )
    
    # Collect all required agents maintaining order
    all_agents: List[AgentType] = []
    seen_agents: Set[AgentType] = set()
    
    rule_details = []
    
    for rule in sorted_rules:
        required_agents = ReviewRuleRouter.get_required_agents(rule, include_prerequisites=True)
        
        # Add agents in order, avoiding duplicates
        for agent in required_agents:
            if agent not in seen_agents:
                all_agents.append(agent)
                seen_agents.add(agent)
        
        rule_details.append({
            "rule": rule,
            "risk_level": ReviewRuleRouter.get_risk_level(rule),
            "agents": [a.value for a in required_agents],
            "is_critical": ReviewRuleRouter.is_critical_rule(rule),
        })
    
    return {
        "execution_order": [a.value for a in all_agents],
        "total_agents": len(all_agents),
        "rules_by_priority": sorted_rules,
        "rule_details": rule_details,
        "has_critical_rules": any(ReviewRuleRouter.is_critical_rule(r) for r in review_rules),
    }


if __name__ == "__main__":
    print("=" * 70)
    print("AGENT ROUTING CONFIGURATION")
    print("=" * 70)
    
    # Show routing summary
    print("\n1. Routing Summary:")
    print("-" * 70)
    import json
    summary = ReviewRuleRouter.get_routing_summary()
    print(json.dumps(summary, indent=2))
    
    # Test individual rule routing
    print("\n2. Individual Rule Examples:")
    print("-" * 70)
    
    for rule in ReviewRuleRouter.get_all_review_rules():
        agents = ReviewRuleRouter.get_agent_names(rule)
        risk = ReviewRuleRouter.get_risk_level(rule)
        print(f"\n{rule} ({risk}):")
        print(f"  Agents: {' → '.join(agents)}")
        if ReviewRuleRouter.requires_prerequisites(rule):
            prereqs = [a.value for a in ReviewRuleRouter.PREREQUISITES[rule]]
            print(f"  Prerequisites: {', '.join(prereqs)}")
    
    # Test execution plan for multiple rules
    print("\n3. Multi-Rule Execution Plan:")
    print("-" * 70)
    test_rules = ["INCOME_VALIDATION", "FRAUD_CHECK", "IDENTITY_VERIFICATION"]
    plan = get_agent_execution_plan(test_rules)
    print(json.dumps(plan, indent=2))
    
    print("\n" + "=" * 70)
    print("KEY INSIGHTS:")
    print("=" * 70)
    print("• FRAUD_CHECK triggers Identity + Income verification first")
    print("• HIGH_RISK_PROFILE invokes all three agents")
    print("• CRITICAL rules are executed with highest priority")
    print("• Agent deduplication prevents redundant checks")
