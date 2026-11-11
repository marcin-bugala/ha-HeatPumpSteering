# Specyfikacja produktu — projekt v0.7

Stan wymagań: 11 listopada 2026. Uzgodnienia i propozycje rozróżnia [rejestr decyzji](decisions.md). Statusy realizacji znajdują się w [Issues](README.md). Brak implementacji produktu.

## Cel i użytkownicy

Publiczna integracja niestandardowa HA ma powoli regulować ogrzewanie z uwzględnieniem komfortu stref oraz dużej bezwładności budynku. Ma ograniczać przegrzewanie, tłumić krótkie zakłócenia i wyjaśniać decyzje. Nie gwarantujemy oszczędności, dokładności predykcji ani niezależnych temperatur tam, gdzie instalacja nie daje niezależnego sterowania.

Odbiorca ma istniejące integracje pompy, termometrów i ewentualnie wyjść wykonawczych. Produkt korzysta z encji HA, nie wymaga jednego producenta sterowników, własnej chmury ani danych logowania Hisense. Hisense/HiMitII to pierwsza konfiguracja referencyjna, nie zamknięty zakres marek.

PC zachowuje sterowanie sprężarką, defrostem, ochroną urządzenia i pompami obiegowymi. Demand oznacza zezwolenie na ogrzewanie, nie odcięcie zasilania pompy. Nie planujemy sterowania sprężarką ani zastępowania zabezpieczeń sprzętowych.

## Podstawa i wybór możliwości

CO i CWU są niezależnie wybieranymi modułami: obsługujemy samo CO, samo CWU albo oba. CO obejmuje regulację nastawy wody; nie wprowadzamy osobnego trybu samych zaworów. Konfiguracja tylko CWU nie wymaga stref, outdoor ani encji nastawy CO1. Wymagane są encje sterowania i nastawy CWU. Osobny tryb F01 pozostaje pytaniem przyszłej wersji. Ustalenie rundy 6 zastępuje wcześniejszy wymóg CO1 w każdej konfiguracji.

Dwie niezależne opcje konfiguracji: sterowanie strefami oraz sterowanie demandem. Dopuszczamy wszystkie cztery kombinacje. Bez demandu nie przełączamy ogrzewania ON/OFF, także przez encję obiegu CO1; pompa decyduje o pracy według swoich zasad i nastawy wody.

| Wejście/wyjście | Warunek wymagania |
| --- | --- |
| Temperatura wnętrza | Dla CO co najmniej jeden czujnik na aktywną strefę |
| Cel komfortu | Własny cel każdej aktywnej strefy |
| Bieżąca temperatura zewnętrzna | Wymagana dla regulacji CO1; sama prognoza jej nie zastępuje |
| Nastawa CO1 | Wymagana przy konfiguracji modułu CO, także w obserwacji. Nie wymagana dla samego CWU |
| Wyjścia zaworów | Tylko przy włączeniu sterowania zaworami danej strefy; NC/NO wybierane osobno dla tej strefy |
| Wyjście demand | Tylko po włączeniu funkcji demand |
| Prognozy pogody, nasłonecznienia/PV | Odłożone do przyszłej wersji; nie konfigurujemy ani nie używamy w bieżącej |
| Moc/energia PC, zasilanie i powrót | Opcjonalna diagnostyka |
| Sterowanie i nastawa CWU | Wymagane tylko dla włączonego modułu CWU, także przy konfiguracji bez CO |

Brak opcjonalnego źródła nie oznacza zera ani awarii całego produktu. Niedostępność uprzednio wybranego źródła jest jawna. Progi świeżości i zachowanie awaryjne określa runda 4. Awaria ogranicza zależne funkcje, nie całą integrację.

## Model instalacji i stref — ustalenia rundy 1

Pełny zapis uzgodnień i scenariuszy: [runda 1](round-01-installation-zones.md).

