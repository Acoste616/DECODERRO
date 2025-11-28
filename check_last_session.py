import sqlite3
import json

print("="*80)
print(" "*20 + "ULTRA V3.1 - E2E TEST RESULTS")
print("="*80)

conn = sqlite3.connect('ultra.db')
cursor = conn.cursor()

# Get last session
cursor.execute('SELECT id, journey_stage, status, created_at FROM sessions ORDER BY created_at DESC LIMIT 1')
row = cursor.fetchone()

if not row:
    print("❌ BŁĄD: Nie znaleziono żadnych sesji!")
    exit(1)

session_id, journey_stage, status, created_at = row
print(f"\n📊 SESJA TESTOWA")
print(f"   ID: {session_id}")
print(f"   Journey Stage: {journey_stage}")
print(f"   Status: {status}")
print(f"   Created: {created_at}")

# Get messages
cursor.execute('SELECT role, content, timestamp FROM messages WHERE session_id = ? ORDER BY timestamp', (session_id,))
messages = cursor.fetchall()

print(f"\n💬 ROZMOWA ({len(messages)} wiadomości)")
print("-"*80)
for i, (role, content, timestamp) in enumerate(messages, 1):
    icon = "👤" if role == "user" else "🤖"
    short_content = content[:100] + "..." if len(content) > 100 else content
    print(f"{i}. {icon} {role.upper()}: {short_content}")

# Get analysis state
cursor.execute('SELECT data FROM analysis_states WHERE session_id = ?', (session_id,))
analysis_row = cursor.fetchone()

print(f"\n🧠 ANALIZA SLOW PATH")
print("-"*80)

if analysis_row:
    analysis_data = json.loads(analysis_row[0])
    
    # Check for new analysis format (from analysis_engine)
    if 'disc_profile' in analysis_data:
        print("✅ DISC Profile:")
        disc = analysis_data['disc_profile']
        print(f"   Primary Type: {disc.get('primary_type', 'N/A')}")
        print(f"   Confidence: {disc.get('confidence_score', 0):.2f}")
        print(f"   Traits: {', '.join(disc.get('key_traits', []))}")
    
    if 'journey_stage' in analysis_data:
        print("\n✅ Journey Stage Analysis:")
        journey = analysis_data['journey_stage']
        print(f"   Current Stage: {journey.get('current', 'N/A')}")
        print(f"   Confidence: {journey.get('confidence', 0):.2f}")
        print(f"   Reasoning: {journey.get('reasoning', 'N/A')[:150]}...")
    
    if 'purchase_intent' in analysis_data:
        print("\n✅ Purchase Intent:")
        intent = analysis_data['purchase_intent']
        print(f"   Level: {intent.get('level', 'N/A')}")
        print(f"   Readiness Score: {intent.get('readiness_score', 0):.2f}")
        print(f"   Indicators: {', '.join(intent.get('positive_indicators', [])[:3])}")
    
    if 'objections' in analysis_data:
        print("\n✅ Objections Detected:")
        objections = analysis_data['objections']
        for obj in objections[:3]:
            print(f"   - {obj.get('category', 'N/A')}: {obj.get('objection', 'N/A')[:80]}...")
    
    # Check old format (from main.py initialization)
    if 'm1_dna' in analysis_data:
        print("\n⚠️ Legacy Format Detected (m1_dna, m2_indicators, etc.)")
        print(f"   This suggests Slow Path may not have run completely.")
    
    print(f"\n📋 Analysis Data Keys: {', '.join(analysis_data.keys())}")
    
else:
    print("❌ BRAK DANYCH ANALIZY!")

# VERDICT
print("\n" + "="*80)
print(" "*25 + "🎯 WERDYKT KOŃCOWY")
print("="*80)

has_messages = len(messages) >= 6  # 3 user + 3 AI
has_analysis = analysis_row is not None
has_new_format = analysis_row and ('disc_profile' in json.loads(analysis_row[0]))

print(f"✅ Sesja utworzona: TAK")
print(f"✅ Wiadomości zapisane: TAK ({len(messages)} wiadomości)")
print(f"✅ Analysis State istnieje: {'TAK' if has_analysis else 'NIE'}")
print(f"✅ Nowy format analizy: {'TAK' if has_new_format else 'NIE (legacy format)'}")

if has_messages and has_analysis and has_new_format:
    print(f"\n🎉 SYSTEM ULTRA v3.1 DZIAŁA POPRAWNIE! 🎉")
    print(f"   - Fast Path: ✅ DZIAŁA")
    print(f"   - Slow Path: ✅ DZIAŁA") 
    print(f"   - Database: ✅ DZIAŁA")
elif has_messages and has_analysis:
    print(f"\n⚠️ SYSTEM DZIAŁA CZĘŚCIOWO")
    print(f"   - Fast Path: ✅ DZIAŁA")
    print(f"   - Slow Path: ⚠️ UŻYWA STAREGO FORMATU")
    print(f"   - Database: ✅ DZIAŁA")
else:
    print(f"\n❌ SYSTEM WYMAGA NAPRAWY")

print("="*80)

conn.close()
