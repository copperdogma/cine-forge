#!/usr/bin/env python3
# ruff: noqa: E501
"""Generate the synthetic Story 030 video-understanding benchmark dataset."""

from __future__ import annotations

import json
import math
import shutil
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont

REPO_ROOT = Path(__file__).resolve().parents[2]
DATASET_ROOT = REPO_ROOT / "benchmarks" / "video_understanding"
OUTPUT_SIZE = (640, 360)
FPS = 8
FONT_PATH = "/System/Library/Fonts/Supplemental/Arial.ttf"
TITLE_FONT = ImageFont.truetype(FONT_PATH, 24)
LABEL_FONT = ImageFont.truetype(FONT_PATH, 17)
SMALL_FONT = ImageFont.truetype(FONT_PATH, 13)


@dataclass(frozen=True)
class ClipSpec:
    slug: str
    title: str
    scene_kind: str
    anchor_subset: bool
    duration_seconds: float
    primary_color: tuple[int, int, int]
    secondary_color: tuple[int, int, int]
    accent_color: tuple[int, int, int]
    tags: list[str]
    summary_reference: str
    required_keywords: list[str]
    tone_tags: list[str]
    emotion_tags: list[str]
    color_tags: list[str]
    camera_tags: list[str]
    motion_tags: list[str]
    continuity_status: str
    continuity_notes: list[str]
    audio_tags: list[str]
    transcript: str | None = None
    audio_description: str | None = None
    prop_label: str | None = None
    prop_color_start: tuple[int, int, int] | None = None
    prop_color_end: tuple[int, int, int] | None = None
    overlay_label: str | None = None


