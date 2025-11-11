import json
import os
import sys
from typing import Dict, Any, List

import psycopg2
from psycopg2.extras import execute_batch
from qdrant_client import QdrantClient, models
from sentence_transformers import SentenceTransformer

# --- Konfiguracja ---
# Zmienne środowiskowe (zgodnie z PEGT Moduł 5 i 7)
DB_USER = os.environ.get("POSTGRES_USER", "user")
DB_PASS = os.environ.get("POSTGRES_PASSWORD", "password")
DB_HOST = os.environ.get("POSTGRES_HOST", "localhost")
DB_PORT = os.environ.get("POSTGRES_PORT", 5432)
DB_NAME = os.environ.get("POSTGRES_DB", "ultra_db")

QDRANT_HOST = os.environ.get("QDRANT_HOST", "localhost")
QDRANT_PORT = os.environ.get("QDRANT_PORT", 6333)

# Konfiguracja modelu (zgodnie z PEGT Moduł 2 i 11)
EMBEDDING_MODEL_NAME = "paraphrase-multilingual-MiniLM-L12-v2"
# Wymiar wektora dla tego modelu to 384
VECTOR_DIMENSION = 384 
QDRANT_COLLECTION_NAME = "ultra_rag_v1"

# Ścieżki do plików danych (zgodnie z listą plików)
RAG_DATA_FILE = "DATA_01_RAG.md" # Plik .md zawiera JSON
GOLDEN_STANDARDS_FILE = "DATA_02_Golden_Standards.md" # Plik .md zawiera JSON

def load_json_from_md(file_path: str) -> List[Dict[str, Any]]:
    """Wczytuje listę obiektów JSON z pliku .md"""
    print(f"Wczytywanie pliku: {file_path}...")
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            # Stripowanie nagłówków Markdown (T2)
            lines = content.split('\n')
            json_lines = [line for line in lines if not line.strip().startswith('#')]
            json_content = '\n'.join(json_lines).strip()
            data = json.loads(json_content)
            if not isinstance(data, list):
                raise ValueError("Plik nie zawiera listy JSON.")
            print(f"Wczytano {len(data)} obiektów.")
            return data
    except Exception as e:
        print(f"KRYTYCZNY BŁĄD: Nie można wczytać lub sparsować pliku {file_path}. Błąd: {e}")
        sys.exit(1)

