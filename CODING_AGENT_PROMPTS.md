# Coding Agent Prompts for Underwriting AI Assistant POC

## Tech Stack
- **Framework**: LangGraph (for agent orchestration)
- **LLM**: OpenAI GPT-4 or GPT-3.5-turbo
- **Vector DB**: ChromaDB (for policy document storage and retrieval)
- **Language**: Python 3.10+
- **Additional Libraries**: 
  - `langchain` and `langgraph` for agent framework
  - `chromadb` for vector database
  - `pydantic` for data models
  - `fastapi` (optional, for API wrapper)
  - `python-dotenv` for environment variables
  - `pyyaml` for structured rule storage

---

## Prompt 1: Project Setup & Base Structure

**Task**: Set up the project structure and implement base configuration

**Requirements**:
1. Create a Python project with the following structure:
```
UW-AGent/
├── README.md
├── requirements.txt
├── .env.example
├── config/
│   ├── __init__.py
│   └── settings.py
├── models/
│   ├── __init__.py
│   └── application.py
├── agents/
│   ├── __init__.py
│   ├── orchestrator.py
│   ├── identity_agent.py
│   ├── income_agent.py
│   ├── fraud_agent.py
│   └── base_agent.py
├── tools/
│   ├── __init__.py
│   ├── mock_apis.py
│   ├── vector_store.py
│   └── policy_executor.py
├── policies/
│   ├── sample_policies.txt
│   └── structured_rules.json
├── main.py
└── tests/
    └── __init__.py
```

2. Create `requirements.txt` with:
```
langchain>=0.1.0
langgraph>=0.0.40
openai>=1.10.0
chromadb>=0.4.22
pydantic>=2.5.0
python-dotenv>=1.0.0
fastapi>=0.109.0
uvicorn>=0.27.0
pyyaml>=6.0.1
```

3. Create `.env.example` with:
```
OPENAI_API_KEY=your_openai_api_key_here
CHROMA_PERSIST_DIRECTORY=./chroma_db
```

4. Implement `config/settings.py` with configuration management using pydantic Settings
5. Create basic Pydantic models in `models/application.py` for:
   - `CreditApplication` (with fields: application_id, customer_name, ssn, annual_income, credit_score, dti_ratio, review_rules)
   - `UnderwritingDecision` (with fields: application_id, decision, confidence_score, findings, timestamp)
   - `AgentFinding` (with fields: agent_name, check_type, status, details, risk_level)

**Expected Output**: Complete project structure with base configuration and data models

---

## Prompt 2: Vector Store & Policy Management

**Task**: Implement ChromaDB integration for policy document storage and retrieval

**Requirements**:
1. In `tools/vector_store.py`, create a `PolicyVectorStore` class with methods:
   - `initialize_db()`: Initialize ChromaDB with persistent storage
   - `load_policies(policy_texts: List[str])`: Embed and store policy documents
   - `query_policy(review_rule: str, top_k: int = 3)`: Query relevant policy sections based on review rule

2. Create sample policy documents in `policies/sample_policies.txt`:
```
REVIEW_RULE: IDENTITY_VERIFICATION
Description: Perform identity verification when customer information cannot be verified through automated systems
Checks Required:
- Verify SSN against credit bureau records
- Check for identity theft flags
- Validate address history
- Cross-reference with government databases
Risk Level: HIGH
Decision Criteria: All checks must pass for approval

REVIEW_RULE: INCOME_VALIDATION
Description: Validate stated income when it exceeds normal thresholds or lacks documentation
Checks Required:
- Verify employment status
- Validate income documentation
- Check income stability (3+ months)
- Calculate DTI ratio (must be < 43%)
Risk Level: MEDIUM
Decision Criteria: Income must be verified and DTI within limits

REVIEW_RULE: FRAUD_CHECK
Description: Investigate potential fraud indicators flagged by the system
Checks Required:
- Check OFAC sanctions list
- Verify recent credit inquiries pattern
- Analyze application velocity
- Cross-check device/IP fingerprint
Risk Level: CRITICAL
Decision Criteria: No fraud indicators allowed for approval

REVIEW_RULE: HIGH_RISK_PROFILE
Description: Additional scrutiny for high-risk applicants
Checks Required:
- Comprehensive identity verification
- Enhanced income validation
- Fraud screening
- Review past credit behavior
Risk Level: HIGH
Decision Criteria: Must pass all checks with manual review sign-off
```