CLIPS: list[ClipSpec] = [
    ClipSpec(
        slug="dialogue_confession_push_in",
        title="Dialogue confession push-in",
        scene_kind="dialogue",
        anchor_subset=True,
        duration_seconds=4.0,
        primary_color=(19, 31, 58),
        secondary_color=(44, 90, 112),
        accent_color=(235, 214, 178),
        tags=["dialogue", "quiet_emotion"],
        summary_reference="A cool blue two-shot slowly pushes toward the hesitant speaker holding a white envelope during a hushed confession.",
        required_keywords=["confession", "blue", "push-in"],
        tone_tags=["intimate", "regretful"],
        emotion_tags=["hesitation", "vulnerability"],
        color_tags=["navy", "teal"],
        camera_tags=["locked_two_shot", "slow_push_in"],
        motion_tags=["measured"],
        continuity_status="intact",
        continuity_notes=["The white envelope stays in the right speaker's hand through the push-in."],
        audio_tags=["soft_music", "speech"],
        transcript="I should have told you before the train left.",
        audio_description="Soft piano under a single confession line.",
        prop_label="ENVELOPE",
        prop_color_start=(242, 239, 229),
        prop_color_end=(242, 239, 229),
        overlay_label="CONFESSION",
    ),
    ClipSpec(
        slug="alarm_chase_whip_pan",
        title="Alarm chase whip pan",
        scene_kind="chase",
        anchor_subset=True,
        duration_seconds=4.0,
        primary_color=(31, 10, 10),
        secondary_color=(130, 20, 20),
        accent_color=(255, 89, 64),
        tags=["action", "motion"],
        summary_reference="Red alarm light pulses through a corridor as the camera whip-pans after a sprinting figure clutching a bag.",
        required_keywords=["alarm", "red", "chase"],
        tone_tags=["urgent", "tense"],
        emotion_tags=["panic"],
        color_tags=["red"],
        camera_tags=["whip_pan"],
        motion_tags=["escalating", "fast_lateral", "pulsing_light"],
        continuity_status="intact",
        continuity_notes=["The red bag remains with the runner."],
        audio_tags=["alarm", "percussion"],
        audio_description="A pulsing alarm and clipped percussion hits.",
        prop_label="BAG",
        prop_color_start=(201, 32, 32),
        prop_color_end=(201, 32, 32),
        overlay_label="ALARM",
    ),
    ClipSpec(
        slug="quiet_bedside_vigil",
        title="Quiet bedside vigil",
        scene_kind="vigil",
        anchor_subset=True,
        duration_seconds=4.0,
        primary_color=(39, 42, 54),
        secondary_color=(93, 79, 64),
        accent_color=(242, 203, 135),
        tags=["quiet_emotion", "interior"],
        summary_reference="A static bedside composition holds on one seated figure under a warm lamp while the room stays almost still.",
        required_keywords=["bedside", "warm", "still"],
        tone_tags=["intimate", "mournful"],
        emotion_tags=["tenderness", "grief"],
        color_tags=["amber", "desaturated"],
        camera_tags=["static", "wide_master"],
        motion_tags=["stillness"],
        continuity_status="intact",
        continuity_notes=["The folded blanket remains untouched at frame right."],
        audio_tags=["heartbeat", "soft_music"],
        audio_description="A soft room tone with a faint heartbeat monitor and low piano.",
        overlay_label="VIGIL",
    ),
    ClipSpec(
        slug="prop_swap_continuity_break",
        title="Prop swap continuity break",
        scene_kind="tableau",
        anchor_subset=True,
        duration_seconds=4.0,
        primary_color=(25, 27, 43),
        secondary_color=(61, 67, 96),
        accent_color=(216, 80, 80),
        tags=["continuity", "prop"],
        summary_reference="A table scene cuts between matching framings, but the folder on the tabletop changes from red to blue after the cut.",
        required_keywords=["folder", "continuity", "break"],
        tone_tags=["detached", "tense"],
        emotion_tags=["suspicion"],
        color_tags=["navy"],
        camera_tags=["cross_cut", "static"],
        motion_tags=["abrupt_cut"],
        continuity_status="broken",
        continuity_notes=["The tabletop folder changes from red to blue after the cut."],
        audio_tags=["silent"],
        prop_label="FOLDER",
        prop_color_start=(205, 48, 48),
        prop_color_end=(47, 114, 205),
        overlay_label="CONTINUITY",
    ),
    ClipSpec(
        slug="neon_crosswalk_reveal",
        title="Neon crosswalk reveal",
        scene_kind="stylized_city",
        anchor_subset=True,
        duration_seconds=4.0,
        primary_color=(20, 19, 50),
        secondary_color=(151, 38, 121),
        accent_color=(66, 224, 209),
        tags=["stylized_color", "city"],
        summary_reference="A wet crosswalk glows in magenta and cyan as the camera cranes up to reveal the street geometry.",
        required_keywords=["neon", "crosswalk", "reveal"],
        tone_tags=["surreal", "tense"],
        emotion_tags=["wonder"],
        color_tags=["magenta", "neon", "teal"],
        camera_tags=["overhead_reveal"],
        motion_tags=["slow_drift"],
        continuity_status="intact",
        continuity_notes=["Light reflections stay consistent across the reveal."],
        audio_tags=["drone"],
        audio_description="A low synth drone hangs under the reveal.",
        overlay_label="NEON",
    ),
    ClipSpec(
        slug="muzak_aftermath_tableau",
        title="Muzak aftermath tableau",
        scene_kind="tableau",
        anchor_subset=True,
        duration_seconds=4.0,
        primary_color=(76, 77, 91),
        secondary_color=(189, 189, 186),
        accent_color=(244, 194, 96),
        tags=["audio_intent", "contrast"],
        summary_reference="A static aftermath tableau holds on a trashed table while cheerful elevator-style muzak creates tonal dissonance.",
        required_keywords=["muzak", "aftermath", "tableau"],
        tone_tags=["playful", "detached"],
        emotion_tags=["suspicion"],
        color_tags=["desaturated"],
        camera_tags=["static", "wide_master"],
        motion_tags=["stillness"],
        continuity_status="intact",
        continuity_notes=["The tipped chair and broken glass stay fixed in place."],
        audio_tags=["muzak"],
        audio_description="Cheerful store music plays against a wrecked room.",
        overlay_label="AFTERMATH",
    ),
    ClipSpec(
        slug="radio_hold_tracking",
        title="Radio hold tracking",
        scene_kind="tracking",
        anchor_subset=False,
        duration_seconds=4.0,
        primary_color=(18, 38, 66),
        secondary_color=(48, 84, 126),
        accent_color=(250, 180, 80),
        tags=["dialogue", "procedural"],
        summary_reference="A lateral tracking move follows two officers along a blue corridor while a radio command orders them to hold position.",
        required_keywords=["radio", "hold", "tracking"],
        tone_tags=["urgent"],
        emotion_tags=["resolve"],
        color_tags=["navy", "teal"],
        camera_tags=["lateral_track"],
        motion_tags=["measured"],
        continuity_status="intact",
        continuity_notes=["The amber flashlight stays with the lead officer."],
        audio_tags=["radio", "speech"],
        transcript="Unit three, hold position until the lights settle.",
        audio_description="A dry radio dispatch over light room tone.",
        prop_label="LIGHT",
        prop_color_start=(250, 180, 80),
        prop_color_end=(250, 180, 80),
        overlay_label="HOLD",
    ),
    ClipSpec(
        slug="hallway_standoff_crosscut",
        title="Hallway standoff cross-cut",
        scene_kind="dialogue",
        anchor_subset=False,
        duration_seconds=4.0,
        primary_color=(46, 28, 31),
        secondary_color=(90, 54, 64),
        accent_color=(212, 214, 217),
        tags=["dialogue", "conflict"],
        summary_reference="A tense hallway standoff cross-cuts between two profiles as each side waits for the other to move.",
        required_keywords=["standoff", "cross-cut", "hallway"],
        tone_tags=["tense"],
        emotion_tags=["anger", "suspicion"],
        color_tags=["desaturated"],
        camera_tags=["cross_cut", "profile_closeup"],
        motion_tags=["abrupt_cut"],
        continuity_status="intact",
        continuity_notes=["The silver knife stays at the same side of frame when the aggressor returns."],
        audio_tags=["speech"],
        transcript="Take one more step and this hallway closes on both of us.",
        audio_description="Dry, unscored dialogue in a dead corridor.",
        prop_label="KNIFE",
        prop_color_start=(214, 214, 217),
        prop_color_end=(214, 214, 217),
        overlay_label="STANDOFF",
    ),
    ClipSpec(
        slug="sunset_reunion_pullback",
        title="Sunset reunion pull-back",
        scene_kind="memory",
        anchor_subset=False,
        duration_seconds=4.0,
        primary_color=(205, 123, 72),
        secondary_color=(255, 197, 104),
        accent_color=(241, 225, 181),
        tags=["quiet_emotion", "exterior"],
        summary_reference="A golden reunion begins in medium framing, then slowly pulls back to hold both figures against the horizon.",
        required_keywords=["sunset", "reunion", "pull-back"],
        tone_tags=["hopeful", "nostalgic"],
        emotion_tags=["relief", "tenderness"],
        color_tags=["gold", "amber"],
        camera_tags=["slow_pull_back"],
        motion_tags=["slow_drift"],
        continuity_status="intact",
        continuity_notes=["The shared coat stays around both figures through the pull-back."],
        audio_tags=["soft_music"],
        audio_description="Warm strings carry the reunion without dialogue.",
        overlay_label="REUNION",
    ),
    ClipSpec(
        slug="surveillance_green_monitor",
        title="Surveillance green monitor",
        scene_kind="surveillance",
        anchor_subset=False,
        duration_seconds=4.0,
        primary_color=(7, 26, 14),
        secondary_color=(24, 87, 42),
        accent_color=(119, 245, 128),
        tags=["stylized_color", "monitor"],
        summary_reference="A green surveillance feed watches a quiet doorway in a locked wide frame with timestamp overlays and monitor noise.",
        required_keywords=["surveillance", "green", "monitor"],
        tone_tags=["detached", "ominous"],
        emotion_tags=["isolation"],
        color_tags=["green", "monochrome"],
        camera_tags=["wide_master", "static"],
        motion_tags=["stillness"],
        continuity_status="intact",
        continuity_notes=["The doorway and feed overlays remain stable."],
        audio_tags=["drone"],
        audio_description="A low electrical hum with no dialogue.",
        overlay_label="MONITOR",
    ),
    ClipSpec(
        slug="flashback_sepia_drift",
        title="Flashback sepia drift",
        scene_kind="memory",
        anchor_subset=False,
        duration_seconds=4.0,
        primary_color=(143, 104, 67),
        secondary_color=(208, 170, 124),
        accent_color=(234, 219, 177),
        tags=["flashback", "memory"],
        summary_reference="A sepia memory drifts past two figures near the water with a soft, nostalgic voiceover.",
        required_keywords=["sepia", "memory", "voiceover"],
        tone_tags=["nostalgic"],
        emotion_tags=["nostalgia", "wonder"],
        color_tags=["sepia", "gold"],
        camera_tags=["slow_push_in"],
        motion_tags=["slow_drift"],
        continuity_status="intact",
        continuity_notes=["The oar remains with the parent figure during the drift."],
        audio_tags=["voiceover", "soft_music"],
        transcript="We thought the tide would keep carrying us forward.",
        audio_description="A gentle voiceover rides over soft strings.",
        prop_label="OAR",
        prop_color_start=(168, 120, 81),
        prop_color_end=(168, 120, 81),
        overlay_label="FLASHBACK",
    ),
    ClipSpec(
        slug="rooftop_escape_crash_zoom",
        title="Rooftop escape crash zoom",
        scene_kind="chase",
        anchor_subset=False,
        duration_seconds=4.0,
        primary_color=(20, 23, 44),
        secondary_color=(66, 77, 116),
        accent_color=(255, 205, 80),
        tags=["action", "vertical_space"],
        summary_reference="A runner clears a rooftop gap as the camera crash-zooms toward the leap under hard sodium light.",
        required_keywords=["rooftop", "crash", "leap"],
        tone_tags=["urgent", "tense"],
        emotion_tags=["panic", "resolve"],
        color_tags=["amber", "navy"],
        camera_tags=["crash_zoom"],
        motion_tags=["escalating"],
        continuity_status="intact",
        continuity_notes=["The yellow cable remains looped at the runner's waist."],
        audio_tags=["percussion", "drone"],
        audio_description="Aggressive percussion punches through a low synth bed.",
        prop_label="CABLE",
        prop_color_start=(255, 205, 80),
        prop_color_end=(255, 205, 80),
        overlay_label="ESCAPE",
    ),
    ClipSpec(
        slug="mirror_isolation_profile",
        title="Mirror isolation profile",
        scene_kind="portrait",
        anchor_subset=False,
        duration_seconds=4.0,
        primary_color=(40, 24, 51),
        secondary_color=(105, 69, 117),
        accent_color=(211, 191, 221),
        tags=["quiet_emotion", "portrait"],
        summary_reference="A violet profile close-up and mirror split isolate one figure in a hushed self-interrogation.",
        required_keywords=["mirror", "profile", "isolation"],
        tone_tags=["detached", "mournful"],
        emotion_tags=["isolation", "hesitation"],
        color_tags=["violet", "desaturated"],
        camera_tags=["profile_closeup", "static"],
        motion_tags=["stillness"],
        continuity_status="intact",
        continuity_notes=["The cracked mirror line stays centered between face and reflection."],
        audio_tags=["silent"],
        overlay_label="MIRROR",
    ),
    ClipSpec(
        slug="warehouse_drone_wide",
        title="Warehouse drone wide",
        scene_kind="warehouse",
        anchor_subset=False,
        duration_seconds=4.0,
        primary_color=(22, 24, 26),
        secondary_color=(66, 67, 70),
        accent_color=(121, 132, 146),
        tags=["wide_space", "ominous"],
        summary_reference="A wide warehouse master holds on empty aisles while a low drone turns the stillness ominous.",
        required_keywords=["warehouse", "wide", "drone"],
        tone_tags=["ominous"],
        emotion_tags=["isolation"],
        color_tags=["desaturated", "monochrome"],
        camera_tags=["wide_master", "static"],
        motion_tags=["stillness"],
        continuity_status="intact",
        continuity_notes=["The hanging work light stays over the same aisle."],
        audio_tags=["drone"],
        audio_description="A low industrial drone with no speech.",
        overlay_label="WAREHOUSE",
    ),
    ClipSpec(
        slug="storm_tunnel_lateral_run",
        title="Storm tunnel lateral run",
        scene_kind="tracking",
        anchor_subset=False,
        duration_seconds=4.0,
        primary_color=(19, 36, 55),
        secondary_color=(61, 95, 120),
        accent_color=(134, 209, 227),
        tags=["action", "weather"],
        summary_reference="A lateral run through a storm tunnel pushes water streaks across frame as the camera keeps pace.",
        required_keywords=["storm", "tunnel", "lateral"],
        tone_tags=["urgent", "tense"],
        emotion_tags=["resolve"],
        color_tags=["teal", "navy"],
        camera_tags=["lateral_track"],
        motion_tags=["fast_lateral"],
        continuity_status="intact",
        continuity_notes=["The cyan flare remains in the runner's hand."],
        audio_tags=["percussion", "drone"],
        audio_description="Rain hiss and driving percussion.",
        prop_label="FLARE",
        prop_color_start=(134, 209, 227),
        prop_color_end=(134, 209, 227),
        overlay_label="STORM",
    ),
    ClipSpec(
        slug="countdown_control_room",
        title="Countdown control room",
        scene_kind="control_room",
        anchor_subset=False,
        duration_seconds=4.0,
        primary_color=(17, 32, 53),
        secondary_color=(23, 56, 99),
        accent_color=(255, 87, 67),
        tags=["dialogue", "procedural"],
        summary_reference="A control room cuts between screens and a central operator as a countdown and red warning lights intensify.",
        required_keywords=["countdown", "control room", "warning"],
        tone_tags=["urgent", "tense"],
        emotion_tags=["panic"],
        color_tags=["navy", "red"],
        camera_tags=["cross_cut", "locked_two_shot"],
        motion_tags=["pulsing_light"],
        continuity_status="intact",
        continuity_notes=["The countdown clock stays synchronized across the screen wall."],
        audio_tags=["alarm", "speech"],
        transcript="Thirty seconds. If the relay drops, the whole block goes dark.",
        audio_description="Operator dialogue rides above warning bleeps.",
        overlay_label="COUNTDOWN",
    ),
    ClipSpec(
        slug="golden_memory_orbit",
        title="Golden memory orbit",
        scene_kind="memory",
        anchor_subset=False,
        duration_seconds=4.0,
        primary_color=(175, 132, 72),
        secondary_color=(246, 206, 129),
        accent_color=(255, 242, 191),
        tags=["flashback", "stylized_color"],
        summary_reference="A golden memory circles gently around two figures, turning the scene into a tender, idealized recollection.",
        required_keywords=["golden", "memory", "orbit"],
        tone_tags=["hopeful", "nostalgic"],
        emotion_tags=["tenderness", "wonder"],
        color_tags=["gold", "amber"],
        camera_tags=["slow_push_in"],
        motion_tags=["spiral_orbit", "slow_drift"],
        continuity_status="intact",
        continuity_notes=["The shared lantern stays centered between the figures."],
        audio_tags=["soft_music"],
        audio_description="Warm, floating strings with no dialogue.",
        prop_label="LANTERN",
        prop_color_start=(255, 242, 191),
        prop_color_end=(255, 242, 191),
        overlay_label="MEMORY",
    ),
    ClipSpec(
        slug="handheld_panic_stairwell",
        title="Handheld panic stairwell",
        scene_kind="panic",
        anchor_subset=False,
        duration_seconds=4.0,
        primary_color=(42, 22, 18),
        secondary_color=(105, 43, 36),
        accent_color=(243, 132, 78),
        tags=["action", "panic"],
        summary_reference="A handheld stairwell scramble jolts violently as the subject glances back and loses the frame edge.",
        required_keywords=["handheld", "stairwell", "panic"],
        tone_tags=["urgent", "tense"],
        emotion_tags=["panic"],
        color_tags=["red", "desaturated"],
        camera_tags=["handheld_jitter"],
        motion_tags=["jitter", "escalating"],
        continuity_status="intact",
        continuity_notes=["The orange scarf stays around the subject's neck."],
        audio_tags=["heartbeat", "percussion"],
        audio_description="Heavy breaths, heartbeat, and clipped percussion.",
        prop_label="SCARF",
        prop_color_start=(243, 132, 78),
        prop_color_end=(243, 132, 78),
        overlay_label="PANIC",
    ),
    ClipSpec(
        slug="match_cut_envelope",
        title="Match-cut envelope",
        scene_kind="tableau",
        anchor_subset=False,
        duration_seconds=4.0,
        primary_color=(32, 38, 57),
        secondary_color=(74, 80, 111),
        accent_color=(240, 239, 231),
        tags=["continuity", "match_cut"],
        summary_reference="A sharp match cut preserves the white envelope's placement across two different framings of the same exchange.",
        required_keywords=["match cut", "envelope", "continuity"],
        tone_tags=["intimate", "tense"],
        emotion_tags=["hesitation"],
        color_tags=["navy", "desaturated"],
        camera_tags=["cross_cut", "profile_closeup"],
        motion_tags=["match_cut", "abrupt_cut"],
        continuity_status="intact",
        continuity_notes=["The envelope remains at the same hand and angle across the cut."],
        audio_tags=["speech"],
        transcript="Read it now, before the room changes its mind.",
        audio_description="Low dialogue with no underscore.",
        prop_label="ENVELOPE",
        prop_color_start=(240, 239, 231),
        prop_color_end=(240, 239, 231),
        overlay_label="MATCH CUT",
    ),
    ClipSpec(
        slug="violet_dream_percussion",
        title="Violet dream percussion",
        scene_kind="dream",
        anchor_subset=False,
        duration_seconds=4.0,
        primary_color=(45, 20, 63),
        secondary_color=(110, 49, 146),
        accent_color=(226, 106, 217),
        tags=["stylized_color", "dream"],
        summary_reference="A violet dreamscape blooms with circular light patterns while sharp percussion turns the beauty slightly threatening.",
        required_keywords=["violet", "dream", "percussion"],
        tone_tags=["surreal", "ominous"],
        emotion_tags=["wonder", "suspicion"],
        color_tags=["violet", "magenta", "neon"],
        camera_tags=["wide_master"],
        motion_tags=["spiral_orbit", "slow_drift"],
        continuity_status="intact",
        continuity_notes=["The central halo stays aligned with the sleeper figure."],
        audio_tags=["percussion", "drone"],
        audio_description="Sharp percussion accents inside a dreamlike synth bed.",
        overlay_label="DREAM",
    ),
]


