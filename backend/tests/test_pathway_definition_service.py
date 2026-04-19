import unittest
import uuid
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

from fastapi import HTTPException

from app.services.pathway_definition_service import PathwayDefinitionService


class PathwayDefinitionServiceTests(unittest.TestCase):
    def test_parse_definition_id_or_400_rejects_invalid_value(self):
        with self.assertRaises(HTTPException) as context:
            PathwayDefinitionService.parse_definition_id_or_400("not-a-uuid")

        self.assertEqual(context.exception.status_code, 400)
        self.assertEqual(context.exception.detail, "Invalid pathway definition ID format")


class PathwayDefinitionServiceAsyncTests(unittest.IsolatedAsyncioTestCase):
    async def test_list_active_definitions_serializes(self):
        service = PathwayDefinitionService(db=object())
        item_id = uuid.uuid4()

        with patch(
            "app.services.pathway_definition_service.pathway_definition_repository.list_active_definitions",
            new=AsyncMock(
                return_value=[
                    SimpleNamespace(
                        id=item_id,
                        slug="sukunet-7",
                        title="Sükûnet 7",
                        pathway_type="anxiety_management",
                        summary="Hazır sakinleşme yolu",
                        total_days=8,
                    )
                ]
            ),
        ):
            result = await service.list_active_definitions()

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["id"], str(item_id))
        self.assertEqual(result[0]["slug"], "sukunet-7")

    async def test_get_definition_returns_nested_structure(self):
        service = PathwayDefinitionService(db=object())
        definition_id = uuid.uuid4()
        day_id = uuid.uuid4()
        task_id = uuid.uuid4()

        with patch(
            "app.services.pathway_definition_service.pathway_definition_repository.get_definition_with_days_and_tasks",
            new=AsyncMock(
                return_value=(
                    SimpleNamespace(
                        id=definition_id,
                        slug="sukunet-7",
                        title="Sükûnet 7",
                        pathway_type="anxiety_management",
                        summary="Hazır sakinleşme yolu",
                        total_days=8,
                        is_active=True,
                    ),
                    [
                        (
                            SimpleNamespace(
                                id=day_id,
                                day_number=0,
                                title="Başlangıç",
                                description="Yumuşak giriş",
                                is_day0=True,
                                is_skippable=True,
                            ),
                            [
                                SimpleNamespace(
                                    id=task_id,
                                    task_type="day0_intro",
                                    title="Niyet",
                                    description="Kısa niyet",
                                    duration_minutes=2,
                                    order_index=0,
                                    task_metadata={"k": "v"},
                                )
                            ],
                        )
                    ],
                )
            ),
        ):
            result = await service.get_definition(str(definition_id))

        self.assertEqual(result["id"], str(definition_id))
        self.assertEqual(result["days"][0]["tasks"][0]["id"], str(task_id))

    async def test_start_pathway_from_definition_raises_404_when_missing(self):
        service = PathwayDefinitionService(db=object())

        with patch(
            "app.services.pathway_definition_service.pathway_definition_repository.get_definition_with_days_and_tasks",
            new=AsyncMock(return_value=None),
        ):
            with self.assertRaises(HTTPException) as context:
                await service.start_pathway_from_definition(
                    definition_id=str(uuid.uuid4()),
                    user_id=uuid.uuid4(),
                )

        self.assertEqual(context.exception.status_code, 404)
        self.assertEqual(context.exception.detail, "Pathway definition not found")

    async def test_start_pathway_from_definition_builds_admin_blueprint(self):
        service = PathwayDefinitionService(db=object())
        definition_id = uuid.uuid4()

        definition = SimpleNamespace(
            id=definition_id,
            slug="sukunet-7",
            title="Sükûnet 7",
            pathway_type="anxiety_management",
            summary="Hazır sakinleşme yolu",
            total_days=8,
            is_active=True,
        )
        day = SimpleNamespace(
            id=uuid.uuid4(),
            day_number=1,
            title="1. gün",
            description="Giriş",
            is_day0=False,
            is_skippable=False,
        )
        task = SimpleNamespace(
            id=uuid.uuid4(),
            task_type="morning",
            title="Sabah nefesi",
            description="3 dakika",
            duration_minutes=3,
            order_index=0,
            task_metadata={"source": "admin"},
        )

        service.pathway_service.instantiate_blueprint = AsyncMock(
            return_value=SimpleNamespace(id=uuid.uuid4())
        )

        with patch(
            "app.services.pathway_definition_service.pathway_definition_repository.get_definition_with_days_and_tasks",
            new=AsyncMock(return_value=(definition, [(day, [task])])),
        ):
            await service.start_pathway_from_definition(
                definition_id=str(definition_id),
                user_id=uuid.uuid4(),
                topic_summary="Kişisel özet",
            )

        service.pathway_service.instantiate_blueprint.assert_awaited_once()
        kwargs = service.pathway_service.instantiate_blueprint.await_args.kwargs
        blueprint = kwargs["blueprint"]
        self.assertEqual(blueprint.source, "admin")
        self.assertEqual(blueprint.topic_summary, "Kişisel özet")
        self.assertEqual(blueprint.days[0].tasks[0].title, "Sabah nefesi")


if __name__ == "__main__":
    unittest.main()
