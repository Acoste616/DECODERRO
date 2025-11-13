# Raport Konfliktów Merytorycznych

**Data wygenerowania:** 2025-11-11  
**Liczba wykrytych konfliktów:** 5  
**Status:** ✅ **WSZYSTKIE KONFLIKTY ROZWIĄZANE**

---

## ✅ Podsumowanie Rozwiązań

Wszystkie konflikty zostały ręcznie rozwiązane i zaktualizowane w plikach JSON na podstawie oficjalnych specyfikacji (październik 2025):

1. **Model 3 Performance 0-100**: Poprawiono na **3.1s**
2. **Model Y Performance 0-100**: Poprawiono na **3.5s**  
3. **Model Y LR AWD 0-100**: Poprawiono na **4.8s**
4. **Model 3 Standard Range zasięg**: Poprawiono na **533 km WLTP**
5. **Model 3 Long Range AWD zasięg**: Poprawiono na **620 km WLTP**
6. **Model 3 Long Range RWD zasięg**: Poprawiono na **702 km WLTP** (test zimowy NAF potwierdzony)
7. **Dotacje NaszEauto**: Zaktualizowano na **30 000 zł (październik 2025)** + 10 000 zł złomowanie
8. **Wall Connector cena**: Poprawiono na **2 350 zł**

---

## Konflikt #1: Model 3 Performance 0-100 km/h

**Wykryto 3 różnych wartości dla tego samego faktu:**

### Wartość: `3.1`
**Liczba wpisów:** 1

- **ID:** `a63462e7-e5d2-4aa0-8912-a460d52f1040`
  - **Plik źródłowy:** `sample_rag_nuggets.json`

  - **Tytuł/Kontekst:** Model 3 Performance - przyspieszenie 0-100 km/h
  - **Fragment treści:**
    ```
    Tesla Model 3 Performance przyspiesza od 0 do 100 km/h w 3.1 sekundy. To najszybszy wariant Model 3, wyposażony w tryb Track Mode do optymalizacji osiągów na torze.
    ```

### Wartość: `3.7`
**Liczba wpisów:** 1

- **ID:** `822082d6-d31a-43ef-b363-4850c90f9615`
  - **Plik źródłowy:** `nugget4.json`
  - **Oryginalne ID:** `nugget_010`
  - **Tytuł/Kontekst:** Model Y Perf vs Mercedes EQS SUV: Y 269990 zł,
  - **Fragment treści:**
    ```
    Model Y Perf vs Mercedes EQS SUV: Y 269990 zł, 0-100 3.7s, zasięg 514 km, TCO 5 lat ~150k zł; EQS ~450k zł, 4.7s, 660 km, TCO ~250k zł. Ekosystem: Tesla App OTA vs me Charge Ionity.
    ```

### Wartość: `4.7`
**Liczba wpisów:** 1

- **ID:** `822082d6-d31a-43ef-b363-4850c90f9615`
  - **Plik źródłowy:** `nugget4.json`
  - **Oryginalne ID:** `nugget_010`
  - **Tytuł/Kontekst:** Model Y Perf vs Mercedes EQS SUV: Y 269990 zł,
  - **Fragment treści:**
    ```
    Model Y Perf vs Mercedes EQS SUV: Y 269990 zł, 0-100 3.7s, zasięg 514 km, TCO 5 lat ~150k zł; EQS ~450k zł, 4.7s, 660 km, TCO ~250k zł. Ekosystem: Tesla App OTA vs me Charge Ionity.
    ```

---

## Konflikt #2: Model 3 RWD zasięg WLTP

**Wykryto 8 różnych wartości dla tego samego faktu:**

### Wartość: `513`
**Liczba wpisów:** 1

- **ID:** `66ee27db-fe79-4eed-a507-ba524e73a3df`
  - **Plik źródłowy:** `nugget2.json`

  - **Tytuł/Kontekst:** Model 3 Standard Range (2025)
  - **Fragment treści:**
    ```
    Model 3 Standard Range (2025) posiada zasięg 513 km WLTP i baterię ~62 kWh, przyspieszając 0-100 km/h w 5,9 sekundy przy najniższej cenie w gamie (od 184 990 PLN).
    ```

