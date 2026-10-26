#!/usr/bin/env bash
# Copy the retro tiles into a cleanyourtv checkout, rebuild the launcher with them, and push the theme.
#   TV_HOST=<tv ip> ./install.sh <path to your cleanyourtv checkout>
set -euo pipefail
: "${TV_HOST:?set TV_HOST to the TV IP address, e.g. TV_HOST=192.168.1.50 $0 ../cleanyourtv}"
HERE="$(cd "$(dirname "$0")" && pwd)"
CYT="$(cd "${1:?usage: TV_HOST=<tv ip> $0 <path to cleanyourtv>}" && pwd)"
[ -x "$CYT/launcher/build-and-install.sh" ] || { echo "$CYT is not a cleanyourtv checkout" >&2; exit 1; }

cp "$HERE"/tiles/banner_retro_*.png "$CYT/launcher/app/src/main/res/drawable-nodpi/"
"$CYT/launcher/build-and-install.sh"
"$CYT/tools/theme.sh" "$HERE/theme"
