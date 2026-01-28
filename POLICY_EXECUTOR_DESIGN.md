# Policy Executor - Technical Deep Dive

## Overview

The **Policy Executor** is a key optimization component that converts natural language policy documents into semi-structured rules during initialization. This eliminates the need for vector DB queries and LLM reasoning during runtime, significantly improving performance and reducing costs.

## Architecture Flow

### One-Time Setup (Initialization)
```
1. Load Policies → Vector DB (ChromaDB)
2. Policy Executor reads from Vector DB
3. LLM processes and structures policies
4. Generate structured_rules.json
5. Save to disk for future use
```

### Runtime (Per Application)
```
1. Application arrives
2. Load structured_rules.json (instant, no LLM)
3. Orchestrator reads relevant rules
4. Execute workflow based on pre-processed rules
5. No vector DB queries needed!
```

## Benefits Comparison

| Aspect | Without Policy Executor | With Policy Executor |
|--------|------------------------|----------------------|
| **Initialization** | Load policies to Vector DB | Load policies + Generate rules |
| **Per Application** | Query Vector DB + LLM reasoning | Read JSON file (instant) |
| **LLM Calls** | Every application (~3-5 calls) | Zero during runtime |
| **Latency** | 2-5 seconds per application | <100ms for rule lookup |
| **Cost** | $0.01-0.05 per application | $0 (after setup) |
| **Consistency** | May vary based on LLM | 100% consistent |
| **Debuggability** | Hard to inspect policies | Easy - just read JSON |

## Structured Rule Format

### Input (Policy Document)
```
REVIEW_RULE: IDENTITY_VERIFICATION
Description: Perform identity verification when customer information cannot be verified
Checks Required:
- Verify SSN against credit bureau records
- Check for identity theft flags
- Validate address history
Risk Level: HIGH
Decision Criteria: All checks must pass for approval
```

### Output (Structured Rule)
```json
{
  "IDENTITY_VERIFICATION": {
    "description": "Perform identity verification when customer information cannot be verified",
    "risk_level": "HIGH",
    "required_agents": ["identity"],
    "checks": [
      {
        "name": "ssn_validation",
        "description": "Verify SSN against credit bureau records",
        "tool": "check_identity",
        "required": true
      },
      {
        "name": "identity_theft_check",
        "description": "Check for identity theft flags",
        "tool": "check_identity",
        "required": true
      },
      {
        "name": "address_verification",
        "description": "Validate address history",
        "tool": "check_identity",
        "required": true
      }
    ],
    "decision_criteria": {
      "approval_condition": "all_checks_pass",
      "min_confidence": 0.8,
      "allow_manual_override": false
    },
    "workflow_config": {
      "parallel_execution": false,
      "timeout_seconds": 30,
      "retry_on_failure": true
    }
  }
}
```

## Implementation Details

### PolicyExecutor Class

```python
class PolicyExecutor:
    def __init__(self, vector_store: PolicyVectorStore):
        self.vector_store = vector_store
        self.structured_rules = {}
        
    def generate_structured_rules(self) -> Dict[str, StructuredRule]:
        """
        One-time generation of structured rules from policy documents.
        Uses LLM to extract and structure information.
        """
        # 1. Get all policy documents from vector store
        # 2. For each policy, use LLM to extract:
        #    - Review rule name
        #    - Description
        #    - Risk level
        #    - Required agents
        #    - Individual checks
        #    - Decision criteria
        #    - Workflow configuration
        # 3. Validate structure with Pydantic models
        # 4. Return structured rules dictionary
        
    def save_rules(self, filepath: str):
        """Save structured rules to JSON file"""
        
    def load_rules(self, filepath: str):
        """Load pre-generated rules from JSON"""
        
    def get_workflow_config(self, review_rule: str) -> Dict:
        """Get workflow configuration for a specific rule"""
        
    def get_decision_criteria(self, review_rule: str) -> Dict:
        """Get decision criteria for a specific rule"""
```

### Pydantic Models

```python
from pydantic import BaseModel
from typing import List, Dict, Optional

class CheckConfig(BaseModel):
    name: str
    description: str
    tool: str
    required: bool
    threshold: Optional[float] = None
    zero_tolerance: Optional[bool] = False

class WorkflowConfig(BaseModel):
    parallel_execution: bool = False
    timeout_seconds: int = 30
    retry_on_failure: bool = False
    cascade_mode: bool = False

class DecisionCriteria(BaseModel):
    approval_condition: str
    min_confidence: float
    dti_threshold: Optional[float] = None
    zero_tolerance_checks: Optional[List[str]] = []
    requires_manual_signoff: bool = False

class StructuredRule(BaseModel):
    description: str
    risk_level: str
    required_agents: List[str]
    checks: List[CheckConfig]
    decision_criteria: DecisionCriteria
    workflow_config: WorkflowConfig
```

