"""Qualification boundary for stills automatically generated before paid video."""


def validate_image_backfill_target(*, model: str) -> None:
    """No live backfill target has checked current pricing in this repair.

    Existing references and no-work cases bypass this check. Explicit mock
    fixtures are deterministic and free; no live model is silently substituted.
    """
    if model == "mock":
        return
    if model.startswith("imagen-4"):
        raise ValueError(
            f"{model} is unavailable: Imagen 4 Developer API shut down 2026-08-17. "
            "Source: https://ai.google.dev/gemini-api/docs/deprecations "
            "(checked 2026-10-23)."
        )
    raise ValueError(
        f"No qualified current automatic image-backfill price for {model}. "
        "Supply an existing reference or qualify the model before generation."
    )