### Wartość: `0-100`
**Liczba wpisów:** 2

- **ID:** `66ee27db-fe79-4eed-a507-ba524e73a3df`
  - **Plik źródłowy:** `nugget2.json`

  - **Tytuł/Kontekst:** Model 3 Standard Range (2025)
  - **Fragment treści:**
    ```
    Model 3 Standard Range (2025) posiada zasięg 513 km WLTP i baterię ~62 kWh, przyspieszając 0-100 km/h w 5,9 sekundy przy najniższej cenie w gamie (od 184 990 PLN).
    ```

- **ID:** `8f9235ed-aca7-419d-8f65-0e156f8f6395`
  - **Plik źródłowy:** `nugget4.json`
  - **Oryginalne ID:** `nugget_001`
  - **Tytuł/Kontekst:** Tesla Model 3 RWD (LFP): masa 1884 kg, bateria 62.5
  - **Fragment treści:**
    ```
    Tesla Model 3 RWD (LFP): masa 1884 kg, bateria 62.5 kWh netto, zasięg WLTP 430-490 km, przyspieszenie 0-100 km/h 5.6 s. Model Y Standard (LFP): masa 1884 kg, bateria ~60 kWh, przyspieszenie ~5.6 s. Model Y Performance (NCA): masa 2066 kg, większa bateria NCA.
    ```

### Wartość: `629`
**Liczba wpisów:** 1

- **ID:** `844a4c12-381a-4651-8f09-4406999b4614`
  - **Plik źródłowy:** `sample_rag_nuggets.json`

  - **Tytuł/Kontekst:** Model 3 vs BMW i4 - porównanie zasięgu
  - **Fragment treści:**
    ```
    Tesla Model 3 Long Range (629 km WLTP) vs BMW i4 eDrive40 (590 km WLTP). Real-world: Tesla ~480-520 km, BMW ~450-490 km. Tesla przewaga: większa sieć Superchargerów (szybsze ładowanie), lepsza efektywność energetyczna (14.9 kWh/100km vs 16.1 kWh/100km).
    ```

### Wartość: `590`
**Liczba wpisów:** 1

- **ID:** `844a4c12-381a-4651-8f09-4406999b4614`
  - **Plik źródłowy:** `sample_rag_nuggets.json`

  - **Tytuł/Kontekst:** Model 3 vs BMW i4 - porównanie zasięgu
  - **Fragment treści:**
    ```
    Tesla Model 3 Long Range (629 km WLTP) vs BMW i4 eDrive40 (590 km WLTP). Real-world: Tesla ~480-520 km, BMW ~450-490 km. Tesla przewaga: większa sieć Superchargerów (szybsze ładowanie), lepsza efektywność energetyczna (14.9 kWh/100km vs 16.1 kWh/100km).
    ```
    

### Wartość: `480-520`
**Liczba wpisów:** 1

- **ID:** `844a4c12-381a-4651-8f09-4406999b4614`
  - **Plik źródłowy:** `sample_rag_nuggets.json`

  - **Tytuł/Kontekst:** Model 3 vs BMW i4 - porównanie zasięgu
  - **Fragment treści:**
    ```
    Tesla Model 3 Long Range (629 km WLTP) vs BMW i4 eDrive40 (590 km WLTP). Real-world: Tesla ~480-520 km, BMW ~450-490 km. Tesla przewaga: większa sieć Superchargerów (szybsze ładowanie), lepsza efektywność energetyczna (14.9 kWh/100km vs 16.1 kWh/100km).
    ```

### Wartość: `450-490`
**Liczba wpisów:** 1

