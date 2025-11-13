#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Tesla Knowledge Base JSON Processor
Consolidates 9 source JSON files into 2 output files with conflict detection
"""

import json
import uuid
import re
from pathlib import Path
from collections import defaultdict
from typing import List, Dict, Any, Tuple

# Configuration
BASE_DIR = Path(r"c:\Users\barto\OneDrive\Pulpit\decoder")
DATA_DIR = BASE_DIR / "datatoupload"

# Input files mapping
GOLDEN_STANDARDS_SOURCES = [
    DATA_DIR / "gol1.json",
    DATA_DIR / "gol2.json",
    DATA_DIR / "gol3.json",
    BASE_DIR / "sample_golden_standards.json"
]

RAG_NUGGETS_SOURCES = [
    DATA_DIR / "nugget1.json",
    DATA_DIR / "nugget2.json",
    DATA_DIR / "nugget3.json",
    BASE_DIR / "sample_rag_nuggets.json",
    DATA_DIR / "nugget4.json",  # Needs adaptation
    DATA_DIR / "gol4.json"       # Needs adaptation
]

# Output files
OUTPUT_GOLDEN = BASE_DIR / "golden_standards_final.json"
OUTPUT_RAG = BASE_DIR / "rag_nuggets_final.json"
OUTPUT_REPORT = BASE_DIR / "conflict_report.md"

# Conflict detection patterns
CONFLICT_PATTERNS = [
    {
        "name": "Model 3 Performance 0-100 km/h",
        "patterns": [r"Model\s*3\s*Performance.*?0-100", r"3\s*Performance.*?przyspiesz", r"0-100.*?3\.\d+\s*s"],
        "value_regex": r"(\d+\.\d+)\s*s(?:ekund)?",
        "field": "content"
    },
    {
        "name": "Wartość rezydualna Model 3",
        "patterns": [r"wartość\s*rezydualna.*?Model\s*3", r"Model\s*3.*?rezydualna", r"RV.*?Model\s*3"],
        "value_regex": r"(\d+(?:-\d+)?)\s*%",
        "field": "content"
    },
    {
        "name": "Model 3 RWD zasięg WLTP",
        "patterns": [r"Model\s*3\s*RWD.*?zasięg", r"Model\s*3.*?(?:430|490|513)\s*km", r"zasięg.*?Model\s*3\s*RWD"],
        "value_regex": r"(\d+(?:-\d+)?)\s*km",
        "field": "content"
    },
    {
        "name": "Model 3 Long Range zasięg",
        "patterns": [r"Model\s*3\s*Long\s*Range.*?zasięg", r"Model\s*3\s*LR.*?(\d+)\s*km"],
        "value_regex": r"(\d+)\s*km",
        "field": "content"
    },
    {
        "name": "Dotacje NaszEauto",
        "patterns": [r"NaszEauto.*?dotac", r"Mój\s*Elektryk.*?dotac", r"dotac.*?(\d+k?\s*zł)"],
        "value_regex": r"(\d+(?:\.\d+)?k?)\s*zł",
        "field": "content"
    },
    {
        "name": "Model Y zasięg zimą",
        "patterns": [r"Model\s*Y.*?zim.*?zasięg", r"zasięg.*?zimą.*?Model\s*Y"],
        "value_regex": r"(\d+)\s*km",
        "field": "content"
    },
    {
        "name": "Wall Connector cena",
        "patterns": [r"Wall\s*Connector.*?cena", r"Wall\s*Connector.*?\d+\s*zł"],
        "value_regex": r"(\d+)\s*zł",
        "field": "content"
    },
    {
        "name": "Model 3 Performance przyspieszenie (alternative)",
        "patterns": [r"przyspieszenie.*?3\.\d+\s*sekund", r"Model.*?Performance.*?3\.\d+"],
        "value_regex": r"3\.(\d+)\s*s",
        "field": "content"
    }
]


def generate_uuid() -> str:
    """Generate UUID v4"""
    return str(uuid.uuid4())


def extract_title_from_content(content: str, max_words: int = 10, max_chars: int = 70) -> str:
    """Extract title from content (first N words or chars)"""
    # Remove extra whitespace
    cleaned = re.sub(r'\s+', ' ', content.strip())
    
    # Try word-based extraction first
    words = cleaned.split()
    if len(words) <= max_words:
        title = cleaned[:max_chars]
    else:
        title = ' '.join(words[:max_words])
    
    # Truncate to max_chars
    if len(title) > max_chars:
        title = title[:max_chars].rsplit(' ', 1)[0]  # Cut at last word boundary
    
    return title.strip()


def extract_keywords(content: str, max_keywords: int = 6) -> str:
    """Extract keywords from content using simple heuristics"""
    # Common Polish stop words
    stop_words = {
        'i', 'w', 'z', 'na', 'do', 'dla', 'po', 'od', 'ze', 'o', 'oraz', 'to', 'jest',
        'się', 'że', 'jak', 'przy', 'ma', 'co', 'przez', 'lub', 'gdy', 'bez', 'może'
    }
    
    # Extract potential keywords (capitalized words, numbers with units, Model names)
    words = re.findall(r'\b(?:Model\s+[A-Z0-9]+|[A-ZŁŚĆŹĄĘŃÓ][a-złśćźąęń]+|\d+\s*(?:km|kW|zł|%|s|kg))\b', content)
    
    # Also extract important technical terms
    tech_terms = re.findall(r'\b(?:Tesla|FSD|Autopilot|Supercharger|WLTP|LFP|NCA|OTA|TCO|leasing|zasięg|bateria)\b', content, re.IGNORECASE)
    
    # Combine and deduplicate
    keywords = []
    seen = set()
    for word in words + tech_terms:
        word_lower = word.lower()
        if word_lower not in stop_words and word_lower not in seen and len(word) > 2:
            keywords.append(word)
            seen.add(word_lower)
            if len(keywords) >= max_keywords:
                break
    
    return ', '.join(keywords[:max_keywords]) if keywords else 'Tesla, informacja'


def load_json_file(file_path: Path) -> List[Dict[str, Any]]:
    """Load JSON file and return list of objects"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            if not isinstance(data, list):
                data = [data]
            return data
    except Exception as e:
        print(f"Error loading {file_path}: {e}")
        return []


