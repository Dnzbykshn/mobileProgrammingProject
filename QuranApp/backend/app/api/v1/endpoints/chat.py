"""
Chat endpoint - Conversational therapy interface with state machine.
Manages: conversation lifecycle, message persistence, phase transitions.
Context-aware: injects user profile, active plans, and cross-conversation history.
Redis-cached: chat history, user context, guardrail results.
"""
import uuid
import traceback
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, Request
from typing import Optional
import redis.asyncio as aioredis
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update

from app.schemas.chat import ChatRequest, ChatResponse
from app.core.dependencies import get_redis, get_master_brain, get_db, get_current_user
from app.core.cache import (
    get_cached_history, set_cached_history, invalidate_history,
    get_cached_context, set_cached_context,
)
from app.services.master_brain import MasterBrain
from app.services.prescription_engine import PrescriptionEngine
from app.services.plan_service import PlanService
from app.services.journey_decision_service import JourneyDecisionService
from app.services.memory_extraction_service import extract_memories_from_conversation
from app.services.language_style_analyzer import extract_language_features, evolve_conversational_tone
from app.models.conversation import Conversation, Message
from app.models.prescription import Prescription
from app.models.user_profile import UserProfile
from app.repositories import profile_repository, plan_repository
from app.repositories.profile_repository import profile_to_context_str
from app.repositories.plan_repository import active_plans_to_context_str
from app.core.rate_limit import limiter

router = APIRouter()


async def get_or_create_conversation(
    db: AsyncSession,
    conversation_id: Optional[str],
    user_id: Optional[str],
) -> Conversation:
    """Get existing conversation or create a new one."""
    if conversation_id:
        # Validate UUID format before querying
        try:
            conv_uuid = uuid.UUID(conversation_id)
        except (ValueError, AttributeError):
            conv_uuid = None  # Invalid UUID — treat as new conversation

        if conv_uuid:
            result = await db.execute(
                select(Conversation).where(Conversation.id == conv_uuid)
            )
            conv = result.scalar_one_or_none()
            if conv:
                conv_user_id = str(conv.user_id) if conv.user_id else None
                # Authorization:
                # - authenticated callers can only continue their own conversations
                # - anonymous callers can only continue anonymous conversations
                is_authorized = (
                    (user_id is not None and conv_user_id == user_id)
                    or (user_id is None and conv_user_id is None)
                )
                if is_authorized:
                    return conv
    # Create new conversation
    conv = Conversation(
        id=uuid.uuid4(),
        user_id=uuid.UUID(user_id) if user_id else None,
        phase="IDLE",
        gathering_context={},
    )
    db.add(conv)
    await db.flush()
    return conv


async def get_conversation_history(
    db: AsyncSession,
    conversation_id,
    redis_client: Optional[aioredis.Redis] = None,
) -> list:
    """Get messages for a conversation. Redis first → DB fallback."""
    conv_id_str = str(conversation_id)

    # Try Redis cache first
    cached = await get_cached_history(redis_client, conv_id_str)
    if cached:
        return cached

    # DB fallback
    result = await db.execute(
        select(Message)
        .where(Message.conversation_id == conversation_id)
        .order_by(Message.created_at.asc())
    )
    messages = result.scalars().all()
    history = [
        {"sender": m.sender, "content": m.content}
        for m in messages
    ]

    # Write to Redis for next time
    await set_cached_history(redis_client, conv_id_str, history)
    return history


async def save_message(
    db: AsyncSession,
    conversation_id,
    sender: str,
    content: str,
    metadata: dict = None,
):
    """Save a message to the conversation."""
    msg = Message(
        conversation_id=conversation_id,
        sender=sender,
        content=content,
        metadata_=metadata,
    )
    db.add(msg)
    await db.flush()


def build_conversation_context(history: list) -> str:
    """Build a string representation of the conversation for AI context."""
    lines = []
    for msg in history:
        role = "Kullanıcı" if msg["sender"] == "user" else "Terapist"
        lines.append(f"{role}: {msg['content']}")
    return "\n".join(lines)


