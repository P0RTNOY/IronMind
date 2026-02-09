from google.cloud import firestore
from app.config import settings

_db = None

def get_db() -> firestore.Client:
    """
    Get a singleton Firestore client.
    """
    global _db
    if _db is None:
        project_id = settings.FIREBASE_PROJECT_ID or settings.PROJECT_ID
        _db = firestore.Client(project=project_id)
    return _db