def main() -> None:
    if DATASET_ROOT.exists():
        shutil.rmtree(DATASET_ROOT)
    DATASET_ROOT.mkdir(parents=True, exist_ok=True)

    manifest = []
    for spec in CLIPS:
        clip_dir = DATASET_ROOT / spec.slug
        clip_dir.mkdir(parents=True, exist_ok=True)
        render_clip(spec, clip_dir)
        manifest.append(
            {
                "clip_id": spec.slug,
                "title": spec.title,
                "anchor_subset": spec.anchor_subset,
                "tags": spec.tags,
            }
        )

    (DATASET_ROOT / "manifest.json").write_text(json.dumps({"clips": manifest}, indent=2) + "\n")
    (DATASET_ROOT / "README.md").write_text(_dataset_readme())


def render_clip(spec: ClipSpec, clip_dir: Path) -> None:
    total_frames = int(spec.duration_seconds * FPS)
    with tempfile.TemporaryDirectory() as tmp_dir_name:
        tmp_dir = Path(tmp_dir_name)
        frame_files = []
        for frame_idx in range(total_frames):
            image = _render_frame(spec, frame_idx, total_frames)
            frame_path = tmp_dir / f"frame_{frame_idx:03d}.png"
            image.save(frame_path)
            frame_files.append(frame_path)

        audio_path = _make_audio(spec, tmp_dir)
        output_path = clip_dir / "clip.mp4"
        _assemble_video(frame_files[0].parent, audio_path, output_path)
        _write_analysis_frames(frame_files, clip_dir / "frames")
        _write_target_files(spec, clip_dir)


