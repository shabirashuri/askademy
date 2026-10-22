from fastapi import APIRouter

from app.api.v1.endpoints import auth, courses, enrollments, health, materials, users

api_router = APIRouter()
api_router.include_router(health.router, tags=["health"])
api_router.include_router(auth.router, tags=["auth"])
api_router.include_router(users.router)
api_router.include_router(courses.router)
api_router.include_router(enrollments.router)
api_router.include_router(materials.router)
