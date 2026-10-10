"""Small provider configuration facade used by the queue GUI."""

from __future__ import annotations

from dataclasses import replace
from typing import Callable

from doctranslate.ai import AiProfile, ProfileStore


def provider_options(provider_id: str) -> dict[str, object]:
    """Return UI hints; provider modules remain free of tkinter imports."""
    common = {
        "provider": provider_id,
        "has_profile": False,
        "has_configuration": False,
        "supports_login": provider_id == "gemini",
        "requires_api_key": provider_id in {"openai", "gemini", "claude"},
        "model_discovery": provider_id == "ollama",
    }
    if provider_id in {"openai", "gemini", "claude"}:
        common.update(has_profile=True, has_configuration=True)
    return common


def open_provider_dialog(
    parent,
    profile: AiProfile,
    profile_store: ProfileStore,
    *,
    on_saved: Callable[[AiProfile], None] | None = None,
) -> None:
    """Open a minimal provider-specific Tk dialog and save a new revision."""
    import tkinter as tk
    from tkinter import messagebox

    window = tk.Toplevel(parent)
    window.title(f"{profile.provider_id} – configuration")
    window.transient(parent)
    fields = {}
    for row, (label, value) in enumerate((
        ("Model", profile.model),
        ("Credential reference", profile.credential_ref or ""),
    )):
        tk.Label(window, text=label).grid(row=row, column=0, sticky="w", padx=8, pady=4)
        variable = tk.StringVar(value=value)
        tk.Entry(window, textvariable=variable, width=42).grid(row=row, column=1, padx=8, pady=4)
        fields[label] = variable

    def save():
        updated = AiProfile(
            profile.profile_id,
            profile.revision + 1,
            profile.provider_id,
            fields["Model"].get().strip(),
            profile.auth_type,
            fields["Credential reference"].get().strip() or None,
            profile.options,
        )
        profile_store.save(updated)
        if on_saved:
            on_saved(updated)
        window.destroy()

    tk.Button(window, text="Save", command=save).grid(row=2, column=1, sticky="e", padx=8, pady=8)
    window.grab_set()
