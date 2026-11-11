# Rejestr decyzji i pytań

Stan: 11 listopada 2026, po rundach 1–6 i rozstrzygnięciach P01–P12 w PR #36. „Przyjęte” oznacza potwierdzony kierunek produktu; nie oznacza implementacji ani zatwierdzenia wszystkich parametrów. Status realizacji historii znajduje się w Issues.

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
| D42 — wyjątek D99 | Zakres z ustawień PC, opcjonalnie zawężany; pełna precyzja i końcowa kwantyzacja, połówki w górę; domyślnie krok zmiany 1°C/120 min | US16, US17 |
| D43 | Demand OR: ON po gotowości jednej strefy, globalne otwieranie 3 min; OFF bez dodatkowej zwłoki; minimum przerwy OFF 15 min, bez minimum ON | US09, US10 |
| D44 | Cykl programu 5 min plus zmiany użytkownika; timery według terminów. Strojenie w osobnej konfiguracji zaawansowanej | US12, US17 |
| D45 | Prognozy odłożone do kolejnej wersji; wymagania zachowane. Od początku modułowe korekty, wybór aktywnych modułów i zawsze obowiązujące ograniczenia | US20, US21 |
| D46 | Utrata części termometrów pozwala pracować na pozostałych. Skok po zmianie zestawu nie jest nagłym spadkiem | US01, US06 |
| D47 | Świeżość raportów 120 min wnętrza i 30 min outdoor. Gotowość okna 80% pokrycia i świeży bieżący pomiar | US16, US19 |
| D48 | Brak wszystkich termometrów strefy: 30 min zachowania żądań, następnie awaryjne otwarcie bez własnego demandu i korekty pokojowej | US05, US09 |
| D49 | Brak wszystkich temperatur stref: krzywa z outdoor i OFF demandu po okresie przejściowym. Wszystkie strefy zamknięte przy poprawnych pomiarach: utrzymanie CO1 | US09, US17, US18 |
| D50 | Brak outdoor, aktualnej nastawy lub zakresu PC blokuje odpowiednie zapisy CO1. Pozostałe poprawne moduły działają | US16, US17 |
| D51 — doprecyzowane D90 | Niepotwierdzone otwarcie zaworów nie wystarcza do ON demandu. Przerwę demandu liczymy od raportowanego potwierdzonego OFF | US05, US09, US10 |
| D52 | Trzy próby zapisu łącznie, potem błąd i odstępy Fibonacciego do 120 min. Licznik osobno dla wyjścia | US04, US09, US13, US17, US19 |
| D53 | Odbudowa pomiarów, filtrów i trendów przy uruchomieniu z dostępnej historii, domyślnie 48 h | US03, US19 |
| D54 | Po restarcie odtwarzamy zapisane tryby CO/CWU, pamięć i terminy. Sterowanie podejmuje bieżącą decyzję po sprawdzeniu gotowości | US03, US19 |
| D55 | Blokady czasowe mogą upływać w przerwie przy wiarygodnym stanie. Potwierdzenia temperatury liczą poprawną obserwację | US05, US09, US17, US19 |
| D56 — doprecyzowane D90 | CWU po restarcie zachowuje ważne nadpisanie lub stosuje aktualny przedział. Temperaturę potwierdzamy przed ON, OFF wysyłamy niezależnie | US13, US14 |
| D57 | Nagły spadek względem temperatury komfortowej przekracza domyślnie 0,7°C. Próg strefy | US06 |
| D58 | Bez poprzedniego żądania w strefie między progami zachowujemy odczytany stan i czekamy na warunek otwarcia przed zgłoszeniem zapotrzebowania | US05, US09 |
| D59 | Przy gotowym pomiarze do zaworów i braku gotowego trendu używamy progów niejasnego trendu z komunikatem o brakujących danych | US05, US19 |
| D60 — doprecyzowane D90 | Czas potwierdzenia zapisu domyślnie 2 min, wspólny i konfigurowalny. Odstęp ponowienia od wysłania poprzedniej próby | US04, US17, US19 |
| D61 | Ręczna zmiana nastawy wody na pompie pozostawia regulator aktywny, bez dodatkowej pauzy. Kolejny dozwolony zapis realizuje bieżący wynik | US07, US17 |
| D62 | CWU Wyłączone blokuje temperaturę i plan, Stałe udostępnia temperaturę, Harmonogram udostępnia plan | US13 |
| D63 | Zapis panelu w Harmonogram natychmiast stosuje aktualny przedział i kończy nadpisanie, także przy identycznym planie | US07, US13, US14 |
| D64 | Nadpisania spoza panelu przy stałym planie tygodniowym trwają do ręcznej zmiany lub zapisu panelu w Harmonogram | US07, US13, US14 |
| D65 | Harmonogram według strefy HA, pominięte pola przy przeskoku, powtórzone pola przy cofnięciu. Timery według rzeczywistego upływu | US14, US19 |
| D66 | Jeden globalny „Czas pracy siłowników”, domyślnie 3 min, obejmuje otwieranie i zamykanie oraz start oceny ostrzeżenia | US05, US09, US10 |
| D67 | Scenariusze A01–A59 obejmują US01–US21 jako kryteria przyszłego odbioru | Wszystkie historie |

