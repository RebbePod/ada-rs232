# ADA brand source

`ada-logo-source.png` is the original, unmodified PNG supplied by the maintainer:

https://www.pngfind.com/pngs/b/620-6203243_ada-logo-png.png

The artwork identifies Audio Design Associates. The software's MIT license does
not grant rights to the company artwork or trademarks.

Run `uv run python scripts/generate_brand.py` to reproduce the integration assets.
The full wordmark becomes `logo.png`; the existing left-hand ADA mark becomes the
square `icon.png`. Both have standard and high-resolution sizes. White versions
use the same transparency for display on dark backgrounds.

The files in `custom_components/ada_rs232/brand/` can also be used for the separate
Home Assistant brands submission when preparing a Core integration PR.
