import sys
sys.path.insert(0, 'backend')

try:
    print("Testing ingest script...")
    from pathlib import Path
    
    PROJECT_ROOT = Path("backend/ingest_knowledge.py").parent.parent
    DATA_DIR = PROJECT_ROOT / "dane"
    
    print(f"PROJECT_ROOT: {PROJECT_ROOT}")
    print(f"DATA_DIR: {DATA_DIR}")
    print(f"DATA_DIR exists: {DATA_DIR.exists()}")
    
    if DATA_DIR.exists():
        files = list(DATA_DIR.glob("*.json"))
        print(f"JSON files found: {len(files)}")
        for f in files:
            print(f"  - {f.name}")
    
except Exception as e:
    print(f"ERROR: {e}")
    import traceback
    traceback.print_exc()