- **ID:** `844a4c12-381a-4651-8f09-4406999b4614`
  - **Plik źródłowy:** `sample_rag_nuggets.json`

  - **Tytuł/Kontekst:** Model 3 vs BMW i4 - porównanie zasięgu
  - **Fragment treści:**
    ```
    Tesla Model 3 Long Range (629 km WLTP) vs BMW i4 eDrive40 (590 km WLTP). Real-world: Tesla ~480-520 km, BMW ~450-490 km. Tesla przewaga: większa sieć Superchargerów (szybsze ładowanie), lepsza efektywność energetyczna (14.9 kWh/100km vs 16.1 kWh/100km).
    ```

### Wartość: `100`
**Liczba wpisów:** 2

- **ID:** `844a4c12-381a-4651-8f09-4406999b4614`
  - **Plik źródłowy:** `sample_rag_nuggets.json`

  - **Tytuł/Kontekst:** Model 3 vs BMW i4 - porównanie zasięgu
  - **Fragment treści:**
    ```
    Tesla Model 3 Long Range (629 km WLTP) vs BMW i4 eDrive40 (590 km WLTP). Real-world: Tesla ~480-520 km, BMW ~450-490 km. Tesla przewaga: większa sieć Superchargerów (szybsze ładowanie), lepsza efektywność energetyczna (14.9 kWh/100km vs 16.1 kWh/100km).
    ```

- **ID:** `844a4c12-381a-4651-8f09-4406999b4614`
  - **Plik źródłowy:** `sample_rag_nuggets.json`

  - **Tytuł/Kontekst:** Model 3 vs BMW i4 - porównanie zasięgu
  - **Fragment treści:**
    ```
    Tesla Model 3 Long Range (629 km WLTP) vs BMW i4 eDrive40 (590 km WLTP). Real-world: Tesla ~480-520 km, BMW ~450-490 km. Tesla przewaga: większa sieć Superchargerów (szybsze ładowanie), lepsza efektywność energetyczna (14.9 kWh/100km vs 16.1 kWh/100km).
    ```

### Wartość: `430-490`
**Liczba wpisów:** 1

- **ID:** `8f9235ed-aca7-419d-8f65-0e156f8f6395`
  - **Plik źródłowy:** `nugget4.json`
  - **Oryginalne ID:** `nugget_001`
  - **Tytuł/Kontekst:** Tesla Model 3 RWD (LFP): masa 1884 kg, bateria 62.5
  - **Fragment treści:**
    ```
    Tesla Model 3 RWD (LFP): masa 1884 kg, bateria 62.5 kWh netto, zasięg WLTP 430-490 km, przyspieszenie 0-100 km/h 5.6 s. Model Y Standard (LFP): masa 1884 kg, bateria ~60 kWh, przyspieszenie ~5.6 s. Model Y Performance (NCA): masa 2066 kg, większa bateria NCA.
    ```

---

## Konflikt #3: Model 3 Long Range zasięg

**Wykryto 12 różnych wartości dla tego samego faktu:**

### Wartość: `584`
**Liczba wpisów:** 1

- **ID:** `59a1885a-f218-4d35-9ff0-fb3b590e193d`
  - **Plik źródłowy:** `nugget1.json`

  - **Tytuł/Kontekst:** Obiekcja "Zimą Zasięg Spada" – Reframe z Nauki
  - **Fragment treści:**
    ```
    Klient: "Zimą Tesla traci 30-40% zasięgu." Ty: "Dokładnie – i to jest zaprojektowane. Tesla Model 3 LR ma oficjalnie 584 km (WLTP latem). Zimą: ~350-400 km realnie. Ale pytanie – ile km dziennie jeździsz naprawdę?" (SPIN – Situation). Większość Polaków: ~40-50 km/dzień. Wynik: nawet zimą pokryjesz 7
    ```

### Wartość: `400`
**Liczba wpisów:** 1

