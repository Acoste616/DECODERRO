#!/usr/bin/env python3
"""
ULTRA v3.0 Backend Reality Check
=================================
Skrypt weryfikacyjny do audytu faktycznego stanu systemu.

Sprawdza:
1. Czy backend odpowiada (GET /)
2. Czy endpoint /api/chat działa (POST)
3. Czas odpowiedzi Fast Path (<3s wymóg)
4. Czy RAG zwraca konkretne dane (nie ogólniki)
5. Czy odpowiedź zawiera polskie słowa kluczowe

Autor: Senior Backend Architect & QA Lead
Data: 2025-11-20
"""

import requests
import time
import json
import sys
from typing import Dict, Any, List

# Konfiguracja
BACKEND_URL = "http://localhost:8000"
TIMEOUT = 15  # seconds

# Kolory dla outputu
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'

def print_section(title: str):
    """Wypisuje sekcję raportu."""
    print(f"\n{Colors.BLUE}{Colors.BOLD}{'='*60}{Colors.ENDC}")
    print(f"{Colors.BLUE}{Colors.BOLD}{title}{Colors.ENDC}")
    print(f"{Colors.BLUE}{Colors.BOLD}{'='*60}{Colors.ENDC}")

def print_test(name: str, passed: bool, details: str = ""):
    """Wypisuje wynik testu."""
    status = f"{Colors.GREEN}✓ PASS{Colors.ENDC}" if passed else f"{Colors.RED}✗ FAIL{Colors.ENDC}"
    print(f"{status} | {name}")
    if details:
        print(f"      {details}")

def test_backend_health() -> bool:
    """Test 1: Czy backend odpowiada?"""
    print_section("TEST 1: Backend Health Check")

    try:
        start = time.time()
        response = requests.get(f"{BACKEND_URL}/", timeout=TIMEOUT)
        elapsed = time.time() - start

        if response.status_code == 200:
            data = response.json()
            print_test(
                "Backend Health",
                True,
                f"Status: {data.get('status', 'Unknown')} | Response time: {elapsed:.2f}s"
            )
            return True
        else:
            print_test(
                "Backend Health",
                False,
                f"HTTP {response.status_code}: {response.text}"
            )
            return False
    except requests.exceptions.ConnectionError:
        print_test(
            "Backend Health",
            False,
            f"Cannot connect to {BACKEND_URL} - Backend nie działa!"
        )
        return False
    except Exception as e:
        print_test("Backend Health", False, f"Error: {str(e)}")
        return False

