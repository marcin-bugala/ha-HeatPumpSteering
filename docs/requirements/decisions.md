# Rejestr decyzji i pytań

Stan: 10 listopada 2026, po rundach 1–3. „Przyjęte” oznacza potwierdzony kierunek produktu; nie oznacza implementacji ani zatwierdzenia wszystkich parametrów. Status realizacji historii znajduje się w Issues.

## Przyjęte decyzje

| ID | Decyzja | Powiązania |
| --- | --- | --- |
| D01 | Publiczna custom integration HA, repozytorium ha-HeatPumpSteering, PL/EN i planowana dystrybucja HACS | Produkt, etapy |
| D02 | main dla produktu; poc/co1-automation dla POC; osobne gałęzie i PR-y do main | US08 |
| D03 | Produkt uniwersalny przez encje HA; Hisense/HiMitII pierwszy profil referencyjny | US16, US19 |
| D04 | Pierwsza publiczna wersja testowa: CO1 i strefy; F01 później | Etapy |
| D05 | Regulacja nastawy PC zawsze podstawą; zawory stref i demand jako dwie niezależne opcje | US09 |
| D06 | Bez demandu nie przełączamy ogrzewania ON/OFF, także przez encję CO1 | US09, US19 |
| D07 | Jedna strefa Dom albo wiele stref; każda aktywna wymaga co najmniej termometru i celu | US01, US15 |
| D08 | Sterownik zaworów wymagany tylko po włączeniu ich sterowania; konfiguracja NC/NO | US05, US10 |
| D09 | Nowa konfiguracja zaczyna w obserwacji; użytkownik sam aktywuje algorytm | US03 |
| D10 | Krzywa A+B×(Tref−Ta); wszystkie trzy współczynniki konfigurowalne, outdoor wymagany dla CO1 | US17, US16 |
| D11 — doprecyzowane | Bieżące priorytety dotyczą stref. Wagi prognoz są odłożone do US21; nie mieszamy zewnętrznych celów komfortu | US18, US21 |
| D12 — częściowo zastąpione | Telemetria opcjonalna; prognozy odłożone do przyszłej wersji decyzją D45. PV nie jest bezpośrednim ciepłem domu | US16, US21 |
| D13 | CWU stale lub wg harmonogramu; 7 oddzielnych dni, krok 30 min, temperatura na przedział; harmonogram tylko CWU | US13, US14 |
| D14 | Zachować doświadczenia POC, ale nie kopiować bez oceny progów ani aktywnego auto STOP do produktu bez demandu | US06, US08, US19 |
| D15 — opis sprzętu | Referencja: 5 NC na parterze, 7 NC na piętrze. Inne pętle to sprzęt użytkownika, nie wejście algorytmu (D31) | US05, US10 |
| D16 | Git przechowuje treść wymagań; Issue — dyskusję i status. Sam PR dokumentacji nie zamyka funkcji | Indeks |
| D17 | Pierwsza wersja: jeden wspólny obieg i jedna nastawa PC dla wielu stref | US09, US15 |
| D18 | Strefy niezależne; grupy tylko porządkowe, bez własnego celu i dodatkowego udziału w regulacji | US01, US15 |
| D19 — doprecyzowane | Jeden lub kilka termometrów, główny albo średnia/mediana; domyślnie średnia, przed oknami czasowymi (D32) | US01, US15 |
| D20 | Każde wyjście zaworów należy do jednej strefy; wiele wyjść w strefie i przekaźnik grupowy dozwolone | US05, US15 |
| D21 | NC/NO osobno dla strefy, wspólne dla wszystkich jej wyjść; bez globalnego typu i wyjątków na wyjściach | US10 |
| D22 — zastąpione przez D31 | Historyczny wybór pola o otwartych pętlach usunięty: nie ma takiego modelu ani pola w programie | US05, US15 |
| D23 | Encja nastawy PC wymagana już przy konfiguracji obserwacji; minimum także outdoor i aktywna strefa z termometrem/celem | US03, US16 |
| D24 | Osobne przełączniki obserwacja/sterowanie dla CO i CWU | US03 |
| D25 | Ręczna zmiana celu CO to trwała nastawa konkretnej strefy, także po restarcie; brak harmonogramu CO | US02, US07, US11 |
| D26 | CWU: Wyłączone, Stałe i Harmonogram; przedział może wyłączać CWU | US13, US14 |
| D27 | Nadpisanie CWU działa po Zapisz do następnej rzeczywistej zmiany harmonogramu; identyczne pola 30 min go nie kasują | US07, US13, US14 |
| D28 | Ręczne włączenie CWU omija zaplanowaną przerwę do końca okresu; podpowiedź ostatniej temperatury z edycją przed zapisem | US07, US13 |
| D29 | Jeden panel i Zapisz tylko dla ustawień CWU; edycja robocza, walidacja całości, bez częściowego zapisu ustawień | US13, US14 |
| D30 | Zamknięcie panelu z niezapisanymi zmianami wymaga potwierdzenia odrzucenia; brak osobnego potwierdzenia Wyłączone | US13 |
| D31 | Brak modelu i pola stale otwartych pętli; ostrzeżenie hydrauliczne przy konfiguracji zaworów. Zastępuje D22 | US05, US09, US15 |
| D32 | Najpierw agregacja termometrów (średnia domyślna), potem funkcje/okna wspólne programu; progi reakcji dla stref | US01, US06 |
| D33 | Zawory: średnia 30 min; komfort: mediana 3 h. Wybór średnia/mediana, 30 min–6 h co 30 min | US05, US06, US17 |
| D34 | Trend zaworów: wspólna funkcja obu punktów, domyślnie średnie 30 min/4 h; niezależne czasy, zakresy i zakaz 2 h/2 h | US05, US06 |
| D35 | Próg trendu strefy ±0,2°C; rosnący zamyka od celu, malejący otwiera do celu, niejasny używa ±0,2°C | US05 |
| D36 | Po nagłym spadku potwierdzenie niedogrzania 30 min; po zamknięciu minimum 30 min do otwarcia; konfigurowalne dla stref i równoległe | US05, US06 |
| D37 | Priorytet stref 1–5, domyślnie 3; ważona średnia błędów; zamknięte wyjścia wyłączają strefę z korekty, nie z monitorowania | US18 |
| D38 | Strefa bez wyjść: blokada wzrostu CO1 przy +0,5°C/60 min, zwolnienie przy +0,2°C/30 min; progi/czasy dla stref | US17, US18 |
| D39 | Ostrzeżenie po czasie zamykania i 120 min zamknięcia, komfortu ≥cel+0,5°C i rosnącego trendu; bez przesądzania awarii | US05, US12 |
| D40 | Komfort: martwa strefa ±0,2°C, mnożnik 1,5 po jej odjęciu, limit komfortu ±2°C; osobny konfigurowalny limit sumy korekt domyślnie ±2°C | US17, US20 |
| D41 | Trend CO1: 12 h, wzrost 0,2–0,5°C daje liniowo 0 do −0,5°C, bez dodatniej korekty za sam spadek i tylko bez ważonego niedogrzania | US06, US17 |
| D42 | Zakres z ustawień PC, opcjonalnie zawężany; pełna precyzja i końcowa kwantyzacja, połówki w górę; domyślnie krok zmiany 1°C/120 min | US16, US17 |
| D43 | Demand OR: ON po gotowości jednej strefy, globalne otwieranie 3 min; OFF bez dodatkowej zwłoki; minimum przerwy OFF 15 min, bez minimum ON | US09, US10 |
| D44 | Cykl programu 5 min plus zmiany użytkownika; timery według terminów. Strojenie w osobnej konfiguracji zaawansowanej | US12, US17 |
| D45 | Prognozy odłożone do kolejnej wersji; wymagania zachowane. Od początku modułowe korekty, wybór aktywnych modułów i zawsze obowiązujące ograniczenia | US20, US21 |

