from typing import List, Optional, Literal
from datetime import datetime
from pydantic import BaseModel, Field

# Context Models
class UserContext(BaseModel):
    uid: str
    email: Optional[str] = None
    name: Optional[str] = None
    is_admin: bool = False

# Domain Models
class Entitlement(BaseModel):
    id: str
    uid: str
    kind: Literal["course", "membership"]
    status: Literal["active", "inactive"]
    source: Literal["one_time", "subscription", "manual"]
    courseId: Optional[str] = None
    stripeSubscriptionId: Optional[str] = None
    createdAt: datetime
    expiresAt: Optional[datetime] = None

# Public Domain Models
class CoursePublic(BaseModel):
    id: str
    titleHe: str
    descriptionHe: str
    type: Literal["one_time", "subscription"]
    published: bool
    createdAt: Optional[datetime] = None
    updatedAt: Optional[datetime] = None

class LessonPublic(BaseModel):
    id: str
    courseId: str
    titleHe: str
    descriptionHe: str
    movementCategory: str
    tags: List[str] = []
    vimeoVideoId: Optional[str] = None
    orderIndex: int
    published: bool

class PlanPublic(BaseModel):
    id: str
    courseId: Optional[str] = None
    titleHe: str
    descriptionHe: str
    tags: List[str] = []
    pdfPath: Optional[str] = None
    published: bool

class SearchResult(BaseModel):
    courses: List[CoursePublic] = []
    lessons: List[LessonPublic] = []
    plans: List[PlanPublic] = []

# --- Admin Models ---

class CourseUpsertRequest(BaseModel):
    titleHe: str
    descriptionHe: str
    type: Literal["one_time", "subscription"]
    published: Optional[bool] = None
    coverImageUrl: Optional[str] = None
    tags: List[str] = []

class CourseAdmin(BaseModel):
    id: str
    titleHe: str
    descriptionHe: str
    type: Literal["one_time", "subscription"]
    published: bool
    coverImageUrl: Optional[str] = None
    tags: List[str] = []
    createdAt: Optional[datetime] = None
    updatedAt: Optional[datetime] = None

class LessonUpsertRequest(BaseModel):
    courseId: str
    titleHe: str
    descriptionHe: str
    movementCategory: str
    tags: List[str] = []
    vimeoVideoId: Optional[str] = None
    orderIndex: int = 0
    published: Optional[bool] = None

class LessonAdmin(BaseModel):
    id: str
    courseId: str
    titleHe: str
    descriptionHe: str
    movementCategory: str
    tags: List[str] = []
    vimeoVideoId: Optional[str] = None
    orderIndex: int
    published: bool
    createdAt: Optional[datetime] = None
    updatedAt: Optional[datetime] = None

class PlanUpsertRequest(BaseModel):
    courseId: Optional[str] = None
    titleHe: str
    descriptionHe: str
    tags: List[str] = []
    pdfPath: Optional[str] = None
    published: Optional[bool] = None

class PlanAdmin(BaseModel):
    id: str
    courseId: Optional[str] = None
    titleHe: str
    descriptionHe: str
    tags: List[str] = []
    pdfPath: Optional[str] = None
    published: bool
    createdAt: Optional[datetime] = None
    updatedAt: Optional[datetime] = None

class MetricsOverview(BaseModel):
    courses_total: int
    courses_published: int
    lessons_total: int
    lessons_published: int
    plans_total: int
    plans_published: int
    purchases_total: int
    subscriptions_total: int
    entitlements_total: int

# --- Access Models ---

class AccessMeResponse(BaseModel):
    uid: str
    email: Optional[str] = None
    isAdmin: bool
    membershipActive: bool
    membershipExpiresAt: Optional[datetime] = None
    entitledCourseIds: List[str] = []

class AccessCheckResponse(BaseModel):
    allowed: bool
