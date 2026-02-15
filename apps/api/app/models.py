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
    # For future CDN flexibility
    coverImagePath: Optional[str] = None
    tags: List[str] = []
    
    # Pricing
    stripePriceIdOneTime: Optional[str] = None
    stripePriceIdSubscription: Optional[str] = None
    currency: str = "usd" # Default to USD as per plan, though config says ILS. Sticking to plan default.

class CourseAdmin(BaseModel):
    id: str
    titleHe: str
    descriptionHe: str
    type: Literal["one_time", "subscription"]
    published: bool
    coverImageUrl: Optional[str] = None
    coverImagePath: Optional[str] = None
    tags: List[str] = []
    
    stripePriceIdOneTime: Optional[str] = None
    stripePriceIdSubscription: Optional[str] = None
    currency: str = "usd"
    
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

class Entitlement(BaseModel):
    id: str
    uid: str
    kind: Literal["course", "membership"]
    status: Literal["active", "inactive"]
    source: str
    courseId: Optional[str] = None
    stripeSubscriptionId: Optional[str] = None
    expiresAt: Optional[datetime] = None
    createdAt: Optional[datetime] = None
    updatedAt: Optional[datetime] = None

class AdminUserRow(BaseModel):
    uid: str
    email: Optional[str] = None
    name: Optional[str] = None
    lastSeenAt: Optional[datetime] = None
    membershipActive: bool
    membershipExpiresAt: Optional[datetime] = None
    entitledCourseIds: List[str]

class AdminUsersListResponse(BaseModel):
    users: List[AdminUserRow]
    nextCursor: Optional[str] = None

class AdminUserDetailResponse(BaseModel):
    profile: AdminUserRow
    entitlements: List[Entitlement]
    purchases: List[dict] = [] # Placeholder until purchases repo is ready


class AccessCheckResponse(BaseModel):
    allowed: bool

# --- Access Models ---

class AccessMeResponse(BaseModel):
    uid: str
    email: Optional[str] = None
    isAdmin: bool
    membershipActive: bool
    membershipExpiresAt: Optional[datetime] = None
    entitledCourseIds: List[str] = []

# --- User Management ---

class User(BaseModel):
    uid: str
    email: Optional[str] = None
    name: Optional[str] = None
    lastSeenAt: Optional[datetime] = None
    createdAt: Optional[datetime] = None

# --- Uploads ---

class UploadSignRequest(BaseModel):
    kind: Literal["cover", "plan_pdf"]
    filename: str
    contentType: str

class UploadSignResponse(BaseModel):
    uploadUrl: str
    publicUrl: str
    objectPath: str
