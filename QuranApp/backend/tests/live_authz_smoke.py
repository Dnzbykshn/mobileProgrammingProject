#!/usr/bin/env python3
"""
Live (no-mock) auth/authz smoke checks against a running backend.

Requirements:
- Backend API running on http://127.0.0.1:8000
- PostgreSQL reachable with backend .env credentials
- Redis reachable (for logout revocation check)
"""

from __future__ import annotations

import os
import sys
import uuid
from datetime import datetime, timezone
from typing import Tuple

import httpx
import psycopg2
from psycopg2.extras import Json

from app.core.config import settings
from app.core.security import decode_access_token


API_BASE_URL = os.getenv("API_BASE_URL", "http://127.0.0.1:8000/api/v1")
HEALTH_URL = os.getenv("HEALTH_URL", "http://127.0.0.1:8000/health")
OPENAPI_URL = os.getenv("OPENAPI_URL", "http://127.0.0.1:8000/openapi.json")
REQUEST_TIMEOUT_SECONDS = float(os.getenv("REQUEST_TIMEOUT_SECONDS", "20"))


def _auth_header(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def _auth_header_with_device(token: str, device_id: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}", "X-Device-ID": device_id}


def _device_header(device_id: str) -> dict[str, str]:
    return {"X-Device-ID": device_id}


def _expect_status(resp: httpx.Response, expected: int, context: str) -> None:
    if resp.status_code != expected:
        raise RuntimeError(
            f"{context}: expected {expected}, got {resp.status_code}, body={resp.text}"
        )


def _register_and_get_user(
    client: httpx.Client,
    email: str,
    password: str,
    device_id: str,
) -> Tuple[str, str, str]:
    register_resp = client.post(
        f"{API_BASE_URL}/auth/register",
        headers=_device_header(device_id),
        json={"email": email, "password": password},
    )
    _expect_status(register_resp, 201, f"register({email})")
    token_payload = register_resp.json()
    access_token = token_payload["access_token"]
    refresh_token = token_payload.get("refresh_token")
    if not refresh_token:
        raise RuntimeError("register response did not include refresh_token")

    me_resp = client.get(
        f"{API_BASE_URL}/auth/me",
        headers=_auth_header_with_device(access_token, device_id),
    )
    _expect_status(me_resp, 200, f"auth/me({email})")
    user_id = me_resp.json()["id"]
    return access_token, refresh_token, user_id


def _assert_token_ttl_is_24h(token: str) -> None:
    payload = decode_access_token(token)
    if not payload or "exp" not in payload:
        raise RuntimeError("Token decode failed while checking expiration window")

    exp_ts = int(payload["exp"])
    now_ts = int(datetime.now(timezone.utc).timestamp())
    remaining_seconds = exp_ts - now_ts
    remaining_minutes = remaining_seconds / 60

    # Tolerant bounds for clock/runtime delays.
    if remaining_minutes < 20 * 60 or remaining_minutes > 26 * 60:
        raise RuntimeError(
            "Access token TTL is outside expected 24h window: "
            f"{remaining_minutes:.1f} minutes remaining"
        )


def _db_conn():
    return psycopg2.connect(
        host=settings.DB_HOST,
        port=settings.DB_PORT,
        dbname=settings.DB_NAME,
        user=settings.DB_USER,
        password=settings.DB_PASSWORD,
    )


def _assert_cors_policy(client: httpx.Client) -> None:
    allowed_origin = "http://localhost:5173"
    disallowed_origin = "https://evil.example"

    allowed = client.options(
        f"{API_BASE_URL}/auth/login",
        headers={
            "Origin": allowed_origin,
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "content-type,x-device-id",
        },
    )
    if allowed.status_code not in (200, 204):
        raise RuntimeError(
            f"allowed CORS preflight failed: status={allowed.status_code}, body={allowed.text}"
        )
    allow_origin_header = allowed.headers.get("access-control-allow-origin")
    if allow_origin_header != allowed_origin:
        raise RuntimeError(
            "allowed CORS preflight missing/incorrect allow-origin header: "
            f"{allow_origin_header!r}"
        )

    disallowed = client.options(
        f"{API_BASE_URL}/auth/login",
        headers={
            "Origin": disallowed_origin,
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "content-type,x-device-id",
        },
    )
    disallowed_header = disallowed.headers.get("access-control-allow-origin")
    if disallowed_header == disallowed_origin:
        raise RuntimeError("disallowed origin unexpectedly accepted by CORS policy")


def _assert_target_api_signature(client: httpx.Client) -> None:
    openapi = client.get(OPENAPI_URL)
    _expect_status(openapi, 200, "openapi")
    title = openapi.json().get("info", {}).get("title")
    if title != "Spiritual Therapy AI API":
        raise RuntimeError(
            f"unexpected target API detected at {OPENAPI_URL}: title={title!r}"
        )


def _seed_prescription_and_plan_for_user(user_id: str) -> Tuple[str, str]:
    prescription_id = str(uuid.uuid4())
    plan_id = str(uuid.uuid4())

    with _db_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO prescriptions
                    (id, user_id, title, description, emotion_category, prescription_data, status)
                VALUES
                    (%s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    prescription_id,
                    user_id,
                    "Authz Test Prescription",
                    "Security smoke test row",
                    "anxiety",
                    Json({"source": "live_authz_smoke", "ok": True}),
                    "active",
                ),
            )

            cur.execute(
                """
                INSERT INTO daily_plans
                    (id, user_id, prescription_id, journey_title, journey_type,
                     topic_summary, topic_keywords, total_days, current_day, status, day0_skipped)
                VALUES
                    (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    plan_id,
                    user_id,
                    prescription_id,
                    "Authz Smoke Journey",
                    "security_test",
                    "authorization check",
                    Json(["security", "authz"]),
                    8,
                    0,
                    "active",
                    False,
                ),
            )
        conn.commit()

    return prescription_id, plan_id


def _cleanup_users(user_ids: list[str]) -> None:
    if not user_ids:
        return
    with _db_conn() as conn:
        with conn.cursor() as cur:
            for uid in user_ids:
                cur.execute("DELETE FROM users WHERE id = %s", (uid,))
        conn.commit()


def main() -> int:
    suffix = uuid.uuid4().hex[:10]
    email_a = f"authz.live.a.{suffix}@example.com"
    email_b = f"authz.live.b.{suffix}@example.com"
    password = "StrongPass1A"
    device_a = f"device-a-{suffix}"
    device_b = f"device-b-{suffix}"
    created_user_ids: list[str] = []

    try:
        with httpx.Client(timeout=REQUEST_TIMEOUT_SECONDS) as client:
            _assert_target_api_signature(client)
            health = client.get(HEALTH_URL)
            _expect_status(health, 200, "health")
            _assert_cors_policy(client)

            access_a, refresh_a, user_a_id = _register_and_get_user(
                client, email_a, password, device_a
            )
            created_user_ids.append(user_a_id)
            access_b, refresh_b, user_b_id = _register_and_get_user(
                client, email_b, password, device_b
            )
            created_user_ids.append(user_b_id)

            _assert_token_ttl_is_24h(access_a)

            sessions_a = client.get(
                f"{API_BASE_URL}/auth/sessions",
                headers=_auth_header_with_device(access_a, device_a),
            )
            _expect_status(sessions_a, 200, "list sessions")
            sessions_a_data = sessions_a.json()
            if not isinstance(sessions_a_data, list) or not sessions_a_data:
                raise RuntimeError("list sessions returned empty payload for active user")
            if not any(s.get("is_current_device") for s in sessions_a_data):
                raise RuntimeError("current device session flag not found in sessions list")

            prescription_b_id, plan_b_id = _seed_prescription_and_plan_for_user(user_b_id)

            # Unauthenticated list must be blocked.
            unauth_list = client.get(f"{API_BASE_URL}/prescriptions/")
            _expect_status(unauth_list, 401, "unauthenticated prescriptions list")

            # Cross-user prescription access must be blocked.
            rx_other = client.get(
                f"{API_BASE_URL}/prescriptions/{prescription_b_id}",
                headers=_auth_header_with_device(access_a, device_a),
            )
            _expect_status(rx_other, 404, "cross-user prescription detail")

            # Owner can access own prescription.
            rx_owner = client.get(
                f"{API_BASE_URL}/prescriptions/{prescription_b_id}",
                headers=_auth_header_with_device(access_b, device_b),
            )
            _expect_status(rx_owner, 200, "owner prescription detail")

            # Cross-user plan access must be blocked.
            plan_other = client.get(
                f"{API_BASE_URL}/plans/{plan_b_id}",
                headers=_auth_header_with_device(access_a, device_a),
            )
            _expect_status(plan_other, 404, "cross-user plan detail")

            # Owner can access own plan.
            plan_owner = client.get(
                f"{API_BASE_URL}/plans/{plan_b_id}",
                headers=_auth_header_with_device(access_b, device_b),
            )
            _expect_status(plan_owner, 200, "owner plan detail")

            refresh_wrong_device = client.post(
                f"{API_BASE_URL}/auth/refresh",
                headers=_device_header(device_b),
                json={"refresh_token": refresh_a},
            )
            _expect_status(refresh_wrong_device, 401, "refresh from wrong device")

            # Refresh rotation must succeed and invalidate old refresh token.
            refreshed = client.post(
                f"{API_BASE_URL}/auth/refresh",
                headers=_device_header(device_a),
                json={"refresh_token": refresh_a},
            )
            _expect_status(refreshed, 200, "refresh")
            refreshed_payload = refreshed.json()
            access_a_rotated = refreshed_payload.get("access_token")
            refresh_a_rotated = refreshed_payload.get("refresh_token")
            if not access_a_rotated or not refresh_a_rotated:
                raise RuntimeError("refresh response missing tokens")

            refresh_reuse = client.post(
                f"{API_BASE_URL}/auth/refresh",
                headers=_device_header(device_a),
                json={"refresh_token": refresh_a},
            )
            _expect_status(refresh_reuse, 401, "refresh token reuse")

            me_after_rotation = client.get(
                f"{API_BASE_URL}/auth/me",
                headers=_auth_header_with_device(access_a_rotated, device_a),
            )
            _expect_status(me_after_rotation, 200, "access after refresh rotation")

            # Logout should revoke token immediately (Redis-backed blacklist).
            logout_resp = client.post(
                f"{API_BASE_URL}/auth/logout",
                headers=_auth_header_with_device(access_a_rotated, device_a),
                json={"refresh_token": refresh_a_rotated},
            )
            _expect_status(logout_resp, 200, "logout")

            me_after_logout = client.get(
                f"{API_BASE_URL}/auth/me",
                headers=_auth_header_with_device(access_a_rotated, device_a),
            )
            _expect_status(me_after_logout, 401, "revoked token use after logout")

            refresh_after_logout = client.post(
                f"{API_BASE_URL}/auth/refresh",
                headers=_device_header(device_a),
                json={"refresh_token": refresh_a_rotated},
            )
            _expect_status(refresh_after_logout, 401, "refresh after logout")

            logout_all_resp = client.post(
                f"{API_BASE_URL}/auth/logout-all",
                headers=_auth_header_with_device(access_b, device_b),
            )
            _expect_status(logout_all_resp, 200, "logout all")
            logout_all_payload = logout_all_resp.json()
            if int(logout_all_payload.get("revoked_sessions", 0)) < 1:
                raise RuntimeError("logout-all did not revoke any sessions")

            me_b_after_logout_all = client.get(
                f"{API_BASE_URL}/auth/me",
                headers=_auth_header_with_device(access_b, device_b),
            )
            _expect_status(me_b_after_logout_all, 401, "revoked access after logout-all")

            refresh_b_after_logout_all = client.post(
                f"{API_BASE_URL}/auth/refresh",
                headers=_device_header(device_b),
                json={"refresh_token": refresh_b},
            )
            _expect_status(refresh_b_after_logout_all, 401, "refresh after logout-all")

        print("PASS: live auth/authz smoke checks completed successfully.")
        return 0

    except Exception as exc:
        print(f"FAIL: {exc}")
        return 1

    finally:
        try:
            _cleanup_users(created_user_ids)
        except Exception as cleanup_exc:
            print(f"WARN: cleanup failed: {cleanup_exc}", file=sys.stderr)


if __name__ == "__main__":
    raise SystemExit(main())
