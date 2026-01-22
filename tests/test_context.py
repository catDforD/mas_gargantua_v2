import math
import time

import pytest

from mas.context import (
    ContextCompressor,
    ContextEntry,
    ContextLayer,
    ContextManager,
    ContextScorer,
    ContextStore,
    ContextType,
    ContextWindow,
)


def make_entry(
    entry_id: str,
    context_type: ContextType = ContextType.SHARED_STATE,
    content: str | dict[str, object] = "value",
    source: str | None = None,
    **overrides: object,
) -> ContextEntry:
    return ContextEntry(
        id=entry_id,
        type=context_type,
        content=content,
        timestamp=overrides.pop("timestamp", time.time()),
        source=source or entry_id,
        importance=overrides.pop("importance", 0.5),
        relevance_score=overrides.pop("relevance_score", 0.5),
        access_count=overrides.pop("access_count", 0),
        ttl=overrides.pop("ttl", None),
        parent_id=overrides.pop("parent_id", None),
        related_ids=overrides.pop("related_ids", []),
        is_compressed=overrides.pop("is_compressed", False),
        original_length=overrides.pop("original_length", 0),
        summary=overrides.pop("summary", None),
    )


@pytest.fixture
def context_store() -> ContextStore:
    return ContextStore("session-test")


@pytest.fixture
def context_manager() -> ContextManager:
    return ContextManager(session_id="session-test", llm_client=None, max_tokens=200)


# ContextEntry tests
def test_context_entry_compute_score(monkeypatch: pytest.MonkeyPatch) -> None:
    now = 10_000.0
    monkeypatch.setattr("mas.context.types.time.time", lambda: now)
    entry = make_entry(
        "entry",
        ContextType.SHARED_STATE,
        importance=0.8,
        relevance_score=0.6,
        access_count=5,
        timestamp=now - 1_800,
    )

    score = entry.compute_score()

    recency = math.exp(-(1_800) / 3_600.0)
    expected = (
        0.8 * 0.4  # importance
        + 0.6 * 0.3  # relevance
        + recency * 0.2  # recency score
        + 0.5 * 0.1  # frequency score
    )
    assert math.isclose(score, expected, rel_tol=1e-6)


def test_context_entry_score_recency(monkeypatch: pytest.MonkeyPatch) -> None:
    now = 50_000.0
    monkeypatch.setattr("mas.context.types.time.time", lambda: now)
    newer = make_entry("newer", ContextType.TOOL_RESULT, timestamp=now - 30)
    older = make_entry("older", ContextType.TOOL_RESULT, timestamp=now - 3_600)

    assert newer.compute_score() > older.compute_score()


def test_context_entry_increment_access() -> None:
    entry = make_entry("entry", ContextType.CONFIGURATION)
    assert entry.access_count == 0

    entry.increment_access()

    assert entry.access_count == 1


# ContextStore tests
def test_store_add_and_get(context_store: ContextStore) -> None:
    entry = make_entry("task-entry", ContextType.DEPENDENCY_OUTPUT)
    context_store.add(ContextLayer.TASK, entry)

    retrieved = context_store.get(entry.id)

    assert retrieved is entry
    assert retrieved.access_count == 1


def test_store_get_layer(context_store: ContextStore) -> None:
    first = make_entry("shared-1", ContextType.SHARED_STATE)
    second = make_entry("shared-2", ContextType.SHARED_STATE)
    context_store.add(ContextLayer.WORKFLOW, first, key="one")
    context_store.add(ContextLayer.WORKFLOW, second, key="two")

    layer_entries = context_store.get_layer(ContextLayer.WORKFLOW)

    assert set(layer_entries.keys()) == {"one", "two"}
    assert layer_entries["one"] is first


def test_store_get_for_task(context_store: ContextStore) -> None:
    task_id = "task-123"
    system_entry = make_entry("system", ContextType.CONFIGURATION)
    workflow_entry = make_entry("workflow", ContextType.SHARED_STATE)
    parent_entry = make_entry(
        "parent-match",
        ContextType.DEPENDENCY_OUTPUT,
        parent_id=task_id,
        source="task-a",
    )
    source_entry = make_entry(
        "source-match",
        ContextType.DEPENDENCY_OUTPUT,
        parent_id="task-other",
        source=task_id,
    )
    related_entry = make_entry(
        "related-match",
        ContextType.DEPENDENCY_OUTPUT,
        related_ids=["not-task", task_id],
    )

    context_store.add(ContextLayer.SYSTEM, system_entry)
    context_store.add(ContextLayer.WORKFLOW, workflow_entry)
    context_store.add(ContextLayer.TASK, parent_entry)
    context_store.add(ContextLayer.TASK, source_entry)
    context_store.add(ContextLayer.TASK, related_entry)

    results = context_store.get_for_task(task_id)
    result_ids = {entry.id for entry in results}

    assert {"system", "workflow", "parent-match", "source-match", "related-match"} <= result_ids


