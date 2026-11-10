# Rejestr decyzji i pytań

Stan: 10 listopada 2026. „Przyjęte” oznacza potwierdzony kierunek produktu; nie oznacza implementacji ani zatwierdzenia wszystkich parametrów. Status realizacji historii znajduje się w Issues.

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
| D11 | Wagi dotyczą stref i korekt prognoz, nie mieszania zewnętrznych celów komfortu | US18 |
| D12 | Prognozy i dodatkowa telemetria opcjonalne; PV nie jest bezpośrednim ciepłem domu | US16, US18 |
| D13 | CWU stale lub wg harmonogramu; 7 oddzielnych dni, krok 30 min, temperatura na przedział; harmonogram tylko CWU | US13, US14 |
| D14 | Zachować doświadczenia POC, ale nie kopiować bez oceny progów ani aktywnego auto STOP do produktu bez demandu | US06, US08, US19 |
| D15 | Konfiguracja referencyjna: 5 NC na parterze, 7 NC na piętrze; inne pętle bez siłowników z ręcznym ograniczeniem do 1 l/min | US05, US10 |
| D16 | Git przechowuje treść wymagań; Issue — dyskusję i status. Sam PR dokumentacji nie zamyka funkcji | Indeks |

Wczesne propozycje zaworów na całych rozdzielaczach, 16 siłowników NO i dokładnej krzywej producenta nie są aktualną konfiguracją referencyjną. Wczesna deklaracja pełnej niezależności modułów wymaga doprecyzowania w świetle późniejszego wymogu stałej podstawy CO1.

## Propozycje do walidacji, nie przyjęte parametry produkcyjne

- A=20°C, B=0,2, Tref=20°C, średnia outdoor 2 h.
- Szybki sygnał 5–10 min, filtr komfortu 3–6 h, trend 12–24 h.
- Martwa strefa ±0,2°C, korekta ±2°C, krok 1°C co około 120 min.
- OR zapotrzebowań aktywnych stref jako początek projektu demandu, z jawną niepewnością.
- Połączenie timerów F01 przez późniejszy termin 30 min od startu lub 20 min od stopu.
- heat_pump_steering jako domena integracji.
- Zaawansowane prognozowanie i uczenie z dokumentu POC — osobny zakres do oceny.

Wartości POC, w tym minimum raportowane przez encję 20°C i limit POC 35°C, nie stają się globalnymi limitami wszystkich pomp.

## Otwarte decyzje blokujące pełną specyfikację

| ID | Pytanie | Gdzie doprecyzować |
| --- | --- | --- |
| Q01 | Czy obserwacja/aktywacja obejmuje CWU i F01? Jak odtwarzać tryb po restarcie? | US03, US13 |
| Q02 | Hierarchia dom/kondygnacje/pokoje, wiele termometrów i współdzielone wyjścia | US01, US15 |
| Q03 | NC/NO globalnie, na strefę czy na wyjście; logika odwrócona i czasy ruchu | US05, US10 |
| Q04 | Agregacja komfortu, normalizacja wag, priorytet przegrzania, wpływ pętli niesterowanych | US17–US19 |
| Q05 | Próg świeżości i jakość każdego źródła, luki oraz reakcje wyjść na awarie | US05, US16, US19 |
| Q06 | Pierwszeństwo ręcznej zmiany, czas nadpisania, powrót do automatyki | US07, US13, US14 |
| Q07 | Opcjonalność i wydanie CWU; harmonogram po restarcie, zmiana czasu, higiena | US13, US14 |
| Q08 | Fizyczny/logiczy demand, polaryzacja, timery, potwierdzenia i sekwencje | US09 |
| Q09 | Potwierdzenie świeżego odczytu HiMitII i zakresów realnego urządzenia | US04, US17, US19 |
| Q10 | Profile prognoz, zakres v1, ograniczenia korekt, archiwizacja, ewentualne uczenie | US16, US18 |
| Q11 | Encje climate/number, rodzaj dashboardu, historia decyzji i eksport | US04, US11, US12 |
| Q12 | Minimalna wersja HA, domena, obsługiwane wersje integracji źródłowych i migracja | US08, US19 |
| Q13 | Czy F01 może działać samodzielnie, bez konfiguracji regulatora CO1? | E05 |
| Q14 | Kalibracja F01, faktyczna praca PC, temperatura/histereza, powrót i awarie | E05 |

Otwarte pytania nie są poleceniem dobrania domyślnych wartości podczas implementacji. Rozstrzygamy je wspólnie przed kodowaniem danego zakresu.

## Jak aktualizować

Nową decyzję dopisujemy z datą i powiązanym Issue/PR. Zmiana decyzji wskazuje zastąpiony zapis; nie przepisujemy historii bez wyjaśnienia. Przy zamykaniu pytań aktualizujemy również produkt i odpowiednie user stories.

Źródła: rozmowy wymagań oraz [projekt prognoz POC](https://github.com/marcin-bugala/ha-HeatPumpSteering/blob/poc/co1-automation/docs/full-integration-forecast.md). Materiał POC jest źródłem propozycji i doświadczeń, nie automatycznym zatwierdzeniem rozszerzonego zakresu.