async def build_user_context(
    db: AsyncSession,
    user_id: Optional[str],
    current_message: Optional[str] = None,
    redis_client: Optional[aioredis.Redis] = None,
) -> dict:
    """
    Build full user context for AI with memory retrieval and language style.
    Cached in Redis (5min TTL).

    Includes:
    - User profile (known topics, mood, interaction count)
    - Active plans and today's progress
    - Cross-conversation history
    - Relevant memories (semantic search based on current message)
    - Language style and conversational tone preferences
    """
    if not user_id:
        return {
            "profile_str": "Anonim kullanıcı (giriş yapmamış).",
            "plans_str": "Aktif plan yok.",
            "cross_history": [],
            "memory_str": "",
            "spiritual_prefs": "",
            "language_style": {},
            "conversational_tone": "polite_formal",
        }

    # Try Redis cache first (for static fields: profile, plans, style)
    cached = await get_cached_context(redis_client, user_id)
    if cached:
        # Memory retrieval is ALWAYS dynamic (depends on current message embedding)
        # So we override memory_str from cache with fresh retrieval
        memory_str = ""
        if current_message:
            try:
                from app.services.ai_service import get_embedding
                from app.repositories import memory_repository

                uid_for_mem = uuid.UUID(user_id)
                query_embedding = await get_embedding(current_message)
                memories = await memory_repository.retrieve_relevant_memories(
                    db, uid_for_mem, query_embedding, limit=4
                )
                memory_str = memory_repository.memories_to_context_str(memories)
                print(f"🧠 Memory retrieval (cached path): {len(memories)} memories found")
                if memories:
                    print(f"🧠 Memory context: {memory_str[:200]}...")
            except Exception as e:
                print(f"⚠️ Memory retrieval failed: {e}")
                memory_str = cached.get("memory_str", "")

        cached["memory_str"] = memory_str
        return cached

    uid = uuid.UUID(user_id)

    # Get or create profile
    profile = await profile_repository.get_or_create_profile(db, uid)
    profile_str = profile_to_context_str(profile)

    # Get active plans with today's progress
    active_plans = await plan_repository.get_active_plans_with_progress(db, uid)
    plans_str = active_plans_to_context_str(active_plans)

    # Cross-conversation history (last 20 messages from ALL conversations)
    cross_history = await get_cross_conversation_history(db, uid, limit=20)

    # Retrieve relevant memories (semantic search based on current message)
    memory_str = ""
    if current_message:
        try:
            from app.services.ai_service import get_embedding
            from app.repositories import memory_repository

            # Generate embedding for current message
            query_embedding = await get_embedding(current_message)

            # Hybrid search: semantic + recency + importance
            memories = await memory_repository.retrieve_relevant_memories(
                db, uid, query_embedding, limit=4
            )

            # Format for AI prompt
            memory_str = memory_repository.memories_to_context_str(memories)
            print(f"🧠 Memory retrieval: {len(memories)} memories found for user {user_id}")
            if memories:
                print(f"🧠 Memory context: {memory_str[:200]}...")
        except Exception as e:
            print(f"⚠️ Memory retrieval failed: {e}")
            import traceback
            traceback.print_exc()
            memory_str = "Anı sisteminde geçici bir sorun var."

    # Spiritual preferences (favorite surahs, duas, esmas)
    spiritual_prefs_str = ""
    if hasattr(profile, 'spiritual_preferences') and profile.spiritual_preferences:
        from app.repositories.memory_repository import spiritual_preferences_to_context_str
        spiritual_prefs_str = spiritual_preferences_to_context_str(profile.spiritual_preferences)

    # Language style and conversational tone
    language_style = profile.language_style if hasattr(profile, 'language_style') else {}
    conversational_tone = profile.conversational_tone if hasattr(profile, 'conversational_tone') else "polite_formal"

    context = {
        "profile_str": profile_str,
        "plans_str": plans_str,
        "active_plans": active_plans,
        "cross_history": cross_history,
        "memory_str": memory_str,
        "spiritual_prefs": spiritual_prefs_str,
        "language_style": language_style,
        "conversational_tone": conversational_tone,
    }

    # Cache for next time
    await set_cached_context(redis_client, user_id, context)
    return context


