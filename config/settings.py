"""
Central configuration for the Self-Evaluating Lesson Content Generator.
"""

import os
from dotenv import load_dotenv

load_dotenv()

# ── Groq Model Config ────────────────────────────────────────────────────────
PRIMARY_MODEL   = "openai/gpt-oss-120b"        # Groq-hosted GPT-OSS 120B
FALLBACK_MODEL  = "openai/gpt-oss-20b"        # Rate-limit fallback (smaller variant)
TEMPERATURE     = 0.7                          # Slight creativity for generation
EVAL_TEMPERATURE = 0.0                         # Deterministic for evaluation

GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")

# ── Pipeline Config ───────────────────────────────────────────────────────────
MAX_RETRIES = 2          # Maximum regeneration attempts before forcing output
MIN_WORD_COUNT = 400
MAX_WORD_COUNT = 1200

# ── Paths ─────────────────────────────────────────────────────────────────────
import pathlib

BASE_DIR        = pathlib.Path(__file__).parent.parent
OUTPUT_DIR      = BASE_DIR / "output"
MEMORY_DIR      = BASE_DIR / "memory"
RUN_HISTORY_FILE = MEMORY_DIR / "run_history.json"

OUTPUT_DIR.mkdir(exist_ok=True)
MEMORY_DIR.mkdir(exist_ok=True)

# ── Rubric Checkpoint IDs ─────────────────────────────────────────────────────
CHECKPOINT_IDS = [
    "accurate_and_grounded",
    "beginner_friendly_language",
    "teaches_by_example",
    "covers_key_points",
    "coherent_teaching_flow",
    "no_unexplained_jargon",
    "appropriate_length",
]