- Jedna konfiguracja pierwszej wersji developerskiej obejmuje jedną pompę, maksymalnie jeden obieg CO i jedno CWU. Moduły są niezależnie opcjonalne. Architektura od początku przewiduje przyszłe dwa obiegi CO jednej pompy: osobne przypisania stref, nastawy oraz opcjonalne Demand 1 i Demand 2, z tym samym algorytmem działającym niezależnie. Obsługa dwóch obiegów nie jest funkcją pierwszego wydania.
- Minimum dla modułu CO: wskazana encja nastawy CO1, outdoor oraz co najmniej jedna aktywna strefa z termometrem i celem. Dla samego CWU obowiązują tylko wymagania jego modułu.
- W obserwacji odczytujemy nastawę PC i porównujemy z propozycją, bez wysyłania zmian. Późniejsza niedostępność encji należy do rundy awarii.
- Strefy są niezależne. Grupy porządkowe, np. Parter, służą prezentacji; nie mają odrębnych celów, wyjść ani dodatkowego udziału w regulacji.
- Strefa może mieć jeden lub kilka termometrów: główny albo agregacja, domyślnie średnia. Funkcje i okna są wspólne dla programu; progi reakcji i priorytety są ustawieniami strefy. Reguły liczbowe ustalono w rundzie 3, a zachowanie przy brakach danych w rundzie 4.
- Wyjście zaworów należy do dokładnie jednej strefy i nie może być współdzielone z inną. Strefa może mieć kilka wyjść; jeden przekaźnik może obsługiwać grupę pętli.
- NC/NO wybieramy osobno dla każdej strefy sterującej zaworami, wspólnie dla wszystkich jej wyjść. Typy mogą różnić się między strefami.
- Runda 3 zastępuje wcześniejsze pole o części pętli otwartych: program nie modeluje pętli, przepływów i częściowego odcięcia. Przy konfiguracji zaworów pokazuje ostrzeżenie o obowiązku zapewnienia drogi przepływu także przy zamkniętych strefach.

## Moduły

| ID | Moduł | Zakres |
| --- | --- | --- |
| F00 | Konfiguracja | UI HA, wybór encji, stref i możliwości, późniejsza edycja |
| F01 | Skropliny | Osobna logika grzałki odpływu i diagnostyka, późniejszy etap |
| F02 | CO1 | Krzywa, komfort, trendy, ograniczone korekty i kontrola poleceń |
| F03 | Strefy | Cele, zapotrzebowanie, grupy wyjść, stan polecony/przewidywany/potwierdzony |
| F04 | Demand | Opcjonalne zezwolenie na ogrzewanie, agregacja i sekwencje do dopracowania |
| F05 | Obsługa i diagnostyka | Dashboard, wyjaśnienia, obserwacja, historia i ręczna kontrola |
| F06 | CWU | Praca stała lub tygodniowy harmonogram z temperaturą na przedział |
| F07 | Prognozy — odłożone | Wymagania zachowane dla kolejnej wersji; brak konfiguracji i wpływu w bieżącej |

### F02 — regulacja CO1

Szczegółowe reguły, zakresy ustawień i scenariusze: [runda 3](round-03-regulation.md).