def _render_frame(spec: ClipSpec, frame_idx: int, total_frames: int) -> Image.Image:
    progress = frame_idx / max(total_frames - 1, 1)
    image = Image.new("RGB", OUTPUT_SIZE, spec.primary_color)
    draw = ImageDraw.Draw(image)
    _draw_gradient(draw, OUTPUT_SIZE, spec.primary_color, spec.secondary_color)
    _draw_environment(draw, spec, progress)
    _draw_scene_action(draw, spec, progress)
    _draw_labels(draw, spec, progress)

    if "pulsing_light" in spec.motion_tags:
        overlay = Image.new("RGBA", OUTPUT_SIZE, (*spec.accent_color, int(70 * abs(math.sin(progress * math.pi * 4)))))
        image = Image.alpha_composite(image.convert("RGBA"), overlay).convert("RGB")
    if "surreal" in spec.tone_tags or spec.scene_kind == "dream":
        image = image.filter(ImageFilter.GaussianBlur(radius=0.7))
    return image


def _draw_gradient(
    draw: ImageDraw.ImageDraw,
    size: tuple[int, int],
    top_color: tuple[int, int, int],
    bottom_color: tuple[int, int, int],
) -> None:
    width, height = size
    for y in range(height):
        ratio = y / max(height - 1, 1)
        line_color = tuple(
            int(top_color[index] * (1 - ratio) + bottom_color[index] * ratio) for index in range(3)
        )
        draw.line([(0, y), (width, y)], fill=line_color)