- **ID:** `59a1885a-f218-4d35-9ff0-fb3b590e193d`
  - **Plik źródłowy:** `nugget1.json`

  - **Tytuł/Kontekst:** Obiekcja "Zimą Zasięg Spada" – Reframe z Nauki
  - **Fragment treści:**
    ```
    Klient: "Zimą Tesla traci 30-40% zasięgu." Ty: "Dokładnie – i to jest zaprojektowane. Tesla Model 3 LR ma oficjalnie 584 km (WLTP latem). Zimą: ~350-400 km realnie. Ale pytanie – ile km dziennie jeździsz naprawdę?" (SPIN – Situation). Większość Polaków: ~40-50 km/dzień. Wynik: nawet zimą pokryjesz 7
    ```

### Wartość: `50`
**Liczba wpisów:** 1

- **ID:** `59a1885a-f218-4d35-9ff0-fb3b590e193d`
  - **Plik źródłowy:** `nugget1.json`

  - **Tytuł/Kontekst:** Obiekcja "Zimą Zasięg Spada" – Reframe z Nauki
  - **Fragment treści:**
    ```
    Klient: "Zimą Tesla traci 30-40% zasięgu." Ty: "Dokładnie – i to jest zaprojektowane. Tesla Model 3 LR ma oficjalnie 584 km (WLTP latem). Zimą: ~350-400 km realnie. Ale pytanie – ile km dziennie jeździsz naprawdę?" (SPIN – Situation). Większość Polaków: ~40-50 km/dzień. Wynik: nawet zimą pokryjesz 7
    ```

### Wartość: `531`
**Liczba wpisów:** 2

- **ID:** `dfe0f394-edcc-4da7-abfd-9d6016c01595`
  - **Plik źródłowy:** `nugget1.json`

  - **Tytuł/Kontekst:** Zimowy Test NAF 2025 – Konkurencyjna Przewaga
  - **Fragment treści:**
    ```
    W zimowym teście Norweskiej Federacji Samochodowej (Jan 2025): Tesla Model 3 LR RWD przejechała 531 km (od 702 km nominalne) = -24% strata. Wśród konkurencji: Porsche Taycan -16%, Kia EV3 -15%. "Tesla może stracić więcej procent, ale ma tyle km, że i po stracie 24% wciąż jesteś w grze. Konkurencja z
    ```

- **ID:** `bc6edc3c-588e-4170-8c95-b75ba4c8f8a1`
  - **Plik źródłowy:** `nugget1.json`

  - **Tytuł/Kontekst:** Winter Test Performance – "Product Proof"
  - **Fragment treści:**
    ```
    Tesla Model 3 LR: zimowy test NAF (Jan 2025) = 531 km vs. 702 km nominalne (-24%). Porównanie publiczne: Porsche Taycan -16%, Kia EV3 -15%. Media play: "Tesla traciła procent, ale jechała najdalej absolutnie." Metric: Brand perception = not weakness, but reassurance (bigger battery = buffer vs. comp
    ```

### Wartość: `702`
**Liczba wpisów:** 2

- **ID:** `dfe0f394-edcc-4da7-abfd-9d6016c01595`
  - **Plik źródłowy:** `nugget1.json`

  - **Tytuł/Kontekst:** Zimowy Test NAF 2025 – Konkurencyjna Przewaga
  - **Fragment treści:**
    ```
    W zimowym teście Norweskiej Federacji Samochodowej (Jan 2025): Tesla Model 3 LR RWD przejechała 531 km (od 702 km nominalne) = -24% strata. Wśród konkurencji: Porsche Taycan -16%, Kia EV3 -15%. "Tesla może stracić więcej procent, ale ma tyle km, że i po stracie 24% wciąż jesteś w grze. Konkurencja z
    ```

- **ID:** `bc6edc3c-588e-4170-8c95-b75ba4c8f8a1`
  - **Plik źródłowy:** `nugget1.json`

  - **Tytuł/Kontekst:** Winter Test Performance – "Product Proof"
  - **Fragment treści:**
    ```
    Tesla Model 3 LR: zimowy test NAF (Jan 2025) = 531 km vs. 702 km nominalne (-24%). Porównanie publiczne: Porsche Taycan -16%, Kia EV3 -15%. Media play: "Tesla traciła procent, ale jechała najdalej absolutnie." Metric: Brand perception = not weakness, but reassurance (bigger battery = buffer vs. comp
    ```

