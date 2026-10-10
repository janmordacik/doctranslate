import sys


QUEUE_COMMANDS = {"add", "start", "pause", "stop", "status"}


def _print_dependency_error(exc: ImportError) -> int:
    missing = getattr(exc, "name", None) or "an import"
    if missing == "fitz":
        print(
            "ERROR: PDF support is unavailable (PyMuPDF/fitz is not installed). "
            "Install project dependencies with: python -m pip install -e .",
            file=sys.stderr,
        )
    elif missing == "tkinter":
        print(
            "ERROR: GUI support is unavailable because tkinter is not installed. "
            "Use queue CLI commands or install the Python Tk package.",
            file=sys.stderr,
        )
    else:
        print(f"ERROR: missing Python dependency {missing}: {exc}", file=sys.stderr)
    return 2


def _save_translation_error(exc: Exception) -> None:
    module = sys.modules.get("doctranslate.translate")
    saver = getattr(module, "save_run_error", None)
    if saver is not None:
        try:
            saver(exc)
        except Exception:
            # Never hide the original CLI error when the diagnostic file cannot
            # be written (for example on a full or read-only disk).
            pass


def main(argv=None) -> int:
    argv = sys.argv[1:] if argv is None else list(argv)
    try:
        if not argv or argv == ["--gui"] or argv == ["-gui"]:
            from .queue_app import gui_main
            gui_main()
            return 0
        is_queue = argv[0] in QUEUE_COMMANDS
        is_queue = is_queue or (
            argv[0] == "--queue" and len(argv) >= 3 and argv[2] in QUEUE_COMMANDS
        )
        if is_queue:
            from .queue_app import cli_main
            return int(cli_main(argv) or 0)
        from .translate import entrypoint
        return int(entrypoint(argv) or 0)
    except ModuleNotFoundError as exc:
        return _print_dependency_error(exc)
    except ImportError as exc:
        return _print_dependency_error(exc)
    except (OSError, RuntimeError, ValueError) as exc:
        _save_translation_error(exc)
        print(f"ERROR: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except KeyboardInterrupt:
        print("Interrupted. Completed checkpoints remain saved.", file=sys.stderr)
        raise SystemExit(130)
    except Exception as exc:
        print(f"ERROR: {type(exc).__name__}: {exc}", file=sys.stderr)
        raise SystemExit(1)
