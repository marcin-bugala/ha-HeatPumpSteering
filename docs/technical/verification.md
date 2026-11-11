# Plan weryfikacji i śledzenie wymagań

Wszystkie poniższe testy produktu są planowane, nie wykonane. Źródła:
[US](../requirements/user-stories.md), [D](../requirements/decisions.md),
[A01–A59](../requirements/round-05-acceptance.md),
[B01–B13](../requirements/round-06-architecture.md).
Wynik odbioru dopiero z SHA, konfiguracją, czasami, wejściami i dowodem.

## Macierz US → komponent, dane, awaria i test

| US / Issue | Komponent | Dane | Zachowanie przy awarii | Scenariusze / sposób sprawdzenia | Zależna decyzja |
| --- | --- | --- | --- | --- | --- |
| US01 / #8 | config, measurements | ZoneConfig, source revision | Brak części źródeł; nowe okna po zmianie czujnika | A01,A05,A09,A30; B06,B10 | P08 |
| US02 / #9 | number, persistence | zone_id, cel, revision | Zapis nieudany nie zmienia nastawy; restart zachowuje cel | A07; B05,B06 | P07 |
| US03 / #10 | runtime, commands | enabled, mode, generation | Obserwacja/unload anuluje; restart odtwarza, reenable obserwuje | A07,A08,A40,A41; B01–B04 | P01,P12 |
| US04 / #11 | diagnostics, commands | Decision, Evidence, Warning | Brak dowodu jawny; błąd po trzech timeout | A37–A40,A59; B12 | P01,P11 |
| US05 / #12 | zones, demand | okna, cel, timers, relay evidence | Utrata temperatur: grace i otwarcie bez demandu; błąd przekaźnika unknown | A10–A17,A20,A31,A36,A42 | P01,P04,P07,P11 |
| US06 / #13 | measurements, zones, co | średnia/mediana, source set, accrued duration | Braki wstrzymują potwierdzenia, zmiana składu nie udaje spadku | A06,A09,A15,A22,A30,A42; B08 | P08 |
| US07 / #14 | runtime, dhw, commands | context/provenance, Override | CO nadal aktywne; CWU external do rzeczywistej zmiany planu | A08,A26,A47–A51 | P02,P03 |
| US08 / #15 | persistence, lifecycle | wersje, UUID, terminy | Niezgodny downgrade bez resetu i poleceń | A41,A43,A58; B05–B08 | P12,T08 |
| US09 / #16 | config, demand, commands | opcje, OR, open evidence, off_at | Brak wyjścia tylko diagnostyka; stare ON anulowane | A01–A03,A14,A27–A29,A31,A33–A34,A36,A40,A43,A56; B01–B04,B09 | P01,P03,P04 |
| US10 / #17 | config, zones, commands | NC/NO, polarity, movement deadline | Nieznany przekaźnik nie daje gotowości; mapowanie nie wysyła | A04,A17,A27 | P01,P04 |
| US11 / #18 | number, frontend | cel i snapshot, module availability | Brak danych, wyłączony moduł i rozgrzewanie rozróżnione | A07; B02,B06,B13 + UI | P07,P12 |
| US12 / #19 | sensor, frontend, diagnostics | moc, energia, pompa, evidence | Brak licznika nie jest zerem ani blokadą CO/CWU | A17,A59; B11,B12 + UI | P11 |
| US13 / #20 | dhw, frontend, commands | mode, temperature, schedule, revision | ON czeka na temp; OFF niezależne; częściowe wykonanie jawne | A44–A53; B01,B02,B11,B13 | P01,P02,P05,P06 |
| US14 / #21 | dhw, persistence, frontend | 7×48, timezone HA, expires_at | DST/przerwa stosuje bieżące pole, nie odtwarza kolejki | A44,A47–A56 | P02,P06 |
| US15 / #22 | config, zones, frontend | zone_id, group_id, sensors, outputs | Grupa nie jest strefą; brak modelu przepływów; konflikt wyjścia odrzucony | A01,A04,A05; B06,B09 | P04 |
| US16 / #23 | measurements, config, adapters | jednostki, freshness, min/max/step | Brak outdoor blokuje CO1, poprawne pozostałe funkcje działają | A01–A03,A24,A30,A32,A35; B01,B08,B11 | P01,P08 |
| US17 / #24 | co, constraints, commands | krzywa, wkłady, grid, confirmed setpoint | Brak zakresu blokuje zapis; retry nie tworzy kolejnego kroku | A06,A18–A26,A33–A35,A37–A40 | P01,P09,P10 |
| US18 / #25 | co, zones | priorytety, kwalifikacja, protection | Bez danych pomiń; closed measured hold; mieszane P09 | A05,A18,A20,A21,A34 | P07,P09 |
| US19 / #26 | history, runtime, persistence | 48h, coverage, last state, retry | Bez fikcyjnych próbek/ACK; przerwa nie dolicza obserwacji | A32,A37,A38,A41–A43,A56,A58; B05,B08 | P01,P05,P08 |
| US20 / #29 | co, constraints, models | aktywność i wkłady korekt, circuit_id | Wyłączenie korekty nie znosi limitów; drugi CO nie działa | A23,A57; B02 | P12 |
| US21 / #30 | granica zakresu | brak danych prognoz w v1 | Brak forecast integracji nie blokuje regulatora | A57, kontrola braku konfiguracji/wywołań prognoz | Przyszła specyfikacja |

