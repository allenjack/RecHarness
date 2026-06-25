import json

from recharness import JsonlTraceLogger, RecHarness


def test_jsonl_trace_logger_writes_trace_events(tmp_path):
    trace_path = tmp_path / "traces.jsonl"
    logger = JsonlTraceLogger(trace_path)

    event = logger.log(
        trace_id="trace_001",
        step=1,
        event_type="parse_preferences",
        payload={"query": "Find a backpack"},
    )

    rows = [json.loads(line) for line in trace_path.read_text(encoding="utf-8").splitlines()]

    assert event.trace_id == "trace_001"
    assert rows[0]["trace_id"] == "trace_001"
    assert rows[0]["event_type"] == "parse_preferences"
    assert rows[0]["payload"]["query"] == "Find a backpack"


def test_recharness_assist_writes_trace_events_when_configured(tmp_path):
    trace_path = tmp_path / "assist_traces.jsonl"
    harness = RecHarness.from_jsonl_catalog(
        "examples/backpacks/catalog.jsonl",
        trace_path=trace_path,
    )

    bundle = harness.assist(
        "Find a commuting backpack under 1500 RMB that fits a 14-inch laptop",
        top_k=2,
    )

    rows = [json.loads(line) for line in trace_path.read_text(encoding="utf-8").splitlines()]

    assert {row["event_type"] for row in rows} == {
        "parse_preferences",
        "retrieve",
        "rank",
        "bundle",
    }
    assert all(row["trace_id"] == bundle.trace_id for row in rows)