- PC ma stałą nastawę zasilania kontrolowaną przez HA; nie zakładamy równoległej pogodówki nadpisującej tę nastawę.
- Baza A+B×(Tref−Ta); początkowo A=20°C, B=0,2, Tref=20°C. Outdoor domyślnie średnia 2 h, wybór średnia/mediana i okna 30 min–6 h co 30 min.
- Najpierw agregujemy termometry strefy (domyślnie średnia), potem filtrujemy historię. Do zaworów domyślnie średnia 30 min, do komfortu mediana 3 h; każde okno konfigurowalne 30 min–6 h co 30 min.
- Funkcje i okna są wspólne dla programu. Priorytety stref 1–5, domyślnie 3, są wagami odchyleń cel−temperatura komfortowa.
- Stosujemy średnią ważoną odchyleń. Martwa strefa ±0,2°C, współczynnik 1,5 poza martwą strefą, limit korekty komfortu ±2°C; parametry algorytmu w konfiguracji zaawansowanej.
- Lokalna możliwość zamknięcia strefy ma pierwszeństwo przy przegrzaniu. Po zamknięciu wszystkich przypisanych wyjść strefę pomijamy w korekcie CO1, nadal monitorując. Strefa bez wyjść pozostaje w ocenie i ochronie.
- Ochrona stref bez sterowanych wyjść: ≥cel+0,5°C przez 60 min blokuje wzrost CO1; ≤cel+0,2°C przez 30 min zwalnia. Progi i czasy osobno dla strefy. Blokada nie wyłącza demandu.
- Trend długoterminowy porównuje temperaturę komfortową teraz i 12 h wcześniej, dla tego samego zestawu stref i z ich priorytetami. Przy braku ważonego niedogrzania: wzrost ≤0,2°C daje 0, od 0,2 do 0,5°C liniowo 0 do −0,5°C, ≥0,5°C daje −0,5°C. Bez historii ta korekta nie działa, bez blokowania gotowej podstawy regulatora. Parametry konfigurowalne w programie.
- Suma aktywnych korekt ma konfigurowalny limit, domyślnie ±2°C; może być zwiększony. Nie znosi oddzielnych limitów ani zabezpieczeń.
- Zakres temperatur odczytujemy z ustawień PC przez integrację źródłową; użytkownik może opcjonalnie zawęzić, nigdy rozszerzyć. Nie narzucamy stałego 27°C ani 35°C.
- Obliczenia z pełną precyzją, końcowy wynik do najbliższej dozwolonej wartości kroku PC, połówki w górę, w granicach zakresu.
- Zmiana najwyżej 1°C co 120 min w obu kierunkach; krok zmiany i odstęp w konfiguracji zaawansowanej, zgodne z możliwościami PC. Nie zapisujemy identycznej nastawy.
- Ocena co 5 min, dodatkowo po zmianie celu/trybu; timery działają według terminów bez dodatkowego czekania na cykl. Częstotliwość wspólna dla domu, konfigurowalna.
- Raport HA, last_reported i aktualizacja optymistyczna nie dowodzą wykonania przez urządzenie. Polityka potwierdzeń i awarii należy do następnej rundy.
- Architektura oddziela bazę, moduły korekt i wspólne ograniczenia. Bieżące moduły: komfort i trend, wybiórczo uruchamiane; diagnostyka pokazuje ich wkład. Limity i obserwacja nie są wyłączalnymi korektami.

### F03/F04 — strefy, zawory i demand

Strefy są niezależne; grupy tylko porządkowe. Jedno wyjście należy do jednej strefy, strefa może mieć kilka wyjść. NC/NO wybieramy dla strefy: NC zasilanie otwiera, NO zasilanie zamyka. Bez sprzężenia zwrotnego położenie jest przewidywane.

Trend zaworów to różnica dwóch okien, ze wspólną funkcją średnia/mediana i niezależnymi czasami. Domyślnie średnie 30 min / 4 h; krótsze 15 min–2 h co 15 min, dłuższe 2–12 h co 30 min, 2 h / 2 h niedozwolone. Próg trendu strefy domyślnie ±0,2°C.

Dla temperatury do zaworów T i celu S: rosnący trend zamyka przy T≥S, malejący otwiera przy T≤S, niejasny zamyka przy T≥S+0,2°C i otwiera przy T≤S−0,2°C. W innych warunkach poprzednie żądanie. Progi konfigurowalne w strefie.

Nie ignorujemy całkowicie zakłóceń. Gotowanie/słońce może zamknąć strefę; nagły spadek wymaga 30 min potwierdzonego niedogrzania przed otwarciem. Ustąpienie warunku zeruje potwierdzenie. Minimum zamknięcia 30 min przed ponownym otwarciem, bez analogicznej blokady zamknięcia przy przegrzaniu. Czasy strefy mogą biec równolegle.

