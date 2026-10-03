import unittest

from backend.services.subtitle_builder import (
    align_paragraphs_to_count,
    build_blocks_from_manual_text,
)


class AlignParagraphsToCountTests(unittest.TestCase):
    def test_fewer_source_paragraphs_are_not_duplicated(self):
        aligned = align_paragraphs_to_count(
            ["First source paragraph.", "Second source paragraph."],
            3,
        )

        self.assertEqual(
            aligned,
            ["First source paragraph.", "", "Second source paragraph."],
        )
        self.assertEqual(
            [paragraph for paragraph in aligned if paragraph],
            ["First source paragraph.", "Second source paragraph."],
        )

    def test_one_paragraph_is_aligned_to_the_middle_without_repetition(self):
        aligned = align_paragraphs_to_count(["Only source paragraph."], 3)

        self.assertEqual(aligned, ["", "Only source paragraph.", ""])

    def test_more_source_paragraphs_are_combined_without_loss(self):
        aligned = align_paragraphs_to_count(
            ["First.", "Second.", "Third."],
            2,
        )

        self.assertEqual(aligned, ["First.", "Second. Third."])

    def test_manual_blocks_do_not_repeat_unmatched_translation_paragraphs(self):
        blocks = build_blocks_from_manual_text(
            "Uno.\n\nDos.\n\nTres.",
            "One.\n\nTwo.",
        )

        self.assertEqual([block["text_en"] for block in blocks], ["ONE.", "", "TWO."])
        self.assertEqual([block["chain_index"] for block in blocks], [1, 2, 3])


if __name__ == "__main__":
    unittest.main()
