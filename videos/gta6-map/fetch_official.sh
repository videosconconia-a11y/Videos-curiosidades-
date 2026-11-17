#!/usr/bin/env bash
# Downloads the official Rockstar Games GTA VI screenshots used as backgrounds (not stored in git).
# Source pages: https://www.rockstargames.com/VI/only-in-leonida and /VI/launch-gallery  (© Rockstar Games)
set -euo pipefail
cd "$(dirname "$0")/assets/official"
UA="Mozilla/5.0"
pages=$(curl -sS -A "$UA" https://www.rockstargames.com/VI/only-in-leonida; curl -sS -A "$UA" https://www.rockstargames.com/VI/launch-gallery)
get() {  # get <local name> <Rockstar file prefix>
  p=$(grep -oE "/VI/_next/static/media/$2\.[A-Za-z0-9_.-]*\.jpg" <<<"$pages" | head -1)
  [ -n "$p" ] && curl -sS -A "$UA" -o "$1.jpg" "https://www.rockstargames.com$p" && echo "ok $1" || echo "missing $2"
}
get hero Vice_City_15; get vice_sign Vice_City_01; get vice_night Vice_City_08
get keys Leonida_Keys_01; get keys_boats Leonida_Keys_05
get grass Grassrivers_04; get grass_town Grassrivers_02
get ambrosia Ambrosia_02; get ambrosia_sunset Ambrosia_04
get kalaga_heli Mount_Kalaga_National_Park_02; get kalaga_canyon Mount_Kalaga_National_Park_04
get kalaga_forest Mount_Kalaga_National_Park_03; get kalaga_river Mount_Kalaga_National_Park_06
get kalaga_trails Mount_Kalaga_National_Park_01; get gellhorn Port_Gellhorn_01
