import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.models import CoursePublic, LessonPublic, PlanPublic

client = TestClient(app)

MOCK_COURSE = CoursePublic(
    id="course-1",
    titleHe="Test Course",
    descriptionHe="Desc",
    type="one_time",
    published=True
)

MOCK_LESSON_VIDEO = LessonPublic(
    id="lesson-1",
    courseId="course-1",
    titleHe="Video Lesson",
    descriptionHe="Desc",
    movementCategory="CAT",
    vimeoVideoId=None,
    hasVideo=True,
    playbackEndpoint="/content/lessons/lesson-1/playback",
    orderIndex=0,
    published=True
)

MOCK_LESSON_NO_VIDEO = LessonPublic(
    id="lesson-2",
    courseId="course-1",
    titleHe="No Video Lesson",
    descriptionHe="Desc",
    movementCategory="CAT",
    vimeoVideoId=None,
    hasVideo=False,
    playbackEndpoint=None,
    orderIndex=1,
    published=True
)

MOCK_PLAN_PDF = PlanPublic(
    id="plan-1",
    courseId="course-1",
    titleHe="PDF Plan",
    descriptionHe="Desc",
    pdfPath=None,
    hasPdf=True,
    pdfDownloadEndpoint="/content/plans/plan-1/download",
    published=True
)

@pytest.fixture
def mock_repos(monkeypatch):
    monkeypatch.setattr("app.routers.public.courses.get_published_course", lambda cid: MOCK_COURSE if cid == "course-1" else None)
    
    monkeypatch.setattr("app.routers.public.lessons.list_published_lessons_by_course", lambda cid: [MOCK_LESSON_VIDEO, MOCK_LESSON_NO_VIDEO] if cid == "course-1" else [])
    monkeypatch.setattr("app.routers.public.lessons.get_published_lesson", lambda lid: MOCK_LESSON_VIDEO if lid == "lesson-1" else (MOCK_LESSON_NO_VIDEO if lid == "lesson-2" else None))
    
    monkeypatch.setattr("app.routers.public.plans.list_published_plans_by_course", lambda cid: [MOCK_PLAN_PDF] if cid == "course-1" else [])
    monkeypatch.setattr("app.routers.public.plans.get_published_plan", lambda pid: MOCK_PLAN_PDF if pid == "plan-1" else None)

def test_get_course_lessons(mock_repos):
    res = client.get("/courses/course-1/lessons")
    assert res.status_code == 200
    data = res.json()
    assert len(data) == 2
    assert data[0]["vimeoVideoId"] is None
    assert data[0]["hasVideo"] is True
    assert data[0]["playbackEndpoint"] == "/content/lessons/lesson-1/playback"
    assert data[1]["vimeoVideoId"] is None
    assert data[1]["hasVideo"] is False
    assert data[1]["playbackEndpoint"] is None

def test_get_course_lessons_not_found(mock_repos):
    res = client.get("/courses/invalid/lessons")
    assert res.status_code == 404

def test_get_course_plans(mock_repos):
    res = client.get("/courses/course-1/plans")
    assert res.status_code == 200
    data = res.json()
    assert len(data) == 1
    assert data[0]["pdfPath"] is None
    assert data[0]["hasPdf"] is True
    assert data[0]["pdfDownloadEndpoint"] == "/content/plans/plan-1/download"

def test_get_course_plans_not_found(mock_repos):
    res = client.get("/courses/invalid/plans")
    assert res.status_code == 404

def test_get_lesson(mock_repos):
    res = client.get("/lessons/lesson-1")
    assert res.status_code == 200
    data = res.json()
    assert data["vimeoVideoId"] is None
    assert data["hasVideo"] is True
    assert data["playbackEndpoint"] == "/content/lessons/lesson-1/playback"

def test_get_lesson_not_found(mock_repos):
    res = client.get("/lessons/invalid")
    assert res.status_code == 404

def test_get_plan(mock_repos):
    res = client.get("/plans/plan-1")
    assert res.status_code == 200
    data = res.json()
    assert data["pdfPath"] is None
    assert data["hasPdf"] is True
    assert data["pdfDownloadEndpoint"] == "/content/plans/plan-1/download"

def test_get_plan_not_found(mock_repos):
    res = client.get("/plans/invalid")
    assert res.status_code == 404
