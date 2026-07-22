# Synthetic Ordered-Frame Benchmark Dataset

All 20 project-owned clips are regenerated through one deterministic source. The
maintained eval submits only five ordered JPEGs; MP4 audio is never submitted or scored.
Rendered frames contain no authored title, label, subtitle, character name, or prop name.

## Active frame-eval cases

- `dialogue_confession_push_in`: Positive scale-change control: all five frames visibly tighten on the same two figures.
- `alarm_chase_whip_pan`: Positive lateral-motion and pulsing-light control with five visibly different frames.
- `quiet_bedside_vigil`: Negative temporal control: five byte-identical frames make stillness directly testable.
- `prop_swap_continuity_break`: Positive discontinuity control: a visible two-state color change occurs at a submitted sample boundary.
- `rooftop_escape_crash_zoom`: Positive compound-motion control: submitted frames show lateral travel, an arc over a visible gap, and increasing scale.
- `storm_tunnel_lateral_run`: Positive lateral-motion control with visible tunnel geometry and shifting rain-like streaks, distinct from the red pulse case.

## Quarantined cases

- `neon_crosswalk_reveal`: The generated packet is static and cannot substantiate the former crosswalk or overhead-reveal claims.
- `muzak_aftermath_tableau`: Its defining muzak-versus-aftermath contrast is audio-only and no audio reaches the subject.
- `radio_hold_tracking`: The static shapes do not visually establish radio speech, a hold command, officers, or tracking movement.
- `hallway_standoff_crosscut`: The packet shows a position jump but its abstract shapes do not establish a hallway standoff or knife interaction.
- `sunset_reunion_pullback`: Valid scale-change imagery, but redundant with the active push-in control and unable to establish a reunion from frames alone.
- `surveillance_green_monitor`: A valid static palette fixture, but redundant with the active bedside stillness control and lacking temporal behavior.
- `flashback_sepia_drift`: The frames show a scale change but cannot establish flashback, memory, parenthood, water, or voiceover.
- `mirror_isolation_profile`: A valid static portrait fixture, but redundant with the active stillness control and without distinct temporal evidence.
- `warehouse_drone_wide`: Its defining drone is audio-only, while the static visual is redundant with the active negative control.
- `countdown_control_room`: Frames show pulsing light but no visible countdown, relay, operator action, or screen content.
- `golden_memory_orbit`: The frames support a push-in but not the former orbit, memory, lantern, or tender-recollection claims.
- `handheld_panic_stairwell`: Dynamic but redundant with stronger active run controls; ordered stills cannot cleanly separate camera jitter from subject displacement.
- `match_cut_envelope`: The byte-identical packet contains no cut or framing change, so it cannot test a match cut.
- `violet_dream_percussion`: The packet is static and its defining percussion is audio-only, so former orbit and threat claims were unobservable.
