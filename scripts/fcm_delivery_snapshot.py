#!/usr/bin/env python
"""Run the FCM delivery snapshot. Logic and docs: src/bot/utils/fcm_delivery_snapshot.py.

python scripts/fcm_delivery_snapshot.py --markdown
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src" / "bot" / "utils"))

from fcm_delivery_snapshot import main  # noqa: E402

if __name__ == "__main__":
    sys.exit(main())
