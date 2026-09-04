from pathlib import Path
import re
import struct
import unittest


ROOT = Path(__file__).resolve().parents[2]
CHAPTER = ROOT / "book/chapter9.md"
IMAGES = ROOT / "book/images"
EXPECTED = {
    "fig9-1-tool-call-journey-v2.png": (1024, 1536),
    "fig9-2-boundary-map-v2.png": (1536, 864),
    "fig9-3-tool-contract-v2.png": (1536, 864),
    "fig9-4-tool-loop.png": (1536, 864),
    "fig9-5-mcp-architecture.png": (1536, 864),
    "fig9-6-mcp-primitives.png": (1536, 864),
    "fig9-7-protocol-eras-v2.png": (1536, 864),
    "fig9-8-failure-map.png": (1536, 864),
}


def png_dimensions(path: Path) -> tuple[int, int]:
    with path.open("rb") as stream:
        signature = stream.read(8)
        if signature != b"\x89PNG\r\n\x1a\n":
            raise AssertionError(f"not a PNG: {path.name}")
        length = struct.unpack(">I", stream.read(4))[0]
        chunk = stream.read(4)
        if chunk != b"IHDR" or length < 8:
            raise AssertionError(f"missing PNG IHDR: {path.name}")
        return struct.unpack(">II", stream.read(8))


class ChapterFigureTests(unittest.TestCase):
    def test_all_eight_pngs_have_publication_dimensions(self):
        for name, dimensions in EXPECTED.items():
            with self.subTest(name=name):
                self.assertTrue((IMAGES / name).is_file(), name)
                self.assertEqual(dimensions, png_dimensions(IMAGES / name))

    def test_each_figure_has_unique_alt_text_and_reading_contract(self):
        markdown = CHAPTER.read_text(encoding="utf-8")
        matches = list(
            re.finditer(r"^!\[(?P<alt>[^]]+)\]\(images/(?P<name>fig9-[^)]+\.png)\)$", markdown, re.MULTILINE)
        )
        self.assertEqual(set(EXPECTED), {match.group("name") for match in matches})
        self.assertEqual(len(matches), len({match.group("alt") for match in matches}))
        for index, match in enumerate(matches):
            end = matches[index + 1].start() if index + 1 < len(matches) else len(markdown)
            following = markdown[match.end():end]
            self.assertIn("**读图顺序：**", following, match.group("name"))
            self.assertIn("**这张图要说明：**", following, match.group("name"))

    def test_failure_map_v2_ends_in_a_decision_not_a_second_receipt(self):
        prompt = (
            ROOT
            / "infographic/chapter9-failure-map/prompts/infographic-v2.md"
        ).read_text(encoding="utf-8")
        self.assertIn("继续 / 停止", prompt)
        self.assertIn("never show another receipt after model context", prompt.casefold())


if __name__ == "__main__":
    unittest.main()
