# UW-AGent

AI-Powered Underwriting Assistant using Agentic Workflow (POC)

## Overview

This project implements an AI assistant for credit card manual underwriting using an agentic approach with LangGraph. The system uses an orchestrator agent that coordinates multiple specialized worker agents to perform identity verification, income validation, fraud checks, and other underwriting tasks.

## Key Features

- **Agentic Architecture**: Orchestrator + Worker agents pattern
- **Policy-Driven Decisions**: Vector DB (ChromaDB) stores underwriting policies
- **Policy Executor**: Converts policies to structured rules for fast runtime execution
- **Dynamic Workflow**: Workflow adapts based on application review rules
- **Explainable AI**: Complete audit trail of all decisions
- **Mock APIs**: Simulates real-world integrations for POC

## Documentation

- **[IMPLEMENTATION_PLAN.md](IMPLEMENTATION_PLAN.md)** - High-level architecture, components, workflow examples, and timeline
- **[CODING_AGENT_PROMPTS.md](CODING_AGENT_PROMPTS.md)** - 8 sequential prompts for coding agents to implement the system
- **[POLICY_EXECUTOR_DESIGN.md](POLICY_EXECUTOR_DESIGN.md)** - Deep dive into Policy Executor optimization component

## Architecture

```
Application → Orchestrator (LangGraph) → Policy Executor (Structured Rules)
                    ↓
    ┌───────────────┼───────────────┐
    ↓               ↓               ↓
Identity Agent  Income Agent  Fraud Agent
    ↓               ↓               ↓
  Mock APIs     Mock APIs     Mock APIs
    ↓               ↓               ↓
    └───────────────┴───────────────┘
                    ↓
         Decision Aggregation
                    ↓
         Final Underwriting Decision
```

## Tech Stack

- **LangGraph** - Agent orchestration and workflow management
- **ChromaDB** - Vector database for policy documents
- **OpenAI GPT** - LLM for analysis and reasoning
- **Python 3.10+** - Core language
- **Pydantic** - Data validation and modeling

## Getting Started

### Prerequisites

- Python 3.10 or higher
- OpenAI API key

### Installation

```bash
# Clone the repository
git clone <repository-url>
cd UW-AGent

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Add your OPENAI_API_KEY to .env
```

### Usage

```bash
# Initialize system (one-time setup)
python main.py --init

# Run demo with sample applications
python main.py --demo

# Process a single application
python main.py --application <application_id>

# Regenerate policy rules
python main.py --regenerate-rules
```

## Components

### 1. Policy Executor
Converts natural language policies into structured JSON rules for fast runtime execution. Eliminates vector DB queries during application processing.

### 2. Orchestrator Agent
Master coordinator that builds dynamic workflows based on review rules and routes to appropriate worker agents.

### 3. Worker Agents
- **Identity Agent**: SSN validation, identity theft checks, address verification
- **Income Agent**: Employment verification, income validation, DTI calculation
- **Fraud Agent**: OFAC screening, fraud indicators, inquiry pattern analysis

### 4. Vector Store
ChromaDB stores policy documents for initial rule generation and optional policy explanations.

## Performance Optimization

The Policy Executor provides significant performance improvements:

- **Latency**: <100ms for rule lookup (vs 2-5 seconds with vector DB)
- **Cost**: $0 per application after setup (vs $0.01-0.05 with LLM calls)
- **Consistency**: 100% consistent rule application
- **Scalability**: Handles high volume without LLM bottlenecks

## Sample Output

```
Processing Application: APP-12345
Review Rules: ['INCOME_VALIDATION', 'FRAUD_CHECK']

→ Loading structured rules... ✓
→ Building workflow graph... ✓
→ Executing Income Agent... ✓
  • Employment verified
  • Income: $75,000 (verified)
  • DTI: 38% (PASS)
  
→ Executing Fraud Agent... ✓
  • OFAC: No match (PASS)
  • Inquiry pattern: Normal (PASS)
  • Fraud score: Low risk (PASS)

→ Aggregating findings... ✓
→ Making decision... ✓

DECISION: APPROVED
Confidence: 0.92
Reasoning: All required checks passed with high confidence.
Processing time: 0.8 seconds
```

## Project Structure

```
UW-AGent/
├── README.md
├── IMPLEMENTATION_PLAN.md
├── CODING_AGENT_PROMPTS.md
├── POLICY_EXECUTOR_DESIGN.md
├── requirements.txt
├── .env.example
├── config/
│   └── settings.py
├── models/
│   └── application.py
├── agents/
│   ├── orchestrator.py
│   ├── identity_agent.py
│   ├── income_agent.py
│   ├── fraud_agent.py
│   └── base_agent.py
├── tools/
│   ├── mock_apis.py
│   ├── vector_store.py
│   └── policy_executor.py
├── policies/
│   ├── sample_policies.txt
│   └── structured_rules.json
├── main.py
└── tests/
```

## Development

This is a POC focused on demonstrating the agentic workflow. For production deployment, consider:

- Real API integrations
- Authentication and authorization
- Database for applications and decisions
- Comprehensive testing
- Monitoring and alerting
- Compliance and audit logging
- Scalability optimizations
- Human-in-the-loop workflows

## Implementation Guide

Follow the prompts in [CODING_AGENT_PROMPTS.md](CODING_AGENT_PROMPTS.md) sequentially:

1. Project Setup & Base Structure
2. Vector Store & Policy Management
3. Policy Executor (Structured Rules)
4. Mock Tools & APIs
5. Base Agent & Identity Agent
6. Income & Fraud Agents
7. Orchestrator Agent with LangGraph
8. Main Application & Integration
9. README & Documentation

Estimated implementation time: ~28 hours

## Contributing

This is a POC project. Contributions, suggestions, and improvements are welcome.

## License

[Your License Here]

## Acknowledgments

Built using LangGraph and inspired by modern agentic AI architectures.
