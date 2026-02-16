# IronMind Learning Portal

Admin dashboard & learning platform for IronMind.

## 🚀 Quick Start

### Prerequisites
*   Docker & Docker Compose
*   Node.js 18+ (optional, for local frontend dev)

### Running the App
1.  **Start Services**:
    ```bash
    # From the project root
    # Note: Currently focused on API running in Docker and Web in Docker or Local
    
    # Run API & Firestore Emulator
    cd apps/api
    docker-compose up --build
    
    # Run Web (in another terminal)
    cd apps/web
    npm run dev
    ```

    *Alternatively, if a root docker-compose exists (future): `docker-compose up --build`*

2.  **Access Components**:
    *   **Web App**: [http://localhost:3000](http://localhost:3000)
    *   **API**: [http://localhost:8080](http://localhost:8080)
    *   **Firebase Emulator**: `localhost:8080` (Firestore)

## 🏗 Architecture

### Frontend (`apps/web`)
*   **Stack**: React, TypeScript, Vite, TailwindCSS
*   **Key Libs**: `react-router-dom`, `recharts`, `lucide-react`
*   **Features**:
    *   **Admin Dashboard**: `/admin` (Command Center, Courses, Lessons, Plans, Users)
    *   **User Portal**: `/me` (My Courses, Membership)

### Backend (`apps/api`)
*   **Stack**: FastAPI, Python 3.11
*   **Database**: Google Cloud Firestore (Native mode)
*   **Auth**: Firebase Auth (Verify ID Token)
*   **Key Features**:
    *   **RBAC**: Admin vs User roles via `UserContext` dep.
    *   **Audit Logging**: Tracks all admin actions in `admin_audit` collection.
    *   **Analytics**: Aggregates user growth and engagement.

## 🔑 Admin Access
To access the Admin Dashboard:
1.  Sign in with Google on the frontend.
2.  Add your User UID to the `ADMIN_UIDS` environment variable in `apps/api/docker-compose.yml`.
    ```yaml
    ADMIN_UIDS: '["YOUR_UID_HERE"]'
    ```
3.  Restart the API container.

## 📦 Deployment
*   **Frontend**: Build with `npm run build`. Serve headers for SPA fallback.
*   **Backend**: Dockerfile provided. Deploy to Cloud Run or generic Docker host.
