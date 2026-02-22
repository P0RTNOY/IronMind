import logging
from typing import List, Optional
from fastapi import APIRouter, HTTPException, Query
from app.models import CoursePublic, SearchResult, LessonPublic, PlanPublic
from app.repos import courses, lessons, plans

logger = logging.getLogger(__name__)
router = APIRouter()

@router.get("/courses", response_model=List[CoursePublic])
async def get_courses():
    """
    List all published courses.
    """
    try:
        return courses.list_published_courses()
    except Exception as e:
        logger.error(f"Failed to list courses: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/courses/{course_id}", response_model=CoursePublic)
async def get_course(course_id: str):
    """
    Get a specific published course by ID.
    """
    try:
        course = courses.get_published_course(course_id)
        if not course:
            raise HTTPException(status_code=404, detail="Course not found")
        return course
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get course {course_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/courses/{course_id}/lessons", response_model=List[LessonPublic])
async def get_course_lessons(course_id: str):
    """
    List all published lessons for a specific course.
    """
    try:
        course = courses.get_published_course(course_id)
        if not course:
            raise HTTPException(status_code=404, detail="Course not found")
        return lessons.list_published_lessons_by_course(course_id)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get lessons for course {course_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/courses/{course_id}/plans", response_model=List[PlanPublic])
async def get_course_plans(course_id: str):
    """
    List all published plans for a specific course.
    """
    try:
        course = courses.get_published_course(course_id)
        if not course:
            raise HTTPException(status_code=404, detail="Course not found")
        return plans.list_published_plans_by_course(course_id)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get plans for course {course_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/lessons/{lesson_id}", response_model=LessonPublic)
async def get_lesson(lesson_id: str):
    """
    Get a specific published lesson by ID.
    """
    try:
        lesson = lessons.get_published_lesson(lesson_id)
        if not lesson:
            raise HTTPException(status_code=404, detail="Lesson not found")
        return lesson
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get lesson {lesson_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/plans/{plan_id}", response_model=PlanPublic)
async def get_plan(plan_id: str):
    """
    Get a specific published plan by ID.
    """
    try:
        plan = plans.get_published_plan(plan_id)
        if not plan:
            raise HTTPException(status_code=404, detail="Plan not found")
        return plan
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get plan {plan_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/search", response_model=SearchResult)
async def search(q: str = Query("", min_length=0)):
    """
    Search across published courses, lessons, and plans.
    """
    if not q or not q.strip():
        return SearchResult(courses=[], lessons=[], plans=[])

    try:
        # Parallelize if performance needed, sequential is fine for v1
        found_courses = courses.search_published_courses(q)
        found_lessons = lessons.search_published_lessons(q)
        found_plans = plans.search_published_plans(q)
        
        return SearchResult(
            courses=found_courses,
            lessons=found_lessons,
            plans=found_plans
        )
    except Exception as e:
        logger.error(f"Search failed for query '{q}': {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")