def _draw_environment(draw: ImageDraw.ImageDraw, spec: ClipSpec, progress: float) -> None:
    width, height = OUTPUT_SIZE
    if spec.scene_kind in {"dialogue", "tracking", "tableau", "vigil", "control_room", "portrait"}:
        draw.rectangle((0, height * 0.68, width, height), fill=(28, 28, 34))
    if spec.scene_kind in {"chase", "tracking", "panic"}:
        for x in range(-60, width + 80, 80):
            offset = int((progress * 120) if "fast_lateral" in spec.motion_tags else progress * 35)
            draw.line((x - offset, 20, x + 80 - offset, height - 20), fill=(255, 255, 255, 60), width=2)
    if spec.scene_kind == "stylized_city":
        for x in range(20, width, 60):
            draw.line((x, 0, x, height), fill=(255, 255, 255, 25), width=1)
        for y in range(40, height, 40):
            draw.line((0, y, width, y), fill=(255, 255, 255, 25), width=1)
    if spec.scene_kind == "surveillance":
        draw.rectangle((18, 18, width - 18, height - 18), outline=spec.accent_color, width=2)
        draw.text((28, 24), "CAM 03 / 22:14:08", font=SMALL_FONT, fill=spec.accent_color)
    if spec.scene_kind in {"memory", "dream"}:
        draw.ellipse((420, 32, 610, 210), outline=spec.accent_color, width=4)
    if spec.scene_kind == "warehouse":
        for x in range(70, width, 120):
            draw.rectangle((x, 80, x + 25, height - 30), fill=(45, 45, 45))
            draw.rectangle((x + 35, 110, x + 60, height - 30), fill=(60, 60, 60))