def adapt_nugget4_gol4(entry: Dict[str, Any], source_file: str) -> Dict[str, Any]:
    """Adapt nugget4.json and gol4.json to Format B"""
    content = entry.get('content', '')
    
    adapted = {
        'id': generate_uuid(),
        'title': extract_title_from_content(content),
        'content': content,
        'keywords': extract_keywords(content),
        'type': entry.get('type', entry.get('category', 'knowledge')),
        'tags': entry.get('tags', []),
        'archetype_filter': entry.get('archetype_filter', [])
    }
    
    # Add metadata for tracking
    adapted['_source_file'] = source_file
    adapted['_original_id'] = entry.get('id', '')
    
    return adapted


def add_uuid_to_entry(entry: Dict[str, Any], source_file: str) -> Dict[str, Any]:
    """Add UUID to existing entry"""
    entry_copy = entry.copy()
    entry_copy['id'] = generate_uuid()
    entry_copy['_source_file'] = source_file
    entry_copy['_original_id'] = entry.get('id', '')
    return entry_copy


def normalize_entry(entry: Dict[str, Any]) -> str:
    """Normalize entry for deduplication (exclude id and metadata)"""
    normalized = {k: v for k, v in entry.items() if not k.startswith('_') and k != 'id'}
    return json.dumps(normalized, sort_keys=True, ensure_ascii=False)


