from fastapi import APIRouter

from app.api.v1 import leads, auth, playbooks, analytics, webhooks

api_router = APIRouter()
api_router.include_router(auth.router)
api_router.include_router(leads.router)
api_router.include_router(playbooks.router)
api_router.include_router(analytics.router)
api_router.include_router(webhooks.router)