def _draw_scene_action(draw: ImageDraw.ImageDraw, spec: ClipSpec, progress: float) -> None:
    if spec.scene_kind in {"dialogue", "tracking", "memory"}:
        left_x = int(170 + (-18 if "cross_cut" in spec.camera_tags and progress > 0.5 else 0))
        right_x = int(470 + (18 if "cross_cut" in spec.camera_tags and progress < 0.5 else 0))
        scale = 1.0 + (0.16 * progress if "slow_push_in" in spec.camera_tags else -0.12 * progress if "slow_pull_back" in spec.camera_tags else 0.0)
        _draw_character(draw, left_x, 250, scale, spec.accent_color, "A")
        _draw_character(draw, right_x, 250, scale + 0.05, tuple(reversed(spec.accent_color)), "B")
    elif spec.scene_kind in {"chase", "panic"}:
        x = int(120 + progress * 320)
        if "handheld_jitter" in spec.camera_tags:
            x += int(math.sin(progress * 60) * 10)
        y = 245 + int(math.sin(progress * math.pi * 4) * 8)
        scale = 1.0 + (0.3 * progress if "crash_zoom" in spec.camera_tags else 0.0)
        _draw_character(draw, x, y, scale, spec.accent_color, "RUN")
    elif spec.scene_kind == "vigil":
        draw.rectangle((140, 180, 430, 250), fill=(105, 112, 130), outline=(230, 230, 230), width=3)
        draw.rectangle((120, 200, 145, 300), fill=(166, 127, 76))
        _draw_character(draw, 480, 248, 1.0, spec.accent_color, "A")
    elif spec.scene_kind == "tableau":
        draw.rectangle((150, 170, 500, 230), fill=(96, 82, 72))
        draw.rectangle((130, 230, 520, 280), fill=(70, 52, 43))
    elif spec.scene_kind == "stylized_city":
        draw.polygon([(240, 300), (320, 120), (410, 300)], fill=spec.accent_color)
        draw.rectangle((60, 260, 140, 340), fill=(24, 24, 32))
        draw.rectangle((470, 220, 610, 340), fill=(24, 24, 32))
    elif spec.scene_kind == "surveillance":
        draw.rectangle((270, 120, 370, 280), outline=spec.accent_color, width=3)
        draw.rectangle((305, 160, 335, 280), fill=spec.accent_color)
    elif spec.scene_kind == "portrait":
        _draw_character(draw, 270, 245, 1.25, spec.accent_color, "A")
        draw.line((342, 70, 342, 310), fill=(255, 255, 255), width=3)
        _draw_character(draw, 420, 245, 1.05, tuple(reversed(spec.accent_color)), "")
    elif spec.scene_kind == "warehouse":
        draw.rectangle((280, 90, 360, 170), fill=(220, 215, 175))
    elif spec.scene_kind == "control_room":
        draw.rectangle((80, 70, 240, 150), outline=spec.accent_color, width=3)
        draw.rectangle((255, 60, 385, 140), outline=spec.accent_color, width=3)
        draw.rectangle((400, 70, 560, 150), outline=spec.accent_color, width=3)
        _draw_character(draw, 320, 255, 1.1, spec.accent_color, "OP")
    elif spec.scene_kind == "dream":
        for radius in range(40, 130, 28):
            draw.ellipse(
                (320 - radius, 180 - radius, 320 + radius, 180 + radius),
                outline=spec.accent_color,
                width=4,
            )

    _draw_prop(draw, spec, progress)


