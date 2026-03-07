"""
Plan Service — 7-day journey generation and management.
Uses centralized ai_service for Gemini.
"""
import json
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.ai_service import generate_content
from app.repositories import plan_repository


# Template for different journey types
JOURNEY_TEMPLATES = {
    "anxiety_management": {
        "title_tr": "Kaygı Yönetimi Yolculuğu",
        "focus": "calming, trust in Allah, releasing fears",
        "progression": "Start with breathing + short surahs, progress to reflection + longer dhikr",
    },
    "grief_healing": {
        "title_tr": "Hüzün İyileşme Yolculuğu",
        "focus": "patience, hope, accepting Allah's decree",
        "progression": "Start with comforting duas, progress to gratitude journaling",
    },
    "anger_control": {
        "title_tr": "Öfke Kontrolü Yolculuğu",
        "focus": "patience (sabr), gentleness (hilm), forgiveness",
        "progression": "Start with wudu + istighfar, progress to reflection on patience",
    },
    "spiritual_growth": {
        "title_tr": "Manevi Gelişim Yolculuğu",
        "focus": "deepening connection with Allah, self-improvement",
        "progression": "Start with basic dhikr, progress to tahajjud preparation",
    },
}


class PlanService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_journey(
        self,
        user_id,
        prescription_id=None,
        conversation_id=None,
        journey_type: str = "anxiety_management",
        user_context: str = "",
        prescription_data: dict = None,
        topic_summary: str = "",
        topic_keywords: list = None,
    ):
        """Generate and save a personalized 8-day journey (Day 0 + Days 1-7)."""
        template = JOURNEY_TEMPLATES.get(journey_type, JOURNEY_TEMPLATES["spiritual_growth"])

        # Save plan (total_days=8, current_day=0)
        plan = await plan_repository.create_plan(
            self.db,
            user_id=user_id,
            prescription_id=prescription_id,
            conversation_id=conversation_id,
            journey_title=template["title_tr"],
            journey_type=journey_type,
            topic_summary=topic_summary,
            topic_keywords=topic_keywords or [],
            total_days=8,
        )

        # Create Day 0 tasks from prescription data
        if prescription_data:
            await self._create_day0_tasks(plan.id, prescription_data)

        # Generate Days 1-7 with AI
        prompt = f"""
        You are an Islamic Spiritual Therapy planner.

        Create a 7-day spiritual routine plan in Turkish.

        Journey Type: {template['title_tr']}
        Focus: {template['focus']}
        Progression: {template['progression']}
        User Context: {user_context or 'General spiritual wellness'}

        OUTPUT RULES:
        - Each day has exactly 3 tasks: "morning", "evening", "journal"
        - Day 1 tasks should be 3-5 minutes, Day 7 tasks should be 10-15 minutes
        - Progressive difficulty: start simple, build up
        - All text in Turkish
        - Output valid JSON

        OUTPUT FORMAT:
        {{
            "days": [
                {{
                    "day": 1,
                    "tasks": [
                        {{"type": "morning", "title": "Sabah (3 dk)", "description": "İhlâs - Felak - Nas", "duration": 3}},
                        {{"type": "evening", "title": "Akşam (5 dk)", "description": "İnşirah Suresi + Şükür", "duration": 5}},
                        {{"type": "journal", "title": "Gün İçi", "description": "Bugün seni ne tetikledi?", "duration": 0}}
                    ]
                }}
            ]
        }}

        Generate ALL 7 days.
        """

        try:
            response = await generate_content(prompt)
            raw = response.text.strip()
            # Strip markdown code fences if present
            if raw.startswith("```"):
                raw = raw.split("\n", 1)[1] if "\n" in raw else raw[3:]
                if raw.endswith("```"):
                    raw = raw[:-3]
                raw = raw.strip()
            plan_data = json.loads(raw)
        except Exception as e:
            print(f"⚠️ Plan AI failed ({e}), using default template")
            plan_data = self._default_plan(template)

        # Save tasks for Days 1-7
        for day_data in plan_data.get("days", []):
            day_num = day_data["day"]
            for idx, task_data in enumerate(day_data.get("tasks", [])):
                await plan_repository.add_task(
                    self.db,
                    plan_id=plan.id,
                    day_number=day_num,
                    task_type=task_data["type"],
                    title=task_data["title"],
                    description=task_data.get("description", ""),
                    duration_minutes=task_data.get("duration", 5),
                    order_index=idx,
                )

        await self.db.commit()
        await self.db.refresh(plan)
        return plan

    async def _create_day0_tasks(self, plan_id, prescription_data: dict):
        """Create Day 0 tasks from prescription data."""
        order = 0

        # Verse tasks
        for verse in prescription_data.get("verses", []):
            await plan_repository.add_task(
                self.db,
                plan_id=plan_id,
                day_number=0,
                task_type="day0_verse",
                title=f"{verse.get('surah_name', 'Ayet')} {verse.get('verse_number', '')}",
                description=verse.get("turkish_text", ""),
                duration_minutes=2,
                order_index=order,
                metadata=verse,
            )
            order += 1

        # Esma tasks
        for esma in prescription_data.get("esmas", []):
            await plan_repository.add_task(
                self.db,
                plan_id=plan_id,
                day_number=0,
                task_type="day0_esma",
                title=esma.get("name", "Esma"),
                description=esma.get("meaning", ""),
                duration_minutes=0,
                order_index=order,
                metadata=esma,
            )
            order += 1

        # Dua tasks
        for dua in prescription_data.get("duas", []):
            await plan_repository.add_task(
                self.db,
                plan_id=plan_id,
                day_number=0,
                task_type="day0_dua",
                title=dua.get("name", "Dua"),
                description=dua.get("turkish_text", ""),
                duration_minutes=1,
                order_index=order,
                metadata=dua,
            )
            order += 1

        # Quick routine task (33-count counter)
        await plan_repository.add_task(
            self.db,
            plan_id=plan_id,
            day_number=0,
            task_type="day0_routine",
            title="3 Dakikalık Acil Rutin",
            description="Hasbunallahu ve ni'mel vekîl",
            duration_minutes=3,
            order_index=order,
            metadata={
                "target_count": 33,
                "arabic_text": "حَسْبُنَا اللَّهُ وَنِعْمَ الْوَكِيلُ",
            },
        )

    async def update_journey_remaining_days(
        self,
        plan_id,
        new_prescription_data: dict = None,
        new_user_context: str = "",
        new_journey_type: str = None,
    ):
        """Update an existing journey's remaining (incomplete) days."""
        plan = await plan_repository.get_plan_by_id(self.db, plan_id)
        if not plan:
            return None

        # Find completed days
        completed_days = await plan_repository.get_completed_days(self.db, plan_id)

        # Days to regenerate: current (if incomplete) + all future
        days_to_delete = []
        for day in range(plan.current_day, plan.total_days):
            if day not in completed_days:
                days_to_delete.append(day)

        # Delete incomplete tasks
        if days_to_delete:
            await plan_repository.delete_tasks_for_days(self.db, plan_id, days_to_delete)

        # Update Day 0 if new prescription data provided
        if new_prescription_data and 0 in days_to_delete:
            await self._create_day0_tasks(plan_id, new_prescription_data)

        # Regenerate Days 1-7 if needed
        days_1_7_to_regen = [d for d in days_to_delete if d >= 1]
        if days_1_7_to_regen:
            journey_type = new_journey_type or plan.journey_type
            template = JOURNEY_TEMPLATES.get(journey_type, JOURNEY_TEMPLATES["spiritual_growth"])

            prompt = f"""
            Regenerate spiritual tasks for specific days of a journey.

            Journey Type: {template['title_tr']}
            Focus: {template['focus']}
            User Context: {new_user_context or 'Continuing journey'}

            Days to regenerate: {days_1_7_to_regen}

            OUTPUT: JSON with same format as before, but only for the specified days.
            """

            try:
                response = await generate_content(prompt)
                raw = response.text.strip()
                if raw.startswith("```"):
                    raw = raw.split("\n", 1)[1] if "\n" in raw else raw[3:]
                    if raw.endswith("```"):
                        raw = raw[:-3]
                    raw = raw.strip()
                plan_data = json.loads(raw)

                for day_data in plan_data.get("days", []):
                    day_num = day_data["day"]
                    if day_num in days_1_7_to_regen:
                        for idx, task_data in enumerate(day_data.get("tasks", [])):
                            await plan_repository.add_task(
                                self.db,
                                plan_id=plan.id,
                                day_number=day_num,
                                task_type=task_data["type"],
                                title=task_data["title"],
                                description=task_data.get("description", ""),
                                duration_minutes=task_data.get("duration", 5),
                                order_index=idx,
                            )
            except Exception as e:
                print(f"⚠️ Journey update AI failed ({e}), keeping existing tasks")

        await self.db.commit()
        await self.db.refresh(plan)
        return plan

    async def get_plan_with_tasks(self, plan_id):
        """Get plan with tasks grouped by day number."""
        plan = await plan_repository.get_plan_by_id(self.db, plan_id)
        if not plan:
            return None

        tasks = await plan_repository.get_plan_tasks(self.db, plan_id)

        days = {}
        for task in tasks:
            if task.day_number not in days:
                days[task.day_number] = []
            days[task.day_number].append(task)

        return plan, days

    async def complete_task(self, task_id, plan_id=None):
        return await plan_repository.complete_task(self.db, task_id, plan_id=plan_id)

    async def complete_day(self, plan_id, day_number: int):
        return await plan_repository.complete_day(self.db, plan_id, day_number)

    @staticmethod
    def _default_plan(template: dict) -> dict:
        """Static fallback plan when AI generation fails."""
        morning_tasks = [
            "İhlâs - Felak - Nas", "Fatiha + Ayetel Kürsi", "İnşirah Suresi",
            "Yasin (1-12)", "Mülk Suresi (1-10)", "Rahman Suresi (1-13)", "Yasin Suresi tamam",
        ]
        evening_tasks = [
            "Şükür duası + 3 nefes", "İstihare duası", "Tesbih (33x)",
            "Tövbe + İstiğfar", "Esmaül Hüsna dinle", "Hatim duası", "Tefekkür + Şükür",
        ]
        journal_prompts = [
            "Bugün seni ne tetikledi?", "Neye şükrediyorsun?", "Kimi affetmen gerekiyor?",
            "En çok neyi kontrol etmeye çalışıyorsun?", "Hangi duygudan kaçıyorsun?",
            "Allah'a en çok ne için güveniyorsun?", "7 günde ne değişti?",
        ]
        return {
            "days": [
                {
                    "day": d + 1,
                    "tasks": [
                        {"type": "morning", "title": f"Sabah ({3 + d} dk)", "description": morning_tasks[d], "duration": 3 + d},
                        {"type": "evening", "title": f"Akşam ({5 + d} dk)", "description": evening_tasks[d], "duration": 5 + d},
                        {"type": "journal", "title": "Gün İçi", "description": journal_prompts[d], "duration": 0},
                    ],
                }
                for d in range(7)
            ]
        }
