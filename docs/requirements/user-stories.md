# User stories

Baza v0.7 z 11 listopada 2026, obejmująca rundy 1–6 oraz doprecyzowania D90–D101 z PR #36. Treść poniżej zawiera kryteria akceptacji; status procesu znajduje się w powiązanym Issue. Identyfikatory są trwałe. [Indeks i zasady](README.md) · [Produkt](product.md) · [Decyzje](decisions.md) · [Scenariusze odbioru — runda 5](round-05-acceptance.md).

<a id="us01"></a>

## US01 — Dodawanie i konfiguracja stref

Obszar: [E02](https://github.com/marcin-bugala/ha-HeatPumpSteering/issues/4). Dyskusja i status: [#8](https://github.com/marcin-bugala/ha-HeatPumpSteering/issues/8).

> Jako użytkownik chcę dodać strefę i wybrać jej czujnik temperatury bez edytowania YAML.

### Wstępne kryteria akceptacji

- Strefę można dodać, nazwać, edytować i wyłączyć przez UI integracji.
- Aktywna strefa wymaga jednego lub kilku poprawnie skonfigurowanych termometrów i własnego celu.
- Przy kilku termometrach można wybrać pomiar główny albo agregację średnią/medianą; szczegółowa filtracja należy do rundy regulacji.
- Brak skonfigurowanego sterowania zaworami nie uniemożliwia obserwacji strefy ani wykorzystania jej w regulacji PC.
- Konfiguracja nie zawiera narzuconych nazw pomieszczeń ani identyfikatorów encji.
- Kilka termometrów agregujemy przed filtracją w czasie; domyślnie średnią, z globalnym wyborem średnia/mediana.
- Funkcje i okna pomiarów są wspólne dla programu; progi reakcji stref są ustawiane osobno w konfiguracji zaawansowanej.
- Przy częściowej utracie termometrów strefa działa z pozostałym poprawnym pomiarem i pokazuje liczbę dostępnych źródeł.
- Skok po zmianie zestawu termometrów sam nie uruchamia zabezpieczenia nagłego spadku.

- Strefa ma trwały identyfikator; zmiana nazwy, grupy i czujnika zachowuje encje i ich powiązania. Usunięcie i ponowne dodanie tworzy nową tożsamość.
- Zmiana czujnika odbudowuje okna nowego źródła bez mieszania próbek. Zmiana konfiguracji jest walidowana, unieważnia stare polecenia i zachowuje nadal pasujący stan.

### Do doprecyzowania

- Kontrakty źródeł raportowania i techniczne rozpoznawanie jakości historii.

Powiązania: [US15](#us15), [US16](#us16)

<a id="us02"></a>

## US02 — Nastawa komfortu i pamięć ustawień

Obszar: [E02](https://github.com/marcin-bugala/ha-HeatPumpSteering/issues/4). Dyskusja i status: [#9](https://github.com/marcin-bugala/ha-HeatPumpSteering/issues/9).

> Jako użytkownik chcę zmieniać temperaturę zadaną strefy na dashboardzie i zachować ją po restarcie.

### Wstępne kryteria akceptacji

- Każda aktywna strefa ma własny cel temperatury.
- Ręczna zmiana celu CO jest nową, trwałą nastawą tej strefy, nie czasowym nadpisaniem. Harmonogram dotyczy tylko CWU.
- Cele CO są obsługiwane poza wspólnym panelem zapisu CWU.
- Zmiana celu jest uwzględniana w kolejnej ocenie regulatora; nie omija ograniczeń zapisu CO1.
- Cel pozostaje zachowany po restarcie i przeładowaniu integracji.
- Zmiana celu nie usuwa historii pomiarów.

- Aktualizacje zachowują cele, identyfikatory encji i powiązania zgodnie z US08.

- D96: cel 5–35°C co 0,5°C, początkowo podany przez użytkownika; zmiana celu zeruje zależne potwierdzenia temperatury bez resetu blokad zamknięcia/demandu.

### Do doprecyzowania

- Rozstrzygnięte D96: 5–35°C co 0,5°C; cel początkowy użytkownika. Zmiana celu zeruje zależne potwierdzenia temperatury, zachowuje terminy zamknięcia/demandu i historię.

Powiązania: [US01](#us01)

<a id="us03"></a>

## US03 — Obserwacja decyzji i świadome włączenie sterowania

Obszar: [E01](https://github.com/marcin-bugala/ha-HeatPumpSteering/issues/3). Dyskusja i status: [#10](https://github.com/marcin-bugala/ha-HeatPumpSteering/issues/10).

> Jako użytkownik chcę obserwować decyzje i sam wybrać, czy algorytm je wykonuje, czy wyłącznie pokazuje.

### Wstępne kryteria akceptacji

- Nowa konfiguracja rozpoczyna w obserwacji; obserwowane wyjścia nie otrzymują automatycznych poleceń.
- Dla włączonego CO encja nastawy PC jest wymagana także w obserwacji. Samo CWU nie wymaga encji CO1.
- Na dashboardzie są dwa niezależne przełączniki obserwacja/sterowanie: CO i CWU. Aktywacja jednego nie aktywuje drugiego.
- Przełączniki są poza zbiorczym panelem ustawień CWU; zapis tego panelu nie zmienia trybu obserwacja/sterowanie.
- W obu trybach widoczne są proponowana decyzja, jej powód i rzeczywisty stan instalacji.
- Powrót do obserwacji zatrzymuje następne automatyczne polecenia i nie cofa ostatnich nastaw.
- Aktywacja ponownie ocenia aktualne dane; nie odtwarza kolejki decyzji z obserwacji.
- Niespełnione warunki i brak danych blokują odpowiednie działania również w trybie aktywnym.
- Po restarcie odtwarzamy osobno zapisane tryby CO i CWU. Działanie wznawia się po przygotowaniu historii, sprawdzeniu wymaganych danych i bieżącej ocenie.
- Pierwsza konfiguracja pozostaje w obserwacji. Odbudowa historii nie wydaje poleceń.

- CO i CWU są niezależnie opcjonalne. Ponowne włączenie wyłączonego modułu zaczyna w obserwacji; zwykły restart lub aktualizacja odtwarza zapisany tryb.
- Wyłączenie/usunięcie integracji zatrzymuje polecenia i ponowienia, pozostawiając ostatni stan urządzeń.

### Do doprecyzowania

- Relacja trybów do przyszłego F01 i techniczny sposób zapisu oraz odtworzenia.

Powiązania: brak dodatkowych powiązań.

<a id="us04"></a>

## US04 — Wyjaśnianie decyzji regulatora

Obszar: [E01](https://github.com/marcin-bugala/ha-HeatPumpSteering/issues/3). Dyskusja i status: [#11](https://github.com/marcin-bugala/ha-HeatPumpSteering/issues/11).

> Jako użytkownik chcę wiedzieć, dlaczego regulator proponuje lub wykonuje zmianę CO1.

### Wstępne kryteria akceptacji

- Diagnostyka rozdziela bazę krzywej, aktywne korekty komfortu/trendu i wynik po ograniczeniach; prognozy są odłożone do US21.
- Widać proponowaną, wysłaną i potwierdzoną nastawę; brak dowodu potwierdzenia jest jawny.
- Widoczne są blokady, jakość danych, osiągnięcie limitów i najwcześniejszy kolejny zapis.
- Obserwacja i aktywne sterowanie mają porównywalny zapis przyczyn decyzji.
- Diagnostyka rozdziela wkłady aktywnych modułów komfortu/trendu, wspólny limit sumy, zakres pompy i węższy limit użytkownika.
- Pokazuje ochronę przegrzewania, timery stref/demandu oraz ostrzeżenie nieskutecznego zamknięcia.
- Program nie ocenia konfiguracji stale otwartych pętli; prognozy są odłożone i nie tworzą aktywnych korekt.
- D90: diagnostyka rozróżnia wysłanie, potwierdzenie wstępne od razu, ostateczne po ponownym zgodnym odczycie tej samej encji po 2 min i brak zgodnego odczytu. Nie utożsamia confirmed z dowodem fizycznym.
- Widać utratę pomiarów, odbudowę historii i gotowość okien oraz błąd zapisu po trzeciej nieudanej próbie.
- D90: potwierdzenie wstępne nie kasuje kontroli po domyślnie 2 min od wysłania. Poprawny zgodny ponowny odczyt kończy serię; późny odczyt aktualnego polecenia może zrobić to przed kolejną próbą.

- Eksport diagnostyki na żądanie przez HA obejmuje wersję, parametry, jakość danych, ostatnie decyzje, blokady i błędy. Nazwy własne i encje są zastąpione spójnymi oznaczeniami; brak sekretów i automatycznego wysyłania.
- Ostrzeżenie ustępuje po usunięciu przyczyny i spełnieniu warunków powrotu. Oznaczenie jako przeczytane nie kasuje problemu ani blokady; historia zachowuje wystąpienie i ustąpienie.

### Do doprecyzowania

- D90 rozstrzyga potwierdzenie odczytem tej samej encji HA; format pamięci i historii decyzji opisuje projekt techniczny do przeglądu.

Powiązania: [US03](#us03), [US17](#us17), [US19](#us19)

Scenariusze odbioru [A37, A38, A39, A59](round-05-acceptance.md#scenariusze-odbioru).

<a id="us05"></a>

## US05 — Niezależne ograniczanie grzania przegrzanej strefy

Obszar: [E02](https://github.com/marcin-bugala/ha-HeatPumpSteering/issues/4). Dyskusja i status: [#12](https://github.com/marcin-bugala/ha-HeatPumpSteering/issues/12).

> Jako użytkownik chcę zamknąć sterowane pętle przegrzanej strefy bez zatrzymania ogrzewania innych stref.

### Wstępne kryteria akceptacji

- Lokalne zamknięcie strefy jest pierwszą reakcją na przegrzewanie; wyjście należy tylko do jednej strefy, a strefa może mieć kilka wyjść.
- Typ NC/NO jest wspólny dla wyjść strefy, wybierany osobno dla niej.
- T do zaworów domyślnie jest średnią 30 min. Trend ΔT to różnica średnich 30 min/4 h; próg strefy domyślnie ±0,2°C.
- Rosnący trend zamyka przy T≥cel; malejący otwiera przy T≤cel. Przy niejasnym trendzie zamknięcie przy cel+0,2°C, otwarcie przy cel−0,2°C; poza warunkami poprzednie żądanie.
- Po nagłym spadku otwarcie wymaga 30 min utrzymującego się niedogrzania; ustąpienie warunku zeruje potwierdzenie.
- Minimum 30 min zamknięcia przed ponownym otwarciem; bez analogicznej blokady zamknięcia. Dwie blokady otwarcia biegną równolegle, nie są sumowane.
- Czasy powyżej i progi reakcji są konfigurowalne dla strefy; funkcje i okna są globalne zgodnie z rundą 3.
- Po zamknięciu wszystkich przypisanych wyjść pomijamy odchylenie strefy w korekcie CO1, nadal ją monitorując; strefy bez wyjść pozostają w ocenie.
- Ostrzeżenie po czasie zamykania i 120 min zamknięcia przy temperaturze komfortowej ≥cel+0,5°C i rosnącym trendzie. Czas i próg konfigurowalne dla strefy; bez przesądzania awarii lub automatycznego STOP PC.
- Nie modelujemy stale otwartych pętli. Konfiguracja zaworów pokazuje ostrzeżenie o zapewnieniu hydraulicznej drogi przepływu także przy zamkniętych strefach.
- Brak wszystkich termometrów strefy wstrzymuje potwierdzenia i usuwa jej korekty. Przez 30 min utrzymujemy ostatnie żądania, potem awaryjne otwarcie bez własnego demandu.
- Stan zaworu jest nieznany po błędzie przekaźnika. Strefa nie wystarcza wtedy do ON demandu. Nieudane zamknięcie nie usuwa strefy z ochrony przegrzewania.
- Bez wcześniejszego żądania między progami utrzymujemy odczytany stan i czekamy na warunek otwarcia przed zgłoszeniem zapotrzebowania.
- Gotowy pomiar zaworów bez gotowego trendu używa progów trendu niejasnego. Blokada otwarcia może upłynąć w przerwie przy wiarygodnym stanie.
- Jeden globalny Czas pracy siłowników, domyślnie 3 min, obejmuje otwieranie i zamykanie. Po raporcie przekaźnika pokazujemy ruch, a po czasie przewidywany stan.
- Ocenę 120-minutowego warunku ostrzeżenia rozpoczynamy po czasie pracy przy zamykaniu.

### Do doprecyzowania

- Rozstrzygnięte: D90 potwierdzenie, D93 polaryzacja bindingu, D100 ustąpienie ostrzeżenia przy wiarygodnym zaniku warunku lub otwarciu. Brak danych nie kasuje problemu.

Powiązania: [US09](#us09), [US10](#us10), [US15](#us15)

Scenariusze odbioru [A10, A11, A12, A13, A14, A15, A16, A17, A20, A31, A36, A42](round-05-acceptance.md#scenariusze-odbioru).

<a id="us06"></a>

## US06 — Odporność na wietrzenie i krótkie zyski ciepła

Obszar: [E01](https://github.com/marcin-bugala/ha-HeatPumpSteering/issues/3). Dyskusja i status: [#13](https://github.com/marcin-bugala/ha-HeatPumpSteering/issues/13).

> Jako użytkownik chcę, aby krótkie wietrzenie, gotowanie i słońce nie wywoływały agresywnych zmian CO1.

### Wstępne kryteria akceptacji

- Zakłócenia nie są całkowicie ignorowane: gotowanie/słońce może zamknąć lokalne zawory, bez agresywnej zmiany CO1.
- Nagły spadek wymaga domyślnie 30 min utrzymującego się warunku niedogrzania w poprawnych obserwacjach przed otwarciem. Czas dla strefy, ustąpienie warunku zeruje potwierdzenie.
- Trwały wzrost/spadek przechodzi do filtrów komfortu i nie jest bezterminowo odrzucany.
- Do zaworów domyślnie średnia 30 min, do CO1 mediana 3 h; dla każdego wybór średnia/mediana i 30 min–6 h co 30 min, wspólnie dla programu.
- Trend zaworów: wspólna funkcja dla krótkiego i długiego punktu, niezależne okna i zakresy z rundy 3; 2 h / 2 h odrzucane.
- Korekta długoterminowego wzrostu CO1 jest osobna: 12 h, próg 0,2°C, pełne −0,5°C przy 0,5°C, liniowo pomiędzy, tylko bez ważonego niedogrzania.
- Nagły spadek to bieżący pomiar niższy od temperatury komfortowej o ponad 0,7°C. Próg konfigurowalny dla strefy.
- Zmiana zestawu dostępnych czujników nie tworzy sama alarmu spadku. Potwierdzenie liczy poprawne obserwacje, z zachowaniem postępu po restarcie.

### Do doprecyzowania

- Sposób ustalenia ciągłości historii źródła i szczegółowe scenariusze odbioru.

Powiązania: [US19](#us19)

<a id="us07"></a>

## US07 — Sterowanie ręczne i oddawanie kontroli

Obszar: [E01](https://github.com/marcin-bugala/ha-HeatPumpSteering/issues/3). Dyskusja i status: [#14](https://github.com/marcin-bugala/ha-HeatPumpSteering/issues/14).

> Jako użytkownik chcę zachować kontrolę ręczną i znać zasady powrotu do automatyki.

### Wstępne kryteria akceptacji

- Ręczna zmiana jest rozpoznawana w zakresie pozwalającym na to przez encje HA.
- Dashboard pokazuje obowiązujący tryb i ewentualne nadpisanie.
- Cel CO zmieniony ręcznie jest trwałą nastawą konkretnej strefy.
- Reguły pierwszeństwa są jawne i spójne dla danego modułu.
- Odzyskanie kontroli nie wykonuje nieaktualnych poleceń.
- Rozpoznana ręczna zmiana CO1 na pompie lub w aplikacji pozostawia regulator aktywny, bez dodatkowej pauzy. Kolejny dozwolony zapis realizuje jego bieżącą decyzję.
- W CWU/Harmonogram zmiany spoza panelu tworzą nadpisanie do następnej rzeczywistej zmiany planu lub zapisu panelu w Harmonogram.
- Zapis panelu w Harmonogram kończy nadpisanie i natychmiast stosuje bieżący przedział, także przy identycznym planie.
- Przy jednakowym planie całotygodniowym nadpisanie trwa do ręcznej zmiany lub zapisu panelu w Harmonogram. Dashboard informuje o braku zaplanowanej zmiany.
- Zależna od trybu dostępność pól CWU wyklucza równoczesną edycję temperatury stałej i harmonogramu.

- D91: każda niealgorytmiczna zmiana ustawienia CWU external; brak kategorii ambiguous/blokady pochodzenia. D92: ręczny demand nie zatrzymuje automatu, OFF nie resetuje retry.

### Do doprecyzowania

- D91: każda niealgorytmiczna zmiana CWU external, bez kategorii ambiguous. D92: ręczny demand nie pauzuje; OFF nie resetuje liczników/terminów retry.

Powiązania: [US03](#us03)

Scenariusze odbioru [A08, A26, A47, A48, A49](round-05-acceptance.md#scenariusze-odbioru).

<a id="us08"></a>

## US08 — Aktualizacje, trwałość danych i możliwość wycofania

Obszar: [E01](https://github.com/marcin-bugala/ha-HeatPumpSteering/issues/3). Dyskusja i status: [#15](https://github.com/marcin-bugala/ha-HeatPumpSteering/issues/15).

> Jako użytkownik chcę aktualizować integrację z zachowaniem ustawień, historii i ciągłości działania oraz znać sposób powrotu do wcześniejszego wydania.

### Wstępne kryteria akceptacji

- Aktualizacja zachowuje konfigurację, cele, harmonogramy, tożsamość encji, historię pomiarów i decyzji oraz potrzebne stany, timery, nadpisania i ponowienia.
- Nie powoduje resetu algorytmu, nieplanowanych przełączeń ani zbierania dostępnej historii od zera. Restart oznacza przerwę wykonania, po której następuje poprawna kontynuacja z oceną bieżących danych.
- Konfiguracja korzysta z mechanizmów HA i migracji; stan z Store, historia z Recordera, bez osobnej bazy danych.
- Nie usuwamy historii przy aktualizacji. Dostępność starszych pomiarów podlega filtrom i retencji HA; brakujące pomiary pozostają brakami.
- Każde wydanie określa minimum HA, wersje sprawdzone, zmiany i procedurę powrotu.
- Starsza wersja przy niezgodnych danych pokazuje błąd bez ich resetowania i uruchamiania sterowania. Instrukcja wskazuje potrzebę odtworzenia właściwej kopii HA.
- POC jest osobny i nie stanowi warunku instalacji, aktualizacji ani odbioru produktu. Nie tworzymy importera ani obowiązkowej ścieżki migracji POC.

### Do doprecyzowania

- Schematy i wersjonowanie konfiguracji/Store, procedury migracji, sprawdzanie zgodności i testy aktualizacji.
- D101: minimum HA 2026.10.4 i macierz z 2026.11.1 przyjęte; T08 wymaga zgodnych zależności testowych.

Powiązania: [US02](#us02), [US03](#us03), [US19](#us19)

Scenariusze: A41, A43, A58 oraz B05–B08 w [rundzie 6](round-06-architecture.md).

<a id="us09"></a>

## US09 — Niezależny wybór sterowania strefami i demandem

Obszar: [E02](https://github.com/marcin-bugala/ha-HeatPumpSteering/issues/4). Dyskusja i status: [#16](https://github.com/marcin-bugala/ha-HeatPumpSteering/issues/16).

> Jako użytkownik chcę podczas konfiguracji niezależnie wskazać, czy mam sterowanie strefami i wyjście demand.

### Wstępne kryteria akceptacji

- Podstawą produktu pozostaje regulacja jednej nastawy temperatury PC dla jednego wspólnego obiegu i wielu stref.
- Niezależnie wybieramy sterowanie zaworami stref i demand: obie funkcje wyłączone, same zawory, sam demand lub obie funkcje włączone. Strefy pomiarowe istnieją również bez wyjść zaworów.
- Wyjścia zaworów wymagane są tylko przy ich sterowaniu; wyjście demand tylko przy włączonym demandzie.
- Bez demandu integracja nie przełącza ogrzewania ON/OFF, także przez encję CO1.
- Można później dołączyć te możliwości bez ponownego tworzenia całej konfiguracji.
- Zmiana konfiguracji sama nie aktywuje nowych wyjść.
- Demand jest OR zapotrzebowań aktywnych stref według reguł otwarcia, również wirtualnych dla stref bez wyjść.
- Brak wszystkich zapotrzebowań wyłącza demand bez dodatkowego opóźnienia; brak minimalnego ON.
- Ponowne ON wymaga minimum 15 min od OFF, globalnie konfigurowalne; wyjścia mogą otworzyć się wcześniej, lecz ON wymaga aktualnego zapotrzebowania i gotowości.
- Program nie modeluje otwartych pętli i nie steruje zasilaniem ani wybiegiem PC; ostrzeżenie hydrauliczne w konfiguracji zaworów.
- Awaryjne otwarcie strefy bez pomiaru po okresie przejściowym nie dodaje zapotrzebowania. Po utracie wszystkich temperatur wycofujemy demand i pozostawiamy krzywą z outdoor.
- Po błędzie wyjścia pokazujemy stan żądany i raportowany. Aktualne polecenie podlega wspólnym ponowieniom. Strefa bez potwierdzenia przekaźnika nie jest gotowa do ON.
- Przerwę 15 min liczymy od potwierdzonego raportowanego OFF. Po restarcie uwzględniamy upływ przerwy, jeśli odczyt i zapamiętany czas są wiarygodne.
- ON po przewidywanym otwarciu jednej potrzebującej strefy, po globalnym czasie pracy siłowników domyślnie 3 min i z zachowaniem blokady demandu.
- Dla OFF o 10:00 i potwierdzonego przekaźnika otwarcia o 10:05 gotowość wypada o 10:08, a ON najwcześniej o 10:15. Zanik zapotrzebowania wcześniej anuluje ON.

- Pierwsze kompletne wydanie developerskie obejmuje CO i strefy, opcjonalne zawory i demand oraz niezależne CWU. Jedna konfiguracja obejmuje jedną pompę, maksymalnie jeden obieg CO i jedno CWU.
- Architektura przewiduje przyszłe dwa obiegi CO jednej pompy, z osobnymi strefami, nastawami i Demand 1/2, regulowane tymi samymi regułami niezależnie. Funkcja dwóch obiegów pozostaje przyszła.
- Współdzielenie encji wykonawczej między niezależnymi funkcjami lub konfiguracjami jest blokowane. Czujniki można współdzielić; ostrzegamy o możliwym konflikcie z zewnętrznymi regulatorami bez ich wyłączania.
- Odłączenie wyjścia pokazuje przed zatwierdzeniem jego stan i ostrzeżenie o pozostawieniu tego stanu; anuluje polecenia i ponowienia.

- D92: po ręcznej zmianie demandu następna dozwolona ocena uzgadnia automat; trwałe oddanie kontroli przez obserwację CO. OFF nie resetuje liczników i terminów retry.

### Do doprecyzowania

- D90/D92/D93 rozstrzygają potwierdzenie, ręczny demand i polaryzację; brak dodatkowego warunku niezależnej telemetrii.

Powiązania: [US03](#us03), [US15](#us15), [US16](#us16)

Scenariusze odbioru [A01, A02, A03, A14, A27, A28, A29, A31, A33, A34, A36, A40, A43, A56](round-05-acceptance.md#scenariusze-odbioru).

<a id="us10"></a>

## US10 — Konfiguracja siłowników NC i NO

Obszar: [E02](https://github.com/marcin-bugala/ha-HeatPumpSteering/issues/4). Dyskusja i status: [#17](https://github.com/marcin-bugala/ha-HeatPumpSteering/issues/17).

> Jako użytkownik chcę podczas konfiguracji wybrać NC albo NO, aby integracja poprawnie otwierała i zamykała pętle.

### Wstępne kryteria akceptacji

- Typ NC/NO wybierany jest osobno podczas konfiguracji każdej strefy sterującej zaworami; krok jest pomijany w strefie bez tych wyjść.
- Wszystkie wyjścia strefy używają jej typu NC/NO; różne strefy mogą mieć różne typy. Nie ma globalnego typu ani wyjątków NC/NO dla wyjść.
- NC: zasilanie otwiera, brak zasilania zamyka; NO: zasilanie zamyka, brak zasilania otwiera.
- Dashboard przedstawia polecenie i przewidywany stan hydrauliczny niezależnie od ON/OFF przekaźnika.
- Bez sprzężenia zwrotnego przewidywany stan nie jest oznaczany jako potwierdzony.
- Sam wybór lub zmiana typu nie wysyła poleceń.
- Raport przełączenia przekaźnika jest wymagany przed uznaniem przewidywanego otwarcia po upływie czasu ruchu. Błąd oznacza stan nieznany i wspólną politykę ponowień.
- Jeden Czas pracy siłowników jest ustawieniem domu, domyślnie 3 min, wspólnym dla otwierania i zamykania.
- Po raporcie przekaźnika pokazujemy Otwieranie/Zamykanie, następnie przewidywany stan końcowy. Dalsza ocena ostrzeżenia zamknięcia rozpoczyna się po tym czasie.

- D93: polaryzacja każdego bindingu oddzielnie od NC/NO strefy; zmiana mapowania sama nie wysyła polecenia.

### Do doprecyzowania

- D93: polaryzacja per binding odrębna od NC/NO strefy; D90: odczyt HA i kontrola po 2 min, bez dowodu fizycznego.

Powiązania: [US09](#us09)

Scenariusze odbioru [A04, A17, A27](round-05-acceptance.md#scenariusze-odbioru).

<a id="us11"></a>

## US11 — Dashboard temperatur i celów stref

Obszar: [E02](https://github.com/marcin-bugala/ha-HeatPumpSteering/issues/4). Dyskusja i status: [#18](https://github.com/marcin-bugala/ha-HeatPumpSteering/issues/18).

> Jako użytkownik chcę na dashboardzie widzieć temperaturę aktualną i zadaną oraz zmieniać cel każdej strefy.

### Wstępne kryteria akceptacji

- Dostępne są odczyt i edycja celu każdej aktywnej strefy; zmiana tworzy trwałą nastawę tej strefy.
- Cele CO i niezależne przełączniki obserwacja/sterowanie CO/CWU są poza panelem zbiorczego zapisu CWU.
- Brak danych, nieaktywność i oczekiwanie na filtry są czytelnie rozróżnione.
- Panel działa dla jednej strefy Dom i dla wielu pomieszczeń lub kondygnacji.
- Nie wymaga ręcznego tworzenia helperów do podstawowej obsługi celów.
- Wymaganie uzupełnia US02; nie tworzy drugiego źródła nastaw.

- Gotowa karta i encje do własnych dashboardów są częścią pierwszego wydania; interfejs i komunikaty są w PL/EN. Strojenie pozostaje w osobnym ekranie zaawansowanym.

### Do doprecyzowania

- D101: TypeScript/Lit, cel number; D96: 5–35°C co 0,5°C. Szczegóły UI w projekcie do przeglądu.

Powiązania: [US02](#us02), [US12](#us12), [US15](#us15)

<a id="us12"></a>

## US12 — Dashboard zaworów, pompy, mocy i energii

Obszar: [E01](https://github.com/marcin-bugala/ha-HeatPumpSteering/issues/3). Dyskusja i status: [#19](https://github.com/marcin-bugala/ha-HeatPumpSteering/issues/19).

> Jako użytkownik chcę widzieć stan zaworów i pompy oraz aktualną moc i zużycie energii.

### Wstępne kryteria akceptacji

- Pokazywane są stany sterowanych zaworów z informacją o jakości potwierdzenia.
- Dostępne tryby pompy CO/CWU/postój/nieznany są prezentowane tylko na podstawie wiarygodnych danych.
- Zezwolenie na grzanie nie jest utożsamiane z pracą sprężarki.
- Moc jest przedstawiona w W/kW, energia w kWh; jednostki są weryfikowane.
- Brak opcjonalnego licznika nie blokuje regulatora i nie jest przedstawiany jako zerowe zużycie.
- Ostrzeżenie nieskutecznego zamknięcia wskazuje potrzebę sprawdzenia zaworów i innych źródeł ciepła, bez automatycznej diagnozy usterki.
- Progi, funkcje i czasy algorytmu są w osobnej konfiguracji zaawansowanej; nie są suwakami codziennego dashboardu.
- Dashboard pokazuje ograniczoną dostępność termometrów, nieznany stan zaworów, status zapisu, postęp odbudowy historii i braki w oknach.

- Karta produktu dostarcza stan stref, zaworów, pompy, dostępnej mocy/energii i wyjaśnienia decyzji, bez instalacji kart innych autorów.
- Niedostępność opcjonalnego licznika ogranicza diagnostykę, nie zatrzymuje sprawnego CO ani CWU.

- D100: energia z istniejącego licznika, bez własnej całki mocy i okresów dzień/miesiąc. Brak danych nie kasuje ostrzeżenia nieskutecznego zamknięcia.

### Do doprecyzowania

- D100: energia tylko z istniejącego licznika, bez własnej całki i okresów dzień/miesiąc. Tryb pracy tylko z udokumentowanych źródeł; bez nich nieznany.

Powiązania: [US04](#us04), [US16](#us16)

<a id="us13"></a>

## US13 — CWU stale lub według harmonogramu

Obszar: [E03](https://github.com/marcin-bugala/ha-HeatPumpSteering/issues/5). Dyskusja i status: [#20](https://github.com/marcin-bugala/ha-HeatPumpSteering/issues/20).

> Jako użytkownik chcę w panelu sterowania wybrać stałe podgrzewanie CWU albo pracę według harmonogramu.

### Wstępne kryteria akceptacji

- Panel ma trzy tryby. Wyłączone blokuje pole temperatury i obszar planu. Stałe udostępnia temperaturę i blokuje plan. Harmonogram udostępnia plan i blokuje temperaturę stałą.
- W Wyłączone żądamy OFF CWU bez wyłączania ogrzewania domu. Stałe używa jednej nastawy. Harmonogram stosuje aktualny przedział.
- Jeden Zapisz zatwierdza poprawny zestaw ustawień, a zamknięcie niezapisanej edycji wymaga potwierdzenia odrzucenia. Brak osobnego potwierdzenia samego Wyłączone.
- Zapis panelu w Harmonogram kończy wcześniejsze nadpisanie i od razu stosuje bieżący przedział, także przy identycznym planie.
- Ręczne nadpisania spoza panelu trwają do kolejnej rzeczywistej zmiany planu lub zapisu panelu w Harmonogram. Przy stałym planie tygodniowym trwają do ręcznej zmiany albo tego zapisu, z komunikatem o braku zaplanowanej zmiany.
- Cele CO i przełączniki obserwacja/sterowanie pozostają poza panelem. W obserwacji zapis przygotowuje ustawienia i decyzje.
- Włączenie CWU wymaga wcześniejszego potwierdzenia temperatury. OFF jest niezależne od zapisu temperatury. Po częściowym wykonaniu ponawiamy nadal potrzebne działanie.
- Po restarcie przywracamy ważne nadpisanie albo aktualny przedział. Temperatury respektują zakres urządzenia i jego zabezpieczenia.
- Dashboard pokazuje bieżący tryb, nastawę i najbliższą zmianę. Włączenie oznacza zezwolenie na podgrzewanie pod kontrolą PC.

- CWU jest niezależnie opcjonalnym modułem pierwszego kompletnego wydania. Może działać bez CO, jego stref i outdoor; niekonfigurowany moduł nie udostępnia swojego panelu i encji.
- Panel CWU dostarczamy razem z integracją; interfejs, komunikaty i instrukcje instalacji/konfiguracji są w PL/EN.
- Awaria CWU nie zatrzymuje sprawnego CO; blokujemy tylko zależne działania.

- D94/D95: bez obsługi higieny; start Nieskonfigurowane i jawny zapis temperatury/planu. D90: po nowym zapisie temperatury ON czeka na ostateczny odczyt po 2 min.

### Do doprecyzowania

- D95: początek Nieskonfigurowane, temperatura Stałe/ON i cały plan jawnie zatwierdzone, szkic 7×48 OFF nie steruje. D94: higieny CWU nie obsługujemy; bez dodatkowych encji, wykrywania, blokad i warunku aktywacji.
- D91: każda niealgorytmiczna zmiana CWU external; D90: potwierdzenie wstępne od razu i ostateczny ponowny odczyt tej samej encji po 2 min.

Powiązania: [US14](#us14), [US16](#us16)

Scenariusze odbioru [A44, A45, A46, A47, A48, A49, A50, A51, A52, A53](round-05-acceptance.md#scenariusze-odbioru).

<a id="us14"></a>

## US14 — Tygodniowy harmonogram CWU co 30 minut

Obszar: [E03](https://github.com/marcin-bugala/ha-HeatPumpSteering/issues/5). Dyskusja i status: [#21](https://github.com/marcin-bugala/ha-HeatPumpSteering/issues/21).

> Jako użytkownik chcę oddzielnie zaplanować każdy dzień tygodnia z dokładnością 30 minut i temperaturą na przedział.

### Wstępne kryteria akceptacji

- Każdy dzień ma 48 logicznych przedziałów półgodzinnych.
- Przedział oznacza wyłączone albo zezwolenie na grzanie do wskazanej temperatury.
- Harmonogram i nastawy są zachowane po restarcie.
- Ręczne nadpisanie spoza panelu działa do następnej rzeczywistej zmiany stanu/temperatury planu albo zapisu panelu w Harmonogram. Identyczne sąsiednie pola zachowują nadpisanie.
- Sąsiednie identyczne pola tworzą ciągły okres; nie kasują nadpisania.
- Harmonogram edytujemy razem z pozostałymi ustawieniami CWU, z jednym Zapisz i potwierdzeniem odrzucenia niezapisanej edycji.
- Harmonogram CWU nie steruje ogrzewaniem pomieszczeń ani ich celami.
- Wartości temperatur są walidowane względem urządzenia.
- Restart zachowuje nadpisanie tylko do zapisanego terminu. Po jego upływie stosujemy bieżący przedział harmonogramu bez odtwarzania pominiętych zmian.
- Zapis w Harmonogram natychmiast stosuje jego aktualny przedział i kończy nadpisanie zewnętrzne, także przy ponownym zapisie identycznego planu.
- Plan używa strefy czasowej HA. Po przeskoku zegara stosujemy aktualny lokalny przedział, a cofnięcie powtarza te same pola.
- Blokady i ponowienia mierzą rzeczywisty upływ czasu. Nadpisanie kończy kolejna rzeczywista zmiana ustawienia z lokalnego planu.
- Brak następnej zmiany w tygodniu zachowuje nadpisanie do ręcznej zmiany albo zapisu panelu w Harmonogram, z komunikatem diagnostycznym.

- D95: szkic planu 7×48 OFF i kopiowanie dni są tylko edycją roboczą; bez zatwierdzenia nie wywołują OFF urządzenia.

### Do doprecyzowania

- D95: brak aktywnego planu do jawnego zapisu całego zestawu; szkic 7×48 OFF i kopiowanie dni tylko w draft. Lokalny plan HA i terminy UTC opisuje projekt.

Powiązania: [US13](#us13), [US07](#us07)

Scenariusze odbioru [A44, A47, A48, A49, A50, A51, A54, A55, A56](round-05-acceptance.md#scenariusze-odbioru).

<a id="us15"></a>

## US15 — Dom, kondygnacje lub pomieszczenia jako strefy

Obszar: [E02](https://github.com/marcin-bugala/ha-HeatPumpSteering/issues/4). Dyskusja i status: [#22](https://github.com/marcin-bugala/ha-HeatPumpSteering/issues/22).

> Jako użytkownik chcę odwzorować cały dom, kondygnacje lub pomieszczenia bez narzuconej struktury pięter.

### Wstępne kryteria akceptacji

- Dopuszczalna jest jedna strefa Dom albo wiele nazwanych stref, każda z jednym lub kilkoma termometrami.
- Strefy są niezależne i mają własne cele. Grupy porządkowe służą tylko prezentacji, bez odrębnego celu, wyjść ani dodatkowego ważenia.
- Wszystkie strefy współpracują z jednym wspólnym obiegiem i jedną nastawą PC; wiele niezależnych obiegów pozostaje poza pierwszą wersją.
- Wyjście zaworów należy do jednej strefy; strefa może zawierać kilka wyjść, w tym przekaźnik grupy pętli.
- Każda aktywna strefa ma co najmniej jeden termometr oraz cel.
- Czujnik i obliczane zapotrzebowanie mogą istnieć bez fizycznego zaworu.
- Przyszła trzecia kondygnacja nie wymaga zmiany kodu.
- Nie modelujemy stale otwartych pętli ani przepływów; konfiguracja nie zawiera wcześniejszego pola informacyjnego. To założenia sprzętowe użytkownika.
- Przy sterowaniu zaworami pokazujemy ostrzeżenie o wymaganym przepływie również przy zamkniętych strefach.
- Po zamknięciu wszystkich przypisanych wyjść strefa jest pomijana w korekcie CO1, nadal monitorowana; strefa bez wyjść jest uwzględniana wraz z ochroną przegrzewania.

### Do doprecyzowania

Model stref uzgodniono w rundzie 1. Szczegóły agregacji pomiarów rozwija US01 w rundzie regulacji; nie wprowadzają dodatkowej hierarchii stref.

Powiązania: [US01](#us01), [US09](#us09)

<a id="us16"></a>

## US16 — Wybór wymaganych i opcjonalnych źródeł

Obszar: [E04](https://github.com/marcin-bugala/ha-HeatPumpSteering/issues/6). Dyskusja i status: [#23](https://github.com/marcin-bugala/ha-HeatPumpSteering/issues/23).

> Jako użytkownik chcę dodać tylko dostępne czujniki, prognozy i sterowniki, aby konfiguracja pasowała do instalacji.

### Wstępne kryteria akceptacji

- Aktywna strefa wymaga temperatury; regulacja CO1 wymaga bieżącej temperatury zewnętrznej.
- Encja nastawy CO1 musi być wskazana przy konfiguracji modułu CO, również w obserwacji. Sama konfiguracja CWU jej nie wymaga.
- Minimum modułu CO to nastawa CO1, outdoor i aktywna strefa z termometrem oraz celem. Samo CWU wymaga tylko encji swojego modułu.
- Zawory i demand wymagają wyjść tylko po włączeniu tych funkcji.
- Brak opcjonalnego źródła nie blokuje podstawowych funkcji ani nie oznacza wartości zero.
- Utrata skonfigurowanego źródła jest widoczna wraz z wpływem na działanie.
- Integracja korzysta z encji/integracji HA, bez wymogu konkretnej marki sprzętu.
- Moc/energia PC i temperatury zasilania/powrotu pozostają opcjonalną diagnostyką.
- Prognozy pogody, nasłonecznienia i PV przeniesiono do odłożonej US21; bieżący program ich nie konfiguruje ani nie używa.
- Zakres nastawy czytamy z pompy; użytkownik może go wyłącznie zawęzić. Bieżący outdoor pozostaje wymagany, domyślnie średnia 2 h, konfigurowalna średnia/mediana i okno 30 min–6 h co 30 min.
- Domyślny limit świeżości to 120 min dla termometrów stref i 30 min dla outdoor, liczony od raportu. Jawnie niedostępny lub niepoprawny odczyt jest utracony od razu.
- Brak outdoor, nastawy PC albo wiarygodnych limitów wstrzymuje nowe zapisy CO1. Poprawne zawory, demand i CWU działają według własnych źródeł.

- Transport do urządzeń zapewniają integracje źródłowe. Nasz produkt czyta i steruje przez encje HA.
- Brak opcjonalnego modułu lub urządzenia ogranicza tylko zależne funkcje.

- D90: poprawne min/max/step encji HA wystarczają do walidacji zakresu, bez dodatkowego dowodu ich pochodzenia. Brak/niepoprawny zakres nadal blokuje zapis.

### Do doprecyzowania

- D90: operacyjne potwierdzenie tej samej encji HA, bez wymogu dowodu fizycznego/pochodzenia limitów; D97: konserwatywna historia. Jednostki/raporty opisuje projekt.
- Profile prognoz pozostają w odłożonej US21.

Powiązania: [US09](#us09), [US15](#us15)

<a id="us17"></a>

## US17 — Konfigurowalna krzywa grzewcza A, B i Tref

Obszar: [E01](https://github.com/marcin-bugala/ha-HeatPumpSteering/issues/3). Dyskusja i status: [#24](https://github.com/marcin-bugala/ha-HeatPumpSteering/issues/24).

> Jako użytkownik chcę ustawiać przesunięcie, nachylenie i punkt odniesienia krzywej grzewczej.

### Wstępne kryteria akceptacji

- Bazą jest Tbase = A + B × (Tref − Ta).
- A, B i Tref są ustawiane osobno; początkowe wartości według product.md to 20°C, 0,2 i 20°C.
- Ta jest przefiltrowaną bieżącą temperaturą zewnętrzną, a nie prognozą.
- Aktywne korekty komfortu i trendu są oddzielone od bazy i widoczne diagnostycznie; przyszłe prognozy są odłożone do US21.
- Zmiana współczynników nie omija limitów temperatury, kroku ani częstotliwości zapisu.
- Korekta komfortu używa ważonego błędu stref: martwa strefa ±0,2°C, współczynnik 1,5 po jej odjęciu, limit komfortu ±2°C; parametry zaawansowane programu.
- Trend długoterminowy i jego liniowe progi określa runda 3; brak historii wyłącza tylko tę korektę.
- Suma aktywnych korekt ma globalny konfigurowalny limit, domyślnie ±2°C, dopuszczający większą wartość.
- Zakres z ustawień PC jest nadrzędny; użytkownik może go tylko zawęzić.
- Pełna precyzja obliczeń, końcowe zaokrąglenie do najbliższego kroku PC, połówki w górę, w dozwolonym zakresie.
- Do celu dochodzimy domyślnie o najwyżej 1°C co 120 min w obu kierunkach, bez zapisu identycznej nastawy; parametry programu respektują możliwości PC.
- Regulator przelicza domyślnie co 5 min i po zmianach celu/trybu; timery kończą się niezależnie od cyklu, bez omijania blokad.
- Po utracie temperatur wszystkich stref i upływie okresu przejściowego stosujemy krzywą bez korekt przy poprawnym outdoor. Gdy wszystkie poprawnie mierzone strefy są zamknięte, utrzymujemy nastawę.
- Ponowienie niepotwierdzonej wartości dotyczy tej samej bezwzględnej nastawy. Kolejny krok regulatora wymaga wiarygodnego potwierdzenia oraz blokady 1°C/120 min.
- Trzy próby łącznie w odstępach 5 min, potem błąd i narastające przerwy do 120 min zgodnie z rundą 4.
- Rozpoznana ręczna zmiana nastawy PC pozostawia CO1 aktywne, bez dodatkowej pauzy. Kolejne dozwolone polecenie uwzględnia bieżącą wartość oraz ograniczenia.
- Limit oczekiwania na potwierdzenie wynosi domyślnie 2 min. Próby bez potwierdzenia o 10:00, 10:05 i 10:10 dają błąd o 10:12, następne próby o 10:20 i 10:35.

- D99: gdy obecna nastawa jest poza obowiązującym zakresem, obcinamy do najbliższej dopuszczalnej granicy i oznaczamy konflikt. Korekta graniczna ma pierwszeństwo przed zwykłym krokiem/odstępem i blokadą wzrostu utrzymującą wartość poza zakresem; observation, walidacja i retry nadal obowiązują.

### Do doprecyzowania

- D90: potwierdzenie odczytem tej samej encji po 2 min. D99: nastawę poza zakresem obcinamy do granicy i oznaczamy konflikt; korekta ma pierwszeństwo przed zwykłym krokiem/odstępem. D98: przypadek mieszany bez kwalifikowanych stref daje bazę outdoor.

Powiązania: [US04](#us04), [US16](#us16), [US19](#us19)

Scenariusze odbioru [A06, A18, A19, A20, A21, A22, A23, A24, A25, A26, A33, A34, A35, A37, A38, A39, A40](round-05-acceptance.md#scenariusze-odbioru).

<a id="us18"></a>

## US18 — Priorytety stref i ważony komfort

Obszar: [E04](https://github.com/marcin-bugala/ha-HeatPumpSteering/issues/6). Dyskusja i status: [#25](https://github.com/marcin-bugala/ha-HeatPumpSteering/issues/25).

> Jako użytkownik chcę ustawiać priorytet strefy, aby jej potrzeba komfortu miała odpowiednią wagę w regulacji wspólnej temperatury wody.

### Wstępne kryteria akceptacji

- Priorytet strefy 1–5, domyślnie 3, dostępny wyłącznie w konfiguracji zaawansowanej.
- Dla e=cel−temperatura komfortowa wyliczamy E=suma(w×e)/suma(w); równy priorytet daje równy udział.
- Priorytety nie zmieniają celów ani lokalnych warunków zamknięcia; przy przegrzaniu najpierw ograniczamy lokalne wyjścia.
- Po zamknięciu wszystkich wyjść strefy jej odchylenie pomijamy w korekcie CO1; strefę nadal monitorujemy.
- Dla stref bez sterowanych wyjść przegrzanie ≥cel+0,5°C przez 60 min blokuje wzrost CO1, a ≤cel+0,2°C przez 30 min zwalnia blokadę. Progi i czasy konfigurowalne dla strefy.
- Blokada nie wymusza wyłączenia demandu; jej zwolnienie nie wymusza podniesienia temperatury.
- Nie modelujemy pętli stale otwartych. Wagi prognoz i ich szczegółowy algorytm odłożono do US21.
- Strefa bez poprawnych pomiarów jest pomijana w korekcie pokojowej. Wszystkie zamknięte strefy z poprawnymi danymi oznaczają utrzymanie aktualnej nastawy.

- D98: przypadek mieszany bez kwalifikowanych stref → baza outdoor bez korekt pokojowych, z zachowaniem pozostałych blokad i odrębnych reguł D49.

### Do doprecyzowania

- D98: przypadek mieszany bez kwalifikowanych stref daje bazę bez korekt pokojowych z zachowaniem blokad; przypadki wszystkich poprawnych zamkniętych / wszystkich utraconych pozostają D49.

Powiązania: [US16](#us16), [US17](#us17), [US19](#us19)

<a id="us19"></a>

## US19 — Przeniesienie doświadczeń POC do produktu

Obszar: [E01](https://github.com/marcin-bugala/ha-HeatPumpSteering/issues/3). Dyskusja i status: [#26](https://github.com/marcin-bugala/ha-HeatPumpSteering/issues/26).

> Jako użytkownik chcę zachować sprawdzone mechanizmy POC i oceniać nowy regulator względem prototypu.

### Wstępne kryteria akceptacji

- Wymagania obejmują filtry, trendy, krótkie zakłócenia, konflikt stref i ograniczenia zmian.
- Oceniane są kompletność danych, jednostki i rozgrzewanie filtrów.
- Pamięć zachowuje potrzebne próbki i czasy; braki obserwacji nie stają się fikcyjnymi pomiarami.
- D90: polecenie, raport HA, potwierdzenie wstępne i ostateczny odczyt po 2 min są rozróżnione; niezależny dowód fizyczny jest opcjonalny, niewymagany do sterowania.
- Scenariusze POC służą testom porównawczym, ale konkretne progi nie są bez oceny kopiowane.
- Auto STOP CO1 z POC nie przechodzi automatycznie do konfiguracji produktu bez demandu.
- Przyjęte wartości początkowe i odstępstwa od POC określa runda 3; ustalenia produktu są nadrzędne wobec prototypu.
- Oddzielamy bazę, moduły korekt i zabezpieczenia (US20). Prognozy są poza bieżącą wersją (US21).
- Pierwszy start, restart i przeładowanie odtwarzają dostępne pomiary, średnie, mediany i trendy z domyślnie 48 h historii, bez podwójnego liczenia próbek.
- Każde okno potrzebuje 80% pokrycia i świeżego bieżącego pomiaru. Brak trendu przy gotowym pomiarze zaworów pozwala użyć progów niejasnego trendu.
- Pamięć obejmuje zapisane tryby, stany, timery, postęp potwierdzeń i terminy ponowień. Blokady mogą upływać przy wiarygodnym stanie, a potwierdzenia nie liczą przerw w obserwacji.
- Wspólna polityka zapisów to 3 próby łącznie, błąd i odstępy Fibonacciego do 120 min z licznikiem na wyjście i resetem po potwierdzonym sukcesie.
- Scenariusze A01–A59 w rundzie 5 stanowią tabelę odbioru. Limit potwierdzenia 2 min i odstępy prób od wysłania są elementami scenariuszy.
- Podczas zmiany czasu timery używają rzeczywistego upływu, a harmonogram lokalnej strefy HA.

- POC dostarcza doświadczeń i materiału do testów, ale użytkownik produktu nie musi go znać ani instalować.

### Do doprecyzowania

- Kontrakty historii i Store w projekcie do przeglądu; D90 nie wymaga niezależnego odczytu HiMitII. D101 określa HA, D94 wyłącza obsługę higieny. CWU/defrost/zabezpieczenia pozostają odpowiedzialnością PC.

Powiązania: [US03](#us03), [US06](#us06), [US08](#us08)

Scenariusze odbioru [A37, A38, A41, A42, A43, A56](round-05-acceptance.md#scenariusze-odbioru).

<a id="us20"></a>

## US20 — Modułowy regulator i wybór aktywnych korekt

Obszar: [E01](https://github.com/marcin-bugala/ha-HeatPumpSteering/issues/3). Dyskusja i status: [#29](https://github.com/marcin-bugala/ha-HeatPumpSteering/issues/29).

> Jako użytkownik chcę wybierać dostępne moduły korekt, a jako opiekun produktu chcę móc dodawać następne korekty bez przebudowy podstawowego regulatora.

### Wstępne kryteria akceptacji

- Krzywa bazowa i poszczególne korekty mają rozdzielone obliczenia.
- Bieżąca wersja obejmuje moduły komfortu i długoterminowego trendu; dostępne korekty można włączać w konfiguracji zaawansowanej.
- Aktywne korekty są sumowane i ograniczane wspólnym, konfigurowalnym limitem, domyślnie ±2°C.
- Limity pompy, blokady przegrzewania, szybkość zmian i tryb obserwacji pozostają niezależne od włączania korekt.
- Diagnostyka pokazuje wkład i aktywność każdego modułu.
- Architektura przewiduje przyszłe korekty, w tym prognozy, bez ich implementowania w bieżącej wersji.

- Podział modułów i model danych od początku przewidują niezależne CO/CWU i przyszłe dwa obiegi CO, bez implementowania drugiego obiegu w pierwszym wydaniu.

### Do doprecyzowania

- Kontrakty modułów, schematy danych/migracji i techniczna reprezentacja gotowości — projekt techniczny. Zachowanie wyłączania, restartu i niedostępności ustalają rundy 4 i 6.

Powiązania: [US17](#us17), [US18](#us18), [US21](#us21).

<a id="us21"></a>

## US21 — Prognozy pogody, nasłonecznienia i PV — przyszła wersja

Obszar: [E04](https://github.com/marcin-bugala/ha-HeatPumpSteering/issues/6). Dyskusja i status: [#30](https://github.com/marcin-bugala/ha-HeatPumpSteering/issues/30).

> Jako użytkownik przyszłej wersji chcę opcjonalnie uwzględniać prognozy pogody i zysków słonecznych w korekcie ogrzewania.

### Wstępne kryteria akceptacji

- Wymagania prognoz pozostają udokumentowane; bieżąca wersja ich nie pobiera, nie konfiguruje i nie używa do sterowania.
- Przed wznowieniem ustalamy profile danych, horyzont, wagi, granice korekt i sposób walidacji.
- PV pozostaje wskaźnikiem słońca, a nie bezpośrednim pomiarem ciepła w pomieszczeniach; unikamy podwójnego liczenia PV/nasłonecznienia.
- Brak danych PV nie oznacza braku słońca; nieaktualne lub niewiarygodne prognozy nie mogą trwale blokować grzania.
- Zaawansowane uczenie i prognozowanie z POC pozostają propozycjami, nie obietnicą zakresu.
- Wznowienie wykorzystuje modułową architekturę US20 i wymaga osobnego zatwierdzenia specyfikacji.

### Do doprecyzowania

- Wydanie docelowe oraz pełny algorytm i kryteria jakości.
- Adaptery, archiwizacja prognozy dostępnej w chwili decyzji, walidacja i ewentualne uczenie.

Powiązania: [US17](#us17), [US18](#us18), [US20](#us20).
