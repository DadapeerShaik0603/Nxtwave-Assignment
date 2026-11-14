# Self-Evaluating Lesson Content Generator

> **NxtWave Take-Home Assignment** | Associate GenAI Engineer – Content Systems

An agentic pipeline built with **LangGraph + Groq (llama-3.3-70b-versatile)** that generates a beginner lesson on a given topic, evaluates it against a custom rubric, and regenerates it until it passes — all automatically, before a human ever sees it.

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────┐
│                   LangGraph Pipeline                    │
│                                                         │
│  START → generate_lesson → evaluate_lesson              │
│                                 │                       │
│                     ┌───────────▼──────────┐            │
│                     │   PASS or FAIL?      │            │
│                     └────┬─────────────┬───┘            │
│                          │             │                │
│                     PASS │        FAIL │ (retry ≤ 2)   │
│                          │             │                │
│                   output_lesson   regenerate_lesson     │
│                          │             │                │
│                   persist_memory  evaluate_lesson       │
│                          │        (loops back)          │
│                         END                             │
└─────────────────────────────────────────────────────────┘
```

### Key Components

| Component | Description |
|---|---|
| `pipeline/graph.py` | LangGraph StateGraph — wires all nodes and conditional edges |
| `pipeline/nodes/generate.py` | Calls Groq LLM to generate a structured lesson |
| `pipeline/nodes/evaluate.py` | Runs the rubric against the lesson (7 hard pass/fail checkpoints) |
| `pipeline/nodes/regenerate.py` | Rewrites the lesson incorporating failure feedback |
| `pipeline/nodes/output.py` | Writes `lesson_final.md` and `rejection_log.md` |
| `pipeline/nodes/memory_persist.py` | Saves run history to `memory/run_history.json` |
| `memory/manager.py` | Analyses past failures → injects evolved warnings into future prompts |
| `models/lesson.py` | Pydantic schema for the Lesson object |
| `models/evaluation.py` | Pydantic schema for the EvaluationResult object |

---

## 📐 Evaluation Rubric (7 Hard Pass/Fail Checkpoints)

| # | Checkpoint | Pass Condition |
|---|---|---|
| 1 | Accurate & Grounded | No factually wrong claims about RAG |
| 2 | Beginner-Friendly Language | Simple English; every jargon term defined on first use |
| 3 | Teaches by Example | ≥1 concrete, relatable real-world analogy or worked example |
| 4 | Covers Key Points | Covers what RAG is, why it's needed, and how it works |
| 5 | Coherent Teaching Flow | Logical: concept → why → how → example → summary |
| 6 | No Unexplained Jargon | Every technical term (embedding, vector DB, etc.) defined inline |
| 7 | Appropriate Length | 400–1200 words |

---

## ⚙️ Setup

### Prerequisites
- Python 3.10+
- A [Groq API key](https://console.groq.com) (free tier works)

### Install

```bash
# 1. Clone the repository
git clone <your-repo-url>
cd nxtwave-lesson-generator

# 2. Create a virtual environment (recommended)
python -m venv venv

# Windows
venv\Scripts\activate

# macOS / Linux
source venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure your API key
cp .env.example .env
# Open .env and replace: GROQ_API_KEY=your_groq_api_key_here
```

---

## 🚀 Usage

### Standard run (generate, evaluate, regenerate until passing)
```bash
python main.py --topic "Introduction to RAG (Retrieval-Augmented Generation)"
```

### Demo fail mode (deliberately bad first generation — great for Loom video)
```bash
python main.py --topic "Introduction to RAG" --demo-fail
```

### View memory stats (self-evolution history)
```bash
python main.py --stats
```

### Run tests
```bash
pytest tests/ -v
```

---

## 📂 Output Files

After a run, two files are created in `output/`:

| File | Contents |
|---|---|
| `output/lesson_final.md` | The final passing lesson in clean Markdown |
| `output/rejection_log.md` | Full audit trail — which checkpoints failed, why, and what changed |

---

## 🧬 Self-Evolution / Memory

After every run, `memory/run_history.json` stores:
- Which checkpoints failed and why
- What suggestions were given
- Whether the final lesson passed

On the **next run on the same topic**, `MemoryManager` reads past failure patterns and injects targeted warnings into the generation prompt — e.g.:

```
⚠️ SELF-EVOLVED WARNINGS:
• [teaches_by_example] failed 2 times. Fix: Add a real-world analogy early in the lesson.
• [covers_key_points] failed 1 time. Fix: Explicitly state all 3 steps of RAG.
```

This means the system gets smarter with each run — **without retraining**.

---

## 🤖 Model & Stack

| Layer | Technology |
|---|---|
| LLM | `llama-3.3-70b-versatile` via Groq API |
| Orchestration | LangGraph (StateGraph with conditional edges) |
| Prompt Management | LangChain Core (PromptTemplate, ChatMessages) |
| Structured Output | Pydantic v2 |
| Memory | JSON file (`memory/run_history.json`) |
| CLI / Terminal UI | Rich |
| Config | python-dotenv |
| Tests | pytest |

---

## 🗂️ Project Structure

```
nxtwave-lesson-generator/
├── .env.example              ← Copy to .env and add your API key
├── .gitignore
├── requirements.txt
├── README.md
├── main.py                   ← Entry point
│
├── pipeline/
│   ├── graph.py              ← LangGraph StateGraph
│   ├── state.py              ← AgentState TypedDict
│   ├── router.py             ← Conditional edge logic
│   └── nodes/
│       ├── generate.py
│       ├── evaluate.py
│       ├── regenerate.py
│       ├── output.py
│       └── memory_persist.py
│
├── models/
│   ├── lesson.py             ← Lesson Pydantic model
│   └── evaluation.py         ← EvaluationResult Pydantic model
│
├── prompts/
│   ├── generate_prompt.py
│   ├── evaluate_prompt.py
│   └── regenerate_prompt.py
│
├── memory/
│   ├── manager.py            ← MemoryManager (self-evolution)
│   └── run_history.json      ← Auto-created on first run
│
├── output/
│   ├── lesson_final.md       ← Auto-created after run
│   └── rejection_log.md      ← Auto-created after run
│
├── config/
│   └── settings.py           ← Central config
│
└── tests/
    ├── test_generate.py
    ├── test_evaluate.py
    └── test_memory.py
```

---

