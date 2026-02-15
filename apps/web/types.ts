
export interface UserContext {
  uid: string;
  email?: string | null;
  name?: string | null;
  is_admin: boolean;
}

export interface AccessMeResponse {
  uid: string;
  email?: string | null;
  isAdmin: boolean;
  membershipActive: boolean;
  membershipExpiresAt?: string | null;
  entitledCourseIds: string[];
}

export interface CoursePublic {
  id: string;
  titleHe: string;
  descriptionHe: string;
  type: 'one_time' | 'subscription';
  published: boolean;
  coverImageUrl?: string | null;
  createdAt?: string | null;
  updatedAt?: string | null;
}


export interface CourseAdmin extends CoursePublic {
  tags: string[];
  coverImagePath?: string | null;
  stripePriceIdOneTime?: string | null;
  stripePriceIdSubscription?: string | null;
  currency?: string;
}

export interface LessonPublic {
  id: string;
  courseId: string;
  titleHe: string;
  descriptionHe: string;
  movementCategory: string;
  tags: string[];
  vimeoVideoId?: string | null;
  orderIndex: number;
  published: boolean;
}

export interface PlanPublic {
  id: string;
  courseId?: string | null;
  titleHe: string;
  descriptionHe: string;
  tags: string[];
  pdfPath?: string | null;
  published: boolean;
}

export interface SearchResult {
  courses: CoursePublic[];
  lessons: LessonPublic[];
  plans: PlanPublic[];
}

export interface MetricsOverview {
  courses_total: number;
  courses_published: number;
  lessons_total: number;
  lessons_published: number;
  plans_total: number;
  plans_published: number;
  purchases_total: number;
  subscriptions_total: number;
  entitlements_total: number;
}

export interface AccessCheckResponse {
  allowed: boolean;
}

export interface LessonAdmin extends LessonPublic {
  createdAt?: string | null;
  updatedAt?: string | null;
}

export interface PlanAdmin extends PlanPublic {
  createdAt?: string | null;
  updatedAt?: string | null;
}


export interface Entitlement {
  id: string;
  uid: string;
  kind: 'course' | 'membership';
  status: 'active' | 'inactive';
  source: string;
  courseId?: string;
  stripeSubscriptionId?: string;
  createdAt: string;
  updatedAt?: string;
  expiresAt?: string;
}

export interface AdminUserRow {
  uid: string;
  email?: string;
  name?: string;
  lastSeenAt?: string;
  membershipActive: boolean;
  membershipExpiresAt?: string;
  entitledCourseIds: string[];
}

export interface AdminUsersListResponse {
  users: AdminUserRow[];
  nextCursor?: string;
}

export interface AdminUserDetailResponse {
  profile: AdminUserRow;
  entitlements: Entitlement[];
  purchases: any[];
}

export interface APIResponse<T> {
  data: T | null;
  error: any;
  status: number;
}