| D68 — doprecyzowane D90 | Odczyty i polecenia przez encje HA; transport zapewniają integracje urządzeń | US16 |
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

## Przyjęte rozstrzygnięcia P01–P12 — 11 listopada 2026

| ID | Decyzja | Powiązania |
| --- | --- | --- |
| D90 | Potwierdzenie operacyjne jest dwuetapowe: po zapisie zgodny odczyt tej samej encji HA daje potwierdzenie wstępne; ponowny poprawny, zgodny odczyt po domyślnie 2 min daje potwierdzenie ostateczne i kończy serię ponowień. Nie wymagamy drugiej encji, dowodu nowego raportu transportowego ani fizycznego wykonania. Doprecyzowuje D51/D56/D60/D68 i zastępuje wymóg niezależnego dowodu jako warunku aktywacji. | P01; US03–US05, US09–US10, US13, US16–US19 |
| D91 | Każda zmiana ustawienia CWU niewynikająca z działania naszego algorytmu jest external i ma reguły zmiany użytkownika D27/D63/D64. Nie ma kategorii ambiguous ani blokady zapisów z powodu nieustalonego pochodzenia. | P02; US07, US13–US14 |
| D92 | Ręczna zmiana demandu nie zatrzymuje regulatora: następna dozwolona ocena uzgadnia bieżące zapotrzebowanie. Trwałe oddanie kontroli przez obserwację CO. OFF nie resetuje liczników błędów ani terminów ponowień; brak dodatkowej zwłoki logicznej nie obchodzi polityki retry. | P03; US07, US09 |
| D93 | Jawna polaryzacja każdego bindingu wyjścia jest niezależna od wspólnego dla strefy NC/NO. Zmiana mapowania nie wysyła sama polecenia. | P04; US05, US09–US10 |
| D94 | Produkt nie obsługuje higieny CWU: bez wykrywania, dedykowanych encji, blokad i warunku aktywacji. Higiena pozostaje po stronie pompy. Zmiany nastaw niewynikające z naszego algorytmu są external według D91. | P05; US13, US19 |
| D95 | CWU bez wcześniejszych nastaw zaczyna jako Nieskonfigurowane; użytkownik jawnie podaje temperaturę Stałe/ON i zatwierdza cały plan. Szkic 7×48 OFF nie jest zapisanym planem i nie powoduje OFF urządzenia. Kopiowanie dni dotyczy draft. | P06; US13–US14 |
| D96 | Cel strefy 5–35°C co 0,5°C, początkowo podany przez użytkownika. Zmiana celu zeruje zależne potwierdzenia temperatury, zachowuje terminy zamknięcia i demandu oraz historię pomiarów. | P07; US02, US05–US06, US11, US18 |
| D97 | Niepewna historia pozostaje luką; nie przedłużamy ważności poza świeżość i nie odtwarzamy heartbeat z niezmiennych stanów Recordera. Mediana jest ważona czasem; dokładne 50% między wartościami daje średnią dwóch środkowych. | P08; US01, US06, US16, US19 |
| D98 | Przypadek mieszany bez stref kwalifikowanych do korekty: baza outdoor bez korekt pokojowych, z pozostałymi blokadami. Nadal wszystkie poprawne zamknięte → utrzymanie nastawy; wszystkie utracone po grace → baza i wycofanie demandu. | P09; US17–US18 |
| D99 | Gdy bieżąca nastawa jest poza obowiązującym zakresem, obcinamy ją do najbliższej dopuszczalnej granicy i oznaczamy konflikt. Korekta graniczna ma pierwszeństwo przed zwykłym limitem kroku/odstępu i blokadą wzrostu utrzymującą wartość poza zakresem; nie wyłącza obserwacji ani walidacji wyjścia i retry. Doprecyzowuje wyjątek od D42; nie blokujemy korekty samym konfliktem. | P10; US16–US17 |
| D100 | v1 pokazuje energię z istniejącego licznika, bez własnej całki mocy i okresów dobowych/miesięcznych. Ostrzeżenie nieskutecznego zamknięcia gaśnie przy wiarygodnym ustąpieniu któregokolwiek warunku lub otwarciu; brak danych wstrzymuje ocenę, sam nie kasuje ostrzeżenia. Przeczytanie nie kasuje przyczyny. | P11; US04–US05, US12 |
| D101 | Domena heat_pump_steering, minimum HA 2026.10.4 i macierz z 2026.11.1, cel strefy number, frontend TypeScript/Lit, źródła sterujące number/switch v1 oraz jawna aktywacja nowych bindingów wyjść przyjęte. T08 (zgodny plugin macierzy) pozostaje technicznym zadaniem, a projekt czeka na przegląd właściciela. | P12; US02–US03, US08, US11–US14, US16, US20 |