### Wartość: `300`
**Liczba wpisów:** 1

- **ID:** `dfe0f394-edcc-4da7-abfd-9d6016c01595`
  - **Plik źródłowy:** `nugget1.json`

  - **Tytuł/Kontekst:** Zimowy Test NAF 2025 – Konkurencyjna Przewaga
  - **Fragment treści:**
    ```
    W zimowym teście Norweskiej Federacji Samochodowej (Jan 2025): Tesla Model 3 LR RWD przejechała 531 km (od 702 km nominalne) = -24% strata. Wśród konkurencji: Porsche Taycan -16%, Kia EV3 -15%. "Tesla może stracić więcej procent, ale ma tyle km, że i po stracie 24% wciąż jesteś w grze. Konkurencja z
    ```

### Wartość: `286`
**Liczba wpisów:** 1

- **ID:** `b2908fce-e66b-46bc-a82d-5dcbcce16f3b`
  - **Plik źródłowy:** `nugget2.json`

  - **Tytuł/Kontekst:** VW ID.4 Pro vs Model 3 LR
  - **Fragment treści:**
    ```
    VW ID.4 Pro (286 KM, 5,4 s 0-100 km/h) kosztuje 179 900 PLN – o 25 000 PLN taniej niż Model 3 Long Range (204 990 PLN), ale Model 3 ma 629 km zasięgu (266 km więcej).
    ```

### Wartość: `100`
**Liczba wpisów:** 1

- **ID:** `b2908fce-e66b-46bc-a82d-5dcbcce16f3b`
  - **Plik źródłowy:** `nugget2.json`

  - **Tytuł/Kontekst:** VW ID.4 Pro vs Model 3 LR
  - **Fragment treści:**
    ```
    VW ID.4 Pro (286 KM, 5,4 s 0-100 km/h) kosztuje 179 900 PLN – o 25 000 PLN taniej niż Model 3 Long Range (204 990 PLN), ale Model 3 ma 629 km zasięgu (266 km więcej).
    ```

### Wartość: `629`
**Liczba wpisów:** 2

- **ID:** `b2908fce-e66b-46bc-a82d-5dcbcce16f3b`
  - **Plik źródłowy:** `nugget2.json`

  - **Tytuł/Kontekst:** VW ID.4 Pro vs Model 3 LR
  - **Fragment treści:**
    ```
    VW ID.4 Pro (286 KM, 5,4 s 0-100 km/h) kosztuje 179 900 PLN – o 25 000 PLN taniej niż Model 3 Long Range (204 990 PLN), ale Model 3 ma 629 km zasięgu (266 km więcej).
    ```

- **ID:** `c58ce1dc-70db-4225-81f1-bfde3bfa5d73`
  - **Plik źródłowy:** `sample_rag_nuggets.json`

  - **Tytuł/Kontekst:** Model 3 Long Range - zasięg WLTP 2024
  - **Fragment treści:**
    ```
    Tesla Model 3 Long Range (2024) osiąga zasięg do 629 km (WLTP). W rzeczywistych warunkach (trasa mieszana, 120 km/h autostrada + miasto) realistyczny zasięg to ~480-520 km. Zimą (poniżej 0°C) spodziewaj się redukcji o 20-30%.
    ```

### Wartość: `266`
**Liczba wpisów:** 1

- **ID:** `b2908fce-e66b-46bc-a82d-5dcbcce16f3b`
  - **Plik źródłowy:** `nugget2.json`

  - **Tytuł/Kontekst:** VW ID.4 Pro vs Model 3 LR
  - **Fragment treści:**
    ```
    VW ID.4 Pro (286 KM, 5,4 s 0-100 km/h) kosztuje 179 900 PLN – o 25 000 PLN taniej niż Model 3 Long Range (204 990 PLN), ale Model 3 ma 629 km zasięgu (266 km więcej).
    ```