Ostrzeżenie po upływie czasu zamykania i 120 min utrzymania zamknięcia, temperatury komfortowej ≥cel+0,5°C oraz rosnącego trendu: „Strefa nadal się nagrzewa mimo polecenia zamknięcia. Sprawdź zawory i inne źródła ciepła.” Czas i próg konfigurowalne dla strefy. To nie diagnoza uszkodzenia ani automatyczny STOP całej PC.

Demand jest OR żądań otwarcia aktywnych stref, w tym wirtualnych dla stref bez zaworów. Przed ON otwieramy wyjścia; wystarczy przewidywane otwarcie jednej potrzebującej ciepła strefy. Jeden „Czas pracy siłowników” ma domyślnie 3 min, jest wspólny dla domu i obejmuje otwieranie oraz zamykanie. Strefa już otwarta nie czeka od nowa; strefa bez wyjść nie wymaga tego opóźnienia. Brak wszystkich zapotrzebowań wyłącza demand bez dodatkowego opóźnienia. Przed ponownym ON minimum 15 min od OFF, konfigurowalne dla domu; zawory mogą otworzyć się wcześniej. Nie ma minimum ON opóźniającego wyłączenie. Nie sterujemy zasilaniem PC i wybiegiem producenta. Bez wyjścia demand jest tylko diagnostyczny.

Pętle stale otwarte i częściowe odcięcie hydrauliczne nie są modelowane, nie ma dla nich ustawień ani wpływu na algorytm. Przy konfiguracji zaworów wyświetlamy ostrzeżenie z [rundy 3](round-03-regulation.md) o obowiązku zapewnienia drogi przepływu również przy zamkniętych strefach. To zastępuje wcześniejsze pole informacyjne o pętlach.

### F06 — CWU

Uzgodnione reguły panelu i harmonogramu oraz przykłady zawiera [runda 5](round-05-acceptance.md).

| Tryb panelu | Pole temperatury stałej | Obszar harmonogramu |
| --- | --- | --- |
| Wyłączone | Niedostępne | Niedostępny |
| Stałe | Dostępne | Niedostępny |
| Harmonogram | Niedostępne | Edytowalny |

- Tryb, dostępne temperatury i plan zatwierdzamy jednym Zapisz. Edycja jest robocza, walidujemy zestaw. Zamknięcie niezapisanej edycji wymaga potwierdzenia jej odrzucenia.
- W Harmonogramie można ustalić osobno każdy dzień i każde z 48 pól półgodzinnych jako OFF albo ON z temperaturą. Harmonogram dotyczy wyłącznie CWU.
- Zapis panelu w Harmonogram kończy wcześniejsze nadpisanie i natychmiast stosuje aktualny przedział, również przy identycznym planie.
- Zewnętrzne ręczne zmiany, np. na encji CWU lub w aplikacji pompy, tworzą nadpisanie do następnej rzeczywistej zmiany planu albo do zapisu panelu w Harmonogram. Przy jednakowym planie tygodniowym nadpisanie trwa do ręcznej zmiany lub tego zapisu, z komunikatem o braku zaplanowanej zmiany.
- Plan korzysta z lokalnej strefy HA. Przeskok zegara stosuje aktualny przedział, a cofnięcie ponawia te same lokalne pola. Zapis do urządzenia wynika z różnicy żądanego i aktualnego stanu. Timery mierzą rzeczywisty czas.
- CO i CWU mają osobne przełączniki obserwacja/sterowanie poza panelem zbiorczego zapisu. W obserwacji zapis ustawień przygotowuje decyzję.
- Po restarcie wraca ważne nadpisanie albo aktualny przedział. Włączenie wymaga potwierdzenia docelowej temperatury. Wyłączenie jest niezależne od zapisu temperatury. Częściowe wykonanie uruchamia wspólne ponowienia dla brakującego, nadal potrzebnego polecenia.
- CWU jest opcjonalne, może działać bez CO i należy do pierwszego kompletnego wydania developerskiego. D95: bez nastaw początek Nieskonfigurowane, jawna temperatura i zapis całego planu; draft 7×48 OFF nie steruje urządzeniem. D94: nie obsługujemy higieny CWU — bez wykrywania, encji, specjalnych blokad i warunku aktywacji.

