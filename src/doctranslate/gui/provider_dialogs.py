"""Small provider configuration facade used by the queue GUI."""

from __future__ import annotations

from dataclasses import replace
from typing import Callable

from doctranslate.ai import AiProfile, ProfileStore


def provider_options(provider_id: str) -> dict[str, object]:
    """Return registry capabilities as stable UI hints."""
    from doctranslate.ai import build_default_provider_registry
    descriptor = build_default_provider_registry().get(provider_id)
    return {
        "provider": provider_id,
        "has_profile": descriptor.configuration_supported,
        "has_configuration": descriptor.configuration_supported,
        "supports_login": descriptor.login_supported,
        "requires_api_key": "api_key" in descriptor.auth_methods,
        "model_discovery": descriptor.model_discovery_supported,
    }

def open_provider_dialog(
    parent,
    profile: AiProfile,
    profile_store: ProfileStore,
    *,
    credential_store=None,
    on_saved: Callable[[AiProfile], None] | None = None,
    on_probe: Callable[[object], None] | None = None,
    translate: Callable[[str], str] | None = None,
) -> None:
    """Open a provider-specific Tk dialog."""
    from doctranslate.ai import MemoryCredentialStore, credential_store_for, probe_profile, save_profile_configuration
    credential_store = credential_store or credential_store_for(profile)
    import tkinter as tk
    t = translate or (lambda key: key)
    from tkinter import messagebox

    window = tk.Toplevel(parent)
    window.title(f"{profile.provider_id} – configuration")
    window.transient(parent)
    fields = {}
    values = (
        ("Model", profile.model, False),
        ("Endpoint", str(profile.options.get("base_url", "")), False),
        ("Credential reference", profile.credential_ref or "", False),
        ("API key (stored securely)", "", True),
    )
    for row, (label, value, secret) in enumerate(values):
        tk.Label(window, text=label).grid(row=row, column=0, sticky="w", padx=8, pady=4)
        variable = tk.StringVar(value=value)
        tk.Entry(window, textvariable=variable, width=52, show="*" if secret else "").grid(
            row=row, column=1, padx=8, pady=4
        )
        fields[label] = variable
    def staged_profile(api_key: str | None = None):
        reference = fields["Credential reference"].get().strip() or None
        if api_key:
            reference = reference or f"memory:{profile.provider_id}:{profile.profile_id}"
        options = dict(profile.options)
        endpoint = fields["Endpoint"].get().strip()
        if endpoint:
            options["base_url"] = endpoint
        return replace(profile, model=fields["Model"].get().strip(),
                       auth_type="none" if profile.provider_id == "ollama" else "api_key",
                       credential_ref=reference, options=options)

    def test_connection() -> None:
        try:
            api_key = fields["API key (stored securely)"].get().strip()
            test_store = MemoryCredentialStore() if api_key else credential_store
            staged = staged_profile(api_key)
            if api_key:
                test_store.set(staged.credential_ref or "memory", api_key)
            result = probe_profile(staged, test_store)
            if on_probe:
                on_probe(result)
            detail = f"{result.status} ({result.latency_ms:.0f} ms)" if result.latency_ms is not None else result.status
            (messagebox.showinfo if result.ok else messagebox.showwarning)(t("provider_probe"), detail + " | " + result.message)
        except Exception as exc:
            messagebox.showerror(t("provider_probe"), f"{type(exc).__name__}: {exc}")


    def save():
        try:
            updated = save_profile_configuration(
                profile, profile_store, credential_store,
                model=fields["Model"].get(),
                credential_ref=fields["Credential reference"].get(),
                api_key=fields["API key (stored securely)"].get(),
                base_url=fields["Endpoint"].get(),
            )
        except Exception as exc:
            messagebox.showerror(t("configure"), f"{type(exc).__name__}: {exc}")
            return
        if on_saved:
            on_saved(updated)
        window.destroy()

    actions = tk.Frame(window)
    actions.grid(row=len(values), column=1, sticky="e", padx=8, pady=8)
    tk.Button(actions, text=t("provider_test"), command=test_connection).pack(side="left", padx=4)
    tk.Button(actions, text=t("provider_save"), command=save).pack(side="left", padx=4)
    tk.Button(actions, text=t("provider_cancel"), command=window.destroy).pack(side="left", padx=4)
    window.grab_set()
