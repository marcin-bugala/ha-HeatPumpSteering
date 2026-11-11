# Rejestr decyzji i pytań

Stan: 11 listopada 2026, po rundach 1–6. „Przyjęte” oznacza potwierdzony kierunek produktu; nie oznacza implementacji ani zatwierdzenia wszystkich parametrów. Status realizacji historii znajduje się w Issues.

## Przyjęte decyzje

| ID | Decyzja | Powiązania |
| --- | --- | --- |
| D01 | Publiczna custom integration HA, repozytorium ha-HeatPumpSteering, PL/EN i planowana dystrybucja HACS | Produkt, etapy |
| D02 | main dla produktu; poc/co1-automation dla POC; osobne gałęzie i PR-y do main | US08 |
| D03 | Produkt uniwersalny przez encje HA; Hisense/HiMitII pierwszy profil referencyjny | US16, US19 |
| D04 — zastąpione przez D76 | Pierwsza publiczna wersja testowa: CO1 i strefy; F01 później | Etapy |
| D05 — zastąpione przez D69 | Regulacja nastawy PC zawsze podstawą; zawory stref i demand jako dwie niezależne opcje | US09 |
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
| D23 — zawężone przez D69 | Encja nastawy PC wymagana już przy konfiguracji obserwacji; minimum także outdoor i aktywna strefa z termometrem/celem | US03, US16 |
| D24 | Osobne przełączniki obserwacja/sterowanie dla CO i CWU | US03 |
| D25 | Ręczna zmiana celu CO to trwała nastawa konkretnej strefy, także po restarcie; brak harmonogramu CO | US02, US07, US11 |
| D26 | CWU: Wyłączone, Stałe i Harmonogram; przedział może wyłączać CWU | US13, US14 |
| D27 — doprecyzowane | Nadpisanie CWU z zewnętrznej zmiany trwa do kolejnej rzeczywistej zmiany planu lub zapisu panelu w Harmonogram. Identyczne pola 30 min nie kasują go | US07, US13, US14 |
| D28 — częściowo zastąpione | Zewnętrzne ręczne włączenie może ominąć przerwę planu. Układ pól panelu ustala D62, bez edycji ręcznej temperatury w Harmonogram | US07, US13 |
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
| D46 | Utrata części termometrów pozwala pracować na pozostałych. Skok po zmianie zestawu nie jest nagłym spadkiem | US01, US06 |
| D47 | Świeżość raportów 120 min wnętrza i 30 min outdoor. Gotowość okna 80% pokrycia i świeży bieżący pomiar | US16, US19 |
| D48 | Brak wszystkich termometrów strefy: 30 min zachowania żądań, następnie awaryjne otwarcie bez własnego demandu i korekty pokojowej | US05, US09 |
| D49 | Brak wszystkich temperatur stref: krzywa z outdoor i OFF demandu po okresie przejściowym. Wszystkie strefy zamknięte przy poprawnych pomiarach: utrzymanie CO1 | US09, US17, US18 |
| D50 | Brak outdoor, aktualnej nastawy lub zakresu PC blokuje odpowiednie zapisy CO1. Pozostałe poprawne moduły działają | US16, US17 |
| D51 | Niepotwierdzone otwarcie zaworów nie wystarcza do ON demandu. Przerwę demandu liczymy od raportowanego potwierdzonego OFF | US05, US09, US10 |
| D52 | Trzy próby zapisu łącznie, potem błąd i odstępy Fibonacciego do 120 min. Licznik osobno dla wyjścia | US04, US09, US13, US17, US19 |
| D53 | Odbudowa pomiarów, filtrów i trendów przy uruchomieniu z dostępnej historii, domyślnie 48 h | US03, US19 |
| D54 | Po restarcie odtwarzamy zapisane tryby CO/CWU, pamięć i terminy. Sterowanie podejmuje bieżącą decyzję po sprawdzeniu gotowości | US03, US19 |
| D55 | Blokady czasowe mogą upływać w przerwie przy wiarygodnym stanie. Potwierdzenia temperatury liczą poprawną obserwację | US05, US09, US17, US19 |
| D56 | CWU po restarcie zachowuje ważne nadpisanie lub stosuje aktualny przedział. Temperaturę potwierdzamy przed ON, OFF wysyłamy niezależnie | US13, US14 |
| D57 | Nagły spadek względem temperatury komfortowej przekracza domyślnie 0,7°C. Próg strefy | US06 |
| D58 | Bez poprzedniego żądania w strefie między progami zachowujemy odczytany stan i czekamy na warunek otwarcia przed zgłoszeniem zapotrzebowania | US05, US09 |
| D59 | Przy gotowym pomiarze do zaworów i braku gotowego trendu używamy progów niejasnego trendu z komunikatem o brakujących danych | US05, US19 |
| D60 | Czas potwierdzenia zapisu domyślnie 2 min, wspólny i konfigurowalny. Odstęp ponowienia od wysłania poprzedniej próby | US04, US17, US19 |
| D61 | Ręczna zmiana nastawy wody na pompie pozostawia regulator aktywny, bez dodatkowej pauzy. Kolejny dozwolony zapis realizuje bieżący wynik | US07, US17 |
| D62 | CWU Wyłączone blokuje temperaturę i plan, Stałe udostępnia temperaturę, Harmonogram udostępnia plan | US13 |
| D63 | Zapis panelu w Harmonogram natychmiast stosuje aktualny przedział i kończy nadpisanie, także przy identycznym planie | US07, US13, US14 |
| D64 | Nadpisania spoza panelu przy stałym planie tygodniowym trwają do ręcznej zmiany lub zapisu panelu w Harmonogram | US07, US13, US14 |
| D65 | Harmonogram według strefy HA, pominięte pola przy przeskoku, powtórzone pola przy cofnięciu. Timery według rzeczywistego upływu | US14, US19 |
| D66 | Jeden globalny „Czas pracy siłowników”, domyślnie 3 min, obejmuje otwieranie i zamykanie oraz start oceny ostrzeżenia | US05, US09, US10 |
| D67 | Scenariusze A01–A59 obejmują US01–US21 jako kryteria przyszłego odbioru | Wszystkie historie |

