from __future__ import annotations

import unittest

from app.stitch import remove_boundary_duplicate


class StitchingTest(unittest.TestCase):
    def test_removes_duplicate_chunk_boundary(self) -> None:
        previous = "enterprise AI quality gates make automation safer"
        current = "quality gates make automation safer for long running learning workflows"
        self.assertEqual(
            remove_boundary_duplicate(previous, current),
            "for long running learning workflows",
        )


if __name__ == "__main__":
    unittest.main()
