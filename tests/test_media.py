from __future__ import annotations

from pathlib import Path
import unittest

from app.media import build_chunk_plan, is_supported_input, is_supported_media, is_supported_text, is_video


class MediaRulesTest(unittest.TestCase):
    def test_supported_phone_and_video_formats(self) -> None:
        for name in ("voice.m4a", "voice.mp3", "voice.amr", "voice.3gp", "seminar.mp4", "seminar.webm"):
            self.assertTrue(is_supported_media(Path(name)), name)
        self.assertFalse(is_supported_media(Path("notes.docx")))
        self.assertTrue(is_supported_text(Path("phone_transcript.txt")))
        self.assertTrue(is_supported_text(Path("learning_note.md")))
        self.assertTrue(is_supported_input(Path("phone_transcript.txt")))
        self.assertTrue(is_video(Path("seminar.mp4")))
        self.assertFalse(is_video(Path("voice.m4a")))

    def test_short_file_has_single_chunk(self) -> None:
        chunks = build_chunk_plan(15 * 60)
        self.assertEqual(len(chunks), 1)
        self.assertEqual(chunks[0].start_seconds, 0)

    def test_two_hour_file_uses_twelve_overlapping_chunks(self) -> None:
        chunks = build_chunk_plan(2 * 60 * 60)
        self.assertEqual(len(chunks), 12)
        self.assertEqual(chunks[0].start_seconds, 0)
        self.assertEqual(chunks[1].start_seconds, 585)
        self.assertEqual(chunks[-1].end_seconds, 7200)


if __name__ == "__main__":
    unittest.main()
