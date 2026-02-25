"""Prompt templates for structured probability estimation."""


def build_context_section(context: str | None) -> str:
    """Format optional additional context for prompt insertion."""
    if not context:
        return ""
    return f"\n**Additional Context:**\n{context}\n"


def build_reference_data_section(reference_data: dict | None) -> str:
    """Format structured reference data for prompt insertion."""
    if not reference_data:
        return ""
    lines = ["\n**Reference Data:**"]
    for key, value in reference_data.items():
        lines.append(f"- {key}: {value}")
    return "\n".join(lines) + "\n"
