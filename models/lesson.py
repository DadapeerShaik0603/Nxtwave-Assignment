"""
Pydantic models for the Lesson object produced by the generator.
"""

from pydantic import BaseModel, Field
from typing import List


class Section(BaseModel):
    heading: str = Field(description="Section heading (e.g., 'What is RAG?')")
    content: str = Field(description="Full text content of this section")


class Lesson(BaseModel):
    title: str = Field(description="Full lesson title")
    introduction: str = Field(description="Hook paragraph — why this topic matters to the learner")
    sections: List[Section] = Field(description="Ordered teaching sections")
    summary: str = Field(description="1–3 sentence recap of key takeaways")
    version: int = Field(default=1, description="Version number (increments on retry)")

    def to_markdown(self) -> str:
        """Render lesson as clean Markdown string."""
        lines = [f"# {self.title}\n"]
        lines.append(f"{self.introduction}\n")
        for section in self.sections:
            lines.append(f"## {section.heading}\n")
            lines.append(f"{section.content}\n")
        lines.append("## Summary\n")
        lines.append(f"{self.summary}\n")
        return "\n".join(lines)

    def word_count(self) -> int:
        full_text = self.to_markdown()
        return len(full_text.split())