def deduplicate_entries(entries: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Remove exact duplicates, keeping first occurrence"""
    seen = {}
    unique = []
    
    for entry in entries:
        norm = normalize_entry(entry)
        if norm not in seen:
            seen[norm] = entry
            unique.append(entry)
        else:
            print(f"  Duplicate removed: {entry.get('title', entry.get('trigger_context', 'Unknown'))[:50]}...")
    
    print(f"Deduplication: {len(entries)} → {len(unique)} entries ({len(entries) - len(unique)} duplicates removed)")
    return unique


def detect_conflicts(entries: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Detect semantic conflicts based on patterns"""
    conflicts = []
    
    for pattern_config in CONFLICT_PATTERNS:
        pattern_name = pattern_config['name']
        patterns = pattern_config['patterns']
        value_regex = pattern_config['value_regex']
        field = pattern_config['field']
        
        # Find all entries matching this topic
        matching_entries = []
        for entry in entries:
            text = entry.get(field, '') or entry.get('trigger_context', '') or entry.get('golden_response', '')
            text = str(text).lower()
            
            for pattern in patterns:
                if re.search(pattern, text, re.IGNORECASE):
                    # Extract value
                    matches = re.findall(value_regex, text, re.IGNORECASE)
                    if matches:
                        matching_entries.append({
                            'entry': entry,
                            'values': matches,
                            'text': text[:200]
                        })
                    break
        
        # Check for conflicting values
        if len(matching_entries) >= 2:
            # Group by distinct values
            value_groups = defaultdict(list)
            for item in matching_entries:
                for value in item['values']:
                    value_groups[value].append(item['entry'])
            
            # If we have different values, it's a conflict
            if len(value_groups) > 1:
                conflicts.append({
                    'topic': pattern_name,
                    'value_groups': dict(value_groups),
                    'all_entries': [item['entry'] for item in matching_entries]
                })
    
    return conflicts


def generate_conflict_report(conflicts: List[Dict[str, Any]]) -> str:
    """Generate Markdown conflict report"""
    if not conflicts:
        return "# Raport Konfliktów\n\n✅ **Nie wykryto konfliktów merytorycznych.**\n"
    
    report_lines = [
        "# Raport Konfliktów Merytorycznych",
        "",
        f"**Data wygenerowania:** {Path(__file__).stat().st_mtime}",
        f"**Liczba wykrytych konfliktów:** {len(conflicts)}",
        "",
        "---",
        ""
    ]
    
    for i, conflict in enumerate(conflicts, 1):
        topic = conflict['topic']
        value_groups = conflict['value_groups']
        
        report_lines.extend([
            f"## Konflikt #{i}: {topic}",
            "",
            f"**Wykryto {len(value_groups)} różnych wartości dla tego samego faktu:**",
            ""
        ])
        
        for value, entries in value_groups.items():
            report_lines.extend([
                f"### Wartość: `{value}`",
                f"**Liczba wpisów:** {len(entries)}",
                ""
            ])
            
            for entry in entries:
                entry_id = entry.get('id', 'unknown')
                source_file = entry.get('_source_file', 'unknown')
                original_id = entry.get('_original_id', '')
                
                # Get relevant content excerpt
                content = (entry.get('content') or 
                          entry.get('golden_response') or 
                          entry.get('trigger_context', ''))[:300]
                
                title = entry.get('title', entry.get('trigger_context', 'Brak tytułu'))[:80]
                
                report_lines.extend([
                    f"- **ID:** `{entry_id}`",
                    f"  - **Plik źródłowy:** `{source_file}`",
                    f"  - **Oryginalne ID:** `{original_id}`" if original_id else "",
                    f"  - **Tytuł/Kontekst:** {title}",
                    f"  - **Fragment treści:**",
                    f"    ```",
                    f"    {content}",
                    f"    ```",
                    ""
                ])
        
        report_lines.extend(["---", ""])
    
    report_lines.extend([
        "",
        "## Instrukcje",
        "",
        "1. Przejrzyj każdy konflikt i zdecyduj, która wartość jest poprawna",
        "2. Ręcznie zedytuj pliki `golden_standards_final.json` i `rag_nuggets_final.json`",
        "3. Usuń lub zaktualizuj sprzeczne wpisy używając ID jako klucza",
        "4. Po rozwiązaniu konfliktów, pliki będą gotowe do importu do Qdrant",
        "",
        "**UWAGA:** NIE importuj plików do Qdrant przed rozwiązaniem wszystkich konfliktów!",
        ""
    ])
    
    return '\n'.join(report_lines)


def process_golden_standards() -> Tuple[List[Dict[str, Any]], int]:
    """Process golden standards files"""
    print("\n=== Processing Golden Standards (Format A) ===")
    all_entries = []
    
    for file_path in GOLDEN_STANDARDS_SOURCES:
        if not file_path.exists():
            print(f"⚠️  File not found: {file_path}")
            continue
        
        print(f"Loading: {file_path.name}")
        entries = load_json_file(file_path)
        
        # Add UUID to each entry
        for entry in entries:
            entry_with_uuid = add_uuid_to_entry(entry, file_path.name)
            all_entries.append(entry_with_uuid)
        
        print(f"  Loaded {len(entries)} entries")
    
    # Deduplicate
    print("\nDeduplicating golden standards...")
    unique_entries = deduplicate_entries(all_entries)
    
    return unique_entries, len(all_entries)


def process_rag_nuggets() -> Tuple[List[Dict[str, Any]], int]:
    """Process RAG nuggets files"""
    print("\n=== Processing RAG Nuggets (Format B) ===")
    all_entries = []
    
    for file_path in RAG_NUGGETS_SOURCES:
        if not file_path.exists():
            print(f"⚠️  File not found: {file_path}")
            continue
        
        print(f"Loading: {file_path.name}")
        entries = load_json_file(file_path)
        
        # Check if adaptation needed
        needs_adaptation = file_path.name in ['nugget4.json', 'gol4.json']
        
        for entry in entries:
            if needs_adaptation:
                adapted = adapt_nugget4_gol4(entry, file_path.name)
                all_entries.append(adapted)
            else:
                entry_with_uuid = add_uuid_to_entry(entry, file_path.name)
                all_entries.append(entry_with_uuid)
        
        print(f"  Loaded {len(entries)} entries {'(adapted)' if needs_adaptation else ''}")
    
    # Deduplicate
    print("\nDeduplicating RAG nuggets...")
    unique_entries = deduplicate_entries(all_entries)
    
    return unique_entries, len(all_entries)


def clean_metadata(entry: Dict[str, Any]) -> Dict[str, Any]:
    """Remove metadata fields before final output"""
    return {k: v for k, v in entry.items() if not k.startswith('_')}


def main():
    """Main processing function"""
    print("=" * 80)
    print("Tesla Knowledge Base Consolidation Script")
    print("=" * 80)
    
    # Process both collections
    golden_entries, golden_total = process_golden_standards()
    rag_entries, rag_total = process_rag_nuggets()
    
    # Detect conflicts in both collections
    print("\n=== Detecting Conflicts ===")
    print("Analyzing golden standards...")
    golden_conflicts = detect_conflicts(golden_entries)
    print(f"  Found {len(golden_conflicts)} conflict groups in golden standards")
    
    print("Analyzing RAG nuggets...")
    rag_conflicts = detect_conflicts(rag_entries)
    print(f"  Found {len(rag_conflicts)} conflict groups in RAG nuggets")
    
    all_conflicts = golden_conflicts + rag_conflicts
    
    # Generate conflict report
    print("\n=== Generating Conflict Report ===")
    report = generate_conflict_report(all_conflicts)
    
    with open(OUTPUT_REPORT, 'w', encoding='utf-8') as f:
        f.write(report)
    print(f"✅ Conflict report saved: {OUTPUT_REPORT}")
    print(f"   Total conflicts: {len(all_conflicts)}")
    
    # Clean metadata and save final files
    print("\n=== Saving Final JSON Files ===")
    
    golden_clean = [clean_metadata(e) for e in golden_entries]
    with open(OUTPUT_GOLDEN, 'w', encoding='utf-8') as f:
        json.dump(golden_clean, f, ensure_ascii=False, indent=2)
    print(f"✅ Golden standards saved: {OUTPUT_GOLDEN}")
    print(f"   Entries: {len(golden_clean)} (from {golden_total} original)")
    
    rag_clean = [clean_metadata(e) for e in rag_entries]
    with open(OUTPUT_RAG, 'w', encoding='utf-8') as f:
        json.dump(rag_clean, f, ensure_ascii=False, indent=2)
    print(f"✅ RAG nuggets saved: {OUTPUT_RAG}")
    print(f"   Entries: {len(rag_clean)} (from {rag_total} original)")
    
    # Summary
    print("\n" + "=" * 80)
    print("PROCESSING COMPLETE")
    print("=" * 80)
    print(f"""
Summary:
  Golden Standards: {len(golden_clean)} entries (removed {golden_total - len(golden_clean)} duplicates)
  RAG Nuggets:      {len(rag_clean)} entries (removed {rag_total - len(rag_clean)} duplicates)
  Conflicts Found:  {len(all_conflicts)} topic groups
  
Output Files:
  ✓ {OUTPUT_GOLDEN.name}
  ✓ {OUTPUT_RAG.name}
  ✓ {OUTPUT_REPORT.name}

⚠️  CRITICAL NEXT STEPS:
  1. Review {OUTPUT_REPORT.name} for all conflicts
  2. Manually resolve conflicts by editing the JSON files
  3. DO NOT import to Qdrant until conflicts are resolved!
    """)


if __name__ == "__main__":
    main()
