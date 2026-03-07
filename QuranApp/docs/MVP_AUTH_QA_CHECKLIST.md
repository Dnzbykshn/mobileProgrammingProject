# MVP Auth QA Checklist

Use this checklist before shipping the current auth/session MVP.

## 1) Backend Readiness

Run from project root:

```bash
docker compose up -d
docker compose exec -T backend sh -lc "cd /app && alembic upgrade head"
docker compose exec -T backend sh -lc "PYTHONPATH=. python tests/live_authz_smoke.py"
```

Expected:
- Smoke script prints `PASS`.
- No 500 errors in backend logs.

## 2) Mobile Manual QA (Real Device or Emulator)

### Login/Register
1. Open app and go to `Profile` tab.
2. Register a new account.
3. Verify profile header shows email/full name.

Expected:
- Login/register succeeds.
- App stays authenticated after app restart.

### Session List UI
1. Open `Profile` tab.
2. Check `Aktif Oturumlar` card.
3. Tap `Yenile`.

Expected:
- At least one session row is visible.
- Current device row has `BU CİHAZ` label.
- No red error message.

### Auto Refresh
1. Keep app open and use chat/profile endpoints for several minutes.
2. Trigger API calls again (refresh list, open plan, chat).

Expected:
- No forced logout during normal use.
- Requests continue after token renewal.

### Logout (Single Device)
1. Tap `Çıkış Yap`.
2. Try to navigate to protected data again.

Expected:
- User is redirected to login/register experience.
- Protected data is not accessible.

### Logout All Devices
1. Login again.
2. Tap `Tüm Cihazlardan Çıkış Yap`.
3. Confirm dialog.

Expected:
- Success alert appears.
- App returns to logged-out state.
- Reopening protected tabs requires login.

## 3) Security Regression API Checks

Run from backend directory:

```bash
../backend/venv/bin/python -m unittest discover -s tests -p "test_*authz.py"
```

Expected:
- All tests pass.

## 4) Release Gate

Only proceed to deploy if all are true:
- Live smoke test passed.
- Manual mobile QA passed.
- `tsc` and `eslint` passed in `mobile-app`.
- No unexpected auth errors in backend logs.