### F07 — prognozy odłożone do przyszłej wersji

Decyzja rundy 3: brak obsługi prognoz w bieżącej wersji. Poniższe kierunki zachowujemy dla [US21](user-stories.md#us21), bez ustalonego szczegółowego algorytmu. Priorytety stref są nadal częścią bieżącego regulatora, a modularność US20 umożliwia dołączenie przyszłych korekt.

- W przyszłości można osobno określić wpływ pogody i słońca/PV; nie definiujemy wag mieszania zewnętrznych celów komfortu.
- Dane prognoz muszą mieć rozpoznane jednostki, czas wydania/ważności, zasięg i luki.
- PV jest wskaźnikiem słońca, nie miarą ciepła domu. Ekspozycja paneli i okien może się różnić; zachmurzenie, rolety, zacienienie i ograniczenia falownika mogą zaburzać zależność.
- Nie liczymy dwukrotnie tych samych zysków z PV i prognozy nasłonecznienia. Brak PV nie oznacza braku słońca.
- Korekty mają ograniczony wpływ i są wyjaśniane. Zanik jakości prognozy nie może utrzymywać trwałej redukcji ogrzewania.
- Dokument POC proponuje analizę godzinową do 48 h, okna 24/48 h, prognozy temperatur wnętrza 1/3/6 h, uczenie opóźnienia i osobnych zysków stref. To kierunki do oceny, nie zatwierdzony zakres v1.
- Model uczony, jeśli zostanie przyjęty, najpierw pracuje obserwacyjnie. Należy archiwizować prognozę dostępną w chwili decyzji i oddzielić uczenie od walidacji. Nie oceniamy dawnych decyzji później skorygowaną prognozą.

### F01 — skropliny, późniejszy etap

Ustalona potrzeba: grzać przy temperaturze zewnętrznej poniżej −5°C i potwierdzonej pracy pompy; minimum 30 min pracy grzałki; co najmniej 20 min po zatrzymaniu; ponowne uruchomienie pompy anuluje poprzedni wybieg.

Wymagane są histereza temperatury, diagnoza faktycznego poboru, obsługa restartów i zaników odczytów. Nie ustalono progu mocy klasyfikującego pracę. A2W_SW_ON nie jest potwierdzonym stanem sprężarki.

Propozycja łączenia timerów: wyłączenie nie wcześniej niż późniejszy z terminów start grzałki+30 min i ostatni stop pompy+20 min, jeśli nie powstało nowe zapotrzebowanie. Ta reguła, zachowanie po ociepleniu i przy nieznanym stanie wymagają zatwierdzenia.

## Obserwacja, diagnostyka i niezawodność

- Start nowej konfiguracji w obserwacji. Wyjścia objęte obserwacją nie otrzymują poleceń; algorytm nadal oblicza decyzje.
- Użytkownik sam aktywuje sterowanie. Powrót do obserwacji zatrzymuje kolejne polecenia i nie cofa ostatnich nastaw.
- Przy aktywacji ponowna ocena aktualnych danych zamiast wykonywania historycznej kolejki.
- CO i CWU mają dwa niezależne przełączniki obserwacja/sterowanie; włączenie jednego nie aktywuje drugiego. Po restarcie przywracamy oba zapisane tryby i sprawdzamy gotowość. Relacja do F01 pozostaje do uzgodnienia.
- Pamięć zachowuje cele i potrzebny stan; nie dopisuje fikcyjnych pomiarów ani potwierdzeń podczas przerw.
- Wartości domyślne świeżości raportów to 120 min dla stref i 30 min dla outdoor. Gotowość wymaga 80% poprawnego pokrycia każdego okna oraz świeżego bieżącego pomiaru. Brak gotowego trendu zaworów pozwala użyć progów trendu niejasnego, gdy pomiar zaworów jest gotowy.
- Strefa działa na pozostałych poprawnych termometrach. Po utracie wszystkich jej pomiarów korekta pokojowa jest pomijana, ostatnie żądania utrzymujemy przez 30 min, potem stosujemy awaryjne otwarcie bez dodatkowego demandu.
- Utrata wszystkich pomiarów stref prowadzi po okresie przejściowym do krzywej z outdoor i wycofania demandu. Gdy wszystkie poprawnie mierzone strefy są zamknięte, utrzymujemy aktualną nastawę CO1. Brak outdoor, aktualnej nastawy lub wiarygodnego zakresu PC blokuje zapisy CO1.
- D90: zgodny odczyt tej samej encji po zapisie daje od razu potwierdzenie wstępne. Po domyślnie 2 min ponownie odczytujemy jej bieżącą wartość; poprawny zgodny odczyt ostatecznie potwierdza dla regulatora i kończy retry. Nie wymagamy dodatkowej encji ani dowodu fizycznego. Czas kontroli wspólnie konfigurowalny. Późny poprawny odczyt aktualnego polecenia kończy serię przed kolejną próbą.
- Wspólne ponowienia zapisów obejmują trzy próby łącznie w odstępach 5 min, potem błąd i odstępy 10, 15, 25, 40, 65, 105, 120… min. Licznik osobno dla wyjścia. Kolejna próba wynika z aktualnego żądania. Ponowienie CO1 nie jest kolejnym krokiem zmiany o 1°C.
- Przy uruchomieniu odbudowujemy pomiary i filtry z dostępnej historii, domyślnie 48 h, oraz odtwarzamy pamięć i tryby. Przed wznowieniem uzgadniamy bieżące dane i stany. Blokady mogą upływać podczas przerwy przy wiarygodnym odczycie. Potwierdzenia temperatury nie liczą czasu bez poprawnej obserwacji.
- Szczegóły awarii zaworów, demandu, CO1 i CWU opisuje [runda 4](round-04-failures-restarts.md). Ręczna zmiana CO1 poza panelem pozostawia algorytm aktywny i stosuje jego limity. Wyłączenie/usunięcie zatrzymuje polecenia i ponowienia bez przywracania poprzednich nastaw. Kontrakty źródeł i techniczne rozpoznawanie potwierdzeń wymagają projektu technicznego.
- Rozróżniamy zezwolenie na grzanie, raport HA, rzeczywistą pracę sprężarki i fizyczne wykonanie polecenia.
- Dashboard: cele i pomiary, zawory, dostępny stan pompy, moc i energia, jakość danych, filtry/trendy, decyzje, nastawy proponowane/wysłane/potwierdzone, limity i timery.
- Pierwsze wydanie dostarcza encje do własnych dashboardów i automatyzacji, gotową kartę produktu, panel CWU oraz osobny ekran konfiguracji zaawansowanej. Karta i panel są dostarczane razem z integracją, bez dodatkowych kart innych autorów. Dokładne platformy encji i technologia frontendu wymagają projektu technicznego.
- Diagnostyka jest pobierana na żądanie przez standardową funkcję HA. Obejmuje wersję, parametry, jakość danych, ostatnie decyzje, blokady i błędy. Nazwy własne i identyfikatory encji zastępujemy spójnymi oznaczeniami; brak haseł, tokenów i automatycznego wysyłania.

## Architektura i cykl życia — runda 6

Pełny zapis: [runda 6](round-06-architecture.md). Odczyty i polecenia korzystają z encji HA; transport do urządzeń zapewniają ich integracje. D90 rozróżnia potwierdzenie operacyjne (wstępne od razu, ostateczne po ponownym odczycie tej samej encji po 2 min) od dowodu fizycznego, którego produkt nie wymaga.

- Konfiguracja instalacji używa standardowych wpisów konfiguracji HA z migracjami. Harmonogramy, cele i potrzebny stan działania korzystają z wersjonowanego mechanizmu Store. Historia jest w Recorderze, a okna pomiarowe w pamięci odbudowujemy z dostępnej historii. Nie instalujemy dodatkowej bazy danych.
- Aktualizacja ma zachować konfigurację, cele, harmonogramy, historię pomiarów i decyzji, identyfikatory encji, timery, nadpisania i ponowienia. Nie może powodować nieplanowanych przełączeń ani zbierania historii od zera. Restart przerywa wykonywanie programu, ale po nim odtwarzamy stan i sprawdzamy bieżące dane.
- Zachowanie historii podlega retencji i filtrom Recordera użytkownika. Aktualizacja nie usuwa danych; nie obiecujemy odtworzenia historii, której HA nie przechował. Braki są jawne.
- Wyłączenie lub usunięcie integracji zatrzymuje polecenia i ponowienia, pozostawiając ostatni stan urządzeń. Wyłączenie modułu zachowuje jego ustawienia. Jego ponowne włączenie zaczyna w obserwacji; zwykła aktualizacja lub restart przywraca zapisany tryb.
- Zmiana konfiguracji wymaga walidacji całości zmienianego zakresu, unieważnia nieaktualne polecenia i ponownie ocenia dane. Zachowujemy pasującą historię i pamięć. Zmiana czujnika odbudowuje okna nowego źródła bez mieszania ze starym.
- Strefy mają trwałe identyfikatory niezależne od nazwy, grupy i czujnika. Zmiany nie zrywają encji, dashboardów i automatyzacji. Usunięcie i ponowne dodanie tej samej nazwy tworzy nową tożsamość.
- Odłączenie wyjścia lub usunięcie strefy pokazuje przed zatwierdzeniem aktualny stan i ostrzeżenie, że wyjście pozostanie w nim bez dalszego sterowania. Anulujemy jego oczekujące polecenia.
- Blokujemy współdzielenie encji wykonawczych między niezależnymi funkcjami i konfiguracjami integracji. Czujniki można współdzielić. Nie gwarantujemy wykrycia zewnętrznych regulatorów i nie wyłączamy cudzych automatyzacji; przy aktywacji ostrzegamy o konflikcie.
- Ustąpienie przyczyny i spełnienie warunków powrotu kasuje aktywne ostrzeżenie automatycznie. Oznaczenie jako przeczytane nie usuwa problemu ani blokady. Historia zachowuje wystąpienie i ustąpienie. Podejrzenie niesprawnego zaworu nie jest potwierdzoną diagnozą.
- Starsze wydanie może wrócić do działania tylko przy zgodnym formacie danych. Przy niezgodności zgłasza błąd bez resetu danych i aktywacji sterowania. Instrukcja wydania określa powrót oraz potrzebę odtworzenia właściwej kopii HA.

## Codzienna obsługa CO

Zmiana celu CO jest nową, trwałą nastawą konkretnej strefy, zachowaną po restarcie. Nie jest czasowym nadpisaniem i nie ma harmonogramu CO. Obsługa celu jest poza panelem zbiorczego zapisu CWU; nie omija ograniczeń regulatora.

## Referencyjna instalacja użytkownika — nie ograniczenie produktu

Hisense Hi-Therma 8 kW monoblok, podłogówka i bufor jako sprzęgło rozdzielający obieg pompy ciepła i obieg podłogówki. Dwie kondygnacje, docelowo trzecia.

| Element | Ustalenie |
| --- | --- |
| Parter | Cel początkowy 21°C; 8 pętli, 5 planowanych siłowników |
| Piętro | Cel początkowy 22°C; 8 pętli, 7 planowanych siłowników |
| Siłowniki | SALUS T30NC230, NC, M30×1,5, 230 V — ostatnia korekta użytkownika |
| Pozostałe pętle — informacja sprzętowa | Użytkownik planuje ręczną regulację przepływu do 1 l/min; to opis instalacji, nie ustawienie ani wejście algorytmu |
| Wyjścia | Rozważane po jednym Shelly 1PM Mini Gen3 na grupę; KinCony A8v3+ESPHome jako alternatywa wielokanałowa |
| Dodatkowe pomiary | Rozważane sondy zasilania/powrotu; nie uznajemy ich za zainstalowane |
| Demand | Planowany suchy styk; połączenie i znaczenie wejścia Hisense do weryfikacji |

Pompa wtórna i zapewnienie przepływu zostały przez użytkownika odłożone do osobnego zadania. Nie dobieramy ich tutaj i nie traktujemy tego odłożenia jako potwierdzenia gotowości hydraulicznej do uruchomienia wyjść. Jednego konkretnego przepływu nie przedstawiamy jako gwarantowanego zabezpieczenia wszystkich instalacji.

## Publiczna dystrybucja

Pierwsze kompletne wydanie developerskie obejmuje CO i strefy, opcjonalne zawory i demand oraz opcjonalne CWU z harmonogramem. Samo CO, samo CWU i oba moduły muszą działać. Prognozy i skropliny są poza tym wydaniem; skropliny są wstępnie kolejnym etapem.

Dystrybucja: HACS jako custom repository i instalacja ręczna. Wydania testowe, np. 0.1.0-beta.1, są wybierane przez użytkownika. Od pierwszego wydania pełne PL/EN interfejsu, komunikatów i instrukcji instalacji/konfiguracji. Zgłoszenie do domyślnego katalogu HACS po stabilizacji. Każde wydanie określa minimum HA, sprawdzone wersje, zmiany i sposób powrotu. POC jest osobnym projektem, bez importera ani wymaganej ścieżki migracji dla użytkownika produktu.

D101: domena heat_pump_steering, minimum HA 2026.10.4, macierz z 2026.11.1; cel strefy number, źródła sterujące number/switch v1 i frontend TypeScript/Lit. Zgodne zależności testów obu wersji (T08) i przegląd projektu pozostają przed kodowaniem.

## Doprecyzowania właściciela w PR #36 — D90–D101

Przyjęte 11 listopada 2026 [rozstrzygnięcia](decisions.md) zastępują wcześniejsze
otwarte pytania w odpowiednim zakresie. Nie oznaczają implementacji.

- Każda niealgorytmiczna zmiana ustawienia CWU jest external, ze zwykłymi regułami
  nadpisania D27/D63/D64; bez kategorii ambiguous i blokady z powodu pochodzenia.
- Ręczny demand nie pauzuje automatu; kolejna dozwolona ocena uzgadnia aktualne
  żądanie. OFF nie zeruje liczników ani terminów retry. Trwałe oddanie kontroli:
  obserwacja CO.
- Polaryzacja bindingu osobno od NC/NO strefy; zmiana mapowania nie wykonuje polecenia.
- Cel strefy 5–35°C co 0,5°C, początkowo podany przez użytkownika. Nowy cel zeruje
  potwierdzenia temperatury, zachowuje blokady zamknięcia/demandu i historię.
- Niepewna historia to luki, bez domyślnego heartbeat. Mediana ważona czasem;
  przy dokładnym podziale 50% średnia dwóch środkowych wartości.
- Przypadek mieszany bez kwalifikowanych stref daje samą bazę outdoor i dotychczasowe
  blokady; wszystkie poprawne zamknięte nadal utrzymują nastawę, wszystkie utracone
  po grace dają bazę i wycofanie demandu.
- Bieżąca nastawa poza zakresem: obcięcie do najbliższej dopuszczalnej granicy
  i konflikt. Ta korekta ma pierwszeństwo przed zwykłym limitem kroku/odstępu
  oraz blokadą wzrostu utrzymującą wartość poza zakresem; observation, dostępność,
  walidacja i retry nadal obowiązują. Poprawne min/max/step encji HA wystarczają,
  bez dodatkowej bramki pochodzenia limitów i bez własnego fallbacku produktu.
- Energia z istniejącego licznika, bez własnej całki mocy i okresów dzień/miesiąc.
  Ostrzeżenie nieskutecznego zamknięcia gaśnie przy wiarygodnym ustąpieniu dowolnego
  warunku lub otwarciu; brak danych tylko wstrzymuje ocenę, read nie kasuje przyczyny.
