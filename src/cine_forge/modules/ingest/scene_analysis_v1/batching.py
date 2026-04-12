from __future__ import annotations

from typing import Any

from cine_forge.schemas import SceneIndexEntry


def plan_scene_batches(
    entries: list[SceneIndexEntry],
    scene_texts: dict[str, str],
    batch_size: int,
    max_batch_size: int,
    max_batch_words: int,
) -> tuple[list[list[SceneIndexEntry]], dict[str, Any]]:
    if max_batch_size <= batch_size and max_batch_words <= 0:
        batches = create_batches(entries, batch_size)
    else:
        batches = create_adaptive_batches(
            entries=entries,
            scene_texts=scene_texts,
            batch_size=batch_size,
            max_batch_size=max_batch_size,
            max_batch_words=max_batch_words,
        )

    batch_sizes = [len(batch) for batch in batches]
    batch_word_counts = [batch_word_count(batch, scene_texts) for batch in batches]
    return batches, {
        "adaptive_batching": max_batch_size > batch_size or max_batch_words > 0,
        "configured_batch_size": batch_size,
        "configured_max_batch_size": max_batch_size,
        "configured_max_batch_words": max_batch_words,
        "largest_batch_size": max(batch_sizes, default=0),
        "largest_batch_words": max(batch_word_counts, default=0),
        "total_batches": len(batches),
    }


def create_batches(
    entries: list[SceneIndexEntry], batch_size: int
) -> list[list[SceneIndexEntry]]:
    return [
        entries[i : i + batch_size] for i in range(0, len(entries), batch_size)
    ]


def create_adaptive_batches(
    entries: list[SceneIndexEntry],
    scene_texts: dict[str, str],
    batch_size: int,
    max_batch_size: int,
    max_batch_words: int,
) -> list[list[SceneIndexEntry]]:
    batches: list[list[SceneIndexEntry]] = []
    current_batch: list[SceneIndexEntry] = []
    current_words = 0

    for entry in entries:
        entry_words = scene_word_count(scene_texts.get(entry.scene_id, ""))
        would_exceed_word_budget = (
            bool(current_batch)
            and max_batch_words > 0
            and len(current_batch) >= batch_size
            and current_words + entry_words > max_batch_words
        )
        if would_exceed_word_budget:
            batches.append(current_batch)
            current_batch = []
            current_words = 0

        current_batch.append(entry)
        current_words += entry_words

        if len(current_batch) >= max_batch_size:
            batches.append(current_batch)
            current_batch = []
            current_words = 0

    if current_batch:
        batches.append(current_batch)

    return batches


def batch_word_count(
    entries: list[SceneIndexEntry], scene_texts: dict[str, str]
) -> int:
    return sum(
        scene_word_count(scene_texts.get(entry.scene_id, ""))
        for entry in entries
    )


def scene_word_count(scene_text: str) -> int:
    return len(scene_text.split())


def build_macro_analysis_prompt(
    entries: list[SceneIndexEntry], scene_texts: dict[str, str]
) -> str:
    metadata_lines = [
        (
            f"{entry.scene_id}: location={entry.location}, "
            f"time_of_day={entry.time_of_day}, "
            f"characters={entry.characters_present}"
        )
        for entry in entries
    ]
    scene_blocks = [
        (
            f"--- SCENE {entry.scene_id} ({entry.heading}) ---\n"
            f"{scene_texts.get(entry.scene_id, '(text unavailable)')}"
        )
        for entry in entries
    ]

    return (
        "You are enriching screenplay scenes with narrative analysis.\n"
        "Use only the provided scene text. Do not infer beats, tone, or "
        "character motivations from outside film knowledge.\n"
        "Return JSON matching the schema exactly, with one scene entry for "
        "every input scene in the same order.\n\n"
        "For each scene provide:\n"
        "- narrative_beats: the key story beats with beat_type, description, "
        "approximate_location, and confidence.\n"
        "- tone_mood: the dominant emotional tone.\n"
        "- tone_shifts: any notable tonal transitions.\n"
        "- location, time_of_day, characters_present: infer these only when "
        "the current metadata is unresolved; otherwise return null.\n\n"
        "Current scene metadata:\n"
        + "\n".join(metadata_lines)
        + "\n\nScene texts:\n\n"
        + "\n\n".join(scene_blocks)
        + "\n"
    )