def test_fast_path_winter_range() -> Dict[str, Any]:
    """Test 2: Fast Path - Winter Range Query"""
    print_section("TEST 2: Fast Path - Winter Range Query")

    test_query = "Klient boi się zimy - mówi że Tesla traci 40% zasięgu"
    session_id = "TEST-AUDIT-001"

    payload = {
        "session_id": session_id,
        "user_input": test_query,
        "journey_stage": "DISCOVERY",
        "language": "PL",
        "history": []
    }

    try:
        print(f"\n{Colors.YELLOW}Wysyłam zapytanie: '{test_query}'{Colors.ENDC}")
        start = time.time()
        response = requests.post(
            f"{BACKEND_URL}/api/chat",
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=TIMEOUT
        )
        elapsed = time.time() - start

        if response.status_code != 200:
            print_test(
                "API Response Status",
                False,
                f"HTTP {response.status_code}: {response.text}"
            )
            return {"success": False, "elapsed": elapsed}

        data = response.json()

        # Test 2.1: Response time
        time_ok = elapsed < 3.0
        print_test(
            "Response Time < 3s",
            time_ok,
            f"Czas: {elapsed:.2f}s {'(OK)' if time_ok else '(TOO SLOW!)'}"
        )

        # Test 2.2: Response content
        response_text = data.get("response", "")
        print(f"\n{Colors.BOLD}Odpowiedź AI:{Colors.ENDC}")
        print(f"{Colors.YELLOW}{response_text[:300]}...{Colors.ENDC}" if len(response_text) > 300 else f"{Colors.YELLOW}{response_text}{Colors.ENDC}")

        # Test 2.3: Czy zawiera konkretne dane (nie ogólniki)
        # Szukamy kluczowych słów związanych z zimowym zasięgiem
        keywords = {
            "pompa ciepła": False,
            "20": False,  # 20-30% spadek
            "30": False,
            "NAF": False,  # Test NAF
            "Warszawa": False,  # Przykład trasy
            "Kraków": False,
            "300": False,  # 300km trasa
            "zasięg": False
        }

        response_lower = response_text.lower()
        for keyword in keywords:
            if keyword.lower() in response_lower:
                keywords[keyword] = True

        matches = sum(keywords.values())
        has_specific_data = matches >= 2  # Musi mieć przynajmniej 2 kluczowe słowa

        print_test(
            "Zawiera konkretne dane (nie ogólniki)",
            has_specific_data,
            f"Znalezione słowa kluczowe: {matches}/8 ({', '.join([k for k, v in keywords.items() if v])})"
        )

        # Test 2.4: Confidence score
        confidence = data.get("confidence", 0.0)
        confidence_ok = confidence > 0.5
        print_test(
            "Confidence Score > 0.5",
            confidence_ok,
            f"Confidence: {confidence:.2f}"
        )

        # Test 2.5: Questions & Actions exist
        questions = data.get("questions", [])
        actions = data.get("suggested_actions", [])
        has_guidance = len(questions) > 0 or len(actions) > 0
        print_test(
            "Zawiera pytania lub akcje",
            has_guidance,
            f"Questions: {len(questions)}, Actions: {len(actions)}"
        )

        return {
            "success": True,
            "elapsed": elapsed,
            "time_ok": time_ok,
            "has_data": has_specific_data,
            "confidence": confidence,
            "confidence_ok": confidence_ok,
            "has_guidance": has_guidance,
            "response": response_text
        }

    except requests.exceptions.Timeout:
        print_test(
            "API Response",
            False,
            f"Timeout po {TIMEOUT}s - Fast Path powinien odpowiedzieć w <3s!"
        )
        return {"success": False, "elapsed": TIMEOUT}
    except Exception as e:
        print_test(
            "API Response",
            False,
            f"Error: {str(e)}"
        )
        return {"success": False, "error": str(e)}

def test_fast_path_tco() -> Dict[str, Any]:
    """Test 3: Fast Path - TCO Query"""
    print_section("TEST 3: Fast Path - TCO Comparison Query")

    test_query = "Klient porównuje Model 3 Long Range z Audi A4 Diesel - pyta o koszty"
    session_id = "TEST-AUDIT-002"

    payload = {
        "session_id": session_id,
        "user_input": test_query,
        "journey_stage": "OBJECTION_HANDLING",
        "language": "PL",
        "history": []
    }

    try:
        print(f"\n{Colors.YELLOW}Wysyłam zapytanie: '{test_query}'{Colors.ENDC}")
        start = time.time()
        response = requests.post(
            f"{BACKEND_URL}/api/chat",
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=TIMEOUT
        )
        elapsed = time.time() - start

        if response.status_code != 200:
            print_test(
                "API Response Status",
                False,
                f"HTTP {response.status_code}"
            )
            return {"success": False}

        data = response.json()
        response_text = data.get("response", "")

        print(f"\n{Colors.BOLD}Odpowiedź AI:{Colors.ENDC}")
        print(f"{Colors.YELLOW}{response_text[:300]}...{Colors.ENDC}" if len(response_text) > 300 else f"{Colors.YELLOW}{response_text}{Colors.ENDC}")

        # Szukamy słów kluczowych TCO
        keywords = {
            "229": False,  # Cena Model 3
            "280": False,  # Cena Audi A4
            "oszczędność": False,
            "TCO": False,
            "paliwo": False,
            "prąd": False,
            "serwis": False
        }

        response_lower = response_text.lower()
        for keyword in keywords:
            if str(keyword).lower() in response_lower:
                keywords[keyword] = True

        matches = sum(keywords.values())
        has_specific_data = matches >= 2

        print_test(
            "Response Time < 3s",
            elapsed < 3.0,
            f"Czas: {elapsed:.2f}s"
        )

        print_test(
            "Zawiera dane TCO",
            has_specific_data,
            f"Znalezione słowa kluczowe: {matches}/7"
        )

        return {
            "success": True,
            "elapsed": elapsed,
            "has_data": has_specific_data
        }

    except Exception as e:
        print_test("TCO Query", False, f"Error: {str(e)}")
        return {"success": False}

