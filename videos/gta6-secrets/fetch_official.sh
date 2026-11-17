#!/usr/bin/env bash
# Downloads the official Rockstar Games GTA VI images listed in official_images.txt (not stored in git).
# Source pages on rockstargames.com/VI (© Rockstar Games).
set -euo pipefail
cd "$(dirname "$0")"; mkdir -p assets/official
UA="Mozilla/5.0"
pages=$(for p in VI VI/media VI/only-in-leonida VI/launch-gallery VI/editions; do curl -sS -A "$UA" "https://www.rockstargames.com/$p"; done)
grep -v '^#' official_images.txt | while read -r key prefix _; do
  path=$(grep -oE "/VI/_next/static/media/${prefix}\.[A-Za-z0-9_.-]*\.jpg" <<<"$pages" | grep -v Mobile | head -1 || true)
  if [ -n "$path" ]; then curl -sS -A "$UA" -o "assets/official/$key.jpg" "https://www.rockstargames.com$path" && echo "ok $key"; else echo "missing $prefix"; fi
done
