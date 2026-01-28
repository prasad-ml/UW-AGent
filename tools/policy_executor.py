"""
Policy Executor - Converts policy documents into structured rules.

This module processes natural language policy documents and generates
semi-structured JSON rules for fast runtime lookup, eliminating the need
for vector DB queries during application processing.
"""

import json
import logging
from typing import Dict, List, Optional
from pathlib import Path
from pydantic import BaseModel, Field

from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from config import settings
from tools.vector_store import PolicyVectorStore

logger = logging.getLogger(__name__)


# Pydantic models for structured rules
class CheckConfig(BaseModel):
    """Configuration for an individual check."""
    name: str = Field(..., description="Check name")
    description: str = Field(..., description="Check description")
    tool: str = Field(..., description="Tool/API to use")
    required: bool = Field(True, description="Whether check is required")
    threshold: Optional[float | str] = Field(None, description="Threshold value if applicable")
    zero_tolerance: bool = Field(False, description="Whether any failure is critical")


class WorkflowConfig(BaseModel):
    """Workflow execution configuration."""
    parallel_execution: bool = Field(False, description="Execute checks in parallel")
    timeout_seconds: int = Field(30, description="Timeout for workflow")
    retry_on_failure: bool = Field(False, description="Retry on failure")
    cascade_mode: bool = Field(False, description="Stop on first failure")


class DecisionCriteria(BaseModel):
    """Decision-making criteria."""
    approval_condition: str = Field(..., description="Condition for approval")
    min_confidence: float = Field(0.8, description="Minimum confidence score")
    dti_threshold: Optional[float] = Field(None, description="DTI threshold if applicable")
    zero_tolerance_checks: List[str] = Field(default_factory=list, description="Zero tolerance check names")
    requires_manual_signoff: bool = Field(False, description="Requires manual review")


class StructuredRule(BaseModel):
    """Complete structured rule for a review rule."""
    description: str = Field(..., description="Rule description")
    risk_level: str = Field(..., description="Risk level: LOW, MEDIUM, HIGH, CRITICAL")
    required_agents: List[str] = Field(..., description="Required agent names")
    checks: List[CheckConfig] = Field(default_factory=list, description="Individual checks")
    decision_criteria: DecisionCriteria = Field(..., description="Decision criteria")
    workflow_config: WorkflowConfig = Field(..., description="Workflow configuration")


