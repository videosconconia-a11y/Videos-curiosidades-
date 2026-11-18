#!/usr/bin/env bash
# Official images (© Rockstar Games) are not in git. Copy them from the shared download folder into assets/official.
# Prefixes used: GTAVI_Pre_Load Vice_City_08 ULTIMATE_EDITION_GROTTI_CHEETAH_04 Vice_City_24 Vice_City_06 Vice_City_17
#                Leonida_Keys_04 Leonida_Keys_07 Vice_City_26 Jason_Lucia_Rooftop_portrait
# Source pages: https://www.rockstargames.com/VI (characters, places, Ultimate Edition, downloads).
set -e; SRC=${1:?usage: fetch_official.sh <folder with downloaded rockstargames.com/VI images>}
mkdir -p "$(dirname "$0")/assets/official"
for p in GTAVI_Pre_Load Vice_City_08 ULTIMATE_EDITION_GROTTI_CHEETAH_04 Vice_City_24 Vice_City_06 Vice_City_17 Leonida_Keys_04 Leonida_Keys_07 Vice_City_26 Jason_Lucia_Rooftop_portrait; do
  cp "$SRC"/$p.*jpg "$(dirname "$0")/assets/official/"; done