## Usage in Orchestrator

### Before (With Vector DB Query)
```python
def process_application(application):
    # Query vector DB for each review rule (slow, uses LLM)
    for rule in application.review_rules:
        policy = vector_store.query_policy(rule)  # 1-2 seconds + LLM call
        # Parse and interpret policy with LLM
        workflow = interpret_policy(policy)  # Another LLM call
        # Execute workflow
```

### After (With Policy Executor)
```python
def process_application(application):
    # Load pre-processed rules (instant, no LLM)
    for rule in application.review_rules:
        structured_rule = policy_executor.get_workflow_config(rule)  # <1ms
        # Rules already structured and ready to use
        # Execute workflow directly
```

## When to Regenerate Rules

Rules should be regenerated when:
1. Policy documents are updated
2. New review rules are added
3. Decision criteria change
4. Workflow configurations are modified

Command: `python main.py --regenerate-rules`

## Trade-offs

### Advantages
✅ **Performance**: Eliminates 2-5 seconds per application
✅ **Cost**: Saves $0.01-0.05 per application (LLM calls)
✅ **Consistency**: Same rules every time
✅ **Debuggability**: JSON is easy to inspect and modify
✅ **Reliability**: No dependency on Vector DB during runtime

### Disadvantages
❌ **Initial Setup**: Takes longer to initialize (one-time)
❌ **Manual Updates**: Rules need regeneration when policies change
❌ **Storage**: Additional JSON file (minimal ~50KB)
❌ **Flexibility**: Less dynamic than real-time policy interpretation

## Best Practices

1. **Version Control**: Track `structured_rules.json` in git
2. **Validation**: Always validate rules after generation
3. **Testing**: Test rules against sample applications
4. **Documentation**: Document rule generation process
5. **Monitoring**: Log when rules are loaded/regenerated
6. **Backup**: Keep Vector DB for policy explanations/audits

## POC vs Production

### POC Approach
- Generate rules once during setup
- Store in local JSON file
- Manual regeneration when needed
- Simple validation

### Production Considerations
- Automated rule regeneration pipeline
- Version control for rules
- A/B testing for rule changes
- Advanced validation and testing
- Rule analytics and monitoring
- Rollback capabilities
- Multi-environment support (dev/staging/prod)

## Example: Complete Flow

```python
# main.py

# ONE-TIME SETUP (Run once or when policies change)
def initialize_system():
    # 1. Load policies to vector DB
    vector_store = PolicyVectorStore()
    vector_store.load_policies(policy_texts)
    
    # 2. Generate structured rules
    policy_executor = PolicyExecutor(vector_store)
    policy_executor.generate_structured_rules()  # Uses LLM once
    policy_executor.save_rules("policies/structured_rules.json")
    
    print("✅ System initialized. Rules generated and saved.")

# RUNTIME (Every application)
def process_application(application):
    # Load pre-processed rules (fast!)
    policy_executor = PolicyExecutor()
    policy_executor.load_rules("policies/structured_rules.json")
    
    # Orchestrator uses rules directly
    orchestrator = UnderwritingOrchestrator(policy_executor)
    decision = orchestrator.process(application)
    
    return decision
```

## Performance Metrics (Estimated)

| Operation | Without Policy Executor | With Policy Executor |
|-----------|------------------------|----------------------|
| System Init | 5-10 seconds | 15-20 seconds |
| Per App (Cold) | 3-5 seconds | 0.5-1 second |
| Per App (Warm) | 2-3 seconds | 0.3-0.5 seconds |
| LLM Calls/App | 3-5 | 0 |
| Cost/App | $0.01-0.05 | $0 |
| Vector DB Queries/App | 1-3 | 0 |

**ROI**: After ~50 applications, the Policy Executor pays for itself in cost savings alone. Performance benefits are immediate.

---

**Conclusion**: The Policy Executor is a crucial optimization that transforms dynamic policy retrieval into static rule lookup, dramatically improving performance and reducing costs while maintaining flexibility through easy rule regeneration.
