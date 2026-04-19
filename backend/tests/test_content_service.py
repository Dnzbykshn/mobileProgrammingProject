import unittest
from unittest.mock import AsyncMock, patch

from app.domain.content.models import ContentSearchQuery
from app.domain.content.service import ContentService


class ContentServiceHybridTests(unittest.IsolatedAsyncioTestCase):
    async def test_search_hybrid_mode_merges_graph_terms_and_reranks_results(self):
        service = ContentService(db=None)
        service.graph_context_service.get_context = AsyncMock(
            return_value={
                "graph_keywords": ["ferahlık", "tevekkül"],
                "graph_passages": [{"id": 2}, {"id": 1}],
                "graph_sub_categories": ["sükunet"],
                "graph_root_categories": ["duygu"],
                "graph_summary": "",
                "suggested_pathway_type": None,
            }
        )
        service._vector_search = AsyncMock(
            return_value=[
                (1, "quran", "İlk sonuç", "Açıklama 1", {}),
                (2, "quran", "İkinci sonuç", "Açıklama 2", {}),
            ]
        )
        service._text_search = AsyncMock(return_value=[])
        # backfill path: results (2) < limit (3) → called, but returns empty to keep test focused
        service.repository.fetch_rows_by_ids = AsyncMock(return_value=[])

        results = await service.search(
            ContentSearchQuery(
                query="içim daralıyor",
                limit=3,
                source_types=["quran"],
            )
        )

        # final_query passed to _vector_search must contain original + graph terms
        called_query = service._vector_search.await_args.kwargs["query"]
        self.assertIn("içim daralıyor", called_query)
        self.assertIn("ferahlık", called_query)
        self.assertIn("tevekkül", called_query)

        # graph re-rank: graph says [2, 1], so id=2 should come first
        self.assertEqual([item.id for item in results], [2, 1])
        # graph context present → all hints should be "hybrid"
        self.assertTrue(all(item.score_hint == "hybrid" for item in results))

    async def test_search_appends_graph_rows_when_vector_results_are_short(self):
        service = ContentService(db=None)
        service.graph_context_service.get_context = AsyncMock(
            return_value={
                "graph_keywords": ["teselli"],
                "graph_passages": [{"id": 7}],
                "graph_sub_categories": [],
                "graph_root_categories": [],
                "graph_summary": "",
                "suggested_pathway_type": None,
            }
        )
        service._vector_search = AsyncMock(
            return_value=[
                (1, "quran", "Mevcut sonuç", "Açıklama", {}),
            ]
        )
        service._text_search = AsyncMock(return_value=[])
        service.repository.fetch_rows_by_ids = AsyncMock(
            return_value=[
                (7, "quran", "Graf sonucu", "Graf açıklama", {}),
            ]
        )

        results = await service.search(
            ContentSearchQuery(
                query="bunaldım",
                limit=2,
                source_types=["quran"],
            )
        )

        self.assertEqual([item.id for item in results], [1, 7])
        self.assertEqual(results[0].score_hint, "hybrid")
        self.assertEqual(results[1].score_hint, "graph")
        service.graph_context_service.get_context.assert_awaited_once()

    async def test_structured_query_bypasses_semantic_search(self):
        service = ContentService(db=None)
        service.repository.lookup_by_reference = AsyncMock(
            return_value=[
                (255, "quran", "Ayetel Kürsi metni", "Açıklama", {"surah_no": 2, "verse_no": 255}),
            ]
        )

        results = await service.search(
            ContentSearchQuery(query="2:255", limit=5, source_types=["quran"])
        )

        service.repository.lookup_by_reference.assert_awaited_once_with(
            service.db, surah_no=2, verse_no=255, limit=5
        )
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].id, 255)
        self.assertEqual(results[0].score_hint, "lookup")

    async def test_text_search_failure_does_not_break_search(self):
        service = ContentService(db=None)
        service.graph_context_service.get_context = AsyncMock(
            return_value={
                "graph_keywords": [],
                "graph_passages": [],
                "graph_sub_categories": [],
                "graph_root_categories": [],
                "graph_summary": "",
                "suggested_pathway_type": None,
            }
        )
        service._vector_search = AsyncMock(
            return_value=[(1, "quran", "Sonuç", "Açıklama", {})]
        )
        # mock at repository level so the try/except in _text_search catches it
        service.repository.text_search = AsyncMock(side_effect=Exception("DB error"))

        # Should not raise; falls back to vector-only results
        results = await service.search(
            ContentSearchQuery(query="sabır", limit=3, source_types=["quran"])
        )
        self.assertGreater(len(results), 0)


if __name__ == "__main__":
    unittest.main()
