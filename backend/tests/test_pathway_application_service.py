import unittest
from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

from fastapi import HTTPException

from app.services.pathway_application_service import PathwayApplicationService


class PathwayApplicationServiceTests(unittest.TestCase):
    def test_parse_pathway_id_or_400_rejects_invalid_value(self):
        with self.assertRaises(HTTPException) as context:
            PathwayApplicationService.parse_pathway_id_or_400('not-a-uuid')

        self.assertEqual(context.exception.status_code, 400)
        self.assertEqual(context.exception.detail, 'Invalid pathway ID format')

    def test_format_pathway_response_groups_tasks(self):
        pathway = SimpleNamespace(
            id='550e8400-e29b-41d4-a716-446655440000',
            title='Sükûnet Yolu',
            pathway_type='anxiety_management',
            total_days=8,
            current_day=1,
            status='active',
            started_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
            topic_summary='Kaygı döneminde sakinleşme',
            day0_skipped=False,
        )
        task = SimpleNamespace(
            id='660e8400-e29b-41d4-a716-446655440000',
            day_number=1,
            task_type='morning',
            title='Sabah nefesi',
            description='3 dakika nefes',
            duration_minutes=3,
            order_index=0,
            is_completed=False,
            completed_at=None,
            task_metadata=None,
        )

        response = PathwayApplicationService.format_pathway_response(pathway, {1: [task]})

        self.assertEqual(response.title, 'Sükûnet Yolu')
        self.assertEqual(response.pathway_type, 'anxiety_management')
        self.assertEqual(len(response.days), 1)
        self.assertEqual(response.days[0].tasks[0].title, 'Sabah nefesi')
        self.assertFalse(response.days[0].is_day0)


class PathwayApplicationServiceAsyncTests(unittest.IsolatedAsyncioTestCase):
    async def test_get_active_pathways_returns_canonical_ids(self):
        service = PathwayApplicationService(db=object())
        current_user = SimpleNamespace(id='user-1')

        with patch(
            'app.services.pathway_application_service.pathway_repository.get_active_pathways_with_progress',
            new=AsyncMock(
                return_value=[
                    {
                        'pathway_id': 'path-123',
                        'title': 'Sükûnet Yolu',
                        'pathway_type': 'anxiety_management',
                        'topic_summary': 'Kaygı için sade adımlar',
                        'current_day': 2,
                        'total_days': 8,
                        'today_completed': 1,
                        'today_total': 3,
                        'started_at': '2026-01-01T00:00:00+00:00',
                    }
                ]
            ),
        ):
            summaries = await service.get_active_pathways(current_user=current_user)

        self.assertEqual(len(summaries), 1)
        self.assertEqual(summaries[0].pathway_id, 'path-123')
        self.assertEqual(summaries[0].title, 'Sükûnet Yolu')
        self.assertEqual(summaries[0].pathway_type, 'anxiety_management')

    async def test_complete_day_requires_current_day(self):
        service = PathwayApplicationService(db=object())
        current_user = SimpleNamespace(id='user-1')

        service.get_authorized_pathway_or_404 = AsyncMock(
            return_value=SimpleNamespace(id='path-1', current_day=2)
        )

        with self.assertRaises(HTTPException) as context:
            await service.complete_day(pathway_id='path-1', day_number=1, current_user=current_user)

        self.assertEqual(context.exception.status_code, 409)
        self.assertIn('Only current day can be completed', context.exception.detail)

    async def test_complete_day_requires_all_tasks_completed(self):
        service = PathwayApplicationService(db=object())
        current_user = SimpleNamespace(id='user-1')

        service.get_authorized_pathway_or_404 = AsyncMock(
            return_value=SimpleNamespace(id='path-1', current_day=0)
        )
        service.pathway_service.complete_day = AsyncMock()

        with patch(
            'app.services.pathway_application_service.pathway_repository.get_pathway_tasks',
            new=AsyncMock(
                return_value=[
                    SimpleNamespace(day_number=0, is_completed=True),
                    SimpleNamespace(day_number=0, is_completed=False),
                ]
            ),
        ):
            with self.assertRaises(HTTPException) as context:
                await service.complete_day(pathway_id='path-1', day_number=0, current_user=current_user)

        self.assertEqual(context.exception.status_code, 409)
        self.assertEqual(context.exception.detail, 'Complete all tasks before finishing the day')
        service.pathway_service.complete_day.assert_not_awaited()

    async def test_toggle_task_returns_iso_timestamp(self):
        service = PathwayApplicationService(db=object())
        current_user = SimpleNamespace(id='user-1')
        completed_at = datetime(2026, 1, 1, 12, 30, tzinfo=timezone.utc)

        service.get_authorized_pathway_or_404 = AsyncMock(
            return_value=SimpleNamespace(id='path-1', current_day=0)
        )
        service.pathway_service.complete_task = AsyncMock(
            return_value=SimpleNamespace(
                id='task-1',
                is_completed=True,
                completed_at=completed_at,
            )
        )

        with patch(
            'app.services.pathway_application_service.pathway_repository.get_pathway_task_by_id',
            new=AsyncMock(return_value=SimpleNamespace(id='task-1', day_number=0)),
        ):
            response = await service.toggle_task(
                pathway_id='path-1',
                task_id='task-1',
                current_user=current_user,
            )

        self.assertEqual(response['completed_at'], completed_at.isoformat())

    async def test_toggle_task_blocks_future_day_tasks(self):
        service = PathwayApplicationService(db=object())
        current_user = SimpleNamespace(id='user-1')

        service.get_authorized_pathway_or_404 = AsyncMock(
            return_value=SimpleNamespace(id='path-1', current_day=1)
        )
        service.pathway_service.complete_task = AsyncMock()

        with patch(
            'app.services.pathway_application_service.pathway_repository.get_pathway_task_by_id',
            new=AsyncMock(return_value=SimpleNamespace(id='task-9', day_number=3)),
        ):
            with self.assertRaises(HTTPException) as context:
                await service.toggle_task(pathway_id='path-1', task_id='task-9', current_user=current_user)

        self.assertEqual(context.exception.status_code, 409)
        self.assertEqual(context.exception.detail, 'Future day tasks cannot be updated yet')
        service.pathway_service.complete_task.assert_not_awaited()

    async def test_skip_day0_requires_starting_day(self):
        service = PathwayApplicationService(db=object())
        current_user = SimpleNamespace(id='user-1')

        service.get_authorized_pathway_or_404 = AsyncMock(
            return_value=SimpleNamespace(id='path-1', current_day=2)
        )

        with self.assertRaises(HTTPException) as context:
            await service.skip_day0(pathway_id='path-1', current_user=current_user)

        self.assertEqual(context.exception.status_code, 409)
        self.assertEqual(context.exception.detail, 'Day 0 can only be skipped at the start')


if __name__ == '__main__':
    unittest.main()
