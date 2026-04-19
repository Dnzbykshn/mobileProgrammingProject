from __future__ import annotations

import json
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.pathways.models import PathwayBlueprint, PathwayDayDraft, PathwayTaskDraft
from app.repositories import pathway_repository
from app.services.ai_service import generate_content
from app.services.pathway_graph_context_service import PathwayGraphContextService


PATHWAY_TEMPLATES: dict[str, dict[str, str]] = {
    "anxiety_management": {
        "title": "Sükûnet Yolu",
        "focus": "calming the heart, trust in Allah, nervous-system regulation, daily grounding",
        "progression": "start with short, low-friction routines and build toward reflection and stable habits",
    },
    "grief_healing": {
        "title": "Teselli Yolu",
        "focus": "mercy, patience, grief processing, remembering without collapsing",
        "progression": "start with comfort and breathing, build toward remembrance and gentle journaling",
    },
    "anger_control": {
        "title": "Sükûnet ve Hilm Yolu",
        "focus": "pause, patience, self-control, regulation before reaction",
        "progression": "start with interruption rituals, then build toward deeper reflection and forgiveness",
    },
    "spiritual_growth": {
        "title": "Yakınlık Yolu",
        "focus": "spiritual consistency, closeness to Allah, practical daily worship rhythm",
        "progression": "start simple, then deepen repetition, meaning, and reflection",
    },
}


