from __future__ import absolute_import, unicode_literals
import sys


mode = sys.argv[1] if len(sys.argv) > 2 else "functional"
if mode == "functional":
    from . import functional

    functional.run()
else:
    raise RuntimeError("Unknown mode: " + mode)
