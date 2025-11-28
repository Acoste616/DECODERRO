"""
ULTRA V3.1 - END-TO-END CONVERSATION TEST
==========================================
QA Engineer: Full Functional Test

Simulates a realistic 3-turn sales conversation with a "Skeptical Analyst" persona.
Tests:
1. Fast Path: RAG-powered responses
2. Slow Path: Real-time psychometric profiling and journey stage detection
3. Database: Session and analysis persistence

Scenario: Customer interested in Tesla Model 3, concerned about winter range,
         TCO vs diesel, and business financing options.
"""

import asyncio
import websockets
import httpx
import json
import sqlite3
import sys
from datetime import datetime
from typing import Dict, List, Any

# Configuration
BACKEND_URL = "http://localhost:8000"
WS_URL = "ws://localhost:8000"
DATABASE_PATH = "ultra.db"

# ANSI Colors for beautiful output
class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

# Conversation Scenario
CONVERSATION_TURNS = [
    {
        "turn": 1,
        "label": "OTWARCIE (Opening)",
        "message": "Cześć. Zastanawiam się nad Teslą Model 3, ale słyszałem, że zimą zasięg spada o połowę. Czy to prawda?",
        "expectations": {
            "fast_path": ["zasięg", "zima", "pompa ciepła", "procent", "%"],
            "slow_path": ["DISC", "personality", "journey_stage", "DISCOVERY"],
            "keywords": ["winter", "range", "concern"]
        }
    },
    {
        "turn": 2,
        "label": "POGŁĘBIENIE/OBIEKCJA (Objection)",
        "message": "Rozumiem, ale robię 500 km tygodniowo. Jak to wygląda kosztowo w porównaniu do mojego Diesla? Paliwo kosztuje mnie krocie.",
        "expectations": {
            "fast_path": ["TCO", "koszt", "diesel", "oszczędności", "ładowanie"],
            "slow_path": ["CONSIDERATION", "analytical", "cost", "data"],
            "keywords": ["cost", "comparison", "analytical"]
        }
    },
    {
        "turn": 3,
        "label": "DOMKNIĘCIE (Closing)",
        "message": "Brzmi logicznie. Jakie są opcje finansowania dla firmy?",
        "expectations": {
            "fast_path": ["leasing", "finansowanie", "firma", "dotacje"],
            "slow_path": ["PURCHASE_INTENT", "High", "Ready"],
            "keywords": ["financing", "business", "ready to buy"]
        }
    }
]

