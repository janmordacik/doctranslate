from __future__ import annotations

from pathlib import Path

from doctranslate import translate


def test_performance_metadata_is_collected_after_output_is_written(tmp_path: Path):
    output = tmp_path / "output.pdf"
    document = translate.fitz.open()
    document.new_page(width=100, height=100)
    document.new_page(width=100, height=100)
    document.save(output)
    document.close()

    metadata = translate.pdf_output_metadata(output)

    assert metadata == {
        "output_exists": True,
        "output_bytes": output.stat().st_size,
        "output_pages": 2,
    }


def test_performance_metadata_is_safe_for_missing_output(tmp_path: Path):
    assert translate.pdf_output_metadata(tmp_path / "missing.pdf") == {
        "output_exists": False,
    }
