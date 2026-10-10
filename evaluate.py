import tempfile
from pathlib import Path

from memory_engine.ingestion import extract_memories
from memory_engine.retrieval import LocalEmbedder, MemoryRetriever
from memory_engine.storage import MemoryStore


CASES = [
    # Operating-system facts
    (["I use Arch Linux."], "What operating system does the user use?", ["Arch Linux"]),
    (["I use Ubuntu."], "Which operating system is installed?", ["Ubuntu"]),
    (["I run Windows 11."], "What OS does the user run?", ["Windows 11"]),
    (["I use Fedora Linux."], "Which Linux distribution does the user use?", ["Fedora Linux"]),
    (["I run macOS."], "What computer operating system does the user use?", ["macOS"]),

    # Preferences
    (["I prefer Python."], "Which programming language does the user prefer?", ["Python"]),
    (["I prefer PostgreSQL."], "What database does the user prefer?", ["PostgreSQL"]),
    (["I like dark mode."], "What interface theme does the user like?", ["dark mode"]),
    (["I love tea."], "Which drink does the user prefer?", ["tea"]),
    (["I enjoy hiking."], "What activity does the user enjoy?", ["hiking"]),

    # Project details
    (["I'm building a Next.js app."], "What framework is the user building with?", ["Next.js"]),
    (["I am building a study planner app."], "What kind of app is the user building?", ["study planner"]),
    (["I'm building a weather dashboard."], "What is the user developing?", ["weather dashboard"]),
    (["I am building a task tracking tool."], "What tool is the user building?", ["task tracking"]),
    (["I'm building a mobile app with Flutter."], "What is the user building?", ["mobile app"]),

    # Dates and goals
    (["My project deadline is October 15."], "When is the project deadline?", ["October 15"]),
    (
        ["My project deadline is October 15.", "Actually, the deadline moved to November 2."],
        "When is the current project deadline?",
        ["November 2"],
    ),
    (["I want to learn machine learning."], "What does the user want to learn?", ["machine learning"]),
    (["I plan to build a portfolio."], "What is the user planning to build?", ["portfolio"]),
    (["I hope to improve Python."], "What does the user hope to improve?", ["Python"]),

    # Retrieval phrasing and multi-memory recall
    (["I prefer PostgreSQL."], "Which database would the user choose?", ["PostgreSQL"]),
    (["I'm building a Next.js app."], "What is the user's current web project?", ["Next.js"]),
    (
        ["I use Arch Linux.", "I'm building a Next.js app."],
        "Tell me the user's operating system and app framework.",
        ["Arch Linux", "Next.js"],
    ),

    # Unknown questions and messages that should not create memories
    (["I use Arch Linux."], "What is the user's favorite food?", []),
    (["I prefer Python."], "What is the user's home address?", []),
    (["I'm building a study planner app."], "How many siblings does the user have?", []),
    (["My project deadline is October 15."], "What is the user's monthly salary?", []),
    (["ok thanks"], "What operating system does the user use?", []),
    (["sure"], "What project is the user building?", []),
    (["I enjoy hiking."], "What is the user's phone number?", []),
    (["I run Windows 11."], "What is the user's favorite food?", []),
]


def run_case(embedder, number, case):
    messages, query, expected_texts = case

    with tempfile.TemporaryDirectory() as temp_dir:
        db_path = Path(temp_dir) / "case.sqlite3"
        store = MemoryStore(str(db_path))

        for message in messages:
            for candidate in extract_memories(message):
                vector = embedder.encode(candidate.text)
                store.add_memory(
                    text=candidate.text,
                    memory_type=candidate.memory_type,
                    source_message=message,
                    slot=candidate.slot,
                    embedding=vector,
                )

        retriever = MemoryRetriever(store, embedder)
        results = retriever.recall(query, top_k=5)
        found_texts = [item["text"].lower() for item in results]

        if not expected_texts:
            passed = len(results) == 0
        else:
            passed = all(
                any(expected.lower() in found for found in found_texts)
                for expected in expected_texts
            )

        if not passed:
            print(f"FAIL {number}: {query}")
            print(f"  Expected: {expected_texts or 'no memories'}")
            print(f"  Got: {[item['text'] for item in results]}")

        return passed


def main():
    print(f"Loading local embedding model; running {len(CASES)} cases...")
    embedder = LocalEmbedder()

    passed = 0
    for number, case in enumerate(CASES, start=1):
        if run_case(embedder, number, case):
            passed += 1

    total = len(CASES)
    accuracy = passed / total * 100
    print(f"\nEvaluation: {passed}/{total} passed ({accuracy:.1f}%)")


if __name__ == "__main__":
    main()