def generate_report(results: Dict[str, Any]):
    """Generuje końcowy raport audytu."""
    print_section("RAPORT KOŃCOWY AUDYTU")

    # Podsumowanie
    backend_ok = results.get("backend_health", False)
    test2 = results.get("test2", {})
    test3 = results.get("test3", {})

    total_tests = 8
    passed_tests = 0

    if backend_ok:
        passed_tests += 1
    if test2.get("success"):
        passed_tests += 1
    if test2.get("time_ok"):
        passed_tests += 1
    if test2.get("has_data"):
        passed_tests += 1
    if test2.get("confidence_ok"):
        passed_tests += 1
    if test2.get("has_guidance"):
        passed_tests += 1
    if test3.get("success"):
        passed_tests += 1
    if test3.get("has_data"):
        passed_tests += 1

    success_rate = (passed_tests / total_tests) * 100

    print(f"\n{Colors.BOLD}Wynik: {passed_tests}/{total_tests} testów zaliczonych ({success_rate:.1f}%){Colors.ENDC}")

    if success_rate >= 80:
        print(f"{Colors.GREEN}✓ System działa prawidłowo!{Colors.ENDC}")
        verdict = "PASS"
    elif success_rate >= 60:
        print(f"{Colors.YELLOW}⚠ System działa, ale wymaga poprawek{Colors.ENDC}")
        verdict = "PARTIAL"
    else:
        print(f"{Colors.RED}✗ System ma poważne problemy!{Colors.ENDC}")
        verdict = "FAIL"

    # Szczegółowe zalecenia
    print(f"\n{Colors.BOLD}ZALECENIA:{Colors.ENDC}")

    if not backend_ok:
        print(f"{Colors.RED}1. Backend nie odpowiada - uruchom serwer: uvicorn backend.main:app --reload{Colors.ENDC}")

    if test2.get("success") and not test2.get("time_ok"):
        print(f"{Colors.YELLOW}2. Fast Path zbyt wolny ({test2.get('elapsed', 0):.2f}s > 3s) - sprawdź połączenie z Gemini API{Colors.ENDC}")

    if test2.get("success") and not test2.get("has_data"):
        print(f"{Colors.RED}3. RAG nie zwraca konkretnych danych - KRYTYCZNY BŁĄD!{Colors.ENDC}")
        print(f"   - Sprawdź czy Qdrant działa (localhost:6333)")
        print(f"   - Sprawdź nazwę kolekcji (powinno być 'ultra_knowledge' lub 'ultra_rag_v1')")
        print(f"   - Sprawdź czy dane są załadowane (uruchom load_rag_data.py)")

    if test2.get("success") and not test2.get("confidence_ok"):
        print(f"{Colors.YELLOW}4. Niski Confidence Score ({test2.get('confidence', 0):.2f}) - AI nie jest pewne odpowiedzi{Colors.ENDC}")

    return verdict

def main():
    """Główna funkcja audytu."""
    print(f"\n{Colors.BOLD}{Colors.BLUE}")
    print("╔═══════════════════════════════════════════════════════════╗")
    print("║  ULTRA v3.0 BACKEND REALITY CHECK                         ║")
    print("║  Senior Backend Architect & QA Lead Audit                 ║")
    print("╚═══════════════════════════════════════════════════════════╝")
    print(f"{Colors.ENDC}")

    results = {}

    # Test 1: Backend Health
    results["backend_health"] = test_backend_health()

    if not results["backend_health"]:
        print(f"\n{Colors.RED}{Colors.BOLD}STOP: Backend nie odpowiada. Uruchom serwer przed kontynuacją.{Colors.ENDC}")
        print(f"{Colors.YELLOW}Komenda: cd backend && uvicorn backend.main:app --reload{Colors.ENDC}")
        sys.exit(1)

    # Test 2: Winter Range Query
    results["test2"] = test_fast_path_winter_range()

    # Test 3: TCO Query
    results["test3"] = test_fast_path_tco()

    # Raport końcowy
    verdict = generate_report(results)

    # Exit code
    sys.exit(0 if verdict == "PASS" else 1)

if __name__ == "__main__":
    main()