US21 realizuje w tym wydaniu wyłącznie granicę odłożenia. E05/F01 poza wydaniem.
Każda kryterialna lista US jest wejściem review testów — samo dopasowanie ID
do pliku nie potwierdza realizacji wszystkich punktów.

## Dane i warstwy

| Kod zestawu | Dane i zegar | Awaria / dowód | Wykonanie |
| --- | --- | --- | --- |
| CFG | Syntetyczne ConfigEntry, UUID, encje number/switch/sensor, dwa konkurencyjne flow | Brak bindingu, wspólne wyjście, niepoprawna jednostka/krok | Pytest HA, mock usług, PL/EN flow |
| OBS | Te same dane w observation/control i niezależne CO/CWU | Licznik call_service, zmiana trybu w await | HA lifecycle; wymagane zero wywołań źródeł w observation |
| ZONE | Przedziały czasowe różnych termometrów, mediany, zmienny skład | Luki, grace, skok zestawu, race timera | Czyste funkcje + zegar kontrolowany + HA |
| CO | Outdoor, błędy/wagi stref, limity i siatka urządzenia | Brak źródła, brak legalnego kroku, ręczna nastawa | Czyste funkcje + testy integracji wykonawcy |
| DEM | NC/NO, polaryzacja, raport przekaźnika i movement/off deadlines | Nieudane otwarcie, zanik żądania, ręczny demand | Zegar kontrolowany + HA; mock nie udaje fizycznej hydrauliki |
| CMD | Request/revisions/generation, osobny raport optimistic i niezależny | Timeout, stary ACK, późny ACK, zmiana wartości, unload | Asynchroniczne testy HA i kolejności wywołań |
| HIST | Recorder z syntetycznymi stanami, start-state, brak heartbeat, checkpoint | Retencja, wykluczenia, przerwa procesu, błąd zapytania | HA na obu wersjach; brak własnego SQL |
| DHW | 7×48, draft/revision, external provenance, strefa Europe/Warsaw | Partial write, równoległy zapis, DST, brak temp | Czysty planner + HA + testy przeglądarkowe UI |
| LIFE | Wersjonowane payloady, aktywne timers/retry/override | Setup/unload/reload, crash granicy zapisu, niezgodny downgrade | HA, fixtures schematów, żadnego fizycznego wyjścia |
| UI | Snapshoty jakości, brak licznika, różne języki, mały ekran | Błąd sieci/Store, konflikt revision, niezapisany draft | Testy komponentów + browser na obu frontendach HA |

