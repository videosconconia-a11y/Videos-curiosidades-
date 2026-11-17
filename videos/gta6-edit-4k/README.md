# GTA VI beauty edit — 20 s, vertical 4K (2160×3840, 30 fps), no music

Deliverables (from `./build.sh`): `gta6_edit_4K.mp4` (2160×3840, 2-pass ~16 Mb/s, ~39 MB) and `gta6_edit_1080p.mp4` (~24 MB). v2 uses hard beat cuts with a short zoom punch (no blur transitions), the best-looking official images and no on-screen credit.

15 official Rockstar Games images, none of them repeated from the highlights clip: Vice City boat at dusk, the 80s Vice City couple, a sunset kayak, a resort pool, an underwater cave, a dolphin over turquoise water, the Grassrivers stilt town, the Mount Kalaga forest, Ambrosia at night, the Ocean View Hotel, cars, an aerial of boats, a bar, and the neon dance final with "GTA VI".

Look: slow Ken Burns moves (Lanczos upscale + unsharp mask), zoom-blur crossfades, bloom, drifting light leaks, warm/teal grade, fine grain, fade in/out.
Rhythm: 2 s, 2 s, then 1 s cuts from 0:04 to 0:16, final 4 s shot (works with ~120 BPM music; put the drop at 0:04).

Images © Rockstar Games (from rockstargames.com/VI), not stored in git: put them in `assets/official/`, then run `./build.sh`.
