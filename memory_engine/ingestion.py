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
        raw_os = match.group(1).strip()
        known_operating_systems = [
            ("windows 11", "Windows 11"),
            ("windows 10", "Windows 10"),
            ("linux mint", "Linux Mint"),
            ("arch linux", "Arch Linux"),
            ("fedora linux", "Fedora Linux"),
            ("elementary os", "elementary OS"),
            ("chrome os", "Chrome OS"),
            ("chromeos", "Chrome OS"),
            ("pop os", "Pop!_OS"),
            ("ubuntu", "Ubuntu"),
            ("debian", "Debian"),
            ("fedora", "Fedora"),
            ("windows", "Windows"),
            ("macos", "macOS"),
            ("mac os", "macOS"),
            ("nixos", "NixOS"),
            ("opensuse", "openSUSE"),
            ("manjaro", "Manjaro"),
            ("linux", "Linux"),
            ("android", "Android"),
            ("ios", "iOS"),
        ]
        normalized_os = next(
            (
                label
                for prefix, label in known_operating_systems
                if raw_os.lower().startswith(prefix)
            ),
            None,
        )
        if normalized_os is None:
            return []
        return [
            MemoryCandidate(
                text=f"User uses {normalized_os}",
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
        preference = match.group(1).strip()
        value = preference.lower()
        categories = {
            "programming_language": (
                "python", "java", "javascript", "typescript",
                "c++", "c#", "rust", "golang",
            ),
            "database": (
                "postgresql", "postgres", "mysql", "sqlite",
                "mongodb", "redis",
            ),
            "theme": ("dark mode", "light mode"),
            "drink": ("tea", "coffee"),
        }
        category = next(
            (
                name
                for name, terms in categories.items()
                if any(term in value for term in terms)
            ),
            None,
        )
        slot = f"preference:{category}" if category else None
        return [
            MemoryCandidate(
                text=f"User prefers {preference}",
                memory_type="preference",
                slot=slot,
            )
        ]

    # Example: "I'm building a Next.js app."
    match = re.search(r"\bI(?:'m| am)\s+building\s+(.+)", text, re.IGNORECASE)
    if match:
        return [
            MemoryCandidate(
                text=f"User is building {match.group(1).strip()}",
                memory_type="project",
                slot=None,
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