class PolicyExecutor:
    """
    Policy Executor converts natural language policies into structured rules.
    
    This optimization eliminates runtime vector DB queries and LLM calls,
    providing instant rule lookup from cached JSON.
    """
    
    def __init__(self, vector_store: Optional[PolicyVectorStore] = None):
        """
        Initialize Policy Executor.
        
        Args:
            vector_store: Optional PolicyVectorStore for policy retrieval
        """
        self.vector_store = vector_store
        self.structured_rules: Dict[str, StructuredRule] = {}
        self.llm = None
        
        logger.info("PolicyExecutor initialized")
    
    def initialize(self, vector_store: PolicyVectorStore) -> None:
        """
        Initialize with vector store reference.
        
        Args:
            vector_store: PolicyVectorStore instance
        """
        self.vector_store = vector_store
        
        # Initialize LLM for rule generation
        self.llm = ChatOpenAI(
            model=settings.openai_model,
            temperature=0.1,  # Low temperature for consistent extraction
            openai_api_key=settings.openai_api_key
        )
        
        logger.info("PolicyExecutor initialized with vector store and LLM")
    
    def _create_extraction_prompt(self) -> ChatPromptTemplate:
        """
        Create prompt template for extracting structured rules from policies.
        
        Returns:
            ChatPromptTemplate for rule extraction
        """
        template = """You are an expert at analyzing underwriting policy documents and extracting structured information.

Given the following policy document, extract and structure the information into JSON format.

Policy Document:
{policy_text}

Extract the following information:
1. Review rule name (from REVIEW_RULE: line)
2. Description
3. Risk level (LOW, MEDIUM, HIGH, or CRITICAL)
4. Required agents (identity, income, fraud, or combination)
5. Individual checks required
6. Decision criteria
7. Workflow configuration

For each check, identify:
- Check name (snake_case)
- Description
- Tool/API to use (check_identity, verify_income, check_fraud_indicators, check_ofac, etc.)
- Whether it's required
- Any thresholds (e.g., DTI < 43%)
- Zero tolerance flags

Respond with ONLY valid JSON in this exact format:
{{
  "rule_name": "IDENTITY_VERIFICATION",
  "description": "Policy description",
  "risk_level": "HIGH",
  "required_agents": ["identity"],
  "checks": [
    {{
      "name": "ssn_validation",
      "description": "Verify SSN",
      "tool": "check_identity",
      "required": true,
      "threshold": null,
      "zero_tolerance": false
    }}
  ],
  "decision_criteria": {{
    "approval_condition": "all_checks_pass",
    "min_confidence": 0.8,
    "dti_threshold": null,
    "zero_tolerance_checks": [],
    "requires_manual_signoff": false
  }},
  "workflow_config": {{
    "parallel_execution": false,
    "timeout_seconds": 30,
    "retry_on_failure": true,
    "cascade_mode": false
  }}
}}

JSON:"""
        
        return ChatPromptTemplate.from_template(template)
    
    def _parse_policy_to_rule(self, policy_text: str, review_rule: str) -> Optional[StructuredRule]:
        """
        Parse a policy document into a structured rule using LLM.
        
        Args:
            policy_text: Raw policy text
            review_rule: Review rule name
            
        Returns:
            StructuredRule or None if parsing fails
        """
        try:
            prompt = self._create_extraction_prompt()
            
            # Generate structured data using LLM
            messages = prompt.format_messages(policy_text=policy_text)
            response = self.llm.invoke(messages)
            
            logger.debug(f"LLM Response for {review_rule}: {response.content[:200]}")
            
            # Parse JSON response - handle potential markdown wrapping
            content = response.content.strip()
            
            # Remove markdown code blocks if present
            if content.startswith("```json"):
                content = content[7:]  # Remove ```json
            if content.startswith("```"):
                content = content[3:]  # Remove ```
            if content.endswith("```"):
                content = content[:-3]  # Remove trailing ```
            
            content = content.strip()
            
            # Parse JSON
            rule_data = json.loads(content)
            
            # Handle case where LLM returns an array
            if isinstance(rule_data, list):
                # Find the matching rule
                for item in rule_data:
                    if item.get("rule_name", "").upper() == review_rule.upper():
                        rule_data = item
                        break
                else:
                    # If no match found, use first item
                    if rule_data:
                        rule_data = rule_data[0]
                    else:
                        logger.error(f"No rule data found in array for {review_rule}")
                        return None
            
            # Convert to Pydantic model
            structured_rule = StructuredRule(
                description=rule_data["description"],
                risk_level=rule_data["risk_level"],
                required_agents=rule_data["required_agents"],
                checks=[CheckConfig(**check) for check in rule_data["checks"]],
                decision_criteria=DecisionCriteria(**rule_data["decision_criteria"]),
                workflow_config=WorkflowConfig(**rule_data["workflow_config"])
            )
            
            logger.info(f"Successfully parsed policy for {review_rule}")
            return structured_rule
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON for {review_rule}: {e}")
            logger.error(f"LLM response: {response.content if 'response' in locals() else 'N/A'}")
            return None
        except Exception as e:
            logger.error(f"Error parsing policy {review_rule}: {e}")
            logger.error(f"Response content: {response.content[:500] if 'response' in locals() else 'N/A'}")
            import traceback
            logger.error(traceback.format_exc())
            return None
    
    def generate_structured_rules(self) -> Dict[str, Dict]:
        """
        Generate structured rules from all policies in vector store.
        
        Returns:
            Dictionary of structured rules keyed by review rule name
        """
        if not self.vector_store:
            raise RuntimeError("Vector store not initialized. Call initialize() first.")
        
        if not self.llm:
            raise RuntimeError("LLM not initialized. Call initialize() first.")
        
        logger.info("Generating structured rules from policies...")
        
        # Get all policy names
        policy_names = self.vector_store.list_all_policies()
        logger.info(f"Found {len(policy_names)} policies to process")
        
        generated_rules = {}
        
        for review_rule in policy_names:
            logger.info(f"Processing policy: {review_rule}")
            
            # Get complete policy text
            policy_text = self.vector_store.get_policy_by_rule(review_rule)
            
            if not policy_text:
                logger.warning(f"No policy found for {review_rule}")
                continue
            
            # Parse policy to structured rule
            structured_rule = self._parse_policy_to_rule(policy_text, review_rule)
            
            if structured_rule:
                # Store as dict for JSON serialization
                self.structured_rules[review_rule] = structured_rule
                generated_rules[review_rule] = structured_rule.model_dump()
            else:
                logger.warning(f"Failed to generate structured rule for {review_rule}")
        
        logger.info(f"Successfully generated {len(generated_rules)} structured rules")
        return generated_rules
    
    def save_rules(self, filepath: str) -> None:
        """
        Save structured rules to JSON file.
        
        Args:
            filepath: Path to save JSON file
        """
        if not self.structured_rules:
            logger.warning("No structured rules to save")
            return
        
        # Convert Pydantic models to dict
        rules_dict = {
            rule_name: rule.model_dump()
            for rule_name, rule in self.structured_rules.items()
        }
        
        # Ensure directory exists
        Path(filepath).parent.mkdir(parents=True, exist_ok=True)
        
        # Save to JSON
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(rules_dict, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Saved {len(rules_dict)} structured rules to {filepath}")
    
    def load_rules(self, filepath: str) -> Dict[str, StructuredRule]:
        """
        Load pre-generated structured rules from JSON file.
        
        Args:
            filepath: Path to JSON file
            
        Returns:
            Dictionary of structured rules
        """
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                rules_dict = json.load(f)
            
            # Convert to Pydantic models
            self.structured_rules = {
                rule_name: StructuredRule(**rule_data)
                for rule_name, rule_data in rules_dict.items()
            }
            
            logger.info(f"Loaded {len(self.structured_rules)} structured rules from {filepath}")
            return self.structured_rules
            
        except FileNotFoundError:
            logger.error(f"Rules file not found: {filepath}")
            return {}
        except Exception as e:
            logger.error(f"Error loading rules: {e}")
            return {}
    
    def get_workflow_config(self, review_rule: str) -> Optional[Dict]:
        """
        Get workflow configuration for a specific review rule.
        
        Args:
            review_rule: Review rule name
            
        Returns:
            Workflow configuration dictionary or None
        """
        if review_rule not in self.structured_rules:
            logger.warning(f"No structured rule found for {review_rule}")
            return None
        
        rule = self.structured_rules[review_rule]
        return {
            "review_rule": review_rule,
            "description": rule.description,
            "risk_level": rule.risk_level,
            "required_agents": rule.required_agents,
            "checks": [check.model_dump() for check in rule.checks],
            "workflow_config": rule.workflow_config.model_dump()
        }
    
    def get_decision_criteria(self, review_rule: str) -> Optional[Dict]:
        """
        Get decision criteria for a specific review rule.
        
        Args:
            review_rule: Review rule name
            
        Returns:
            Decision criteria dictionary or None
        """
        if review_rule not in self.structured_rules:
            logger.warning(f"No structured rule found for {review_rule}")
            return None
        
        return self.structured_rules[review_rule].decision_criteria.model_dump()
    
    def get_rule(self, review_rule: str) -> Optional[StructuredRule]:
        """
        Get complete structured rule for a review rule.
        
        Args:
            review_rule: Review rule name
            
        Returns:
            StructuredRule or None
        """
        return self.structured_rules.get(review_rule)
    
    def list_rules(self) -> List[str]:
        """
        List all available review rules.
        
        Returns:
            List of review rule names
        """
        return list(self.structured_rules.keys())
    
    def refresh_rules(self) -> Dict[str, Dict]:
        """
        Re-generate structured rules from updated policies.
        
        Returns:
            Dictionary of newly generated rules
        """
        logger.info("Refreshing structured rules...")
        return self.generate_structured_rules()
    
    def get_stats(self) -> Dict:
        """
        Get statistics about loaded rules.
        
        Returns:
            Dictionary with statistics
        """
        total_checks = sum(
            len(rule.checks)
            for rule in self.structured_rules.values()
        )
        
        risk_levels = {}
        for rule in self.structured_rules.values():
            risk_level = rule.risk_level
            risk_levels[risk_level] = risk_levels.get(risk_level, 0) + 1
        
        return {
            "total_rules": len(self.structured_rules),
            "total_checks": total_checks,
            "risk_level_distribution": risk_levels,
            "rules": list(self.structured_rules.keys())
        }
