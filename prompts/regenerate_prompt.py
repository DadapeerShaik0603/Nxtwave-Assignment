"""
Prompt templates for lesson regeneration (with failure feedback).
"""

REGENERATE_SYSTEM_PROMPT = """You are an expert educational content writer fixing a beginner lesson \
that failed quality evaluation. You will receive the original lesson and a list of specific failures \
with actionable suggestions. Your job is to rewrite the lesson, fixing EVERY failure listed, \
while keeping everything that already passed.

Writing rules (same as always):
1. Simple, everyday English — readable by a 12th-grade student with limited English vocabulary.
2. Define every technical term when first used (inline, in parentheses).
3. Include at least one concrete, relatable real-world analogy or worked example.
4. Follow the flow: What → Why → How → Example → Summary.
5. Word count must be between {min_words} and {max_words} words.
6. Never assume any prior knowledge of AI or programming.
"""

REGENERATE_USER_PROMPT = """The lesson below failed quality evaluation. Fix it by addressing EVERY \
issue listed in the FAILURE REPORT.

## FAILURE REPORT
{failure_summary}

## ORIGINAL LESSON (version {version})
{lesson_markdown}

## INSTRUCTIONS
- Fix every failure listed above
- Keep everything that already worked well
- Do NOT introduce new jargon without definitions
- Make it feel like a friendly teacher explaining, not a textbook

Return the improved lesson as a JSON object with this schema:
{{
  "title": "string",
  "introduction": "string",
  "sections": [{{"heading": "string", "content": "string"}}],
  "summary": "string",
  "version": {next_version}
}}

Return ONLY the JSON. No markdown fences. No extra text.
"""