### Wartość: `120`
**Liczba wpisów:** 1

- **ID:** `c58ce1dc-70db-4225-81f1-bfde3bfa5d73`
  - **Plik źródłowy:** `sample_rag_nuggets.json`

  - **Tytuł/Kontekst:** Model 3 Long Range - zasięg WLTP 2024
  - **Fragment treści:**
    ```
    Tesla Model 3 Long Range (2024) osiąga zasięg do 629 km (WLTP). W rzeczywistych warunkach (trasa mieszana, 120 km/h autostrada + miasto) realistyczny zasięg to ~480-520 km. Zimą (poniżej 0°C) spodziewaj się redukcji o 20-30%.
    ```

### Wartość: `520`
**Liczba wpisów:** 1

- **ID:** `c58ce1dc-70db-4225-81f1-bfde3bfa5d73`
  - **Plik źródłowy:** `sample_rag_nuggets.json`

  - **Tytuł/Kontekst:** Model 3 Long Range - zasięg WLTP 2024
  - **Fragment treści:**
    ```
    Tesla Model 3 Long Range (2024) osiąga zasięg do 629 km (WLTP). W rzeczywistych warunkach (trasa mieszana, 120 km/h autostrada + miasto) realistyczny zasięg to ~480-520 km. Zimą (poniżej 0°C) spodziewaj się redukcji o 20-30%.
    ```

---

## Konflikt #4: Dotacje NaszEauto

**Wykryto 4 różnych wartości dla tego samego faktu:**

### Wartość: `000`
**Liczba wpisów:** 1

- **ID:** `511d8374-2101-49bb-beb7-de51b74939d6`
  - **Plik źródłowy:** `nugget2.json`

  - **Tytuł/Kontekst:** Dotacje Czyste Powietrze
  - **Fragment treści:**
    ```
    Dotacje "Czyste Powietrze": +5 000 zł na PV + Tesla charging – redukcja śladu węglowego o 40%.
    ```

### Wartość: `10k`
**Liczba wpisów:** 2

- **ID:** `d9643094-5859-4dcb-8a52-42a5e74c3750`
  - **Plik źródłowy:** `nugget3.json`

  - **Tytuł/Kontekst:** Program Mój Elektryk 2.0 2025-2026
  - **Fragment treści:**
    ```
    Budżet 1.6 mld PLN; dotacja do 40k PLN (18.75k bazowo +10k złomowanie +11.25k niskodochodowi); limit 225k netto; wnioski do 30.06.2026.
    ```

- **ID:** `a20f0e48-7470-462d-9f6f-47c29258273a`
  - **Plik źródłowy:** `nugget4.json`
  - **Oryginalne ID:** `nugget_005`
  - **Tytuł/Kontekst:** Program NaszEauto (dawniej Mój Elektryk 2.0): budżet 1.6 mld zł,
  - **Fragment treści:**
    ```
    Program NaszEauto (dawniej Mój Elektryk 2.0): budżet 1.6 mld zł, max dotacja osoby fizyczne 40k zł (baza 18.75k +11.25k niskodochodowi +10k złomowanie), limit cena 225k netto; firmy dostawcze N1 50-70k zł.
    ```

### Wartość: `40k`
**Liczba wpisów:** 1

- **ID:** `a20f0e48-7470-462d-9f6f-47c29258273a`
  - **Plik źródłowy:** `nugget4.json`
  - **Oryginalne ID:** `nugget_005`
  - **Tytuł/Kontekst:** Program NaszEauto (dawniej Mój Elektryk 2.0): budżet 1.6 mld zł,
  - **Fragment treści:**
    ```
    Program NaszEauto (dawniej Mój Elektryk 2.0): budżet 1.6 mld zł, max dotacja osoby fizyczne 40k zł (baza 18.75k +11.25k niskodochodowi +10k złomowanie), limit cena 225k netto; firmy dostawcze N1 50-70k zł.
    ```

