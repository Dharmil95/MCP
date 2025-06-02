from fastapi import APIRouter
from app.api.documents import router as documents_router
from app.api.chat import router as chat_router

router = APIRouter()

# Include document routes
router.include_router(documents_router, tags=["documents"])

# Include chat routes for the supervisor integration
router.include_router(chat_router, tags=["chat"], prefix="/chat")