| D68 | Odczyty i polecenia przez encje HA; transport zapewniają integracje urządzeń | US16 |
| D69 | CO i CWU niezależnie opcjonalne: samo CO, samo CWU lub oba. Wymagania nastawy CO1/outdoor/stref dotyczą wyłącznie CO; zastępuje ogólne D05 i zawęża D23 | US03, US09, US13, US16 |
| D70 | Pierwsza konfiguracja: jedna pompa, maks. jeden CO i jedno CWU. Architektura przewiduje przyszłe dwa CO z osobnymi strefami, nastawami i Demand 1/2 | US09, US20 |
| D71 | Konfiguracja HA + Store dla potrzebnego stanu + Recorder dla historii + okna w pamięci; bez dodatkowej bazy | US08, US19 |
| D72 | Aktualizacja musi zachować dane, tożsamość encji i ciągłość stanu; retencja HA obowiązuje, restart jest przerwą wykonania | US02, US08, US19 |
| D73 | Wyłączenie/usunięcie zatrzymuje polecenia i ponowienia bez zmiany ostatniego stanu urządzeń | US03, US09 |
| D74 | Ponowne włączenie modułu zachowuje ustawienia, lecz zaczyna w obserwacji. Restart/aktualizacja przywraca zapisany tryb | US03 |
| D75 | POC osobny, bez wymaganego importera i migracji produktu; doświadczenia są materiałem testowym | US08, US19 |
| D76 | Pierwsze kompletne wydanie developerskie: CO, strefy, opcjonalne zawory/demand i CWU z planem. Zastępuje etapowy zakres D04 | US09, US13, etapy |
| D77 | Prognozy i skropliny później; skropliny wstępnie kolejne. Odbiór wymaga testów, wyników na instalacji i jawnego zakresu symulacji | US19, US21, E05 |
| D78 | HACS custom repo i ręcznie, wersje testowe wybierane przez użytkownika; domyślny katalog po stabilizacji | Etapy |
| D79 | Pełny interfejs/komunikaty i instrukcje instalacji/konfiguracji PL/EN od pierwszego wydania | US11–US14 |
| D80 | Minimum HA ustalimy przed implementacją; wydanie podaje minimum, sprawdzone wersje i jawne podniesienia wymagań | US08 |
| D81 | Encje do własnych dashboardów, karta, panel CWU i osobna konfiguracja zaawansowana dostarczane razem z produktem | US11–US14 |
| D82 | Eksport diagnostyki na żądanie z anonimizacją nazw/encji, bez sekretów i automatycznej wysyłki | US04, US12 |
| D83 | Ostrzeżenie ustępuje po przyczynie i warunkach powrotu; przeczytanie nie usuwa problemu/blokady. Zachowujemy historię wystąpienia/ustąpienia | US04, US05 |
| D84 | Walidacja zmienianej konfiguracji, anulowanie nieaktualnych poleceń, zachowanie pasujących danych i odbudowa okien nowego czujnika | US01, US16 |
| D85 | Trwała tożsamość stref niezależna od nazwy/grupy/czujnika; usunięcie i ponowne dodanie tworzy nową | US01, US02 |
| D86 | Przed odłączeniem wyjścia/usunięciem strefy pokazujemy stan i ostrzeżenie o pozostawieniu; anulujemy polecenia | US01, US09 |
| D87 | Blokada współdzielenia encji wykonawczych między funkcjami/konfiguracjami; czujniki mogą być wspólne. Wycofano propozycję zaworu współdzielonego | US09, US15 |
| D88 | Awaria ogranicza działania zależne, sprawne moduły pozostają aktywne | US12, US13, US16 |
| D89 | Powrót tylko ze zgodnymi danymi; niezgodność daje błąd bez resetu/sterowania, instrukcja wymaga właściwej kopii HA | US08 |

