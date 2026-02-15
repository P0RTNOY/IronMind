from datetime import datetime, timedelta, timezone
from typing import List, Dict, Any
from app.repos.firestore import get_db

def get_growth_data(days: int = 30) -> List[Dict[str, Any]]:
    """
    Aggregates daily signups and active users for the last N days.
    Returns a list of dicts: { "date": "YYYY-MM-DD", "signups": int, "active": int }
    """
    db = get_db()
    users_ref = db.collection("users")
    
    # We'll fetch all users (for MVP scale) and aggregate in-memory.
    # For scale, this should be a scheduled job writing to a stats collection.
    
    # Fetch fields needed: createdAt, lastSeenAt
    # stream() gets full docs, but we can't select fields easily in python client without projecting,
    # and projections are sometimes tricky in emulators/older libs. Full doc is fine for MVP size.
    
    docs = users_ref.stream()
    
    # Initialize buckets
    end_date = datetime.now(timezone.utc).date()
    start_date = end_date - timedelta(days=days-1)
    
    data_map = {}
    current = start_date
    while current <= end_date:
        fmt = current.isoformat()
        data_map[fmt] = {"date": fmt, "signups": 0, "active": 0}
        current += timedelta(days=1)
        
    for doc in docs:
        d = doc.to_dict()
        
        # 1. Signups (based on createdAt)
        created_at = d.get("createdAt")
        if created_at:
             # Handle Firestore datetime vs string
            if hasattr(created_at, 'date'):
                c_date = created_at.astimezone(timezone.utc).date().isoformat()
            else:
                # Fallback if stored as string? or just skip
                try:
                    c_date = datetime.fromisoformat(str(created_at)).date().isoformat()
                except:
                    c_date = None
            
            if c_date and c_date in data_map:
                data_map[c_date]["signups"] += 1
                
        # 2. Daily Active Users (DAU)? 
        # Actually "Active Users" usually means unique users active ON that day.
        # But we only store `lastSeenAt`. We don't have a daily activity log.
        # So `lastSeenAt` only gives us the LAST day they were active.
        # We can't reconstruct historical DAU from just `lastSeenAt`.
        # Alternative interpretation: "Active users" = Cumulative count of users who have been active within last X days?
        # OR: Just chart "New Signups" vs "Users Last Seen This Day".
        # Let's do "lastSeenAt" distribution for now, as that's what we have.
        # It shows "Recency" distribution.
        
        last_seen = d.get("lastSeenAt")
        if last_seen:
            if hasattr(last_seen, 'date'):
                l_date = last_seen.astimezone(timezone.utc).date().isoformat()
            else:
                try:
                    l_date = datetime.fromisoformat(str(last_seen)).date().isoformat()
                except:
                    l_date = None
            
            if l_date and l_date in data_map:
                data_map[l_date]["active"] += 1

    # Convert to sorted list
    result = sorted(data_map.values(), key=lambda x: x["date"])
    return result
