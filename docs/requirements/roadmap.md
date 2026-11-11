# Etapy wydań, weryfikacja i aktualizacje

Projekt v0.7 z 11 listopada 2026 obejmuje rundy 1–6. Numeracja etapów nie oznacza opublikowanych wersji. Nie ustalamy dat realizacji.

## Zakres pierwszego kompletnego wydania developerskiego

[Decyzja rundy 6](round-06-architecture.md) zastępuje wcześniejsze odkładanie demandu i CWU poza pierwsze wydanie. Zakres: CO i strefy, opcjonalne zawory i demand oraz niezależnie opcjonalne CWU z harmonogramem. Musi umożliwiać pełne działanie samo CO / samo CWU / obu modułów. Jedna konfiguracja obejmuje jedną pompę, maksymalnie jeden CO i jedno CWU.

Architektura przewiduje przyszłe dwa CO jednej pompy z osobnymi strefami, nastawami i Demand 1/2. Funkcja jest poza pierwszym wydaniem. Prognozy i skropliny pozostają późniejsze; skropliny są wstępnie kolejne w kolejności.

## Kolejność prac

| Etap | Zakres | Warunek zakończenia |
| --- | --- | --- |
| P0 — wymagania | Rundy 1–6, US01–US21, decyzje, A01–A59 i B01–B13 | Zapis i przegląd uzgodnień produktu; bez twierdzenia o gotowej implementacji |
| P1 — projekt techniczny | Moduły, dane, domena, minimum HA, encje/potwierdzenia, historia, Store, frontend i testy | Rozwiązanie pytań niezbędnych do implementacji |
| P2 — budowa etapami | Fundament obserwacyjny, potem pełne sterowanie CO/strefami/zaworami/demandem i CWU | Wszystkie funkcje pierwszego wydania działają, nie tylko demonstrator |
| P3 — odbiór i pierwsze wydanie developerskie | Testy, konfiguracje modułów, awarie/restarty/aktualizacje, PL/EN, HACS i ręczna instalacja | Wyniki na instalacji referencyjnej, wskazane konfiguracje tylko symulowane i komplet instrukcji |
| P4 — kolejne rozszerzenia | Skropliny wstępnie następne; prognozy i drugi obieg w przyszłych wersjach | Osobno dopracowany i zatwierdzony zakres każdego rozszerzenia |
| P5 — stabilizacja | Kompatybilność, dokumentacja, regresje i publikacja | Powtarzalny odbiór; zgłoszenie do domyślnego katalogu HACS po stabilizacji |

Dokumentacja nie uruchamia implementacji. Kolejność wewnątrz P2 ustalimy w projekcie technicznym. POC jest całkowicie osobny, nie stanowi etapu produktu.

## Weryfikacja i dowody odbioru

- Deterministyczne testy algorytmu i czasu, filtry, zakłócenia, konflikty stref, limity, kwantyzacja i ponowienia.
- Konfiguracja, cykl życia i trzy warianty CO/CWU; cztery kombinacje zaworów/demandu dla CO.
- Brak poleceń w obserwacji; świadoma aktywacja; odłączenie wyjść; blokada współdzielenia.
- Braki danych, odbudowa historii i gotowość okien; brak fikcyjnych próbek.
- Restarty, aktualizacje/migracje, zachowanie tożsamości, timerów i nadpisań; niezgodny powrót do starszego wydania.
- CWU: plan 7×48, walidacja edycji, nadpisania, Zapisz, zmiana czasu i częściowe wykonanie.
- Kontrole struktury integracji i frontendu, tłumaczeń oraz publikacji, w tym odpowiednie hassfest/HACS.
- Odbiór na rzeczywistej instalacji z wersją, ustawieniami, wejściami, stanami, czasami i wynikami. Jawnie zaznaczamy przypadki tylko symulowane.

Scenariusze są w [rundzie 3](round-03-regulation.md), [rundzie 4](round-04-failures-restarts.md), [A01–A59](round-05-acceptance.md#scenariusze-odbioru) i [B01–B13](round-06-architecture.md). Nie deklarujemy oszczędności ani wykonania testów, które dopiero powstaną.

F01 wymaga przed implementacją klasyfikacji pracy pompy, progów, histerezy i odbioru grzałki/restartów. Prognozy są odłożone; wymagają osobnej walidacji i archiwizacji prognozy dostępnej w chwili decyzji. Modularność nie jest ich implementacją.

## Aktualizacje i wycofanie

Konfiguracja HA i Store są wersjonowane i migrowane. Aktualizacja musi zachować ustawienia, historię, tożsamość encji i potrzebny stan działania; nie resetuje timerów i nadpisań ani nie wywołuje nieplanowanych przełączeń. Restart przerywa wykonywanie, po czym odtwarzamy i uzgadniamy stan. Retencja i filtry Recordera nadal obowiązują.

Każde wydanie określa możliwość powrotu. Starsza wersja odczytuje tylko zgodny format; przy niezgodności błąd bez kasowania danych i aktywacji sterowania. Instrukcja wskazuje właściwą kopię HA do odtworzenia. Dowolna zgodność przyszłych danych ze starszym kodem nie jest obiecana.

POC dostarcza doświadczeń do projektowania/testów, ale nie wymaga importera ani instrukcji migracji użytkownika produktu. Osobna instrukcja przejścia instalacji właściciela może powstać poza wymaganiami publicznego uruchomienia. Niezależnie od POC aktywacja wymaga braku konfliktu regulatorów.

## Publikacja

Instalacja ręczna i HACS custom repository. Pierwsze wydania developerskie testowe, np. 0.1.0-beta.1; aktualizacje wybiera użytkownik. Od pierwszego wydania pełny interfejs, komunikaty i instrukcje instalacji/konfiguracji PL/EN. Karta, panel CWU i konfiguracja zaawansowana są dostarczane z produktem.

Minimum HA dobierzemy przed implementacją; wydanie podaje minimum i sprawdzone wersje. Podniesienie wymagań jest jawne. Domyślny katalog HACS dopiero po stabilizacji. Dokumentacyjny PR nie publikuje wersji i nie zamyka Issues implementacji.
