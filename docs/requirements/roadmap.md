# Etapy wydań, weryfikacja i migracja

Projekt v0.4, 10 listopada 2026, po rundach modelu instalacji/stref, codziennej obsługi i reguł regulacji. Nie ustalamy dat realizacji ani nie obiecujemy niezweryfikowanych funkcji. Numeracja poniżej opisuje etapy, nie opublikowane wersje programu.

## Kolejność

| Etap | Zakres | Warunek zakończenia |
| --- | --- | --- |
| R0 — wymagania | Produkt, US01–US21, decyzje i scenariusze | Kluczowe pytania zakresu kolejnego etapu rozstrzygnięte przez właściciela produktu |
| R1 — fundament obserwacyjny | Konfiguracja UI, encje, pamięć, jakość danych, cele, decyzje i dashboard | Działa instalacja/cykl życia; obserwacja nie wysyła żadnych automatycznych poleceń do objętych nią wyjść |
| R2 — pierwsza publiczna wersja testowa | Regulator CO1 i strefy, opcjonalne wyjścia zaworów, diagnostyka i świadoma aktywacja | Testy porównawcze, scenariusze awarii, sprawdzone limity i dowód odbioru konfiguracji referencyjnej |
| R3 — opcjonalny demand | Agregacja, sekwencje zaworów, timery i potwierdzenia | Zweryfikowane znaczenie wejścia i gotowość instalacji; bez demandu brak ON/OFF CO1 |
| R4 — CWU | Tryb stały i harmonogram 7×48 | Uzgodnione nadpisania, obserwacja, restart, zmiana czasu, brak łączności i relacja do ochrony producenta |
| R5 — prognozy, odłożone do kolejnej wersji | Wymagania US21 zachowane; brak w bieżącym programie | Walidacja słonecznych/pochmurnych dni, zmian pogody i awarii; porównanie z bazą bez prognoz |
| R6 — F01 skroplin | Kalibracja pracy PC, grzałka, timery i diagnostyka | Potwierdzone klasy pracy/progi i testy odbioru grzałki oraz restartów |
| R7 — stabilizacja | Kompatybilność, aktualizacje, dokumentacja PL/EN, wydania | Powtarzalne kontrole, instrukcje wsparcia i udokumentowane ograniczenia |

Zakres i kolejność R3–R6 to propozycja organizacyjna do zatwierdzenia, nie nowa decyzja o priorytetach. Demand jest opcją modelu produktu od początku; jego aktywna obsługa nie jest obiecana w pierwszej wersji testowej. Tak samo obecność CWU i prognoz w wymaganiach nie oznacza ich implementacji w R2.

Nie rozpoczynamy kodowania produktu przy otwartych decyzjach istotnych dla danego etapu. Nie blokuje to dalszego rozwijania POC na jego własnej gałęzi.

## Postęp doprecyzowania wymagań

Runda 1 — model instalacji i stref: uzgodniona, szczegóły i scenariusze w [osobnym zapisie](round-01-installation-zones.md). Nie oznacza zakończenia R0 ani odbioru funkcji. Runda 2 — codzienna obsługa: uzgodniona, [zapis](round-02-daily-operation.md). Runda 3 — reguły regulacji: uzgodniona, [zapis](round-03-regulation.md). Kolejne rundy: awarie i restarty; szczegółowe user stories i odbiór; architektura/migracja/wydania. Agregację i okna pomiarów oraz wspólny czas otwierania doprecyzowano w rundzie 3. Stan początkowy, czasy zamykania, braki danych i potwierdzenia pozostają na dalsze rundy.

## Scenariusze odbioru

### Konfiguracja i cykl życia

- Jeden wspólny obieg; jedna strefa Dom albo wiele niezależnych stref; grupy porządkowe bez podwójnej regulacji.
- Jeden lub kilka termometrów na strefę; wybór głównego albo średniej/mediany, szczegóły w rundzie regulacji.
- Minimalna konfiguracja wymaga encji nastawy PC także w obserwacji, outdoor i aktywnej strefy z termometrem oraz celem.
- Wyjścia nie mogą należeć do dwóch stref; typ NC/NO osobno dla strefy, wspólny dla wszystkich jej wyjść.
- Bez modelu i pola pętli stale otwartych; ostrzeżenie hydrauliczne przy konfiguracji sterowania zaworami, zgodnie z rundą 3.
- Cztery kombinacje zaworów i demandu, poprawne wymaganie encji.
- NC i NO, wyjście grupy lub kilka wyjść; samo zapisanie konfiguracji nie uruchamia urządzeń.
- Restart, przeładowanie, zmiana ustawień i usunięcie integracji według uzgodnionej polityki.
- Zachowanie celów i potrzebnej pamięci; brak fikcyjnych próbek po przerwie.
- Dwie niezależne obserwacje CO/CWU bez poleceń; aktywacja bez odtwarzania zaległej kolejki.
- Zmiana celu jednej strefy CO to trwała nastawa tylko tej strefy, zachowana po restarcie.

