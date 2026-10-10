from __future__ import annotations

import json
from pathlib import Path
import time

import pytest

from doctranslate.performance import PerformanceRecorder


def test_recorder_groups_samples_and_calculates_percentiles():
    recorder = PerformanceRecorder(metadata={"fixture": "small"})
    recorder.add_sample("pdf.page", 10, 4)
    recorder.add_sample("pdf.page", 20, 5)
    recorder.add_sample("pdf.page", 30, 6)
    recorder.count("pages", 3)

    summary = recorder.summary()

    assert summary[0]["name"] == "pdf.page"
    assert summary[0]["count"] == 3
    assert summary[0]["total_ms"] == 60.0
    assert summary[0]["p50_ms"] == 20.0
    assert summary[0]["p95_ms"] == 29.0
    assert recorder.counters == {"pages": 3}


def test_measure_records_timing_and_sanitizes_metadata():
    recorder = PerformanceRecorder()

    with recorder.measure("xhtml.parse", document="a" * 300, blocks=4):
        time.sleep(0.001)

    sample = recorder.samples[0]
    assert sample.name == "xhtml.parse"
    assert sample.elapsed_ms >= 0
    assert sample.cpu_ms >= 0
    assert len(sample.fields["document"]) == 128
    assert sample.fields["blocks"] == 4


def test_reports_are_atomic_and_machine_readable(tmp_path: Path):
    recorder = PerformanceRecorder(metadata={"provider": "mock"})
    recorder.add_sample("ai.mock", 1.25)
    recorder.count("requests")

    json_path = recorder.write_json(tmp_path / "report.json")
    markdown_path = recorder.write_markdown(tmp_path / "report.md", "Offline baseline")

    data = json.loads(json_path.read_text(encoding="utf-8"))
    assert data["schema"] == 1
    assert data["metadata"] == {"provider": "mock"}
    assert data["counters"] == {"requests": 1}
    assert "Offline baseline" in markdown_path.read_text(encoding="utf-8")
    assert not list(tmp_path.glob("*.tmp"))


@pytest.mark.parametrize("operation", ["measure", "count", "add_sample"])
def test_invalid_performance_values_are_rejected(operation):
    recorder = PerformanceRecorder()
    if operation == "measure":
        with pytest.raises(ValueError):
            with recorder.measure(""):
                pass
    elif operation == "count":
        with pytest.raises(ValueError):
            recorder.count("bad", -1)
    else:
        with pytest.raises(ValueError):
            recorder.add_sample("bad", -1)
