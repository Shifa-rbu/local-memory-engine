import re
from dataclasses import dataclass


@dataclass
class MemoryCandidate:
    text: str
    memory_type: str
    slot: str | None = None


SMALL_TALK = {
    "ok",
    "okay",
    "thanks",
    "thank you",
    "got it",
    "sure",
    "sounds good",
}


def extract_memories(message: str) -> list[MemoryCandidate]:
    """Extract useful memories from a message using simple, inspectable rules."""
    message = message.strip()

    if not message or message.lower().strip(" .!?") in SMALL_TALK:
        return []

    text = message.rstrip(".!?").strip()

    # Example: "I use Arch Linux."
    match = re.search(r"\bI\s+(?:use|run)\s+(.+)", text, re.IGNORECASE)
    if match:
        return [
            MemoryCandidate(
                text=f"User uses {match.group(1).strip()}",
                memory_type="fact",
                slot="operating_system",
            )
        ]

    # Examples: "My project deadline is October 15."
    #           "Actually, the deadline moved to November 2."
    match = re.search(
        r"\b(?:my\s+project\s+deadline\s+is|"
        r"(?:actually,?\s*)?the\s+deadline\s+(?:moved|changed)\s+to)\s+(.+)",
        text,
        re.IGNORECASE,
    )
    if match:
        return [
            MemoryCandidate(
                text=f"Project deadline is {match.group(1).strip()}",
                memory_type="event",
                slot="project_deadline",
            )
        ]

    # Example: "I prefer Python."
    match = re.search(
        r"\bI\s+(?:prefer|like|love|enjoy)\s+(.+)",
        text,
        re.IGNORECASE,
    )
    if match:
        return [
            MemoryCandidate(
                text=f"User prefers {match.group(1).strip()}",
                memory_type="preference",
                slot="preference",
            )
        ]

    # Example: "I'm building a Next.js app."
    match = re.search(r"\bI(?:'m| am)\s+building\s+(.+)", text, re.IGNORECASE)
    if match:
        return [
            MemoryCandidate(
                text=f"User is building {match.group(1).strip()}",
                memory_type="project",
                slot="project",
            )
        ]

    # Example: "I want to learn machine learning."
    match = re.search(
        r"\bI\s+(?:want|plan|hope|aim)\s+to\s+(.+)",
        text,
        re.IGNORECASE,
    )
    if match:
        return [
            MemoryCandidate(
                text=f"User plans to {match.group(1).strip()}",
                memory_type="goal",
                slot="goal",
            )
        ]

    # Ignore messages that don't match a useful-memory pattern.
    return []
