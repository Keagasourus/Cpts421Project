"""Diagnostic script: shows the 3 most recent objects and their images."""
from src.database import SessionLocal
from src.models import Object

db = SessionLocal()
try:
    objs = db.query(Object).order_by(Object.id.desc()).limit(3).all()
    for o in objs:
        print(f"Object {o.id}: {o.object_type}")
        print(f"  Images count: {len(o.images)}")
        for i in o.images:
            print(f"    - img {i.id}: {i.file_url}")
finally:
    db.close()