class PathwayService:
    """Creates and updates a single unified pathway format for chat, manual, and future admin flows."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.graph_context_service = PathwayGraphContextService()

    async def create_pathway(
        self,
        *,
        user_id,
        pathway_type: str,
        source: str,
        user_context: str = "",
        conversation_id=None,
        topic_summary: str = "",
        topic_keywords: list[str] | None = None,
    ):
        blueprint = await self.build_blueprint(
            pathway_type=pathway_type,
            source=source,
            user_context=user_context,
            topic_summary=topic_summary,
            topic_keywords=topic_keywords or [],
        )
        return await self.instantiate_blueprint(
            user_id=user_id,
            conversation_id=conversation_id,
            blueprint=blueprint,
        )

    async def build_blueprint(
        self,
        *,
        pathway_type: str,
        source: str,
        user_context: str = "",
        topic_summary: str = "",
        topic_keywords: list[str] | None = None,
    ) -> PathwayBlueprint:
        graph_context = await self.graph_context_service.get_context(
            user_text=f"{topic_summary} {user_context}".strip(),
            keywords=topic_keywords or [],
            top_k=8,
        )

        resolved_pathway_type = pathway_type
        suggested_type = graph_context.get("suggested_pathway_type")
        if pathway_type == "spiritual_growth" and suggested_type:
            resolved_pathway_type = suggested_type

        template = PATHWAY_TEMPLATES.get(resolved_pathway_type, PATHWAY_TEMPLATES["spiritual_growth"])
        merged_keywords = list(
            dict.fromkeys([*(topic_keywords or []), *(graph_context.get("graph_keywords") or [])])
        )
        merged_summary = topic_summary or graph_context.get("graph_summary", "")

        days: list[PathwayDayDraft] = []

        day0_tasks = self._build_intro_day0_tasks(merged_summary or user_context or template["title"])
        days.append(PathwayDayDraft(day_number=0, tasks=day0_tasks))

        generated_days = await self._generate_days_1_to_7(
            pathway_type=resolved_pathway_type,
            title=template["title"],
            focus=template["focus"],
            progression=template["progression"],
            user_context=user_context,
            topic_summary=merged_summary,
            graph_context=graph_context,
        )
        days.extend(generated_days)

        return PathwayBlueprint(
            title=template["title"],
            pathway_type=resolved_pathway_type,
            topic_summary=merged_summary,
            topic_keywords=merged_keywords,
            source=source,  # type: ignore[arg-type]
            total_days=8,
            days=days,
        )

    async def instantiate_blueprint(
        self,
        *,
        user_id,
        conversation_id=None,
        blueprint: PathwayBlueprint,
    ):
        pathway = await pathway_repository.create_pathway(
            self.db,
            user_id=user_id,
            conversation_id=conversation_id,
            title=blueprint.title,
            pathway_type=blueprint.pathway_type,
            topic_summary=blueprint.topic_summary,
            topic_keywords=blueprint.topic_keywords,
            total_days=blueprint.total_days,
        )

        for day in blueprint.days:
            for task in day.tasks:
                await pathway_repository.add_pathway_task(
                    self.db,
                    pathway_id=pathway.id,
                    day_number=task.day_number,
                    task_type=task.task_type,
                    title=task.title,
                    description=task.description,
                    duration_minutes=task.duration_minutes,
                    order_index=task.order_index,
                    metadata=task.metadata,
                )

        await self.db.commit()
        await self.db.refresh(pathway)
        return pathway

    async def update_pathway_remaining_days(
        self,
        *,
        pathway_id,
        new_user_context: str = "",
        new_pathway_type: str | None = None,
        topic_summary: str = "",
        topic_keywords: list[str] | None = None,
    ):
        pathway = await pathway_repository.get_pathway_by_id(self.db, pathway_id)
        if not pathway:
            return None

        completed_days = await pathway_repository.get_completed_pathway_days(self.db, pathway_id)
        days_to_delete = [
            day
            for day in range(pathway.current_day, pathway.total_days)
            if day not in completed_days
        ]

        if days_to_delete:
            await pathway_repository.delete_tasks_for_pathway_days(self.db, pathway_id, days_to_delete)

        days_1_7 = [day for day in days_to_delete if day >= 1]
        if days_1_7:
            graph_context = await self.graph_context_service.get_context(
                user_text=f"{topic_summary or pathway.topic_summary or ''} {new_user_context}".strip(),
                keywords=topic_keywords or pathway.topic_keywords or [],
                top_k=8,
            )

            effective_type = new_pathway_type or pathway.pathway_type or "spiritual_growth"
            if effective_type == "spiritual_growth" and graph_context.get("suggested_pathway_type"):
                effective_type = graph_context["suggested_pathway_type"]

            refreshed_days = await self._generate_days_1_to_7(
                pathway_type=effective_type,
                title=pathway.title or "Manevi Yol",
                focus=PATHWAY_TEMPLATES.get(effective_type, PATHWAY_TEMPLATES["spiritual_growth"])["focus"],
                progression=PATHWAY_TEMPLATES.get(effective_type, PATHWAY_TEMPLATES["spiritual_growth"])["progression"],
                user_context=new_user_context,
                topic_summary=topic_summary or pathway.topic_summary or graph_context.get("graph_summary", ""),
                only_days=days_1_7,
                graph_context=graph_context,
            )
            for day in refreshed_days:
                for task in day.tasks:
                    await pathway_repository.add_pathway_task(
                        self.db,
                        pathway_id=pathway.id,
                        day_number=task.day_number,
                        task_type=task.task_type,
                        title=task.title,
                        description=task.description,
                        duration_minutes=task.duration_minutes,
                        order_index=task.order_index,
                        metadata=task.metadata,
                    )

        if topic_summary:
            pathway.topic_summary = topic_summary
        if topic_keywords is not None:
            pathway.topic_keywords = topic_keywords
        if new_pathway_type:
            pathway.pathway_type = new_pathway_type

        await self.db.commit()
        await self.db.refresh(pathway)
        return pathway

    async def get_pathway_with_tasks(self, pathway_id):
        pathway = await pathway_repository.get_pathway_by_id(self.db, pathway_id)
        if not pathway:
            return None

        tasks = await pathway_repository.get_pathway_tasks(self.db, pathway_id)
        days: dict[int, list[Any]] = {}
        for task in tasks:
            days.setdefault(task.day_number, []).append(task)
        return pathway, days

    async def complete_task(self, task_id, pathway_id=None):
        return await pathway_repository.toggle_task_completion(self.db, task_id, pathway_id=pathway_id)

    async def complete_day(self, pathway_id, day_number: int):
        return await pathway_repository.complete_pathway_day(self.db, pathway_id, day_number)

    async def _generate_days_1_to_7(
        self,
        *,
        pathway_type: str,
        title: str,
        focus: str,
        progression: str,
        user_context: str,
        topic_summary: str,
        only_days: list[int] | None = None,
        graph_context: dict[str, Any] | None = None,
    ) -> list[PathwayDayDraft]:
        requested_days = only_days or [1, 2, 3, 4, 5, 6, 7]

        graph_context = graph_context or {}
        graph_keywords = ", ".join((graph_context.get("graph_keywords") or [])[:6]) or "yok"
        graph_themes = ", ".join((graph_context.get("graph_sub_categories") or [])[:4]) or "yok"
        graph_passages = graph_context.get("graph_passages") or []
        passage_lines = [
            f"- {item.get('translation') or item.get('explanation') or ''}"
            for item in graph_passages[:3]
            if (item.get('translation') or item.get('explanation'))
        ]
        graph_passage_text = "\n".join(passage_lines) if passage_lines else "- yok"

        prompt = f"""
        Sen sade ama çok iyi yapılandırılmış manevi günlük rutin tasarlayan bir planlayıcısın.

        Yol adı: {title}
        Yol tipi: {pathway_type}
        Odak: {focus}
        İlerleme mantığı: {progression}
        Konu özeti: {topic_summary or 'Genel manevi destek'}
        Kullanıcı bağlamı: {user_context or 'Genel manevi destek'}
        Grafik anahtarları: {graph_keywords}
        Grafik temaları: {graph_themes}
        Grafik pasajları:
        {graph_passage_text}
        Üretilecek günler: {requested_days}

        KURALLAR:
        - Her gün tam 3 görev olsun: morning, evening, reflection.
        - Dil Türkçe olsun.
        - Düşük sürtünmeli olsun; kullanıcıyı yormasın.
        - Günler ilerledikçe hafifçe derinleşsin.
        - reflection görevi kısa yazı, düşünme veya farkındalık sorusu olabilir.
        - JSON dışında hiçbir şey yazma.

        JSON formatı:
        {{
          "days": [
            {{
              "day": 1,
              "tasks": [
                {{"type": "morning", "title": "Sabah nefesi", "description": "2 dakikalık nefes ve kısa dua", "duration": 3}},
                {{"type": "evening", "title": "Akşam sükûneti", "description": "Kısa zikir ve içe dönüş", "duration": 5}},
                {{"type": "reflection", "title": "Kısa not", "description": "Bugün kalbini en çok ne yordu?", "duration": 4}}
              ]
            }}
          ]
        }}
        """

        try:
            response = await generate_content(prompt)
            raw = response.text.strip()
            if raw.startswith("```"):
                raw = raw.split("\n", 1)[1] if "\n" in raw else raw[3:]
                if raw.endswith("```"):
                    raw = raw[:-3]
                raw = raw.strip()
            parsed = json.loads(raw)
            return self._map_generated_days(parsed.get("days", []), requested_days)
        except Exception:
            return self._default_days(requested_days)

    def _build_intro_day0_tasks(self, seed_text: str) -> list[PathwayTaskDraft]:
        seed = seed_text[:180]
        return [
            PathwayTaskDraft(
                day_number=0,
                task_type="day0_intro",
                title="Yola giriş",
                description=f"Bu yolun niyeti: {seed or 'Sakinleşmek ve istikrar kazanmak'}",
                duration_minutes=2,
                order_index=0,
            ),
            PathwayTaskDraft(
                day_number=0,
                task_type="day0_reflection",
                title="Başlangıç notu",
                description="Şu an nerede olduğunu bir iki cümleyle yaz.",
                duration_minutes=4,
                order_index=1,
            ),
            PathwayTaskDraft(
                day_number=0,
                task_type="day0_routine",
                title="İlk sakinleşme adımı",
                description="1 dakika nefesini yavaşlat, sonra içinden kısa bir niyet cümlesi kur.",
                duration_minutes=3,
                order_index=2,
            ),
        ]

    def _map_generated_days(self, generated_days: list[dict[str, Any]], requested_days: list[int]) -> list[PathwayDayDraft]:
        mapped: list[PathwayDayDraft] = []
        expected = set(requested_days)
        for day in generated_days:
            day_number = int(day.get("day", 0))
            if day_number not in expected:
                continue
            tasks = []
            for index, task in enumerate(day.get("tasks", [])):
                tasks.append(
                    PathwayTaskDraft(
                        day_number=day_number,
                        task_type=task.get("type", "reflection"),
                        title=task.get("title", "Görev"),
                        description=task.get("description", ""),
                        duration_minutes=int(task.get("duration", 5) or 5),
                        order_index=index,
                    )
                )
            if tasks:
                mapped.append(PathwayDayDraft(day_number=day_number, tasks=tasks))

        missing_days = [day for day in requested_days if day not in {draft.day_number for draft in mapped}]
        if missing_days:
            mapped.extend(self._default_days(missing_days))

        return sorted(mapped, key=lambda item: item.day_number)

    def _default_days(self, requested_days: list[int]) -> list[PathwayDayDraft]:
        morning_tasks = {
            1: ("Sabah nefesi", "3 dakika sakin nefes ve kısa niyet"),
            2: ("Sabah başlangıcı", "Fatiha ve kısa şükür cümlesi"),
            3: ("Sabah dengelemesi", "Kısa zikir ve omuz gevşetme"),
            4: ("Sabah hatırlatması", "Ayetel Kürsi veya sevdiğin kısa bir sure"),
            5: ("Sabah sabitliği", "5 dakikalık sessiz zikir"),
            6: ("Sabah yakınlığı", "Kur'an'dan kısa bir bölüm oku"),
            7: ("Sabah toparlama", "Niyet, dua ve kısa tefekkür"),
        }
        evening_tasks = {
            1: ("Akşam yavaşlama", "Günün yükünü bırakmak için kısa dua"),
            2: ("Akşam sükûneti", "3 dakikalık zikir ve nefes"),
            3: ("Akşam muhasebesi", "Bugünün ağır anını Allah'a emanet et"),
            4: ("Akşam tesellisi", "Kısa dua ve şükür listesi"),
            5: ("Akşam denge", "5 dakikalık sessizlik ve dua"),
            6: ("Akşam derinleşme", "Sevdiğin bir dua veya esmayı tekrar et"),
            7: ("Akşam kapanışı", "Bu yolun sende bıraktığını fark et"),
        }
        reflection_tasks = {
            1: "Bugün seni en çok ne zorladı?",
            2: "Bugün neyin biraz daha hafif geldiğini fark ettin?",
            3: "Tetikleyen bir an olduğunda bedeninde ne oldu?",
            4: "Bugün hangi cümle sana iyi geldi?",
            5: "Kontrol etmeyi bırakabildiğin bir şey oldu mu?",
            6: "Şu an en çok hangi desteğe ihtiyacın var?",
            7: "Bu yolculuktan yanında ne götürmek istiyorsun?",
        }

        drafts: list[PathwayDayDraft] = []
        for day in requested_days:
            morning_title, morning_desc = morning_tasks.get(day, morning_tasks[1])
            evening_title, evening_desc = evening_tasks.get(day, evening_tasks[1])
            reflection_desc = reflection_tasks.get(day, reflection_tasks[1])
            drafts.append(
                PathwayDayDraft(
                    day_number=day,
                    tasks=[
                        PathwayTaskDraft(
                            day_number=day,
                            task_type="morning",
                            title=morning_title,
                            description=morning_desc,
                            duration_minutes=min(3 + day, 12),
                            order_index=0,
                        ),
                        PathwayTaskDraft(
                            day_number=day,
                            task_type="evening",
                            title=evening_title,
                            description=evening_desc,
                            duration_minutes=min(4 + day, 14),
                            order_index=1,
                        ),
                        PathwayTaskDraft(
                            day_number=day,
                            task_type="reflection",
                            title="Kısa içe bakış",
                            description=reflection_desc,
                            duration_minutes=4,
                            order_index=2,
                        ),
                    ],
                )
            )
        return drafts
