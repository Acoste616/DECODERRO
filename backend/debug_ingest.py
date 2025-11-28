import sys
import os
import json
import uuid
import traceback

# Setup Log File immediately
LOG_FILE = "ingestion_debug_log.txt"

def log(message):
    print(message)
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(message + "\n")

# Wipe log file
with open(LOG_FILE, "w", encoding="utf-8") as f:
    f.write("--- STARTING DIAGNOSTIC INGESTION ---\n")

try:
    log("1. Checking Environment...")
    import qdrant_client
    from qdrant_client import QdrantClient
    from qdrant_client.http import models
    import sentence_transformers
    from sentence_transformers import SentenceTransformer
    log("   ✅ Imports successful.")
    
    # PATH DETECTION LOGIC
    log("2. Detecting Data Directory...")
    POSSIBLE_DIRS = ["data", "dane", "../data", "../dane"]
    DATA_DIR = None
    for d in POSSIBLE_DIRS:
        if os.path.exists(d) and os.path.isdir(d):
            DATA_DIR = d
            break
    
    if not DATA_DIR:
        raise FileNotFoundError(f"❌ Could not find data directory. Checked: {POSSIBLE_DIRS}")
    log(f"   ✅ Found Data Directory: '{DATA_DIR}'")

    # CHECK FILES
    files = ["rag_nuggets_final.json", "golden_standards_final.json"]
    for fname in files:
        fpath = os.path.join(DATA_DIR, fname)
        if not os.path.exists(fpath):
            raise FileNotFoundError(f"❌ Missing file: {fpath}")
        log(f"   ✅ Found file: {fname}")

    # CONNECTION
    log("3. Connecting to Qdrant...")
    QDRANT_URL = "http://localhost:6333"
    client = QdrantClient(QDRANT_URL)
    collections = client.get_collections()
    log(f"   ✅ Qdrant Connected. Collections: {[c.name for c in collections.collections]}")

    # RECREATION
    COLLECTION_NAME = "ultra_knowledge"
    log(f"4. Recreating Collection '{COLLECTION_NAME}'...")
    client.recreate_collection(
        collection_name=COLLECTION_NAME,
        vectors_config=models.VectorParams(size=384, distance=models.Distance.COSINE)
    )
    log("   ✅ Collection Reset.")

    # MODEL LOADING
    log("5. Loading Embedding Model (this may take time)...")
    model = SentenceTransformer('all-MiniLM-L6-v2')
    log("   ✅ Model Loaded.")

    # INGESTION LOOP
    log("6. Processing Data...")
    
    all_points = []
    
    # Load Nuggets
    path_nuggets = os.path.join(DATA_DIR, "rag_nuggets_final.json")
    with open(path_nuggets, 'r', encoding='utf-8') as f:
        nuggets = json.load(f)
    log(f"   - Loaded {len(nuggets)} nuggets.")

    for item in nuggets:
        # Safe text extraction
        text = f"{item.get('title', '')} {item.get('content', '')} {item.get('keywords', '')}"
        point_id = str(uuid.uuid4()) # UUID FIX
        item['source_type'] = 'nugget'
        item['original_id'] = item.get('id', 'unknown')
        
        # Create Point
        vector = model.encode(text).tolist()
        all_points.append(models.PointStruct(
            id=point_id,
            vector=vector,
            payload=item
        ))

    # Load Standards
    path_standards = os.path.join(DATA_DIR, "golden_standards_final.json")
    with open(path_standards, 'r', encoding='utf-8') as f:
        standards = json.load(f)
    log(f"   - Loaded {len(standards)} standards.")

    for item in standards:
        text = f"{item.get('trigger_context', '')} {item.get('golden_response', '')}"
        point_id = str(uuid.uuid4()) # UUID FIX
        item['source_type'] = 'standard'
        item['original_id'] = item.get('id', 'unknown')
        
        vector = model.encode(text).tolist()
        all_points.append(models.PointStruct(
            id=point_id,
            vector=vector,
            payload=item
        ))

    total = len(all_points)
    log(f"7. Uploading {total} vectors to Qdrant (Batching)...")
    
    BATCH_SIZE = 100
    for i in range(0, total, BATCH_SIZE):
        batch = all_points[i:i+BATCH_SIZE]
        client.upsert(
            collection_name=COLLECTION_NAME,
            points=batch
        )
        if i % 1000 == 0:
            log(f"   - Uploaded {i}/{total}...")

    # FINAL COUNT
    final_count = client.count(collection_name=COLLECTION_NAME).count
    log(f"\n🎉 SUCCESS! Final Vector Count: {final_count}")
    
    if final_count > 11000:
        log("✅ TARGET MET: Full Knowledge Base Ingested.")
    else:
        log("⚠️ WARNING: Count seems low. Check JSON files.")

except Exception as e:
    log("\n❌ FATAL ERROR ❌")
    log(str(e))
    log(traceback.format_exc())