D24–D30 uzgodniono w [rundzie 2](round-02-daily-operation.md) 10 listopada 2026. D26 rozszerza D13 o jawny tryb Wyłączone; D27–D28 odrzucają błędną interpretację, że harmonogram blokuje ręczne włączenie. D29 dotyczy spójności zapisu ustawień, nie transakcji sprzętowej pompy.

Decyzje D17–D23 przyjęto 10 listopada 2026 w [rundzie 1](round-01-installation-zones.md), aktualizacja w [PR #27](https://github.com/marcin-bugala/ha-HeatPumpSteering/pull/27). D21 doprecyzowuje D08; nie przyjęto proponowanego wariantu globalnego NC/NO z wyjątkami na wyjściach.

Wczesne propozycje zaworów na całych rozdzielaczach, 16 siłowników NO i dokładnej krzywej producenta nie są aktualną konfiguracją referencyjną. D69 ustala niezależność CO/CWU; wymóg nastawy CO1 obowiązuje tylko przy module CO.

## Domyślne parametry przyjęte w rundzie 3

Wartości liczbowe opisano w [rundzie 3](round-03-regulation.md). Są przyjętymi ustawieniami początkowymi do późniejszej walidacji, nie gwarancją optymalnego strojenia wszystkich budynków. W konfiguracji zaawansowanej można zmienić wskazane parametry.

Nadal propozycjami pozostają domena heat_pump_steering, szczegóły F01 i architektury oraz zaawansowane prognozowanie z POC. Raportowane przez urządzenie limity są nadrzędne; nie kopiujemy stałego minimum/maksimum POC.

## Otwarte decyzje blokujące pełną specyfikację

| ID | Pytanie | Gdzie doprecyzować |
| --- | --- | --- |
| Q01 — doprecyzowane | D54 ustala odtworzenie trybów CO/CWU. Zakres F01 pozostaje otwarty | US03, US13 |
| Q02 — doprecyzowane | D46–D47 określają częściową dostępność i świeżość. Techniczne źródło czasu raportu pozostaje do określenia | US01, US16 |
| Q03 — doprecyzowane | NC/NO na strefę i wspólny czas pracy siłowników określone. Pozostają logika odwrócona i techniczne potwierdzenie | US05, US10 |
| Q04 — doprecyzowane | D49 rozróżnia wszystkie strefy zamknięte i utratę temperatur wszystkich stref. Reguły ważenia pozostają w rundzie 3 | US17–US19 |
| Q05 — doprecyzowane | Reguły braków danych, gotowości i restartów są w rundzie 4. Pozostaje sposób pozyskania i oceny historii źródeł | US05, US16, US19 |
| Q06 — doprecyzowane | Ręczne zmiany CO1 i CWU, zapis panelu oraz nadpisanie bez następnej zmiany określono w rundzie 5. Pozostają źródła wykrywania i ręczny demand | US07, US13, US14 |
| Q07 — doprecyzowane | Panel, nadpisania, zmiana czasu i restart ustalone. D69 i D76 rozstrzygają opcjonalność i wydanie; pozostają inicjalizacja i higiena | US13, US14 |
| Q08 — doprecyzowane | D51 i D55 ustalają raportowany OFF oraz odtworzenie blokady. Pozostają profil/polaryzacja i techniczny dowód raportu | US09 |
| Q09 — doprecyzowane | Domyślne potwierdzenie 2 min i polityka ponowień przyjęte. Pozostaje techniczne źródło niezależnego odczytu | US04, US17, US19 |
| Q10 — odłożone | Brak prognoz w bieżącej wersji. Algorytm/adaptery, jakość, archiwizacja i uczenie wrócą przed przyszłym wydaniem | US21 |
| Q11 — częściowo rozstrzygnięte | D29–D30: wspólny zapis panelu CWU i potwierdzenie odrzucenia. D71, D81 i D82 ustalają historię, dostarczenie UI i eksport; technologia oraz platformy encji wymagają projektu | US04, US11–US14 |
| Q12 — doprecyzowane | D71–D80 i D89 ustalają trwałość, aktualizacje i wycofanie. Minimum HA, domena i macierz zgodności pozostają do projektu technicznego | US08, US19 |
| Q13 | Czy F01 może działać samodzielnie, bez konfiguracji regulatora CO1? | E05 |
| Q14 | Kalibracja F01, faktyczna praca PC, temperatura/histereza, powrót i awarie | E05 |

Otwarte pytania nie są poleceniem dobrania domyślnych wartości podczas implementacji. Rozstrzygamy je wspólnie przed kodowaniem danego zakresu.

## Rozstrzygnięcia rundy 1

D23 wymaga nastawy CO1 również dla obserwacji modułu CO; D69 w rundzie 6 dopuszcza konfigurację tylko CWU bez encji CO1. Późniejsza niedostępność źródła jest innym zagadnieniem, do rundy awarii. Zamknięcie rundy modelu nie oznacza zakończenia wszystkich powiązanych user stories.

## Rozstrzygnięcia rundy 2

Runda codziennej obsługi uzgodniona. Tryb CWU Wyłączone nie jest trybem obserwacji: pierwszy opisuje żądany stan CWU, drugi zezwolenie integracji na wykonywanie poleceń. W obserwacji zapis ustawień nie uruchamia CWU.

Nie wprowadzamy harmonogramu CO ani tymczasowych celów pokojowych. Trwałe cele CO, dwa przełączniki CO/CWU i panel ustawień CWU są odrębnymi elementami obsługi.

## Rozstrzygnięcia rundy 3

D31–D45 przyjęto 10 listopada 2026. Aktualny, szczegółowy zapis: [runda 3](round-03-regulation.md). Wczesne propozycje niezależnej funkcji dla obu punktów trendu, mediany jako domyślnej agregacji termometrów oraz czasu otwierania na strefę zostały skorygowane przez użytkownika. Właściwe są: wspólna funkcja punktów trendu, średnia agregacji termometrów i wspólny czas otwierania.

D31 usuwa model otwartych pętli i zastępuje D22. Zawory są oceniane według przypisanych wyjść; bez sprzężenia zwrotnego nie stwierdzamy fizycznego odcięcia. D45 odkłada prognozy, lecz wymaga modularności kodu już w bieżącej wersji. Nie ma jeszcze implementacji.

## Rozstrzygnięcia rundy 4

D46–D59 zapisano w [rundzie 4](round-04-failures-restarts.md). Polityka trzech prób i narastających odstępów zastępuje wcześniejszą propozycję sześciu prób oraz stałe ponawianie co 5 min. Czas oczekiwania na potwierdzenie został doprecyzowany przez D60 w rundzie 5.

## Rozstrzygnięcia rundy 5

D60–D67 przyjęto 11 listopada 2026. [Zapis i tabela odbioru](round-05-acceptance.md) doprecyzowują panel CWU, pierwszeństwo zapisu harmonogramu oraz nadpisania zewnętrzne. Zastąpiona jest propozycja osobnego czasu zamykania. Wspólny parametr obejmuje oba kierunki ruchu.

## Rozstrzygnięcia rundy 6

D68–D89 przyjęto 11 listopada 2026. [Pełny zapis i kryteria B01–B13](round-06-architecture.md). Runda zamknięta na poziomie produktu; projekt techniczny nadal wymagany przed kodowaniem. CWU może działać bez CO, a kompletne pierwsze wydanie obejmuje opcjonalny demand i CWU. POC nie jest wymogiem użytkownika produktu. Wycofana propozycja współdzielenia zaworu nie obowiązuje; obowiązuje blokada.

## Jak aktualizować

Nową decyzję dopisujemy z datą i powiązanym Issue/PR. Zmiana decyzji wskazuje zastąpiony zapis; nie przepisujemy historii bez wyjaśnienia. Przy zamykaniu pytań aktualizujemy również produkt i odpowiednie user stories.

Źródła: rozmowy wymagań oraz [projekt prognoz POC](https://github.com/marcin-bugala/ha-HeatPumpSteering/blob/poc/co1-automation/docs/full-integration-forecast.md). Materiał POC jest źródłem propozycji i doświadczeń, nie automatycznym zatwierdzeniem rozszerzonego zakresu.