## Każdy scenariusz A/B

Dla każdego wiersza poniżej asercja wyniku jest dokładnie kryterium z podanej
rundy; skrót warunku identyfikuje fixture, nie zmienia kryterium. Test parametrów
domyślnych i granic równości osobno od wariantu ustawień zaawansowanych.
Wszystkie wiersze mają wynik „plan”; nie jest to tablica statusów US.

| ID | Zestaw / komponent | Warunek fixture | Źródło asercji |
| --- | --- | --- | --- |
| A01 | CFG / config | Jedna strefa Dom, termometr, outdoor i encja nastawy PC, zawory i demand wyłączone | Runda 5, A01: Konfiguracja może zakończyć się w obserwacji. Strefa uczestniczy w regulacji pomiarowej. |
| A02 | CFG / config | Włączony moduł CO, brak wskazanej encji nastawy PC przy konfiguracji obserwacji | Runda 5, A02: Kreator wskazuje brak i wymaga wyboru encji. |
| A03 | CFG / config | Sprawdzenie czterech kombinacji obsługi zaworów i demandu | Runda 5, A03: Wymagane są tylko wyjścia włączonych funkcji. Bez demandu wynik zapotrzebowania jest diagnostyczny. |
| A04 | CFG / config | Dwie strefy NC/NO, kilka wyjść strefy, próba przypisania tego samego wyjścia kolejnej strefie | Runda 5, A04: Typ strefy obejmuje jej wyjścia. Współdzielenie wyjścia zostaje odrzucone. |
| A05 | CFG / config | Pokoje zebrane w grupie Piętro | Runda 5, A05: Cele i priorytety mają strefy. Grupa służy prezentacji i nie jest dodatkowo liczona w regulacji. |
| A06 | CFG / config | Wybór trendu 2 h / 2 h oraz parametrów poza uzgodnionymi zakresami | Runda 5, A06: Zapis konfiguracji wskazuje błędy. Dla trendu jedna funkcja obejmuje oba punkty. |
| A07 | OBS / runtime | CO w obserwacji, CWU aktywne, zmiana celu Parter z 21 na 21,5°C | Runda 5, A07: Nowy cel jest trwały, cel Piętro pozostaje aktualny. CO pokazuje decyzję bez poleceń, CWU zachowuje własny tryb. |
| A08 | OBS / runtime | Przejście CO z obserwacji do sterowania i ponownie do obserwacji | Runda 5, A08: Aktywacja ocenia aktualne dane i ograniczenia. Obserwacja zatrzymuje kolejne polecenia i ponowienia. |
| A09 | ZONE / zones | Kilka termometrów w strefie, globalna średnia domyślna | Runda 5, A09: Powstaje średnia strefy, potem historia jej okien. Okna i funkcje są wspólne dla programu, progi stref niezależne. |
| A10 | ZONE / zones | Cel 21°C, T do zaworów 21°C, ΔT trendu +0,2°C, dane gotowe | Runda 5, A10: Żądanie zamknięcia strefy. |
| A11 | ZONE / zones | Cel 21°C, T 21°C, ΔT −0,2°C, blokady otwarcia upłynęły | Runda 5, A11: Żądanie otwarcia strefy. |
| A12 | ZONE / zones | Cel 21°C, trend niejasny, T 21,2°C albo 20,8°C | Runda 5, A12: Odpowiednio żądanie zamknięcia albo otwarcia po spełnieniu blokad. |
| A13 | ZONE / zones | Temperatura między progami, wiarygodne poprzednie żądanie | Runda 5, A13: Zachowujemy poprzednie żądanie. |
| A14 | ZONE / zones | Pierwszy start, gotowe pomiary między progami, brak poprzedniego żądania | Runda 5, A14: Zawory pozostają w odczytanym stanie. Strefa czeka ze zgłoszeniem zapotrzebowania na warunek otwarcia. |
| A15 | ZONE / zones | Bieżący pomiar jest niższy od komfortowego o 0,8°C i utrzymuje się warunek niedogrzania | Runda 5, A15: Otwarcie czeka na 30 min poprawnych obserwacji. Ustąpienie warunku przed terminem zeruje potwierdzenie. |
| A16 | ZONE / zones | Minimalne zamknięcie i potwierdzenie niedogrzania kończą się odpowiednio 10:30 i 10:20 | Runda 5, A16: Najwcześniejsze otwarcie 10:30 przy nadal spełnionych warunkach. Czasów nie sumujemy. |
| A17 | ZONE / zones | Przekaźnik potwierdził zamknięcie o 10:00, czas pracy siłowników 3 min | Runda 5, A17: Do 10:03 stan Zamykanie, potem przewidywane zamknięcie. Przy ciągłym spełnieniu warunków ostrzeżenie najwcześniej 12:03. |
| A18 | CO / constraints | Parter e=−0,4°C, priorytet 1, Piętro e=+0,4°C, priorytet 2 | Runda 5, A18: E=(−0,4+0,8)/3≈+0,133°C, w martwej strefie komfortu. Równe priorytety dają równe udziały. |
| A19 | CO / constraints | E=+0,6°C, martwa strefa 0,2°C, mnożnik 1,5 | Runda 5, A19: Korekta komfortu +0,6°C przed sumą, ograniczeniami i zaokrągleniem. |
| A20 | CO / constraints | Przegrzana strefa ma wszystkie przypisane wyjścia zamknięte zgodnie z raportem i czasem ruchu | Runda 5, A20: Jej odchylenie wypada z korekty CO1. Temperatura i warunki ostrzeżenia są nadal monitorowane. |
| A21 | CO / constraints | Strefa bez wyjść ma komfort ≥cel+0,5°C przez 60 min | Runda 5, A21: Wzrost CO1 jest zablokowany także przy dodatnim E. Zwolnienie wymaga ≤cel+0,2°C przez 30 min. |
| A22 | CO / constraints | Ważony wzrost komfortu 0,35°C przez 12 h, brak ważonego niedogrzania | Runda 5, A22: Korekta trendu −0,25°C. Przy wzroście 0,2°C daje 0, a przy ≥0,5°C osiąga −0,5°C. |
| A23 | CO / constraints | Suma modułów przekracza skonfigurowany limit | Runda 5, A23: Suma jest ograniczona. Zwiększenie limitu zachowuje zakres PC, ograniczenie komfortu, blokady i szybkość zmian. |
| A24 | CO / constraints | Pompa ma zakres 20–55°C, użytkownik zawęża do 23–35°C | Runda 5, A24: Wykonywalne nastawy mieszczą się w 23–35°C. Próba rozszerzenia poza zakres pompy jest odrzucona. |
| A25 | CO / constraints | Krok PC 1°C, wynik 27,4°C albo 27,5°C, bieżąca nastawa 30°C | Runda 5, A25: Docelowo odpowiednio 27°C albo 28°C. Najbliższy nowy zapis wynosi najwyżej 29°C, po wymaganym odstępie. |
| A26 | CO / constraints | Rozpoznana ręczna zmiana nastawy w pompie przy aktywnym CO | Runda 5, A26: Regulator pozostaje aktywny i przy najbliższym dozwolonym zapisie zmierza do własnej bieżącej nastawy z zachowaniem ograniczeń. |
| A27 | DEM / demand | Demand OFF potwierdzony 10:00, żądanie i potwierdzenie przekaźnika otwarcia strefy o 10:05 | Runda 5, A27: Strefa przewidywanie gotowa o 10:08. Najwcześniejsze ON demandu 10:15, jeśli zapotrzebowanie trwa. |
| A28 | DEM / demand | Warunki A27, lecz ostatnie zapotrzebowanie zanika 10:12 | Runda 5, A28: Oczekujące ON jest anulowane. Żądany demand pozostaje OFF. |
| A29 | DEM / demand | Potrzebująca strefa jest już otwarta albo ma tylko zapotrzebowanie wirtualne | Runda 5, A29: Nie rozpoczynamy nowego oczekiwania na ruch zaworów. Nadal obowiązuje minimalna przerwa demandu. |
| A30 | ZONE+HIST / fallback | Jeden z dwóch termometrów strefy jest utracony | Runda 5, A30: Działa pozostały poprawny pomiar z ostrzeżeniem 1 z 2. Zmiana zestawu sama nie jest nagłym spadkiem. |
| A31 | ZONE+HIST / fallback | Ostatni termometr strefy staje się jawnie niedostępny o 10:00 | Runda 5, A31: Do 10:30 zachowujemy żądania. Korekty pokojowe są pomijane. Potem awaryjne otwarcie bez własnego demandu. |
| A32 | ZONE+HIST / fallback | Brak nowego raportu wnętrza przez ponad 120 min albo outdoor przez ponad 30 min | Runda 5, A32: Źródło jest nieaktualne. Niezmienna wartość z aktualnymi raportami pozostaje poprawna. |
| A33 | ZONE+HIST / fallback | Wszystkie temperatury stref utracone, okresy przejściowe minęły, outdoor poprawny | Runda 5, A33: Awaryjne otwarcie, wycofanie demandu i CO1 z samej krzywej. |
| A34 | ZONE+HIST / fallback | Wszystkie aktywne strefy poprawnie mierzone i zamknięte | Runda 5, A34: Utrzymanie bieżącego CO1 oraz OFF demandu przy braku zapotrzebowania. |
| A35 | ZONE+HIST / fallback | Utrata outdoor albo aktualnej nastawy/wiarygodnego zakresu PC | Runda 5, A35: Odpowiednie zapisy CO1 wstrzymane. Sprawne zawory, demand i CWU działają według własnych danych. |
| A36 | ZONE+HIST / fallback | Błąd przekaźnika otwierania albo zamykania | Runda 5, A36: Stan nieznany i ponowienia. Niepotwierdzone otwarcie nie wystarcza do ON demandu. Nieudane zamknięcie zachowuje strefę w ochronie przegrzewania. |
| A37 | CMD / commands | Zapis CO1 wysłany 10:00 bez niezależnego potwierdzenia | Runda 5, A37: Próba niepotwierdzona o 10:02. Kolejne wysłania 10:05 i 10:10. Błąd zapisu po braku potwierdzenia do 10:12. |
| A38 | CMD / commands | Seria A37 nadal bez sukcesu | Runda 5, A38: Dalsze próby 10:20, 10:35, 11:00, 11:40, 12:45, 14:30, 16:30, potem co 120 min. Przed każdą aktualna ocena potrzeby. |
| A39 | CMD / commands | Po limicie 10:02 poprawne potwierdzenie aktualnego polecenia dociera 10:03 | Runda 5, A39: Koniec ponowień i reset serii błędów. Próba 10:05 nie jest wysyłana. |
| A40 | CMD / commands | Oczekujące ponowienie, lecz użytkownik przechodzi w obserwację albo aktualne żądanie się zmienia | Runda 5, A40: Przed kolejną próbą obowiązuje bieżący tryb i decyzja. Poprzednie polecenie nie jest odtwarzane z kolejki. |
| A41 | HIST+LIFE / startup | Start z dostępną historią 48 h i świeżymi źródłami | Runda 5, A41: Odtworzone pomiary, okna i gotowość pozwalają działać bez ponownego zbierania pełnej historii. Zachowane tryby przywracamy po sprawdzeniu bieżących stanów. |
| A42 | HIST+LIFE / startup | Pomiar zaworów gotowy, trend niegotowy; okno komfortu ma mniej niż 80% poprawnego pokrycia | Runda 5, A42: Zawory używają progów niejasnego trendu z komunikatem. Korekta komfortu czeka na gotowość własnego okna. |
| A43 | HIST+LIFE / startup | OFF demandu potwierdzony 10 min przed restartem, przerwa 2 min, aktualny raport nadal OFF | Runda 5, A43: Pozostają 3 min blokady. Potwierdzenia temperatury nie doliczają przerwy w obserwacji. |
| A44 | DHW / planner, frontend | Wybór Wyłączone, Stałe albo Harmonogram w panelu | Runda 5, A44: Wyłączone blokuje temperaturę i plan. Stałe udostępnia temperaturę, blokuje plan. Harmonogram udostępnia plan, blokuje temperaturę stałą. |
| A45 | DHW / planner, frontend | Zmiana pól panelu i próba zamknięcia bez Zapisz | Runda 5, A45: Edycja jest robocza. Zamknięcie wymaga potwierdzenia odrzucenia. Jeden Zapisz zatwierdza poprawny zestaw. |
| A46 | DHW / planner, frontend | Aktywne CWU, tryb Wyłączone zapisany w panelu | Runda 5, A46: Wykonujemy żądanie OFF CWU. Obsługa ogrzewania domu pozostaje zależna od własnych reguł. |
| A47 | DHW / planner, frontend | Zewnętrzne ręczne ON 48°C o 14:00 podczas planu OFF do 16:00, potem ON 45°C | Runda 5, A47: Podgrzewanie może działać według nadpisania do 16:00. Pola 14:30/15:00/15:30 nie kasują go. O 16:00 obowiązuje 45°C. |
| A48 | DHW / planner, frontend | Warunki A47, o 14:30 zapis panelu w Harmonogram, plan bieżący OFF | Runda 5, A48: Nadpisanie kończy się o 14:30 i obowiązuje OFF z bieżącego pola. Dotyczy również zapisu identycznego planu. |
| A49 | DHW / planner, frontend | Nadpisanie aktywne, zapis zmienionego planu o 14:30, którego obecny przedział to ON 46°C, następna zmiana 15:00 | Runda 5, A49: O 14:30 obowiązuje 46°C z zapisanego planu. Nie czekamy do 15:00. |
| A50 | DHW / planner, frontend | Cały tydzień ma jednakowy stan i temperaturę, potem zewnętrzne nadpisanie | Runda 5, A50: Nadpisanie trwa do ręcznej zmiany lub zapisu panelu w Harmonogram. Widoczny komunikat o braku zaplanowanej zmiany. |
| A51 | DHW / planner, frontend | Restart podczas ważnego nadpisania albo po jego terminie | Runda 5, A51: Odtwarzamy ważne nadpisanie. Po upływie terminu stosujemy bieżący przedział bez wydłużania i bez kolejki pominiętych zmian. |
| A52 | DHW / planner, frontend | Żądanie ON wymaga nowej temperatury, zapis temperatury zawodzi | Runda 5, A52: ON czeka na potwierdzenie temperatury. Ponawiamy aktualnie potrzebny zapis zgodnie z polityką. |
| A53 | DHW / planner, frontend | Aktualne żądanie zmienia się na OFF podczas niepotwierdzonej temperatury | Runda 5, A53: OFF jest wykonywane bez oczekiwania na temperaturę. Zachowujemy zatwierdzone ustawienia i pokazujemy wynik operacji. |
| A54 | DHW / planner, frontend | Zmiana zegara do przodu pomija lokalne pola planu | Runda 5, A54: Po zmianie stosujemy aktualny lokalny przedział. Pominiętych pól nie odtwarzamy. |
| A55 | DHW / planner, frontend | Cofnięcie zegara powtarza godzinę planu | Runda 5, A55: Ponownie obowiązują te same lokalne pola. Polecenie jest potrzebne przy różnicy stanu/temperatury. |
| A56 | DHW / planner, frontend | Zmiana czasu podczas blokady lub ponowień i przy nadpisaniu | Runda 5, A56: Timery mierzą rzeczywisty upływ. Nadpisanie kończy następna rzeczywista zmiana ustawienia z lokalnego planu. |
| A57 | CO / modules | Wyłączony moduł korekty lub bieżąca wersja bez prognoz | Runda 5, A57: Wkład modułu odpowiada jego aktywności, a wspólne limity i obserwacja obowiązują. Prognozy pozostają poza bieżącym programem. |
| A58 | LIFE / installation | Uruchomienie produktu na HA bez POC | Runda 5, A58: Instalacja nie wymaga POC ani importera. Ogólne ostrzeżenie o konflikcie regulatorów pozostaje. Runda 6 zastępuje wcześniejszy scenariusz migracji. |
| A59 | UI / diagnostics | Dowolna decyzja, ograniczenie, awaria lub niedostępny opcjonalny licznik | Runda 5, A59: Widać przyczynę, jakość danych i dostępny stan. Brak licznika nie jest prezentowany jako zerowy pobór. |
| B01 | CFG+OBS / lifecycle | Konfiguracja tylko CWU | Runda 6, B01: Brak wymagań CO1, outdoor i stref; harmonogram działa przy poprawnych encjach CWU |
| B02 | CFG+OBS / lifecycle | Samo CO / samo CWU / oba | Runda 6, B02: Każdy wariant jest konfigurowalny; nieobecne moduły nie pokazują paneli i encji |
| B03 | CFG+OBS / lifecycle | Ponowne włączenie wcześniej wyłączonego modułu | Runda 6, B03: Ustawienia zachowane, początek w obserwacji po odczytach i odbudowie okien |
| B04 | CFG+OBS / lifecycle | Wyłączenie/usunięcie integracji lub odłączenie wyjścia | Runda 6, B04: Koniec poleceń i ponowień, ostatni stan pozostaje; przy odłączeniu uprzednia informacja |
| B05 | LIFE+HIST / persistence | Aktualizacja przy aktywnych blokadach, nadpisaniu i ponowieniach | Runda 6, B05: Stan, terminy i tryby zachowane; brak nieplanowanych przełączeń i zerowania historii |
| B06 | LIFE+HIST / persistence | Zmiana nazwy/grupy/czujnika oraz usunięcie i odtworzenie nazwy | Runda 6, B06: Pierwsze zachowują tożsamość; nowe źródło ma własne okna; odtworzona strefa ma nową tożsamość |
| B07 | LIFE+HIST / persistence | Powrót do wersji niezgodnej z danymi | Runda 6, B07: Jawny błąd bez resetu danych i aktywacji; udokumentowane odtworzenie kopii |
| B08 | LIFE+HIST / persistence | Recorder nie zachował pełnych 48 h | Runda 6, B08: Jawna niepełność, reguły gotowości okien, brak fikcyjnych próbek |
| B09 | CFG+CMD / ownership | Jedna encja wykonawcza przypisana drugiej niezależnej funkcji/konfiguracji | Runda 6, B09: Zapis odrzucony; współdzielenie czujnika dozwolone |
| B10 | CFG+CMD / ownership | Błędna konfiguracja lub zmiana unieważniająca stare polecenie | Runda 6, B10: Walidacja zakresu przed zatwierdzeniem; stare polecenie nie jest odtwarzane |
| B11 | OBS / isolation | Awaria CWU, licznika lub jednej strefy | Runda 6, B11: Działają funkcje z poprawnymi zależnościami; widoczna przyczyna ograniczeń |
| B12 | UI / diagnostics | Eksport oraz trwające/ustępujące ostrzeżenie | Runda 6, B12: Anonimizacja, brak sekretów i wysyłki; przeczytanie nie kasuje problemu; historia ma początek i koniec |
| B13 | UI+LIFE / clean HA | Instalacja na czystym HA bez POC | Runda 6, B13: Konfiguracja i pełne działanie bez znajomości POC; karta/panel i PL/EN dostarczone z produktem |

