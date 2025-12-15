# Supervisor-Based Multi-Agent Architecture

## Design & Implementation Document

---

## 1. Background & Motivation

The current chatbot implementation relies on a **single large medical agent** with:
- A long and complex prompt
- Many heterogeneous tools
- Multiple responsibilities (profile, vitals, labs, medications, lifestyle, analysis)

### Problems with the current approach
- Prompt is hard to maintain and reason about
- Tool selection logic is implicit and fragile
- Difficult to extend safely
- No clear separation of responsibilities
- Not aligned with scalable agent-based architecture

---

## 2. Goal

Refactor the chatbot into a **Supervisor-based multi-agent system** where:

- A **Supervisor Agent** orchestrates the conversation
- Multiple **small, focused sub-agents (workers)** handle specific domains
- Each agent has:
  - A small, well-scoped prompt
  - A minimal and relevant toolset

The system must be maintainable, extensible, and auditable (medical safety).

---

## 3. High-Level Architecture

```
User
  ↓
SupervisorAgent
  ├── ProfileAgent
  ├── HistoryLifestyleAgent
  ├── VitalsAgent
  ├── LabsAgent
  └── MedicationAgent
```

**Key principle:**  
Supervisor decides. Workers execute.

---

## 4. Responsibilities

### 4.1 Supervisor Agent

The Supervisor Agent **does not perform medical reasoning**.

Responsibilities:
1. Understand user intent
2. Decide which sub-agent should handle the request
3. Delegate the request
4. Return a unified response

The Supervisor must never:
- Call medical tools directly
- Interpret lab values
- Provide medical advice

---

### 4.2 Sub-Agents (Workers)

Each sub-agent:
- Handles exactly one domain
- Has a small, focused prompt
- Uses only the tools required for its domain
- Is independent and testable

---

## 5. Sub-Agent Definitions

### ProfileAgent
**Responsibility:** Basic user profile information  
**Tools:** `get_user_profile_summary`

---

### HistoryLifestyleAgent
**Responsibility:** Medical history and lifestyle factors  
**Tools:**  
- `get_medical_history_summary`  
- `get_lifestyle_summary`

---

### VitalsAgent
**Responsibility:** Blood pressure, blood sugar, weight, and trends  
**Tools:**  
- `get_measurements`  
- `get_weight_trend`  
- `add_blood_pressure_measurement`  
- `add_blood_sugar_measurement`  
- `add_weight_measurement`

---

### LabsAgent
**Responsibility:** Laboratory results and explanations  
**Tools:** `get_labs`

---

### MedicationAgent
**Responsibility:** Medication schedules and usage information  
**Tools:** `get_medication_schedule`

---

## 6. Prompt Strategy

### Supervisor Prompt
- Very small
- No medical content
- Focused on routing and delegation
- Persian language (user-facing consistency)

### Worker Prompts
- Strictly domain-limited
- Explicitly define what the agent must not do
- Avoid cross-domain assumptions
- Clear, constrained medical language

---

## 7. Routing Strategy (Phase 1)

Routing is rule-based and deterministic.

Examples:
- Numbers + BP / glucose / weight → VitalsAgent
- Lab terms (HbA1c, LDL, TSH, آزمایش) → LabsAgent
- Drugs, pills, dosage → MedicationAgent
- Medical history or lifestyle → HistoryLifestyleAgent
- Age or personal info → ProfileAgent

This ensures predictability, safety, and debuggability.

---

## 8. Out of Scope (Future Phases)

- LLM-based intent classification
- Multi-step orchestration
- Parallel agent execution
- Shared long-term memory
- Clinical decision support logic

---

## 9. Technical Decisions

- Existing `BaseAgent` remains unchanged
- All workers inherit from `BaseAgent`
- Supervisor initially does not require an LLM
- Session and memory management remain centralized

---

## 10. Success Criteria

The refactor is successful if:
- Prompts are short and readable
- New domains can be added without modifying existing agents
- Tool usage is explicit and traceable
- Supervisor logic is easy to audit
- The system scales without prompt explosion

---

## 11. Implementation Roadmap

1. Implement SupervisorAgent (routing only)
2. Extract LabsAgent
3. Extract VitalsAgent
4. Extract remaining agents
5. Remove monolithic medical prompt