def seed_postgresql(standards_data: List[Dict[str, Any]]):
    """Ładuje Złote Standardy do bazy PostgreSQL."""
    print("\n--- Rozpoczynanie seedowania PostgreSQL ---")
    conn = None
    try:
        conn_string = f"postgresql://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
        conn = psycopg2.connect(conn_string)
        print("Połączono z PostgreSQL.")
        
        with conn.cursor() as cur:
            # Tworzenie tabeli (zgodnie z PEGT Moduł 10)
            # Używamy "CREATE TABLE IF NOT EXISTS" dla idempotencji
            # Tworzenie WSZYSTKICH tabel (Rekomendacja K6)
            cur.execute("""
CREATE TABLE IF NOT EXISTS sessions (
    session_id TEXT PRIMARY KEY,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
    ended_at TIMESTAMP WITH TIME ZONE NULL,
    status TEXT NULL CHECK (status IN ('Sprzedaż','Utrata'))
);

CREATE TABLE IF NOT EXISTS conversation_log (
    log_id SERIAL PRIMARY KEY,
    session_id TEXT NOT NULL REFERENCES sessions(session_id),
    timestamp TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
    role TEXT NOT NULL CHECK (role IN ('Sprzedawca','FastPath','FastPath-Questions')),
    content TEXT NOT NULL,
    language TEXT NOT NULL CHECK (language IN ('pl','en'))
);
CREATE INDEX idx_conversation_log_session ON conversation_log(session_id);

CREATE TABLE IF NOT EXISTS slow_path_logs (
    log_id SERIAL PRIMARY KEY,
    session_id TEXT NOT NULL REFERENCES sessions(session_id),
    timestamp TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
    json_output JSONB NOT NULL,
    status TEXT NOT NULL CHECK (status IN ('Success','Error'))
);
CREATE INDEX idx_slow_path_logs_session ON slow_path_logs(session_id);

CREATE TABLE IF NOT EXISTS feedback_logs (
    feedback_id SERIAL PRIMARY KEY,
    session_id TEXT NOT NULL REFERENCES sessions(session_id),
    log_id_ref INT NULL,
    feedback_type TEXT NOT NULL CHECK (feedback_type IN ('up','down')),
    original_input TEXT NOT NULL,
    bad_suggestion TEXT NOT NULL,
    feedback_note TEXT NOT NULL,
    language TEXT NOT NULL CHECK (language IN ('pl','en')),
    journey_stage TEXT NULL CHECK (journey_stage IN ('Odkrywanie','Analiza','Decyzja')),
    refined_suggestion TEXT NULL,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now()
);
CREATE INDEX idx_feedback_logs_session ON feedback_logs(session_id);
CREATE INDEX idx_feedback_logs_language ON feedback_logs(language);
CREATE INDEX idx_feedback_logs_created ON feedback_logs(created_at DESC);

-- (golden_standards już jest w seed.py)
""")
            print("Wszystkie tabele sprawdzone/stworzone.")
            
            # (K5) Dodanie przykładowej sesji testowej
            cur.execute("""
                INSERT INTO sessions (session_id, created_at, status)
                VALUES ('S-TEST-001', now(), NULL)
                ON CONFLICT (session_id) DO NOTHING;
            """)
            conn.commit()
            print("Dodano przykładową sesję testową: S-TEST-001")
            
            cur.execute("""
            CREATE TABLE IF NOT EXISTS golden_standards (
                gs_id SERIAL PRIMARY KEY,
                category TEXT NOT NULL,
                trigger_context TEXT NOT NULL,
                golden_response TEXT NOT NULL,
                language TEXT NOT NULL DEFAULT 'pl' CHECK (language IN ('pl','en')),
                created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
                updated_at TIMESTAMP NULL,
                UNIQUE(trigger_context, language)
            );
            """)
            # Indeksy dla golden_standards (L1)
            cur.execute("""
            CREATE INDEX IF NOT EXISTS idx_golden_standards_language ON golden_standards(language);
            CREATE INDEX IF NOT EXISTS idx_golden_standards_category ON golden_standards(category);
            CREATE INDEX IF NOT EXISTS idx_golden_standards_created ON golden_standards(created_at DESC);
            """)
            print("Tabela 'golden_standards' sprawdzona/stworzona.")
            
            # Przygotowanie danych do załadowania
            # Używamy ON CONFLICT... DO NOTHING, aby uniknąć błędów duplikatów
            insert_query = """
            INSERT INTO golden_standards (category, trigger_context, golden_response, language)
            VALUES (%s, %s, %s, %s)
            ON CONFLICT (trigger_context, language) DO NOTHING;
            """
            
            # (T5) Normalizacja trigger_context przed wstawieniem
            for item in standards_data:
                if 'trigger_context' in item:
                    item['trigger_context'] = ' '.join(item['trigger_context'].split())
            
            # Mapowanie danych z JSON (zgodnie z DATA_02 i PEGT Moduł 10)
            data_to_insert = [
                (
                    item.get('category', 'Inne'), # Pobierz kategorię (wymagane)
                    item['trigger_context'],
                    item['golden_response'],
                    item.get('language', 'pl') # Pobierz język (wymagane)
                ) for item in standards_data
            ]
            
            print(f"Ładowanie {len(data_to_insert)} Złotych Standardów do PostgreSQL...")
            execute_batch(cur, insert_query, data_to_insert)
            conn.commit()
            print(f"Zakończono. Dodano {cur.rowcount} nowych standardów (ignorowano duplikaty).")
            
    except psycopg2.DatabaseError as e:
        print(f"BŁĄD POSTGRESQL: {e}")
        if conn:
            conn.rollback()
    except Exception as e:
        print(f"Nieoczekiwany błąd seedowania PostgreSQL: {e}")
    finally:
        if conn:
            conn.close()
            print("Połączenie z PostgreSQL zamknięte.")

