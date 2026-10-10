from __future__ import annotations

from pathlib import Path

from doctranslate import translate


def test_memory_estimate_has_conservative_minimum(tmp_path: Path):
    source = tmp_path / "source.pdf"
    source.write_bytes(b"x" * 1024)

    estimate = translate.estimate_pdf_memory(source)

    assert estimate >= translate.PDF_MEMORY_MINIMUM


def test_adaptive_mode_uses_memory_when_reserve_is_sufficient(tmp_path: Path, monkeypatch):
    source = tmp_path / "source.pdf"
    source.write_bytes(b"x" * 1024)
    monkeypatch.setattr(translate, "available_memory_bytes", lambda: 8 * 1024**3)

    assert translate.select_pdf_save_mode("adaptive", source) == "memory"


def test_adaptive_mode_falls_back_to_checkpoint_when_reserve_is_low(tmp_path: Path, monkeypatch):
    source = tmp_path / "source.pdf"
    source.write_bytes(b"x" * 1024)
    monkeypatch.setattr(translate, "available_memory_bytes", lambda: 1)

    assert translate.select_pdf_save_mode("adaptive", source) == "checkpoint"


def test_explicit_mode_is_not_overridden_by_memory_probe(tmp_path: Path, monkeypatch):
    source = tmp_path / "source.pdf"
    source.write_bytes(b"x" * 1024)
    monkeypatch.setattr(translate, "available_memory_bytes", lambda: 1)

    assert translate.select_pdf_save_mode("memory", source) == "memory"
    assert translate.select_pdf_save_mode("checkpoint", source) == "checkpoint"


def test_invalid_checkpoint_environment_uses_safe_default(monkeypatch):
    monkeypatch.setenv("TRANSLATE_PDF_CHECKPOINT_PAGES", "not-a-number")

    assert translate.positive_env_int("TRANSLATE_PDF_CHECKPOINT_PAGES", 16) == 16
    assert translate.positive_env_int("TRANSLATE_PDF_CHECKPOINT_PAGES", 16) > 0