### CO1 i strefy

- Gotowanie/słońce, wietrzenie, trwały wzrost i spadek oraz konflikt stref.
- Zmiana celu i współczynników krzywej, minimum/maksimum, kwantyzacja i odstępy zmian.
- Niepoprawne jednostki, stary outdoor, luki danych, rozgrzewanie filtrów i awaria jednej strefy.
- Ręczna zmiana, nieudany zapis, brak niezależnego potwierdzenia i powrót łączności.
- Po zamknięciu wszystkich przypisanych wyjść strefa nie wpływa na korektę CO1, ale jest monitorowana; brak sprzężenia nie jest przedstawiany jako potwierdzone fizyczne odcięcie.
- Brak demandu: żadnych poleceń ON/OFF ogrzewania.

### CWU, prognozy i skropliny — przed wdrożeniem danego modułu

- CWU: trzy tryby, granice przedziałów, osobne dni i temperatura na przedział.
- Ręczne włączenie w przerwie harmonogramu, podpowiedź ostatniej nastawy, nadpisanie do rzeczywistej zmiany i brak kasowania przez identyczne pola.
- Zbiorczy Zapisz tylko CWU: robocze zmiany nie sterują urządzeniem, walidacja całości, potwierdzenie odrzucenia; w obserwacji brak poleceń również po zapisie.
- CWU: restart, zmiana czasu, edycja harmonogramu podczas nadpisania i niedostępność pompy — oczekiwania do dopracowania.
- Prognozy: luki, zasięg krótszy od oczekiwanego, przeterminowanie, zmieniona prognoza, brak PV, podwójne źródła słońca i konflikt komfortu.
- F01: stop przed 30 min, wybieg ≥20 min, restart PC w wybiegu, restart HA, brak poboru grzałki, ocieplenie i nieznana praca PC.

Przed implementacją określimy mierzalne oczekiwane wyniki i tolerancje każdego scenariusza. Nie deklarujemy na tym etapie procentowej poprawy komfortu ani oszczędności.

Dodatkowe scenariusze liczbowe i czasowe zawiera [runda 3](round-03-regulation.md). W bieżącej wersji prognozy są odłożone, ale od początku wymagamy rozdzielenia modułów korekt i zawsze obowiązujących ograniczeń (US20). Nie rozpoczynamy implementacji prognoz w ramach modularności.

## Weryfikacja techniczna

- Deterministyczne testy rdzenia i czasu oraz odtwarzanie historii POC.
- Testy konfiguracji i cyklu życia w HA oraz brak niezamierzonych wywołań wyjść.
- Kontrole struktury integracji, tłumaczeń i publikacji, w tym hassfest/HACS w zakresie odpowiednim dla wydania.
- Odtwarzanie historii bez dostępu do przyszłych pomiarów lub później poprawionych prognoz.
- Testy lokalne nie zastępują odbioru na rzeczywistej instalacji. Dobór zestawu narzędzi i minimalnej wersji HA nastąpi przed kodowaniem.

## Migracja z POC

1. Zidentyfikować aktywne automatyzacje zapisu nastawy oraz oddzielny auto STOP/START CO1. Brak jednego zapisu nie oznacza wyłączenia drugiej funkcji.
2. Rozpocząć obserwację produktu bez przejmowania wyjść; porównać dane i decyzje.
3. Przed aktywacją usunąć konflikt regulatorów i udokumentować stan pozostawiony w urządzeniu.
4. Zachować lub jawnie przenieść cele i ustawienia; nie usuwać historii. Import buforów pozostaje decyzją.
5. Udokumentować wycofanie: zatrzymanie nowych poleceń, sprawdzenie bieżących nastaw i uruchomienie tylko jednego regulatora.

Samo usunięcie POC lub produktu nie musi przywrócić poprzedniej nastawy ani stanu obiegu. Produkt bez demandu nie dziedziczy automatycznie auto STOP CO1.

## Publikacja

Publiczne repozytorium, instalacja ręczna i HACS custom repository; kolejne wydania z opisem zmian, kompatybilnością, PL/EN i procedurą wycofania. Zgłoszenie do domyślnego katalogu HACS po stabilizacji. Dokumentacyjny PR nie tworzy wydania i nie zamyka Issues funkcji.