D24–D30 uzgodniono w [rundzie 2](round-02-daily-operation.md) 10 listopada 2026. D26 rozszerza D13 o jawny tryb Wyłączone; D27–D28 odrzucają błędną interpretację, że harmonogram blokuje ręczne włączenie. D29 dotyczy spójności zapisu ustawień, nie transakcji sprzętowej pompy.

Decyzje D17–D23 przyjęto 10 listopada 2026 w [rundzie 1](round-01-installation-zones.md), aktualizacja w [PR #27](https://github.com/marcin-bugala/ha-HeatPumpSteering/pull/27). D21 doprecyzowuje D08; nie przyjęto proponowanego wariantu globalnego NC/NO z wyjątkami na wyjściach.

Wczesne propozycje zaworów na całych rozdzielaczach, 16 siłowników NO i dokładnej krzywej producenta nie są aktualną konfiguracją referencyjną. Wczesna deklaracja pełnej niezależności modułów wymaga doprecyzowania w świetle późniejszego wymogu stałej podstawy CO1.

## Domyślne parametry przyjęte w rundzie 3

Wartości liczbowe opisano w [rundzie 3](round-03-regulation.md). Są przyjętymi ustawieniami początkowymi do późniejszej walidacji, nie gwarancją optymalnego strojenia wszystkich budynków. W konfiguracji zaawansowanej można zmienić wskazane parametry.

Nadal propozycjami pozostają domena heat_pump_steering, szczegóły F01 i architektury oraz zaawansowane prognozowanie z POC. Raportowane przez urządzenie limity są nadrzędne; nie kopiujemy stałego minimum/maksimum POC.

## Otwarte decyzje blokujące pełną specyfikację

| ID | Pytanie | Gdzie doprecyzować |
| --- | --- | --- |
| Q01 — częściowo rozstrzygnięte | D24: osobne przełączniki CO/CWU. Pozostaje F01 i odtwarzanie trybów po restarcie | US03, US13 |
| Q02 — częściowo rozstrzygnięte | Agregacja i funkcje/okna ustalone w rundzie 3; pozostają jakość/świeżość i częściowa niedostępność termometrów | US01; runda awarii |
| Q03 — częściowo rozstrzygnięte | NC/NO na strefę; czas otwierania globalnie 3 min. Pozostają logika odwrócona, zamykanie i potwierdzenia | US05, US10; runda awarii |
| Q04 — reguły rozstrzygnięte | Ważony błąd i ochrona opisane w rundzie 3; nie modelujemy otwartych pętli. Pozostaje brak kwalifikujących się stref i przerwy danych | US17–US19; runda awarii |
| Q05 | Próg świeżości i jakość każdego źródła, luki oraz reakcje wyjść na awarie | US05, US16, US19 |
| Q06 — częściowo rozstrzygnięte | D25: trwały cel CO; D27–D28: CWU do kolejnej zmiany harmonogramu. Pozostają zmiany spoza panelu, demand, restart i przypadki brzegowe | US07, US13, US14 |
| Q07 | Opcjonalność i wydanie CWU; harmonogram po restarcie, zmiana czasu, higiena | US13, US14 |
| Q08 — częściowo rozstrzygnięte | OR, sekwencja i timery D43 przyjęte; pozostały profil/polaryzacja, dowody wykonania, restart i awarie | US09 |
| Q09 | Potwierdzenie świeżego odczytu HiMitII i zakresów realnego urządzenia | US04, US17, US19 |
| Q10 — odłożone | Brak prognoz w bieżącej wersji. Algorytm/adaptery, jakość, archiwizacja i uczenie wrócą przed przyszłym wydaniem | US21 |
| Q11 — częściowo rozstrzygnięte | D29–D30: wspólny zapis panelu CWU i potwierdzenie odrzucenia. Technologia UI, encje, historia i eksport nadal otwarte | US04, US11–US14 |
| Q12 | Minimalna wersja HA, domena, obsługiwane wersje integracji źródłowych i migracja | US08, US19 |
| Q13 | Czy F01 może działać samodzielnie, bez konfiguracji regulatora CO1? | E05 |
| Q14 | Kalibracja F01, faktyczna praca PC, temperatura/histereza, powrót i awarie | E05 |

Otwarte pytania nie są poleceniem dobrania domyślnych wartości podczas implementacji. Rozstrzygamy je wspólnie przed kodowaniem danego zakresu.

## Rozstrzygnięcia rundy 1

Nie ma już otwartego pytania o dopuszczenie konfiguracji bez encji nastawy PC: D23 wymaga jej wskazania również dla obserwacji. Późniejsza niedostępność źródła jest innym zagadnieniem, do rundy awarii. Zamknięcie rundy modelu nie oznacza zakończenia wszystkich powiązanych user stories.

## Rozstrzygnięcia rundy 2

Runda codziennej obsługi uzgodniona. Tryb CWU Wyłączone nie jest trybem obserwacji: pierwszy opisuje żądany stan CWU, drugi zezwolenie integracji na wykonywanie poleceń. W obserwacji zapis ustawień nie uruchamia CWU.

Nie wprowadzamy harmonogramu CO ani tymczasowych celów pokojowych. Trwałe cele CO, dwa przełączniki CO/CWU i panel ustawień CWU są odrębnymi elementami obsługi.

## Rozstrzygnięcia rundy 3

D31–D45 przyjęto 10 listopada 2026. Aktualny, szczegółowy zapis: [runda 3](round-03-regulation.md). Wczesne propozycje niezależnej funkcji dla obu punktów trendu, mediany jako domyślnej agregacji termometrów oraz czasu otwierania na strefę zostały skorygowane przez użytkownika. Właściwe są: wspólna funkcja punktów trendu, średnia agregacji termometrów i wspólny czas otwierania.

D31 usuwa model otwartych pętli i zastępuje D22. Zawory są oceniane według przypisanych wyjść; bez sprzężenia zwrotnego nie stwierdzamy fizycznego odcięcia. D45 odkłada prognozy, lecz wymaga modularności kodu już w bieżącej wersji. Nie ma jeszcze implementacji.

## Jak aktualizować

Nową decyzję dopisujemy z datą i powiązanym Issue/PR. Zmiana decyzji wskazuje zastąpiony zapis; nie przepisujemy historii bez wyjaśnienia. Przy zamykaniu pytań aktualizujemy również produkt i odpowiednie user stories.

Źródła: rozmowy wymagań oraz [projekt prognoz POC](https://github.com/marcin-bugala/ha-HeatPumpSteering/blob/poc/co1-automation/docs/full-integration-forecast.md). Materiał POC jest źródłem propozycji i doświadczeń, nie automatycznym zatwierdzeniem rozszerzonego zakresu.