async def get_cross_conversation_history(
    db: AsyncSession, user_id, limit: int = 20
) -> list:
    """Get recent messages across ALL conversations for a user."""
    result = await db.execute(
        select(Message)
        .join(Conversation, Message.conversation_id == Conversation.id)
        .where(Conversation.user_id == user_id)
        .order_by(Message.created_at.desc())
        .limit(limit)
    )
    messages = list(reversed(result.scalars().all()))  # Oldest first
    return [
        {"sender": m.sender, "content": m.content}
        for m in messages
    ]


@router.post("/send", response_model=ChatResponse)
@limiter.limit("60/minute")
async def chat_endpoint(
    request: Request,
    chat_request: ChatRequest,
    brain: MasterBrain = Depends(get_master_brain),
    redis_client: Optional[aioredis.Redis] = Depends(get_redis),
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),  # Optional auth
):
    """
    Main chat endpoint with conversation state machine.
    
    Flow:
    1. Get/create conversation
    2. Save user message
    3. Process turn (MasterBrain decides phase)
    4. If READY → create Prescription + Plan together (unified!)
    5. Save assistant response
    6. Update conversation phase
    """
    user_id = str(current_user.id) if current_user else None

    # 1. Get or create conversation
    conv = await get_or_create_conversation(db, chat_request.conversation_id, user_id)
    
    # 2. Save user message
    await save_message(db, conv.id, "user", chat_request.message)

    # 3. Get conversation history (Redis → DB fallback)
    history = await get_conversation_history(db, conv.id, redis_client)
    turn_count = len([m for m in history if m["sender"] == "user"])

    # 3.5 Build user context (cached 5min) with memory retrieval
    user_context = await build_user_context(db, user_id, chat_request.message, redis_client)

    # 4. Process turn through MasterBrain (now context-aware!)
    try:
        result = await brain.process_turn(
            user_message=chat_request.message,
            conversation_history=history,
            current_phase=conv.phase or "IDLE",
            turn_count=turn_count,
            user_context=user_context,
        )
    except Exception as e:
        print(f"⚠️ MasterBrain failed: {type(e).__name__}: {e}")
        # Graceful fallback — don't crash with 500
        result = {
            "intent": "CHAT",
            "response": "Şu an bağlantıda küçük bir sorun yaşıyorum ama seni dinliyorum. Biraz sonra tekrar dener misin? 🤲",
            "new_phase": conv.phase or "IDLE",
            "readiness_score": 0,
        }

    new_phase = result.get("new_phase", conv.phase)
    prescription_data = None
    plan_id = None
    journey_action = None

    # 5. If READY — create prescription + journey together! (with AI decision: new vs update)
    if new_phase == "READY":
        print(f"🟡 READY phase triggered for conv={conv.id}")
        context_str = build_conversation_context(history)
        engine = PrescriptionEngine(db)
        try:
            prescription_data = await engine.process_request(context_str)
            print(f"✅ Prescription data created: keys={list(prescription_data.keys())}")
        except Exception as e:
            print(f"❌ Prescription engine FAILED: {e}")
            traceback.print_exc()
            prescription_data = None

        if prescription_data:
            # Save prescription to DB
            try:
                prescription = Prescription(
                    user_id=uuid.UUID(user_id) if user_id else None,
                    conversation_id=conv.id,
                    title=prescription_data["diagnosis"]["emotional_state"],
                    description=prescription_data.get("advice", ""),
                    emotion_category=prescription_data["diagnosis"]["emotional_state"],
                    prescription_data=prescription_data,
                )
                db.add(prescription)
                await db.flush()
                print(f"✅ Prescription saved: id={prescription.id}")
            except Exception as e:
                print(f"❌ Prescription DB save FAILED: {e}")
                traceback.print_exc()
                prescription_data = None

        if prescription_data:
            # Determine journey type from emotion
            emotion = prescription_data["diagnosis"].get("emotional_state", "").lower()
            emotion_map = {
                "kaygı": "anxiety_management", "korku": "anxiety_management",
                "hüzün": "grief_healing", "üzüntü": "grief_healing",
                "yas": "grief_healing", "öfke": "anger_control",
                "stres": "anxiety_management", "umutsuzluk": "grief_healing",
            }
            journey_type = emotion_map.get(emotion, "spiritual_growth")
            print(f"🗺️ Journey type resolved: emotion='{emotion}' → type='{journey_type}'")

            # Get active journeys and decide: new or update?
            try:
                plan_service = PlanService(db)
                active_plans = await plan_repository.get_active_plans_with_progress(
                    db, uuid.UUID(user_id) if user_id else None
                ) if user_id else []
                print(f"📋 Active plans found: {len(active_plans)}")

                decision = None
                if active_plans:
                    decision_service = JourneyDecisionService(db)
                    decision = await decision_service.decide(
                        user_id=user_id,
                        diagnosis=prescription_data["diagnosis"],
                        active_journeys=active_plans,
                    )
                    print(f"🤖 Journey decision: action={decision.action}, confidence={decision.confidence}")

                # Apply decision
                if decision and decision.action == "update_journey" and decision.confidence >= 0.7:
                    # UPDATE existing journey
                    print(f"🔄 Updating journey: {decision.matching_plan_id}")
                    plan = await plan_service.update_journey_remaining_days(
                        plan_id=decision.matching_plan_id,
                        new_prescription_data=prescription_data,
                        new_user_context=context_str[:500],
                        new_journey_type=journey_type,
                    )
                    plan_id = decision.matching_plan_id
                    journey_action = "updated"
                    result["response"] = (
                        "Anlıyorum, bu konuyu daha iyi anladım. Mevcut yolculuğundaki "
                        "kalan günleri senin için yeniledim, inşaAllah. Tamamladığın günler korundu. 🤲"
                    )
                else:
                    # CREATE new journey
                    topic_summary = f"{prescription_data['diagnosis']['emotional_state']}: {prescription_data['diagnosis']['root_cause'][:100]}"
                    topic_keywords = prescription_data["diagnosis"].get("search_keywords", [])
                    print(f"🆕 Creating NEW journey: type={journey_type}, topic={topic_summary[:50]}")

                    plan = await plan_service.create_journey(
                        user_id=user_id,
                        prescription_id=str(prescription.id),
                        conversation_id=str(conv.id),
                        journey_type=journey_type,
                        user_context=context_str[:500],
                        prescription_data=prescription_data,
                        topic_summary=topic_summary,
                        topic_keywords=topic_keywords,
                    )
                    plan_id = str(plan.id)
                    journey_action = "created"
                    print(f"✅ Journey CREATED: plan_id={plan_id}")
                    result["response"] = (
                        "Bismillah, senin için özel bir manevi yolculuk hazırladım. "
                        "Önce Gün 0'da rutinni incele, sonra 7 gün boyunca sabah sureleri, "
                        "akşam duaları ve günlük tefekkür ile inşaAllah huzur bulacaksın. 🤲"
                    )

                # Invalidate user context cache (journey list changed)
                from app.core.cache import invalidate_context
                await invalidate_context(redis_client, user_id)
                print(f"✅ Cache invalidated for user={user_id}")

            except Exception as e:
                print(f"❌ Journey creation/update FAILED: {type(e).__name__}: {e}")
                traceback.print_exc()
                journey_action = "failed"

            # Update conversation
            conv.prescription_id = prescription.id
            if plan_id:
                conv.plan_id = uuid.UUID(plan_id) if isinstance(plan_id, str) else plan_id
            new_phase = "GENERATED"

    # 6. If UPDATE_PRESCRIPTION — update existing
    elif result.get("needs_prescription_update"):
        context_str = build_conversation_context(history)
        engine = PrescriptionEngine(db)
        prescription_data = await engine.process_request(context_str)

        if conv.prescription_id:
            await db.execute(
                update(Prescription)
                .where(Prescription.id == conv.prescription_id)
                .values(
                    prescription_data=prescription_data,
                    title=prescription_data["diagnosis"]["emotional_state"],
                    description=prescription_data.get("advice", ""),
                )
            )
        new_phase = "ONGOING"
        result["response"] = "rutinni güncellendi. İşte yenilenmiş rutinin."

    # 7. Save assistant response
    await save_message(
        db, conv.id, "assistant", result["response"],
        metadata={"intent": result["intent"], "phase": new_phase},
    )

    # 8. Update conversation phase
    conv.phase = new_phase
    if result.get("gathered_insight"):
        ctx = conv.gathering_context or {}
        insights = ctx.get("insights", [])
        insights.append(result["gathered_insight"])
        ctx["insights"] = insights
        conv.gathering_context = ctx

    await db.commit()

    # 8.1 Invalidate chat cache (new messages added)
    await invalidate_history(redis_client, str(conv.id))

    # 8.2 Extract memories if conversation reached GENERATED phase
    if new_phase == "GENERATED" and user_id:
        try:
            # Extract memories from completed conversation
            memory_ids = await extract_memories_from_conversation(db, conv.id)
            print(f"📝 Extracted {len(memory_ids)} memories from conversation {conv.id}")

            # Invalidate user context cache so next conversation uses new memories
            if memory_ids:
                from app.core.cache import invalidate_context
                await invalidate_context(redis_client, user_id)
                print(f"🔄 User context cache invalidated after memory extraction")
        except Exception as e:
            print(f"⚠️ Memory extraction failed: {e}")
            # Don't crash - memory extraction is non-critical for response

    # 8.5 Update user profile after each interaction
    if user_id:
        try:
            mood = result.get("gathered_insight", "")[:50] if result.get("gathered_insight") else None
            await profile_repository.update_profile(
                db, user_id,
                last_mood=mood,
                increment_interactions=1,
            )
            await db.commit()
        except Exception as e:
            print(f"⚠️ Profile update skipped: {e}")

    # 8.6 Track language style adaptation (learn user's communication style)
    if user_id:
        try:
            # Get current profile with language_style
            profile_result = await db.execute(
                select(UserProfile).where(UserProfile.user_id == uuid.UUID(user_id))
            )
            profile = profile_result.scalar_one_or_none()

            if profile:
                current_style = profile.language_style or {}

                # Extract linguistic features from user message
                updated_style = extract_language_features(chat_request.message, current_style)
                updated_style["last_updated"] = datetime.now(timezone.utc).isoformat()

                # Evolve conversational tone based on relationship duration
                interaction_count = profile.interaction_count or 0
                relationship_start = profile.relationship_start_date or datetime.now(timezone.utc)
                relationship_days = (datetime.now(timezone.utc) - relationship_start).days

                new_tone = evolve_conversational_tone(interaction_count, relationship_days)

                # Update profile
                profile.language_style = updated_style
                profile.conversational_tone = new_tone

                await db.commit()
                print(f"🎨 Language style updated: formality={updated_style.get('formality_level', 0.5):.2f}, tone={new_tone}")
        except Exception as e:
            print(f"⚠️ Language style tracking failed: {e}")

    # 9. Build response
    readiness = result.get("readiness_score", 0)
    response = ChatResponse(
        intent=result["intent"] if not prescription_data else "PRESCRIPTION",
        response_text=result["response"],
        prescription=prescription_data,
        conversation_id=str(conv.id),
        phase=new_phase,
        gathering_progress=readiness,
        crisis_level=result.get("crisis_level"),
        emergency_contacts=result.get("emergency_contacts"),
        plan_id=plan_id,
        journey_action=journey_action,
        proposal_summary=result.get("proposal_summary"),
    )

    return response