def seed_qdrant(rag_data: List[Dict[str, Any]]):
    """Ładuje wiedzę RAG (z embeddingami) do bazy Qdrant."""
    print("\n--- Rozpoczynanie seedowania Qdrant ---")
    try:
        # (T8) Obsługa URL dla QdrantClient (dla Railway)
        if QDRANT_HOST.startswith('http'):
            client = QdrantClient(url=QDRANT_HOST)
        else:
            client = QdrantClient(host=QDRANT_HOST, port=QDRANT_PORT)
        print(f"Połączono z Qdrant ({QDRANT_HOST}:{QDRANT_PORT if not QDRANT_HOST.startswith('http') else ''}).")

        # (K10) Logika idempotentna dla kolekcji (sprawdź, czy istnieje)
        try:
            client.get_collection(collection_name=QDRANT_COLLECTION_NAME)
            print(f"Kolekcja '{QDRANT_COLLECTION_NAME}' już istnieje. Dodawanie nuggetów...")
        except Exception:
            client.create_collection(
                collection_name=QDRANT_COLLECTION_NAME,
                vectors_config=models.VectorParams(
                    size=VECTOR_DIMENSION,
                    distance=models.Distance.COSINE
                )
            )
            print(f"Kolekcja '{QDRANT_COLLECTION_NAME}' utworzona.")

        # (K9) Walidacja struktury nuggetów przed przetwarzaniem
        REQUIRED_FIELDS = ['id', 'type', 'title', 'content', 'tags', 'language']
        for item in rag_data:
            for field in REQUIRED_FIELDS:
                if field not in item:
                    print(f"BŁĄD: Nugget {item.get('id', 'UNKNOWN')} brakuje pola '{field}'")
                    sys.exit(1)
            if 'archetype_filter' in item and isinstance(item['archetype_filter'], str):
                item['archetype_filter'] = [item['archetype_filter']]

        # (T4) Komunikaty przed ładowaniem modelu
        print(f"Pobieranie modelu '{EMBEDDING_MODEL_NAME}' (pierwszy raz może potrwać kilka minut)...")
        print("Upewnij się, że masz połączenie z internetem.")
        
        # Ładowanie modelu Sentence Transformer (zgodnie z PEGT Moduł 2)
        model = SentenceTransformer(EMBEDDING_MODEL_NAME)
        print("Model załadowany.")
        
        # (T3) Pobieranie listy istniejących ID z Qdrant
        print("Pobieranie listy istniejących ID z Qdrant...")
        try:
            existing_points = client.scroll(collection_name=QDRANT_COLLECTION_NAME, with_payload=False, limit=10000)[0]
            existing_ids = {point.id for point in existing_points}
            print(f"Znaleziono {len(existing_ids)} istniejących nuggetów.")
        except Exception as e:
            print(f"Nowa kolekcja, brak istniejących ID. {e}")
            existing_ids = set()
        
        points_to_upsert = []
        
        print(f"Przygotowywanie {len(rag_data)} nuggetów RAG do załadowania...")
        
        # Iterujemy i tworzymy punkty
        for i, item in enumerate(rag_data):
            # (T3) Sprawdzenie, czy nugget już istnieje
            point_id = item['id']
            if point_id in existing_ids:
                continue  # Pomiń ten nugget, już istnieje
            
            # 1. Generowanie embeddingu (zgodnie z PEGT Moduł 2)
            vector = model.encode(item['content']).tolist()
            
            # 2. Przygotowanie metadanych (payload)
            payload = item.copy()
            
            # 3. Używamy 'id' z JSON jako ID punktu w Qdrant
            points_to_upsert.append(
                models.PointStruct(
                    id=point_id,
                    vector=vector,
                    payload=payload
                )
            )
            
            if (i + 1) % 10 == 0 or (i + 1) == len(rag_data):
                print(f"Przetworzono {i + 1}/{len(rag_data)} nuggetów...")

        # Wgranie punktów do Qdrant (w trybie batch)
        print(f"Wysyłanie {len(points_to_upsert)} punktów do Qdrant...")
        client.upsert(
            collection_name=QDRANT_COLLECTION_NAME,
            points=points_to_upsert,
            wait=True # Czekaj na zakończenie operacji
        )
        print("Seedowanie Qdrant zakończone pomyślnie.")
        
    except Exception as e:
        print(f"KRYTYCZNY BŁĄD seedowania Qdrant: {e}")
        print("Upewnij się, że Qdrant jest uruchomiony i dostępny.")

def main():
    print("--- Rozpoczynanie Skryptu Seedującego ULTRA v3.0 ---")
    
    # Krok 1: Wczytaj dane Golden Standards
    standards_data = load_json_from_md(GOLDEN_STANDARDS_FILE)
    
    # Krok 2: Wczytaj dane RAG
    rag_data = load_json_from_md(RAG_DATA_FILE)
    
    # Krok 3: Seeduj PostgreSQL
    seed_postgresql(standards_data)
    
    # Krok 4: Seeduj Qdrant
    seed_qdrant(rag_data)
    
    print("\n--- Seedowanie zakończone ---")

if __name__ == "__main__":
    main()