def _draw_character(
    draw: ImageDraw.ImageDraw,
    x: int,
    y: int,
    scale: float,
    color: tuple[int, int, int],
    label: str,
) -> None:
    body_w = int(40 * scale)
    body_h = int(90 * scale)
    head_r = int(18 * scale)
    draw.ellipse((x - head_r, y - body_h - head_r * 2, x + head_r, y - body_h), fill=color)
    draw.rounded_rectangle((x - body_w, y - body_h, x + body_w, y), radius=14, fill=color)
    if label:
        draw.text((x - 18, y + 10), label, font=SMALL_FONT, fill=(245, 245, 245))


def _draw_prop(draw: ImageDraw.ImageDraw, spec: ClipSpec, progress: float) -> None:
    if not spec.prop_label or not spec.prop_color_start:
        return
    width, _ = OUTPUT_SIZE
    color = spec.prop_color_start
    if spec.prop_color_end and progress > 0.5:
        color = spec.prop_color_end
    x = width - 180 if spec.scene_kind not in {"chase", "panic"} else 190 + int(progress * 230)
    y = 250 if spec.scene_kind != "control_room" else 210
    draw.rounded_rectangle((x, y, x + 80, y + 34), radius=6, fill=color, outline=(255, 255, 255), width=2)
    draw.text((x + 8, y + 8), spec.prop_label, font=SMALL_FONT, fill=(20, 20, 20))


def _draw_labels(draw: ImageDraw.ImageDraw, spec: ClipSpec, progress: float) -> None:
    width, height = OUTPUT_SIZE
    label = spec.overlay_label or spec.title.upper()
    draw.text((24, 22), label, font=TITLE_FONT, fill=(245, 245, 245))
    draw.text((24, 52), spec.title, font=LABEL_FONT, fill=(230, 230, 230))
    if spec.transcript:
        subtitle = spec.transcript
        text_w = draw.textlength(subtitle, font=LABEL_FONT)
        draw.rounded_rectangle((20, height - 54, min(width - 20, text_w + 42), height - 18), radius=10, fill=(0, 0, 0))
        draw.text((30, height - 46), subtitle, font=LABEL_FONT, fill=(255, 255, 255))
    if "overhead_reveal" in spec.camera_tags:
        draw.text((width - 180, 22), "REVEAL", font=LABEL_FONT, fill=spec.accent_color)
    if "whip_pan" in spec.camera_tags:
        draw.text((width - 160, 22), "WHIP", font=LABEL_FONT, fill=spec.accent_color)
    if spec.scene_kind == "control_room":
        countdown = max(0, int(30 - progress * 24))
        draw.text((460, 120), f"T-{countdown:02d}", font=TITLE_FONT, fill=spec.accent_color)