class E2ETester:
    def __init__(self):
        self.session_id = None
        self.conversation_log = []
        self.fast_path_responses = []
        self.slow_path_updates = []
        self.rag_evidence = []
        self.psychometry_evidence = []
        
    def log(self, message: str, color: str = Colors.OKBLUE):
        """Print colored log message"""
        timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        print(f"{color}[{timestamp}] {message}{Colors.ENDC}")
        
    def print_section(self, title: str):
        """Print section header"""
        print(f"\n{Colors.BOLD}{Colors.HEADER}{'='*80}{Colors.ENDC}")
        print(f"{Colors.BOLD}{Colors.HEADER}{title.center(80)}{Colors.ENDC}")
        print(f"{Colors.BOLD}{Colors.HEADER}{'='*80}{Colors.ENDC}\n")
        
    async def create_session(self) -> str:
        """Create a new session via REST API"""
        self.log("📝 Creating new session...", Colors.OKCYAN)
        async with httpx.AsyncClient() as client:
            try:
                resp = await client.post(f"{BACKEND_URL}/api/sessions")
                if resp.status_code != 200:
                    raise Exception(f"Failed to create session: {resp.status_code} {resp.text}")
                session_data = resp.json()
                self.session_id = session_data["id"]
                self.log(f"✅ Session created: {self.session_id}", Colors.OKGREEN)
                return self.session_id
            except Exception as e:
                self.log(f"❌ Error creating session: {e}", Colors.FAIL)
                raise
                
    async def send_message_and_wait(self, websocket, message: str, turn_info: Dict) -> Dict:
        """Send message and collect both Fast Path and Slow Path responses"""
        turn_num = turn_info["turn"]
        label = turn_info["label"]
        
        self.log(f"\n🎯 TURA {turn_num}: {label}", Colors.BOLD)
        self.log(f"👤 KLIENT: {message}", Colors.WARNING)
        
        # Send message
        await websocket.send(message)
        self.conversation_log.append({
            "role": "user",
            "content": message,
            "turn": turn_num
        })
        
        # Wait for responses
        fast_response = None
        slow_updates = []
        timeout = 30  # 30 seconds timeout
        start_time = asyncio.get_event_loop().time()
        
        while True:
            try:
                # Check timeout
                if asyncio.get_event_loop().time() - start_time > timeout:
                    self.log(f"⚠️ Timeout waiting for responses (30s)", Colors.WARNING)
                    break
                    
                # Receive with timeout
                response_text = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                response = json.loads(response_text)
                
                # Handle different event types
                event_type = response.get("type", "unknown")
                
                if event_type == "message":
                    # Fast Path Response
                    fast_response = response
                    ai_text = response.get("content", "")
                    self.log(f"🤖 AI (Fast Path): {ai_text[:150]}...", Colors.OKGREEN)
                    self.conversation_log.append({
                        "role": "ai",
                        "content": ai_text,
                        "turn": turn_num,
                        "path": "fast"
                    })
                    self.fast_path_responses.append(response)
                    
                    # Check for RAG evidence
                    self.check_rag_evidence(ai_text, turn_info)
                    
                elif event_type == "analysis_update":
                    # Slow Path Update
                    self.log(f"🧠 Slow Path Update Received!", Colors.OKCYAN)
                    slow_updates.append(response)
                    self.slow_path_updates.append(response)
                    
                    # Extract and display key analysis data
                    analysis_data = response.get("data", {})
                    self.display_analysis_summary(analysis_data, turn_num)
                    self.check_psychometry_evidence(analysis_data, turn_info)
                    
                elif event_type == "status":
                    status = response.get("message", "")
                    self.log(f"ℹ️ Status: {status}", Colors.OKBLUE)
                    
                elif event_type == "error":
                    error_msg = response.get("message", "Unknown error")
                    self.log(f"❌ Error: {error_msg}", Colors.FAIL)
                    
                # If we have both fast and slow, we can move on
                # But let's wait a bit more for potential additional slow updates
                if fast_response and slow_updates:
                    # Wait 2 more seconds for any additional updates
                    await asyncio.sleep(2)
                    # Check if there are more messages
                    try:
                        additional = await asyncio.wait_for(websocket.recv(), timeout=1.0)
                        response = json.loads(additional)
                        if response.get("type") == "analysis_update":
                            slow_updates.append(response)
                            self.slow_path_updates.append(response)
                    except asyncio.TimeoutError:
                        pass  # No more messages
                    break
                    
            except asyncio.TimeoutError:
                if fast_response:
                    # We got fast response but no slow update yet
                    self.log(f"⏳ Waiting for Slow Path analysis...", Colors.WARNING)
                    continue
                else:
                    self.log(f"⚠️ No response received", Colors.WARNING)
                    break
            except Exception as e:
                self.log(f"❌ Error receiving message: {e}", Colors.FAIL)
                break
                
        return {
            "fast": fast_response,
            "slow": slow_updates
        }
        
    def check_rag_evidence(self, ai_text: str, turn_info: Dict):
        """Check if AI response contains expected RAG keywords"""
        expected_keywords = turn_info["expectations"]["fast_path"]
        ai_text_lower = ai_text.lower()
        
        found_keywords = [kw for kw in expected_keywords if kw.lower() in ai_text_lower]
        
        if found_keywords:
            self.log(f"✅ RAG Evidence Found: {', '.join(found_keywords)}", Colors.OKGREEN)
            self.rag_evidence.append({
                "turn": turn_info["turn"],
                "keywords": found_keywords,
                "text": ai_text
            })
        else:
            self.log(f"⚠️ Expected keywords NOT found: {', '.join(expected_keywords)}", Colors.WARNING)
            
    def display_analysis_summary(self, analysis_data: Dict, turn: int):
        """Display key analysis information"""
        # DISC Profile
        disc = analysis_data.get("disc_profile", {})
        if disc:
            primary = disc.get("primary_type", "Unknown")
            score = disc.get("confidence_score", 0)
            self.log(f"  📊 DISC: {primary} (confidence: {score:.2f})", Colors.OKCYAN)
            
        # Journey Stage
        journey = analysis_data.get("journey_stage", {})
        if journey:
            current = journey.get("current", "Unknown")
            confidence = journey.get("confidence", 0)
            self.log(f"  🎯 Journey Stage: {current} (confidence: {confidence:.2f})", Colors.OKCYAN)
            
        # Purchase Intent
        intent = analysis_data.get("purchase_intent", {})
        if intent:
            level = intent.get("level", "Unknown")
            readiness = intent.get("readiness_score", 0)
            self.log(f"  💰 Purchase Intent: {level} (readiness: {readiness:.2f})", Colors.OKCYAN)
            
    def check_psychometry_evidence(self, analysis_data: Dict, turn_info: Dict):
        """Check if Slow Path analysis contains expected indicators"""
        expected_keywords = turn_info["expectations"]["slow_path"]
        
        # Convert analysis to string for searching
        analysis_str = json.dumps(analysis_data).lower()
        
        found_keywords = [kw for kw in expected_keywords if kw.lower() in analysis_str]
        
        if found_keywords:
            self.log(f"✅ Psychometry Evidence: {', '.join(found_keywords)}", Colors.OKGREEN)
            self.psychometry_evidence.append({
                "turn": turn_info["turn"],
                "keywords": found_keywords,
                "data": analysis_data
            })
        else:
            self.log(f"⚠️ Expected psychometry markers NOT found: {', '.join(expected_keywords)}", Colors.WARNING)
            
    async def verify_database(self):
        """Verify session was saved to database"""
        self.log("\n🔍 Verifying database persistence...", Colors.OKCYAN)
        
        try:
            conn = sqlite3.connect(DATABASE_PATH)
            cursor = conn.cursor()
            
            # Check if session exists
            cursor.execute("SELECT * FROM sessions WHERE id = ?", (self.session_id,))
            session = cursor.fetchone()
            
            if session:
                self.log(f"✅ Session found in database: {self.session_id}", Colors.OKGREEN)
                self.log(f"  Journey Stage: {session[3]}", Colors.OKBLUE)
                self.log(f"  Status: {session[2]}", Colors.OKBLUE)
            else:
                self.log(f"❌ Session NOT found in database!", Colors.FAIL)
                return False
                
            # Check messages
            cursor.execute("SELECT COUNT(*) FROM messages WHERE session_id = ?", (self.session_id,))
            msg_count = cursor.fetchone()[0]
            self.log(f"✅ Messages in DB: {msg_count}", Colors.OKGREEN)
            
            # Check analysis state
            cursor.execute("SELECT * FROM analysis_states WHERE session_id = ?", (self.session_id,))
            analysis_row = cursor.fetchone()
            
            if analysis_row:
                self.log(f"✅ Analysis state found in database", Colors.OKGREEN)
                analysis_json = analysis_row[1]  # data column
                if analysis_json:
                    analysis_data = json.loads(analysis_json)
                    self.log(f"  Analysis contains: {', '.join(analysis_data.keys())}", Colors.OKBLUE)
                    return True
                else:
                    self.log(f"⚠️ Analysis state exists but is EMPTY", Colors.WARNING)
                    return False
            else:
                self.log(f"❌ Analysis state NOT found in database!", Colors.FAIL)
                return False
                
            conn.close()
            
        except Exception as e:
            self.log(f"❌ Database verification failed: {e}", Colors.FAIL)
            return False
            
    def generate_report(self):
        """Generate final test report"""
        self.print_section("RAPORT KOŃCOWY E2E TEST")
        
        # 1. Conversation Log
        print(f"{Colors.BOLD}1. ZAPIS ROZMOWY (User vs AI){Colors.ENDC}")
        print("─" * 80)
        for entry in self.conversation_log:
            role = "👤 KLIENT" if entry["role"] == "user" else "🤖 AI"
            turn = entry.get("turn", "?")
            content = entry["content"][:200] + "..." if len(entry["content"]) > 200 else entry["content"]
            print(f"\n{Colors.WARNING}Tura {turn} | {role}:{Colors.ENDC}")
            print(f"{content}\n")
        
        # 2. RAG Evidence
        print(f"\n{Colors.BOLD}2. DOWÓD DZIAŁANIA RAG{Colors.ENDC}")
        print("─" * 80)
        if self.rag_evidence:
            for evidence in self.rag_evidence:
                print(f"{Colors.OKGREEN}✅ Tura {evidence['turn']}: Znalezione słowa kluczowe: {', '.join(evidence['keywords'])}{Colors.ENDC}")
            print(f"\n{Colors.OKGREEN}WERDYKT: RAG działa poprawnie ✓{Colors.ENDC}")
        else:
            print(f"{Colors.FAIL}❌ WERDYKT: Brak dowodów działania RAG{Colors.ENDC}")
            
        # 3. Slow Path Evidence
        print(f"\n{Colors.BOLD}3. DOWÓD DZIAŁANIA SLOW PATH (Psychometria){Colors.ENDC}")
        print("─" * 80)
        if self.psychometry_evidence:
            for evidence in self.psychometry_evidence:
                print(f"{Colors.OKGREEN}✅ Tura {evidence['turn']}: Wykryte markery: {', '.join(evidence['keywords'])}{Colors.ENDC}")
                # Print sample data
                if evidence['data'].get('disc_profile'):
                    disc = evidence['data']['disc_profile']
                    print(f"   DISC Profile: {disc.get('primary_type', 'N/A')} (score: {disc.get('confidence_score', 0):.2f})")
                if evidence['data'].get('journey_stage'):
                    journey = evidence['data']['journey_stage']
                    print(f"   Journey Stage: {journey.get('current', 'N/A')} (confidence: {journey.get('confidence', 0):.2f})")
            print(f"\n{Colors.OKGREEN}WERDYKT: Slow Path działa poprawnie ✓{Colors.ENDC}")
        else:
            print(f"{Colors.FAIL}❌ WERDYKT: Brak dowodów działania Slow Path{Colors.ENDC}")
            
        # 4. Final Summary
        print(f"\n{Colors.BOLD}4. PODSUMOWANIE KOŃCOWE{Colors.ENDC}")
        print("─" * 80)
        
        rag_ok = len(self.rag_evidence) > 0
        slow_ok = len(self.psychometry_evidence) > 0
        
        print(f"Fast Path (RAG): {'✅ DZIAŁA' if rag_ok else '❌ NIE DZIAŁA'}")
        print(f"Slow Path (Psychometria): {'✅ DZIAŁA' if slow_ok else '❌ NIE DZIAŁA'}")
        print(f"Liczba wymian: {len([e for e in self.conversation_log if e['role'] == 'user'])}")
        print(f"Session ID: {self.session_id}")
        
        if rag_ok and slow_ok:
            print(f"\n{Colors.OKGREEN}{Colors.BOLD}🎉 SYSTEM ULTRA v3.1 DZIAŁA POPRAWNIE! 🎉{Colors.ENDC}")
        else:
            print(f"\n{Colors.FAIL}{Colors.BOLD}⚠️ SYSTEM WYMAGA NAPRAWY ⚠️{Colors.ENDC}")
            
    async def run_full_test(self):
        """Run complete E2E test"""
        try:
            self.print_section("ULTRA V3.1 - END-TO-END FUNCTIONAL TEST")
            
            # Step 1: Create session
            await self.create_session()
            
            # Step 2: Connect to WebSocket
            uri = f"{WS_URL}/ws/chat/{self.session_id}"
            self.log(f"🔌 Connecting to WebSocket: {uri}", Colors.OKCYAN)
            
            async with websockets.connect(uri) as websocket:
                self.log(f"✅ WebSocket connected!", Colors.OKGREEN)
                
                # Step 3: Run conversation turns
                for turn_info in CONVERSATION_TURNS:
                    message = turn_info["message"]
                    responses = await self.send_message_and_wait(websocket, message, turn_info)
                    
                    # Brief pause between turns
                    await asyncio.sleep(2)
                    
            self.log(f"🔌 WebSocket disconnected", Colors.OKBLUE)
            
            # Step 4: Verify database
            await asyncio.sleep(2)  # Give DB time to commit
            db_ok = await self.verify_database()
            
            # Step 5: Generate report
            self.generate_report()
            
            # Database verification in report
            print(f"\n{Colors.BOLD}5. DOWÓD BAZY DANYCH{Colors.ENDC}")
            print("─" * 80)
            if db_ok:
                print(f"{Colors.OKGREEN}✅ Sesja zapisana w bazie danych{Colors.ENDC}")
                print(f"{Colors.OKGREEN}✅ Analysis state nie jest pusty{Colors.ENDC}")
                print(f"{Colors.OKGREEN}WERDYKT: Persistence działa poprawnie ✓{Colors.ENDC}")
            else:
                print(f"{Colors.FAIL}❌ WERDYKT: Problem z zapisem do bazy{Colors.ENDC}")
            
        except Exception as e:
            # Check if it's a connection error
            error_type = type(e).__name__
            if "Connection" in error_type or "Connect" in str(e).lower():
                self.log(f"❌ Backend connection failed: {e}", Colors.FAIL)
                self.log(f"Czy backend działa na {BACKEND_URL}?", Colors.WARNING)
            else:
                self.log(f"❌ Test failed: {e}", Colors.FAIL)
                import traceback
                traceback.print_exc()


async def main():
    """Main entry point"""
    tester = E2ETester()
    await tester.run_full_test()

if __name__ == "__main__":
    print(f"""
{Colors.HEADER}{Colors.BOLD}
╔═══════════════════════════════════════════════════════════════════════════════╗
║                                                                               ║
║                    ULTRA V3.1 - END-TO-END FUNCTIONAL TEST                    ║
║                         Lead QA Engineer - Final Check                        ║
║                                                                               ║
╚═══════════════════════════════════════════════════════════════════════════════╝
{Colors.ENDC}

Testowany scenariusz: "Sceptyczny Analityk"
- 3 tury rozmowy o Tesla Model 3
- Weryfikacja Fast Path (RAG)
- Weryfikacja Slow Path (Psychometria)
- Weryfikacja persistencji (SQLite)

Rozpoczynam test...
""")
    
    asyncio.run(main())