## Przyjęte D → projekt i kontrola

| D | Komponent / dokument | Kontrola |
| --- | --- | --- |
| D01–D03 | ha-contracts, architecture | Dystrybucja, PL/EN, encje, brak transportu produktu; B13 |
| D04/D05/D22/D23 | architecture, README | Review jawnych zastąpień przez D76/D69/D31; bez starych pól |
| D06–D09 | config, commands | A01–A04,A08; bez demandu brak ON/OFF CO |
| D10–D14 | co, dhw, architecture | A06,A18–A26,A44–A57; prognozy poza zakresem |
| D15–D21 | data-model, zones | A04,A05,A09; sprzęt referencyjny nie hardkodowany |
| D24–D30 | frontend, dhw, lifecycle | A07,A08,A44–A53 |
| D31–D36 | zones, measurements | A06,A09–A17; ostrzeżenie hydrauliczne |
| D37–D42 | co, constraints | A18–A25; P09/P10 dla otwartych brzegów |
| D43–D45 | demand, runtime, corrections | A27–A29,A56,A57 |
| D46–D50 | measurements, fallback | A30–A35,A42 |
| D51–D52 | command-confirmation | A36–A40; profil dowodu P01 |
| D53–D59 | persistence, lifecycle | A14,A31,A33,A34,A41–A43,A51–A53; bez fikcyjnego czasu |
| D60–D67 | commands, frontend, timers | A17,A26,A37–A40,A44–A56 |
| D68–D70 | architecture, data-model, config | B01,B02; maks. jeden CO; dane przewidują circuit_id |
| D71–D72 | persistence | B05–B08; payload, rejestry i retencja |
| D73–D74 | lifecycle | B03,B04; brak OFF przy unload |
| D75–D77 | implementation-plan | A58,B13; pełne wydanie i jawny zakres symulacji |
| D78–D81 | frontend, ha-contracts, plan | B13; HACS/manual PL/EN, macierz HA |
| D82–D83 | diagnostics, warnings | B12; anonimizacja i historia; P11 powrót ostrzeżenia |
| D84–D88 | config, runtime | B06,B09–B11; rezerwacje między wpisami, izolacja awarii |
| D89 | persistence | B07; odmowa niezgodnego downgrade bez resetu |

