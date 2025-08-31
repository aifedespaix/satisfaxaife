from __future__ import annotations

import os
import sys
from pathlib import Path

# Ensure pygame uses dummy drivers during tests so that audio and video
# initialization works in headless environments.
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