def test_store_get_by_type(context_store: ContextStore) -> None:
    shared_one = make_entry("shared-one", ContextType.SHARED_STATE)
    shared_two = make_entry("shared-two", ContextType.SHARED_STATE)
    dependency = make_entry("dep", ContextType.DEPENDENCY_OUTPUT)
    context_store.add(ContextLayer.WORKFLOW, shared_one)
    context_store.add(ContextLayer.WORKFLOW, shared_two)
    context_store.add(ContextLayer.TASK, dependency)

    shared_entries = context_store.get_by_type(ContextType.SHARED_STATE)

    assert {entry.id for entry in shared_entries} == {"shared-one", "shared-two"}


def test_store_update(context_store: ContextStore) -> None:
    entry = make_entry("updatable", ContextType.SHARED_STATE, summary=None)
    context_store.add(ContextLayer.WORKFLOW, entry)

    updated = context_store.update(entry.id, summary="compressed", importance=0.9)

    assert updated is True
    assert entry.summary == "compressed"
    assert entry.importance == 0.9
    assert context_store.update("missing", summary="noop") is False


def test_store_remove(context_store: ContextStore) -> None:
    entry = make_entry("removable", ContextType.SHARED_STATE)
    context_store.add(ContextLayer.WORKFLOW, entry, key="state")

    removed = context_store.remove(entry.id)

    assert removed is True
    assert context_store.get(entry.id) is None


def test_store_clear_layer(context_store: ContextStore) -> None:
    context_store.add(ContextLayer.WORKFLOW, make_entry("wf-1", ContextType.SHARED_STATE))
    context_store.add(ContextLayer.WORKFLOW, make_entry("wf-2", ContextType.SHARED_STATE))
    context_store.add(ContextLayer.TASK, make_entry("task-1", ContextType.DEPENDENCY_OUTPUT))

    cleared = context_store.clear_layer(ContextLayer.WORKFLOW)

    assert cleared == 2
    assert context_store.get_layer(ContextLayer.WORKFLOW) == {}
    assert context_store.get_layer(ContextLayer.TASK)


# ContextScorer tests
def test_scorer_task_importance() -> None:
    scorer = ContextScorer()

    critical = scorer.compute_task_importance("critical-task", "builder")
    planner = scorer.compute_task_importance("normal-task", "workflow-planner")
    reviewer = scorer.compute_task_importance("simple", "helper-reviewer")

    assert 0.8 <= critical <= 1.0
    assert planner >= 0.7
    assert reviewer >= 0.65


def test_scorer_relevance_dependency() -> None:
    scorer = ContextScorer()
    dependency_entry = make_entry(
        "dep",
        ContextType.DEPENDENCY_OUTPUT,
        source="task-a",
    )
    related_entry = make_entry(
        "related",
        ContextType.SHARED_STATE,
        related_ids=["task-target"],
    )
    shared_entry = make_entry(
        "shared",
        ContextType.SHARED_STATE,
    )

    assert scorer.compute_relevance(dependency_entry, "task-target", ["task-a"]) == 1.0
    assert scorer.compute_relevance(related_entry, "task-target", []) == 0.9
    assert scorer.compute_relevance(shared_entry, "task-target", []) == pytest.approx(
        scorer.TYPE_WEIGHTS[ContextType.SHARED_STATE]
    )


def test_scorer_rank_entries(monkeypatch: pytest.MonkeyPatch) -> None:
    scorer = ContextScorer()
    now = 200_000.0
    monkeypatch.setattr("mas.context.types.time.time", lambda: now)
    entries = [
        make_entry(
            "dep",
            ContextType.DEPENDENCY_OUTPUT,
            content="dep output",
            source="task-a",
            timestamp=now - 60,
        ),
        make_entry(
            "shared",
            ContextType.SHARED_STATE,
            content="shared state" * 50,
            timestamp=now - 1_800,
        ),
        make_entry(
            "tool",
            ContextType.TOOL_RESULT,
            content="tool result" * 40,
            timestamp=now - 3_600,
        ),
    ]

    ranked = scorer.rank_entries(entries, target_task_id="task-target")

    assert [entry.id for entry in ranked][:2] == ["dep", "shared"]


# ContextWindow tests
def test_window_count_tokens(monkeypatch: pytest.MonkeyPatch) -> None:
    window = ContextWindow(max_tokens=100)
    monkeypatch.setattr(window, "_ensure_encoding", lambda: None)

    text = "abcdefghij"
    tokens = window.count_tokens(text)

    assert tokens == math.ceil(len(text) / 4)