## Regresje poza tabelą

Wyścigi: unload podczas wysyłania, stary ACK po zmianie celu, potwierdzenie
poprzedniej wartości po nowym żądaniu, nowe OFF podczas ON, jednoczesne reconfigure
dwóch entries i brak aktywacji nowych wyjść. Powtórzenie request nie jest krokiem CO.
Sprawdź zgubiony zapis Store i crash pomiędzy ConfigEntry/Store.

Źródła: test referencyjnego HiMitII z syntetyczną sekwencją optimistic→cache
po błędzie→niezależny refresh. Pierwsze dwa nie mogą potwierdzić komendy.
Test fallback min/max jako niewiarygodnego zakresu. Brak profilu nie jest
potajemnie dopuszczany do sterowania.

Diagnostyka: identyczne nazwy w różnych zagnieżdżeniach mapują do tego samego
pseudonimu; sekrety, entity_id i nazwy nie wyciekają przez traceback/tekst wyjątku.
Test kluczy PL/EN, kontrast/focus, panel draft/cancel/save, conflict_revision
i zapis identycznego planu kończący override.

## Odbiór sprzętowy i wydanie

Osobne zlecenie właściciela, poza CI. Zapis: SHA pakietu i HA/integracji źródeł,
parametry, zakres i sposób przerwania, timestampy, żądania, raporty, przewidywanie,
niezależny dowód i rzeczywista obserwacja. Obserwacja/test mock nie potwierdza
ruchu zaworu, hydrauliki, pracy sprężarki ani bezpieczeństwa instalacji.
Wydanie wymaga wyników referencyjnych i listy wariantów tylko symulowanych.
Brak dostępu do domu w CI. Dokumentacyjny PR nie wykonuje A/B na integracji.
