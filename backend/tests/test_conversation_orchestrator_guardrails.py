import unittest

from app.orchestration.conversation_graph import ConversationOrchestrator


class ConversationOrchestratorGuardrailTests(unittest.IsolatedAsyncioTestCase):
    async def test_immediate_crisis_blocks_and_returns_contacts(self):
        orchestrator = ConversationOrchestrator(db=object())

        result = await orchestrator.guardrails_node(
            {
                "user_message": "Artık yaşamak istemiyorum",
                "current_phase": "IDLE",
            }
        )

        self.assertTrue(result["guardrail_hit"])
        self.assertEqual(result["intent"], "CRISIS")
        self.assertEqual(result["crisis_level"], "immediate")
        self.assertGreaterEqual(len(result["emergency_contacts"]), 1)

    async def test_moderate_crisis_preserves_context_without_blocking(self):
        orchestrator = ConversationOrchestrator(db=object())

        result = await orchestrator.guardrails_node(
            {
                "user_message": "Çok yalnızım ve değersiz hissediyorum",
                "current_phase": "GATHERING",
            }
        )

        self.assertFalse(result["guardrail_hit"])
        self.assertEqual(result["crisis_level"], "moderate")
        self.assertGreaterEqual(len(result["emergency_contacts"]), 1)

    async def test_proposing_explicit_acceptance_moves_to_ready(self):
        orchestrator = ConversationOrchestrator(db=object())

        result = await orchestrator.proposing_node({"user_message": "Evet başlayalım"})

        self.assertEqual(result["intent"], "READY")
        self.assertEqual(result["new_phase"], "READY")
        self.assertTrue(result["should_generate_prescription"])

    async def test_proposing_continue_phrase_stays_in_gathering(self):
        orchestrator = ConversationOrchestrator(db=object())

        result = await orchestrator.proposing_node({"user_message": "Devam edelim konuşalım"})

        self.assertEqual(result["intent"], "GATHERING")
        self.assertEqual(result["new_phase"], "GATHERING")
        self.assertFalse(result["should_generate_prescription"])


if __name__ == "__main__":
    unittest.main()