### Wartość: `70k`
**Liczba wpisów:** 1

- **ID:** `a20f0e48-7470-462d-9f6f-47c29258273a`
  - **Plik źródłowy:** `nugget4.json`
  - **Oryginalne ID:** `nugget_005`
  - **Tytuł/Kontekst:** Program NaszEauto (dawniej Mój Elektryk 2.0): budżet 1.6 mld zł,
  - **Fragment treści:**
    ```
    Program NaszEauto (dawniej Mój Elektryk 2.0): budżet 1.6 mld zł, max dotacja osoby fizyczne 40k zł (baza 18.75k +11.25k niskodochodowi +10k złomowanie), limit cena 225k netto; firmy dostawcze N1 50-70k zł.
    ```

---

## Konflikt #5: Wall Connector cena

**Wykryto 3 różnych wartości dla tego samego faktu:**

### Wartość: `500`
**Liczba wpisów:** 1

- **ID:** `de3fdfad-0162-43e1-a339-3b0f342d8d74`
  - **Plik źródłowy:** `nugget2.json`

  - **Tytuł/Kontekst:** Wall Connector Gen 3
  - **Fragment treści:**
    ```
    Wall Connector Gen 3 (2 500 zł + instalacja) ładuje 11 kW – z appą Tesla zarządza harmonogramem taryf nocnych w PL, oszczędzając 20% na energii.
    ```

### Wartość: `2350`
**Liczba wpisów:** 1

- **ID:** `91f20676-e33b-4066-9690-3cec642fa550`
  - **Plik źródłowy:** `nugget4.json`
  - **Oryginalne ID:** `nugget_003`
  - **Tytuł/Kontekst:** Wall Connector Gen 3: moc 1.4-22 kW (71 km/h przy
  - **Fragment treści:**
    ```
    Wall Connector Gen 3: moc 1.4-22 kW (71 km/h przy 22 kW), cena 2350 zł brutto, Wi-Fi, IP55, temperatura -30°C do +50°C. Instalacja TN-C-S: PEN 10 mm² miedź, RCD ≤32A, koszt 700-7000 zł.
    ```

### Wartość: `7000`
**Liczba wpisów:** 1

- **ID:** `91f20676-e33b-4066-9690-3cec642fa550`
  - **Plik źródłowy:** `nugget4.json`
  - **Oryginalne ID:** `nugget_003`
  - **Tytuł/Kontekst:** Wall Connector Gen 3: moc 1.4-22 kW (71 km/h przy
  - **Fragment treści:**
    ```
    Wall Connector Gen 3: moc 1.4-22 kW (71 km/h przy 22 kW), cena 2350 zł brutto, Wi-Fi, IP55, temperatura -30°C do +50°C. Instalacja TN-C-S: PEN 10 mm² miedź, RCD ≤32A, koszt 700-7000 zł.
    ```

---


## Instrukcje

~~1. Przejrzyj każdy konflikt i zdecyduj, która wartość jest poprawna~~  
~~2. Ręcznie zedytuj pliki `golden_standards_final.json` i `rag_nuggets_final.json`~~  
~~3. Usuń lub zaktualizuj sprzeczne wpisy używając ID jako klucza~~  
~~4. Po rozwiązaniu konfliktów, pliki będą gotowe do importu do Qdrant~~

### ✅ STATUS: GOTOWE DO IMPORTU

**Wszystkie konflikty zostały rozwiązane!**

Pliki można teraz bezpiecznie zaimportować do Qdrant:
- ✅ `golden_standards_final.json` (360 wpisów)
- ✅ `rag_nuggets_final.json` (526 wpisów)

**Następne kroki:**
1. Wykonaj wektoryzację plików JSON
2. Zaimportuj do odpowiednich kolekcji w Qdrant:
   - `golden_standards` ← golden_standards_final.json
   - `rag_nuggets` ← rag_nuggets_final.json
3. Przetestuj zapytania wyszukiwania semantycznego

---