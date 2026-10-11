from memory_engine.ingestion import extract_memories
from memory_engine.storage import MemoryStore


def test_small_talk_is_ignored():
    assert extract_memories("ok thanks") == []


def test_recognized_operating_system_is_saved():
    candidate = extract_memories("I use Arch Linux.")[0]
    assert candidate.text == "User uses Arch Linux"
    assert candidate.slot == "operating_system"


def test_programming_language_is_not_mistaken_for_operating_system():
    assert extract_memories("I use Python.") == []


def test_programming_and_database_preferences_use_different_slots():
    language = extract_memories("I prefer Python.")[0]
    database = extract_memories("I prefer PostgreSQL.")[0]

    assert language.slot == "preference:programming_language"
    assert database.slot == "preference:database"


def test_different_projects_do_not_share_a_replacement_slot():
    first = extract_memories("I'm building a weather dashboard.")[0]
    second = extract_memories("I'm building a study planner app.")[0]

    assert first.slot is None
    assert second.slot is None


def test_new_deadline_replaces_old_deadline_and_keeps_history(tmp_path):
    store = MemoryStore(str(tmp_path / "memories.sqlite3"))

    old_id = store.add_memory(
        text="Project deadline is October 15",
        memory_type="event",
        source_message="My project deadline is October 15.",
        slot="project_deadline",
    )
    new_id = store.add_memory(
        text="Project deadline is November 2",
        memory_type="event",
        source_message="Actually, the deadline moved to November 2.",
        slot="project_deadline",
    )

    history = store.list_memories()
    current = store.list_memories(include_replaced=False)

    assert len(history) == 2
    assert history[0]["id"] == old_id
    assert history[0]["status"] == "replaced"
    assert history[0]["replaced_by"] == new_id
    assert len(current) == 1
    assert current[0]["text"] == "Project deadline is November 2"
    assert current[0]["status"] == "active"


def test_unrelated_projects_remain_active(tmp_path):
    store = MemoryStore(str(tmp_path / "memories.sqlite3"))

    store.add_memory(
        "User is building a weather dashboard",
        "project",
        "I'm building a weather dashboard.",
        slot=None,
    )
    store.add_memory(
        "User is building a study planner app",
        "project",
        "I'm building a study planner app.",
        slot=None,
    )

    current = store.list_memories(include_replaced=False)
    assert len(current) == 2
    assert all(item["status"] == "active" for item in current)


def test_memories_persist_after_store_is_reopened(tmp_path):
    database = str(tmp_path / "memories.sqlite3")
    first_store = MemoryStore(database)
    first_store.add_memory(
        "User uses Arch Linux",
        "fact",
        "I use Arch Linux.",
        slot="operating_system",
    )

    reopened_store = MemoryStore(database)
    memories = reopened_store.list_memories()

    assert len(memories) == 1
    assert memories[0]["text"] == "User uses Arch Linux"


def test_delete_returns_false_for_unknown_id(tmp_path):
    store = MemoryStore(str(tmp_path / "memories.sqlite3"))
    assert store.delete_memory(9999) is False