3. Implement text chunking and embedding logic
4. Use OpenAI embeddings for vectorization
5. Add error handling and logging

**Expected Output**: Functional vector store that can load policies and retrieve relevant sections based on review rules

---

## Prompt 2a: Policy Executor - Structured Rule Generation

**Task**: Create a Policy Executor that converts policy documents into semi-structured rules for fast lookup

**Requirements**:
1. In `tools/policy_executor.py`, create a `PolicyExecutor` class with methods:
   - `initialize(vector_store: PolicyVectorStore)`: Initialize with vector store reference
   - `generate_structured_rules()`: Process all policies and create structured rules
   - `get_workflow_config(review_rule: str) -> Dict`: Get pre-processed workflow configuration
   - `get_decision_criteria(review_rule: str) -> Dict`: Get decision criteria for a rule
   - `save_rules(filepath: str)`: Save structured rules to JSON file
   - `load_rules(filepath: str)`: Load pre-generated structured rules

2. Create structured rule format (JSON):
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
  },
  "INCOME_VALIDATION": {
    "description": "Validate stated income when it exceeds normal thresholds",
    "risk_level": "MEDIUM",
    "required_agents": ["income"],
    "checks": [
      {
        "name": "employment_verification",
        "description": "Verify employment status",
        "tool": "verify_income",
        "required": true
      },
      {
        "name": "income_validation",
        "description": "Validate income documentation",
        "tool": "verify_income",
        "required": true
      },
      {
        "name": "dti_calculation",
        "description": "Calculate DTI ratio (must be < 43%)",
        "tool": "verify_income",
        "required": true,
        "threshold": 0.43
      }
    ],
    "decision_criteria": {
      "approval_condition": "income_verified_and_dti_valid",
      "min_confidence": 0.75,
      "dti_threshold": 0.43
    },
    "workflow_config": {
      "parallel_execution": false,
      "timeout_seconds": 20
    }
  },
  "FRAUD_CHECK": {
    "description": "Investigate potential fraud indicators",
    "risk_level": "CRITICAL",
    "required_agents": ["fraud"],
    "checks": [
      {
        "name": "ofac_screening",
        "description": "Check OFAC sanctions list",
        "tool": "check_ofac",
        "required": true,
        "zero_tolerance": true
      },
      {
        "name": "inquiry_pattern_analysis",
        "description": "Verify recent credit inquiries pattern",
        "tool": "check_fraud_indicators",
        "required": true
      },
      {
        "name": "application_velocity",
        "description": "Analyze application velocity",
        "tool": "check_fraud_indicators",
        "required": false
      }
    ],
    "decision_criteria": {
      "approval_condition": "no_fraud_indicators",
      "min_confidence": 0.95,
      "zero_tolerance_checks": ["ofac_screening"]
    },
    "workflow_config": {
      "parallel_execution": true,
      "timeout_seconds": 45
    }
  },
  "HIGH_RISK_PROFILE": {
    "description": "Additional scrutiny for high-risk applicants",
    "risk_level": "HIGH",
    "required_agents": ["identity", "income", "fraud"],
    "checks": [],
    "decision_criteria": {
      "approval_condition": "all_agents_pass",
      "min_confidence": 0.9,
      "requires_manual_signoff": true
    },
    "workflow_config": {
      "parallel_execution": false,
      "timeout_seconds": 60,
      "cascade_mode": true
    }
  }
}
```

3. Implement `generate_structured_rules()` method that:
   - Uses LLM to parse policy documents from vector store
   - Extracts key information: description, risk level, required checks, decision criteria
   - Converts to structured JSON format
   - Validates the structure
   - Caches the result

4. Add Pydantic models for validation:
   - `CheckConfig`: Individual check configuration
   - `WorkflowConfig`: Workflow execution settings
   - `DecisionCriteria`: Decision-making rules
   - `StructuredRule`: Complete rule structure

5. Benefits of this approach:
   - **Performance**: No vector DB query needed during execution (only during initialization)
   - **Consistency**: Same structured rules applied every time
   - **Debuggability**: Easy to inspect and validate rules
   - **Maintainability**: Can manually edit structured rules if needed
   - **Cost**: Reduces LLM API calls during runtime

6. The initialization flow:
   ```
   Startup → Load Policies to Vector DB → Generate Structured Rules (LLM) → 
   Save to JSON → Load Rules on Each Run (No LLM needed)
   ```

7. Add method to refresh rules when policies change:
   - `refresh_rules()`: Re-generate structured rules from updated policies

**Expected Output**: Policy Executor that generates and manages structured rules, eliminating the need for vector DB queries during application processing

---

## Prompt 3: Mock Tools & APIs

**Task**: Create mock tools/APIs to simulate real data sources for the POC

**Requirements**:
1. In `tools/mock_apis.py`, create mock functions:
   - `check_identity(ssn: str, name: str) -> Dict`: Mock identity verification API
   - `verify_income(ssn: str, stated_income: float) -> Dict`: Mock income verification API
   - `check_fraud_indicators(ssn: str, application_id: str) -> Dict`: Mock fraud check API
   - `check_ofac(name: str, ssn: str) -> Dict`: Mock OFAC sanctions check
   - `get_credit_bureau_data(ssn: str) -> Dict`: Mock credit bureau data

2. Each mock function should return realistic data structures with:
   - `status`: "PASS" | "FAIL" | "REVIEW"
   - `details`: Dictionary with specific findings
   - `confidence`: Float between 0-1
   - `timestamp`: Current timestamp

3. Add randomization to simulate various scenarios (80% pass, 15% review, 5% fail)
4. Include delays (0.5-2 seconds) to simulate API calls

**Expected Output**: Mock APIs that simulate real-world data sources with varied responses

---

## Prompt 4: Base Agent & Identity Agent

**Task**: Implement the base agent class and Identity verification agent

**Requirements**:
1. In `agents/base_agent.py`, create `BaseAgent` class with:
   - LLM initialization
   - Common agent logic
   - Result formatting
   - Error handling
   - Methods: `process()`, `format_finding()`, `log_action()`

2. In `agents/identity_agent.py`, create `IdentityAgent` that:
   - Extends `BaseAgent`
   - Uses mock identity APIs
   - Implements `verify_identity(application: CreditApplication) -> AgentFinding`
   - Checks: SSN validation, identity theft flags, address verification
   - Returns structured findings with risk assessment

3. The agent should:
   - Call multiple mock tools
   - Use LLM to analyze and summarize findings
   - Determine risk level based on results
   - Provide clear reasoning for decisions

4. Add comprehensive logging of all actions

**Expected Output**: Base agent infrastructure and fully functional Identity Agent

---

## Prompt 5: Income & Fraud Agents

**Task**: Implement Income validation and Fraud detection agents

**Requirements**:
1. In `agents/income_agent.py`, create `IncomeAgent` that:
   - Verifies stated income against mock employment data
   - Calculates and validates DTI ratio
   - Checks income stability
   - Returns finding with income verification status

2. In `agents/fraud_agent.py`, create `FraudAgent` that:
   - Performs OFAC sanctions check
   - Analyzes credit inquiry patterns
   - Checks for fraud indicators
   - Provides fraud risk assessment
   - Returns detailed fraud check findings

3. Both agents should:
   - Follow the `BaseAgent` pattern
   - Use appropriate mock tools
   - Leverage LLM for analysis and reasoning
   - Return structured `AgentFinding` objects

4. Include decision logic that accounts for:
   - DTI thresholds (< 43% for approval)
   - Income verification confidence
   - Zero tolerance for OFAC matches
   - Fraud risk scoring

**Expected Output**: Fully functional Income and Fraud agents with decision logic

---

## Prompt 6: Orchestrator Agent with LangGraph

**Task**: Implement the orchestrator agent using LangGraph for workflow management

**Requirements**:
1. In `agents/orchestrator.py`, create `UnderwritingOrchestrator` class that:
   - Uses LangGraph to define the workflow graph
   - Uses PolicyExecutor to get pre-processed structured rules (no vector DB query needed)
   - Routes to appropriate worker agents (Identity, Income, Fraud) based on structured rules
   - Manages application state throughout the process
   - Aggregates findings from all agents

2. Implement LangGraph workflow with nodes:
   - `start`: Initialize application processing
   - `load_rules`: Get structured rules from PolicyExecutor (fast lookup, no LLM)
   - `route_workflow`: Determine which agents to invoke based on structured rules
   - `identity_check`: Call Identity Agent (conditional)
   - `income_check`: Call Income Agent (conditional)
   - `fraud_check`: Call Fraud Agent (conditional)
   - `aggregate_findings`: Combine all agent findings
   - `make_decision`: Final decision logic
   - `end`: Return final decision

3. Implement conditional edges based on:
   - Review rules from the application
   - Structured rule configuration (from PolicyExecutor)
   - Previous agent findings
   - Workflow configuration (parallel vs sequential)

4. State management should track:
   - Application data
   - Active structured rules
   - Agent findings
   - Decision reasoning
   - Execution metadata (timing, retries, etc.)

5. Final decision logic should:
   - Require all checks to PASS for approval
   - Set to DENIED if any critical check fails
   - Set to PENDING_REVIEW if any check requires manual review
   - Include confidence score and detailed reasoning

**Expected Output**: Complete orchestrator with LangGraph workflow that dynamically routes based on policies

---

## Prompt 7: Main Application & Integration

**Task**: Create the main application that ties everything together

**Requirements**:
1. In `main.py`, create:
   - Initialization function that:
     * Sets up vector store and loads policies
     * Initializes PolicyExecutor
     * Generates structured rules (one-time, saves to JSON)
     * Loads structured rules for fast access
   - `process_application(application: CreditApplication) -> UnderwritingDecision` function
   - CLI interface to run sample applications
   - Function to generate sample applications with different review rules
   - Optional flag to regenerate rules: `--regenerate-rules`

2. Create sample test scenarios:
   - Application with IDENTITY_VERIFICATION review rule
   - Application with INCOME_VALIDATION review rule
   - Application with FRAUD_CHECK review rule
   - Application with HIGH_RISK_PROFILE (multiple checks)

3. Implement detailed logging and console output showing:
   - Workflow progression
   - Agent invocations
   - Policy retrievals
   - Decision reasoning

4. Add a function to display results in a formatted way:
   - Application summary
   - Policies applied
   - Agent findings (each agent's results)
   - Final decision with confidence
   - Processing time

5. Create a simple demo mode that runs 3-4 sample applications sequentially

**Expected Output**: Complete working application with demo mode

---

## Prompt 8: README & Documentation

**Task**: Create comprehensive documentation for the POC

**Requirements**:
1. Update `README.md` with:
   - Project overview and purpose
   - Architecture diagram (ASCII or markdown)
   - Tech stack explanation
   - Setup instructions (environment, dependencies, API keys)
   - How to run the application
   - Sample output examples
   - Code structure explanation
   - Future improvements and production considerations

2. Add inline code documentation:
   - Docstrings for all classes and methods
   - Type hints throughout the codebase
   - Comments explaining complex logic

3. Create a `ARCHITECTURE.md` that explains:
   - Agentic workflow design
   - LangGraph implementation details
   - Vector DB integration approach
   - Decision-making logic
   - Extension points for production

4. Include troubleshooting section for common issues

**Expected Output**: Complete documentation for easy understanding and setup

---

## Additional Notes for All Prompts:

### Error Handling
- Wrap all external calls (APIs, LLM, Vector DB) in try-except blocks
- Provide meaningful error messages
- Implement fallback behavior where appropriate

### Logging
- Use Python's logging module
- Log at appropriate levels (DEBUG, INFO, WARNING, ERROR)
- Include timestamps and context in logs

### Code Quality
- Follow PEP 8 style guidelines
- Use type hints consistently
- Keep functions focused and modular
- Add docstrings to all public methods

### POC Considerations
- Focus on demonstrating the agentic workflow
- Mock data is acceptable and expected
- Prioritize clarity over optimization
- Keep it simple but functional

### Testing
- While comprehensive tests aren't required for POC, add a few basic test cases in `tests/` to demonstrate:
  - Vector store operations
  - Agent processing
  - End-to-end workflow for one scenario

---

## Execution Order

Execute these prompts in sequence (1→8) as each builds upon the previous:
1. Project Setup → 2. Vector Store → **2a. Policy Executor** → 3. Mock Tools → 4. Base & Identity Agent → 
5. Income & Fraud Agents → 6. Orchestrator → 7. Main Application → 8. Documentation

**Note**: Prompt 2a (Policy Executor) should be done after Vector Store setup, as it depends on the vector store for initial rule generation.

This approach ensures a working POC that demonstrates the agentic workflow for underwriting decisions while remaining simple enough for quick development and iteration.
