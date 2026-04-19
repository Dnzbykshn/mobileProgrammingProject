import unittest

from app.domain.content.service import ContentService


class ContentServiceModeTests(unittest.TestCase):
    def setUp(self):
        self.service = ContentService(db=None)

    def test_short_islamic_query_stays_simple(self):
        self.assertEqual(self.service._resolve_mode("sabır ayet"), "SIMPLE")

    def test_emotional_short_query_uses_rule_mode(self):
        self.assertEqual(self.service._resolve_mode("çok bunaldım bugün"), "RULE")

    def test_emotional_long_query_uses_smart_mode(self):
        # Long queries containing emotion words should not be collapsed to RULE —
        # the full semantic context is needed.
        self.assertEqual(
            self.service._resolve_mode("hayatımda sürekli geç kalmış hissediyorum ve yoruldum"),
            "SMART",
        )

    def test_graph_search_used_for_non_islamic_single_keyword(self):
        self.assertTrue(self.service._should_use_graph_search(mode="SIMPLE", keywords=["kaygı"]))

    def test_graph_search_skipped_for_single_islamic_keyword(self):
        # A lone Islamic keyword like "dua" is well-served by vector search;
        # graph search adds latency without benefit.
        self.assertFalse(self.service._should_use_graph_search(mode="SIMPLE", keywords=["dua"]))

    # ---- Structured query detection ----

    def test_detects_numeric_surah_verse(self):
        ref = self.service._detect_structured_query("2:255")
        self.assertEqual(ref, {"surah_no": 2, "verse_no": 255})

    def test_detects_named_surah_verse(self):
        ref = self.service._detect_structured_query("Bakara 255")
        self.assertEqual(ref, {"surah_name": "Bakara", "verse_no": 255})

    def test_detects_sure_prefix(self):
        ref = self.service._detect_structured_query("Sure Fatiha")
        self.assertIsNotNone(ref)
        self.assertEqual(ref["surah_name"], "Fatiha")

    def test_no_structured_query_for_plain_text(self):
        self.assertIsNone(self.service._detect_structured_query("sabırla nasıl başa çıkarım"))

    # ---- Keyword extraction ----

    def test_extract_keywords_strips_noise(self):
        keywords = self.service._extract_query_keywords("bana namaz için ayet ver")
        self.assertNotIn("bana", keywords)
        self.assertNotIn("için", keywords)
        self.assertNotIn("ver", keywords)
        self.assertIn("namaz", keywords)
        self.assertIn("ayet", keywords)

    def test_extract_keywords_deduplicates(self):
        keywords = self.service._extract_query_keywords("sabır sabır sabır")
        self.assertEqual(keywords.count("sabır"), 1)


if __name__ == "__main__":
    unittest.main()
