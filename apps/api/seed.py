from app.repos import courses, subscriptions
from google.cloud import firestore

def seed():
    # Insert mock user and courses
    db = courses.db
    db.collection("users").document("mock-operative-01").set({
        "email": "mock-operative-01@example.com",
        "created_at": firestore.SERVER_TIMESTAMP
    })

    db.collection("courses").document("alpha-protocol").set({
        "titleHe": "פרוטוקול אלפא",
        "descriptionHe": "קורס מקיף ללימוד יסודות התנועה המורכבת.",
        "type": "one_time",
        "published": True,
        "coverImageUrl": "https://images.unsplash.com/photo-1534438327276-14e5300c3a48?auto=format&fit=crop&q=80&w=800"
    })

    db.collection("courses").document("iron-mind-v1").set({
        "titleHe": "חוסן מנטלי: שלב 1",
        "descriptionHe": "אימון התודעה לעבודה תחת לחץ.",
        "type": "subscription",
        "published": True,
        "coverImageUrl": "https://images.unsplash.com/photo-1506126613408-eca07ce68773?auto=format&fit=crop&q=80&w=800"
    })

if __name__ == "__main__":
    seed()
    print("Seeded successfully")
