from backend.database import get_db, SessionModel
import json

db = next(get_db())
session_id = "debug-session-4"
session = db.query(SessionModel).filter(SessionModel.id == session_id).first()

if session:
    print(f"[OK] Session found: {session_id}")
    if session.analysis_state:
        print("[OK] Analysis State exists!")
        print(json.dumps(session.analysis_state, indent=2, ensure_ascii=False))
    else:
        print("[WARN] Analysis State is NULL/Empty")
else:
    print(f"[ERROR] Session {session_id} not found")