def test_window_select_within_budget(monkeypatch: pytest.MonkeyPatch) -> None:
    now = 5_000.0
    monkeypatch.setattr("mas.context.types.time.time", lambda: now)
    window = ContextWindow(max_tokens=5)
    entries = [
        make_entry("high", ContextType.SHARED_STATE, importance=0.9),
        make_entry("mid", ContextType.SHARED_STATE, importance=0.7),
        make_entry("low", ContextType.SHARED_STATE, importance=0.5),
    ]
    token_map = {"high": 2, "mid": 2, "low": 2}
    monkeypatch.setattr(window, "_entry_tokens", lambda entry: token_map[entry.id])

    selected = window.select(entries, max_tokens=5)

    assert [entry.id for entry in selected] == ["high", "mid"]
    assert entries[0].access_count == 1
    assert entries[1].access_count == 1
    assert entries[2].access_count == 0


def test_window_select_respects_limit(monkeypatch: pytest.MonkeyPatch) -> None:
    now = 8_000.0
    monkeypatch.setattr("mas.context.types.time.time", lambda: now)
    window = ContextWindow(max_tokens=5)
    large = make_entry("large", ContextType.DEPENDENCY_OUTPUT, importance=0.95)
    small = make_entry("small", ContextType.DEPENDENCY_OUTPUT, importance=0.6)
    token_map = {"large": 10, "small": 3}
    monkeypatch.setattr(window, "_entry_tokens", lambda entry: token_map[entry.id])

    selected = window.select([large, small], max_tokens=5)

    assert [entry.id for entry in selected] == ["small"]
    assert token_map[selected[0].id] <= 5


# ContextCompressor tests
def test_compressor_truncate_smart() -> None:
    compressor = ContextCompressor()
    text = "Sentence one contains details. Sentence two has more context."

    truncated = compressor.truncate_smart(text, max_length=35)

    assert truncated.endswith(".")
    assert "Sentence two" not in truncated


@pytest.mark.asyncio
async def test_compressor_should_compress() -> None:
    compressor = ContextCompressor()
    short = await compressor.should_compress("short text")
    long_text = "x" * 4_500
    long_result = await compressor.should_compress(long_text)

    assert short is False
    assert long_result is True


@pytest.mark.asyncio
async def test_compressor_summarize_fallback() -> None:
    compressor = ContextCompressor()
    text = " ".join(["data"] * 200)

    summary = await compressor.summarize(text, max_length=80)

    assert summary == compressor.truncate_smart(text, 80)


# ContextManager tests
@pytest.mark.asyncio
async def test_manager_add_task_output(context_manager: ContextManager) -> None:
    entry_id = await context_manager.add_task_output(
        task_id="task-alpha",
        output="alpha result",
        agent_name="agent-one",
        dependent_task_ids=["task-beta"],
    )

    entries = context_manager.store.get_by_type(ContextType.DEPENDENCY_OUTPUT)

    assert entry_id
    assert len(entries) == 1
    assert "Agent: agent-one" in entries[0].content
    assert entries[0].related_ids == ["task-beta"]


@pytest.mark.asyncio
async def test_manager_add_shared_state(context_manager: ContextManager) -> None:
    entry_id = await context_manager.add_shared_state(
        key="shared-key",
        value={"status": "ok"},
        importance=0.8,
    )

    stored = context_manager.store.get_by_key(ContextLayer.WORKFLOW, "shared-key")

    assert entry_id
    assert stored is not None
    assert stored.content == {"status": "ok"}
    assert stored.importance == 0.8


@pytest.mark.asyncio
async def test_manager_get_context_for_task(context_manager: ContextManager) -> None:
    await context_manager.add_shared_state("config", "shared-info", importance=0.9)
    await context_manager.add_task_output("task-one", "first result", "agent-a")
    await context_manager.add_task_output("task-two", "second result", "agent-b")

    context_text = await context_manager.get_context_for_task(
        task_id="task-three",
        dependency_ids=["task-one"],
        max_tokens=500,
    )

    assert "## 前置任务的输出" in context_text
    assert "first result" in context_text
    assert "## 共享状态" in context_text
    assert "shared-info" in context_text


def test_manager_get_stats(context_manager: ContextManager) -> None:
    context_manager.store.add(ContextLayer.SYSTEM, make_entry("sys", ContextType.CONFIGURATION))
    context_manager.store.add(
        ContextLayer.TASK,
        make_entry("task-entry", ContextType.DEPENDENCY_OUTPUT),
    )

    stats = context_manager.get_stats()

    assert stats["session_id"] == "session-test"
    assert stats["layer_counts"]["system"] == 1
    assert stats["layer_counts"]["task"] == 1
    assert stats["total_entries"] == 2
    assert stats["token_estimate"] >= 0
