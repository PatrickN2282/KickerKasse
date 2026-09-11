"""Atomic HTTP booking boundary, including durable replay of its serialized result."""
import hashlib
import json
import re
from uuid import UUID
from fastapi import HTTPException
from fastapi.routing import APIRoute
from starlette.responses import Response
from starlette.concurrency import run_in_threadpool
from app.core.database import get_db, SessionLocal
from app.core.financial_booking import lock_financial_period


PATTERN = re.compile(r"^/api/(transactions/(sale|cash/(deposit|withdrawal)|zbon/create|voucher/.*)|members/[0-9]+/recharge|deckel(?:/[0-9]+/(book|pay))?|admin/vouchers(?:/.*)?)$")


class BookingRoute(APIRoute):
    def get_route_handler(self):
        original = super().get_route_handler()

        async def handle(request):
            path = request.url.path.rstrip("/")
            if request.method != "POST" or not PATTERN.fullmatch(path):
                return await original(request)
            from app.core.auth import require_authenticated_user
            from app.models import BookingOperation
            # Respect dependency overrides used by isolated HTTP integration tests.
            override = request.app.dependency_overrides.get(get_db)
            supplied = override() if override else None
            async_generator = supplied if hasattr(supplied, "__anext__") else None
            generator = supplied if hasattr(supplied, "__next__") else None
            db = (await anext(async_generator) if async_generator else next(generator) if generator
                  else supplied if supplied is not None else SessionLocal())
            commit = db.commit
            request.state.booking_db = db
            callbacks = []
            request.state.after_booking_commit = callbacks
            try:
                user = require_authenticated_user(request, db)
                key = request.headers.get("Idempotency-Key")
                fingerprint = None
                if key:
                    try:
                        key = str(UUID(key))
                    except ValueError:
                        raise HTTPException(400, "Ungültige Vorgangskennung.")
                    body = await request.json()
                    if not isinstance(body, dict):
                        raise HTTPException(422, "Ein Buchungsobjekt ist erforderlich.")
                    # Password confirmation is checked on the original request, never persisted.
                    body = {k: v for k, v in body.items() if k != "auth_password"}
                    fingerprint = hashlib.sha256(json.dumps([path, body], sort_keys=True,
                        separators=(",", ":"), ensure_ascii=False).encode()).hexdigest()
                await run_in_threadpool(lock_financial_period, db)
                if key:
                    existing = db.query(BookingOperation).filter_by(operation_key=key).first()
                    if existing:
                        if existing.user_id != user.id or existing.fingerprint != fingerprint:
                            raise HTTPException(409, "Die Vorgangskennung gehört zu einer anderen Buchung.")
                        return Response(existing.response_json, status_code=existing.response_status,
                            media_type="application/json", headers={"Idempotency-Replayed": "true"})
                # Existing services may flush several times. Only this boundary commits.
                db.commit = db.flush
                response = await original(request)
                if response.status_code >= 400:
                    db.rollback()
                    return response
                if key:
                    db.add(BookingOperation(operation_key=key, user_id=user.id,
                        fingerprint=fingerprint, response_json=response.body.decode(),
                        response_status=response.status_code))
                commit()
                for callback in callbacks:
                    try:
                        callback()
                    except Exception:
                        import logging
                        logging.getLogger(__name__).exception("Post-booking notification failed")
                return response
            except Exception:
                db.rollback()
                raise
            finally:
                db.commit = commit
                del request.state.booking_db
                if async_generator:
                    await async_generator.aclose()
                elif generator:
                    generator.close()
                elif not override:
                    db.close()
        return handle