def _make_audio(spec: ClipSpec, tmp_dir: Path) -> Path | None:
    if not spec.audio_tags or spec.audio_tags == ["silent"]:
        return None

    tracks = []
    if spec.transcript and ("speech" in spec.audio_tags or "voiceover" in spec.audio_tags):
        speech_path = tmp_dir / "speech.aiff"
        subprocess.run(
            [
                "say",
                "-r",
                "175",
                "-o",
                str(speech_path),
                spec.transcript,
            ],
            check=True,
        )
        tracks.append(speech_path)

    tone_path = tmp_dir / "tone.wav"
    frequency = 330
    volume = 0.10
    if "alarm" in spec.audio_tags:
        frequency = 880
        volume = 0.08
    elif "drone" in spec.audio_tags:
        frequency = 110
        volume = 0.14
    elif "heartbeat" in spec.audio_tags:
        frequency = 60
        volume = 0.15
    elif "muzak" in spec.audio_tags:
        frequency = 440
        volume = 0.08
    elif "percussion" in spec.audio_tags:
        frequency = 180
        volume = 0.12
    subprocess.run(
        [
            "ffmpeg",
            "-y",
            "-f",
            "lavfi",
            "-i",
            f"sine=frequency={frequency}:duration={spec.duration_seconds}",
            "-af",
            f"volume={volume}",
            str(tone_path),
        ],
        check=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    tracks.append(tone_path)

    if len(tracks) == 1:
        return tracks[0]

    mixed_path = tmp_dir / "audio.wav"
    subprocess.run(
        [
            "ffmpeg",
            "-y",
            "-i",
            str(tracks[0]),
            "-i",
            str(tracks[1]),
            "-filter_complex",
            "[0:a][1:a]amix=inputs=2:duration=longest:normalize=0[a]",
            "-map",
            "[a]",
            str(mixed_path),
        ],
        check=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    return mixed_path


def _assemble_video(frame_dir: Path, audio_path: Path | None, output_path: Path) -> None:
    cmd = [
        "ffmpeg",
        "-y",
        "-framerate",
        str(FPS),
        "-i",
        str(frame_dir / "frame_%03d.png"),
    ]
    if audio_path is not None:
        cmd.extend(["-i", str(audio_path)])
    cmd.extend(
        [
            "-c:v",
            "libx264",
            "-pix_fmt",
            "yuv420p",
        ]
    )
    if audio_path is not None:
        cmd.extend(["-c:a", "aac", "-shortest"])
    cmd.append(str(output_path))
    subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def _write_analysis_frames(frame_files: list[Path], frame_output_dir: Path) -> None:
    frame_output_dir.mkdir(parents=True, exist_ok=True)
    total = len(frame_files)
    sample_indexes = sorted({0, total // 4, total // 2, (3 * total) // 4, total - 1})
    for output_idx, frame_idx in enumerate(sample_indexes):
        image = Image.open(frame_files[frame_idx]).convert("RGB")
        image.save(frame_output_dir / f"frame_{output_idx:02d}.jpg", quality=92)


def _write_target_files(spec: ClipSpec, clip_dir: Path) -> None:
    meta = {
        "clip_id": spec.slug,
        "title": spec.title,
        "source_type": "synthetic_previz",
        "source_description": "Generated locally by benchmarks/scripts/generate_video_understanding_dataset.py",
        "rights": "Project-owned synthetic benchmark asset",
        "duration_seconds": spec.duration_seconds,
        "resolution": f"{OUTPUT_SIZE[0]}x{OUTPUT_SIZE[1]}",
        "fps": FPS,
        "has_audio": bool(spec.audio_tags and spec.audio_tags != ["silent"]),
        "transcript": spec.transcript,
        "audio_description": spec.audio_description,
        "tags": spec.tags,
        "anchor_subset": spec.anchor_subset,
        "analysis_frame_policy": "five_evenly_spaced_jpegs_v1",
    }
    target = {
        "clip_id": spec.slug,
        "title": spec.title,
        "source_type": "synthetic_previz",
        "source_description": meta["source_description"],
        "rights": meta["rights"],
        "duration_seconds": spec.duration_seconds,
        "resolution": meta["resolution"],
        "has_audio": meta["has_audio"],
        "transcript": spec.transcript,
        "audio_description": spec.audio_description,
        "summary_reference": spec.summary_reference,
        "required_keywords": spec.required_keywords,
        "tone_tags": spec.tone_tags,
        "emotion_tags": spec.emotion_tags,
        "color_tags": spec.color_tags,
        "camera_tags": spec.camera_tags,
        "motion_tags": spec.motion_tags,
        "continuity_status": spec.continuity_status,
        "continuity_notes": spec.continuity_notes,
        "audio_tags": spec.audio_tags,
        "clip_tags": spec.tags,
        "anchor_subset": spec.anchor_subset,
        "weights": {
            "summary": 0.18,
            "tone": 0.14,
            "emotion": 0.12,
            "color": 0.10,
            "camera": 0.12,
            "motion": 0.10,
            "continuity": 0.12,
            "audio": 0.08,
            "evidence": 0.04,
        },
    }
    target_md = "\n".join(
        [
            f"# {spec.title}",
            "",
            f"- Summary: {spec.summary_reference}",
            f"- Tone: {', '.join(spec.tone_tags)}",
            f"- Emotion: {', '.join(spec.emotion_tags)}",
            f"- Color / grade: {', '.join(spec.color_tags)}",
            f"- Camera language: {', '.join(spec.camera_tags)}",
            f"- Motion: {', '.join(spec.motion_tags)}",
            f"- Continuity: {spec.continuity_status} — {'; '.join(spec.continuity_notes)}",
            f"- Audio intent: {', '.join(spec.audio_tags)}",
            f"- Transcript: {spec.transcript or '[none]'}",
        ]
    )
    (clip_dir / "meta.json").write_text(json.dumps(meta, indent=2) + "\n")
    (clip_dir / "target.json").write_text(json.dumps(target, indent=2) + "\n")
    (clip_dir / "target.md").write_text(target_md + "\n")


def _dataset_readme() -> str:
    anchor_ids = ", ".join(spec.slug for spec in CLIPS if spec.anchor_subset)
    return (
        "# Story 030 Synthetic Video Benchmark Dataset\n\n"
        "These clips are locally generated previz-style fixtures used to calibrate the\n"
        "video-understanding benchmark without licensing ambiguity. Each clip directory contains\n"
        "`clip.mp4`, `target.md`, `target.json`, `meta.json`, and sampled analysis frames.\n\n"
        f"Anchor subset for the first pilot run: {anchor_ids}\n"
    )


if __name__ == "__main__":
    main()