D90–D101 przyjęto 11 listopada 2026 na podstawie odpowiedzi właściciela w rozmowie
projektu, włączonych do [PR #36](https://github.com/marcin-bugala/ha-HeatPumpSteering/pull/36).
Rozstrzygnięcia P nie oznaczają zatwierdzenia całego projektu ani zgody na kod.

D24–D30 uzgodniono w [rundzie 2](round-02-daily-operation.md) 10 listopada 2026. D26 rozszerza D13 o jawny tryb Wyłączone; D27–D28 odrzucają błędną interpretację, że harmonogram blokuje ręczne włączenie. D29 dotyczy spójności zapisu ustawień, nie transakcji sprzętowej pompy.

Decyzje D17–D23 przyjęto 10 listopada 2026 w [rundzie 1](round-01-installation-zones.md), aktualizacja w [PR #27](https://github.com/marcin-bugala/ha-HeatPumpSteering/pull/27). D21 doprecyzowuje D08; nie przyjęto proponowanego wariantu globalnego NC/NO z wyjątkami na wyjściach.

Wczesne propozycje zaworów na całych rozdzielaczach, 16 siłowników NO i dokładnej krzywej producenta nie są aktualną konfiguracją referencyjną. D69 ustala niezależność CO/CWU; wymóg nastawy CO1 obowiązuje tylko przy module CO.

## Domyślne parametry przyjęte w rundzie 3

Wartości liczbowe opisano w [rundzie 3](round-03-regulation.md). Są przyjętymi ustawieniami początkowymi do późniejszej walidacji, nie gwarancją optymalnego strojenia wszystkich budynków. W konfiguracji zaawansowanej można zmienić wskazane parametry.

Domena heat_pump_steering i kontrakty z P12 są przyjęte w D101. Pozostałe szczegóły projektu technicznego oczekują przeglądu. F01 i zaawansowane prognozowanie pozostają przyszłe. Raportowane przez urządzenie limity są nadrzędne; nie kopiujemy stałego minimum/maksimum POC.

## Pytania po rundach 1–6 i ich rozstrzygnięcia w projekcie

| ID | Pytanie | Gdzie doprecyzować |
| --- | --- | --- |
| Q01 — doprecyzowane | D54 ustala odtworzenie trybów CO/CWU. Zakres F01 pozostaje otwarty | US03, US13 |
| Q02 — rozstrzygnięte | D46–D47 i D97 określają jakość raportów/historii; czas raportu HA nie jest dowodem pomiaru fizycznego. | US01, US16 |
| Q03 — rozstrzygnięte | D93 określa polaryzację, D90 potwierdzenie operacyjne; NC/NO strefy i czas siłowników pozostają bez zmian. | US05, US10 |
| Q04 — rozstrzygnięte | D49 zachowane; D98 ustala przypadek mieszany bez stref kwalifikowanych do korekty. | US17–US19 |
| Q05 — rozstrzygnięte | D97 ustala konserwatywne pokrycie, luki i medianę ważoną czasem; techniczny adapter historii w projekcie. | US05, US16, US19 |
| Q06 — rozstrzygnięte | D91: każda niealgorytmiczna zmiana CWU external; D92: ręczny demand bez niejawnej pauzy, OFF nie resetuje retry. | US07, US13, US14 |
| Q07 — rozstrzygnięte | D95 ustala inicjalizację CWU; D94 wyłącza obsługę higieny z zakresu produktu. | US13, US14 |
| Q08 — rozstrzygnięte | D90 określa potwierdzenia, D93 polaryzację, D92 ręczny demand; D55 nadal określa odtwarzanie przerwy. | US09 |
| Q09 — rozstrzygnięte | D90: wstępne potwierdzenie od razu, ostateczne po ponownym zgodnym odczycie tej samej encji po 2 min; bez dodatkowego dowodu fizycznego. | US04, US17, US19 |
| Q10 — odłożone | Brak prognoz w bieżącej wersji. Algorytm/adaptery, jakość, archiwizacja i uczenie wrócą przed przyszłym wydaniem | US21 |
| Q11 — rozstrzygnięte | D100 określa energię i kasowanie ostrzeżeń; D101 przyjmuje platformy i frontend. Przegląd projektu pozostaje wymagany. | US04, US11–US14 |
| Q12 — rozstrzygnięte | D101 przyjmuje domenę/minimum/macierz. T08 wymaga zgodnych zależności testowych; migracje i cały projekt czekają na przegląd. | US08, US19 |
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
