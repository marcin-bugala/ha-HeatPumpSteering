# User stories

Baza v0.4 z 10 listopada 2026, uzupełniona o [rundę 1](round-01-installation-zones.md) [rundę 2](round-02-daily-operation.md) i [rundę 3](round-03-regulation.md). Treść poniżej zawiera wstępne kryteria do uzgodnienia; status procesu znajduje się w powiązanym Issue. Identyfikatory są trwałe. [Indeks i zasady](README.md) · [Produkt](product.md) · [Decyzje](decisions.md).

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

### Do doprecyzowania

- Jakość i częściowa niedostępność termometrów oraz stan początkowy — runda awarii.

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

### Do doprecyzowania

- Zakres i krok nastawy pokojowej; reset potwierdzeń po zmianie celu.

Powiązania: [US01](#us01)

<a id="us03"></a>

## US03 — Obserwacja decyzji i świadome włączenie sterowania

Obszar: [E01](https://github.com/marcin-bugala/ha-HeatPumpSteering/issues/3). Dyskusja i status: [#10](https://github.com/marcin-bugala/ha-HeatPumpSteering/issues/10).

> Jako użytkownik chcę obserwować decyzje i sam wybrać, czy algorytm je wykonuje, czy wyłącznie pokazuje.

### Wstępne kryteria akceptacji

- Nowa konfiguracja rozpoczyna w obserwacji; obserwowane wyjścia nie otrzymują automatycznych poleceń.
- Encja nastawy PC jest obowiązkowo wskazywana również dla obserwacji; odczyt służy porównaniu z propozycją algorytmu.
- Na dashboardzie są dwa niezależne przełączniki obserwacja/sterowanie: CO i CWU. Aktywacja jednego nie aktywuje drugiego.
- Przełączniki są poza zbiorczym panelem ustawień CWU; zapis tego panelu nie zmienia trybu obserwacja/sterowanie.
- W obu trybach widoczne są proponowana decyzja, jej powód i rzeczywisty stan instalacji.
- Powrót do obserwacji zatrzymuje następne automatyczne polecenia i nie cofa ostatnich nastaw.
- Aktywacja ponownie ocenia aktualne dane; nie odtwarza kolejki decyzji z obserwacji.
- Niespełnione warunki i brak danych blokują odpowiednie działania również w trybie aktywnym.

### Do doprecyzowania

- Relacja przełączników do późniejszego F01 i ewentualne dodatkowe uprawnienia wyjść CO.
- Czy i jak odtwarzać aktywny tryb po restarcie?

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

### Do doprecyzowania

- Zakres i czas przechowywania dziennika decyzji oraz format eksportu.

Powiązania: [US03](#us03), [US17](#us17), [US19](#us19)

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

### Do doprecyzowania

- Stan początkowy, czas zamykania, dowody wykonania, reset ostrzeżenia i niedostępność pomiarów/wyjść — runda awarii.
- Rozpoznawanie nagłego spadku i zachowanie wszystkich stref odciętych — do uzupełnienia.

Powiązania: [US09](#us09), [US10](#us10), [US15](#us15)

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

### Do doprecyzowania

- Definicja nagłego spadku, świeżość i ciągłość poprawnych obserwacji oraz zachowanie podczas przerw — runda awarii.

Powiązania: [US19](#us19)

<a id="us07"></a>

## US07 — Sterowanie ręczne i oddawanie kontroli

Obszar: [E01](https://github.com/marcin-bugala/ha-HeatPumpSteering/issues/3). Dyskusja i status: [#14](https://github.com/marcin-bugala/ha-HeatPumpSteering/issues/14).

> Jako użytkownik chcę zachować kontrolę ręczną i znać zasady powrotu do automatyki.

### Wstępne kryteria akceptacji

- Ręczna zmiana jest rozpoznawana w zakresie pozwalającym na to przez encje HA.
- Dashboard pokazuje obowiązujący tryb i ewentualne nadpisanie.
- Cel CO zmieniony ręcznie jest trwałą nastawą konkretnej strefy.
- W CWU/Harmonogram ręczne nadpisanie stanu lub temperatury obowiązuje po Zapisz do następnej zaplanowanej zmiany; identyczne sąsiednie pola nie kończą nadpisania.
- Ręczne włączenie CWU może ominąć aktualnie zaplanowany okres wyłączenia, bez przełączania do Stałe.
- Panel podpowiada ostatnią nastawę CWU do edycji przed zatwierdzeniem włączenia.
- Reguły pierwszeństwa są jawne i spójne dla danego modułu.
- Odzyskanie kontroli nie wykonuje nieaktualnych poleceń.

### Do doprecyzowania

- Edycja harmonogramu przy aktywnym nadpisaniu i przypadek braku przyszłych zmian w cyklicznym harmonogramie.
- Czy zmiana poza dashboardem integracji wstrzymuje regulator i na jak długo?
- Zachowanie przy ręcznym OFF demandu; odtwarzanie nadpisania CWU po restarcie.

Powiązania: [US03](#us03)

<a id="us08"></a>

## US08 — Migracja z POC i możliwość wycofania

Obszar: [E01](https://github.com/marcin-bugala/ha-HeatPumpSteering/issues/3). Dyskusja i status: [#15](https://github.com/marcin-bugala/ha-HeatPumpSteering/issues/15).

> Jako użytkownik POC chcę przejść do integracji bez dwóch regulatorów sterujących tą samą nastawą.

### Wstępne kryteria akceptacji

- Instrukcja identyfikuje automatykę zapisu CO1 i osobną automatykę auto STOP prototypu.
- Migracja wymaga usunięcia konfliktu sterowania przed aktywacją produktu.
- Opisane są stany pozostające w pompie przy wyłączeniu/usunięciu POC i integracji.
- Zachowane lub jawnie mapowane są cele oraz istotne ustawienia; historia nie jest usuwana.
- Nowa integracja może zacząć obserwację obok POC bez wysyłania poleceń.
- Opisany jest powrót do POC bez równoległych aktywnych zapisów.

### Do doprecyzowania

- Migracja ręczna czy importer; przenoszenie historii filtrów i timerów.
- Dokładna lista wspieranych wersji POC i minimalna wersja HA.

Powiązania: [US03](#us03), [US19](#us19)

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
- ON po przewidywanym otwarciu co najmniej jednej potrzebującej strefy; domyślnie 3 min otwierania, globalnie dla domu. Strefa już otwarta nie czeka od nowa; bez wyjść nie wymaga opóźnienia.
- Brak wszystkich zapotrzebowań wyłącza demand bez dodatkowego opóźnienia; brak minimalnego ON.
- Ponowne ON wymaga minimum 15 min od OFF, globalnie konfigurowalne; wyjścia mogą otworzyć się wcześniej, lecz ON wymaga aktualnego zapotrzebowania i gotowości.
- Program nie modeluje otwartych pętli i nie steruje zasilaniem ani wybiegiem PC; ostrzeżenie hydrauliczne w konfiguracji zaworów.

### Do doprecyzowania

- Profil wyjścia i polaryzacja demandu, niezależne potwierdzenia i ręczne zmiany.
- Brak danych, restart i brak gotowych stref — runda awarii.

Powiązania: [US03](#us03), [US15](#us15), [US16](#us16)

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
- Czas otwierania jest parametrem całego domu, domyślnie 3 min, nie parametrem strefy.
- Upływ tego czasu oznacza przewidywane otwarcie; bez sprzężenia nie potwierdza stanu hydraulicznego.

### Do doprecyzowania

- Odwrócona logika przekaźnika, czas zamykania, potwierdzenia i awarie wyjść.

Powiązania: [US09](#us09)

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

### Do doprecyzowania

- Własna karta czy zestaw kart natywnych; reprezentacja celu jako climate lub number.

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

### Do doprecyzowania

- Okresy zużycia energii, integracja mocy do energii i źródła wiarygodnego trybu pracy.

Powiązania: [US04](#us04), [US16](#us16)

<a id="us13"></a>

## US13 — CWU stale lub według harmonogramu

Obszar: [E03](https://github.com/marcin-bugala/ha-HeatPumpSteering/issues/5). Dyskusja i status: [#20](https://github.com/marcin-bugala/ha-HeatPumpSteering/issues/20).

> Jako użytkownik chcę w panelu sterowania wybrać stałe podgrzewanie CWU albo pracę według harmonogramu.

### Wstępne kryteria akceptacji

- Dostępne są trzy tryby CWU: Wyłączone, Stałe i Harmonogram. Wyłączone nie wyłącza ogrzewania domu.
- Tryb stały używa jednej ustawionej temperatury CWU niezależnie od harmonogramu.
- W Harmonogramie można nadpisać stan i temperaturę do następnej rzeczywistej zmiany harmonogramu; dotyczy również włączenia w zaplanowanej przerwie.
- Ręczne włączenie podpowiada ostatnią nastawę CWU, edytowalną przed zapisem.
- Tryb, ręczny stan, temperatury i harmonogram są w jednym panelu, ze zmianami roboczymi i jednym przyciskiem Zapisz.
- Całość ustawień jest walidowana przed zatwierdzeniem; błąd nie zapisuje części zmian. Nie jest to gwarancja atomowego wykonania poleceń pompy.
- Przy zamknięciu z niezapisanymi zmianami pojawia się pytanie Odrzucić niezapisane zmiany?; brak osobnego potwierdzenia samego Wyłączone.
- Panel nie obejmuje celów CO ani dwóch przełączników obserwacja/sterowanie. Zapis w obserwacji nie wykonuje poleceń urządzenia.
- Tryb harmonogramu korzysta z aktualnego przedziału.
- Włączenie CWU oznacza zezwolenie na podgrzewanie; pompa zachowuje własną regulację i zabezpieczenia.
- Dashboard pokazuje aktualny tryb, nastawę i najbliższą zmianę.
- Temperatury są ograniczone zakresem obsługiwanym przez urządzenie.

### Do doprecyzowania

- Opcjonalność modułu i wydanie docelowe.
- Restart, brak danych, funkcje higieniczne producenta i obsługa częściowego błędu wykonania poleceń.
- Podpowiedź temperatury przy pierwszym uruchomieniu bez ostatniej nastawy; edycja harmonogramu podczas nadpisania.
- Wymagane encje i sposób potwierdzania poleceń CWU.

Powiązania: [US14](#us14), [US16](#us16)

<a id="us14"></a>

## US14 — Tygodniowy harmonogram CWU co 30 minut

Obszar: [E03](https://github.com/marcin-bugala/ha-HeatPumpSteering/issues/5). Dyskusja i status: [#21](https://github.com/marcin-bugala/ha-HeatPumpSteering/issues/21).

> Jako użytkownik chcę oddzielnie zaplanować każdy dzień tygodnia z dokładnością 30 minut i temperaturą na przedział.

### Wstępne kryteria akceptacji

- Każdy dzień ma 48 logicznych przedziałów półgodzinnych.
- Przedział oznacza wyłączone albo zezwolenie na grzanie do wskazanej temperatury.
- Harmonogram i nastawy są zachowane po restarcie.
- Ręczne nadpisanie działa po zatwierdzeniu do następnej zaplanowanej zmiany stanu/temperatury, nie do dowolnej granicy 30 minut.
- Sąsiednie identyczne pola tworzą ciągły okres; nie kasują nadpisania.
- Harmonogram edytujemy razem z pozostałymi ustawieniami CWU, z jednym Zapisz i potwierdzeniem odrzucenia niezapisanej edycji.
- Harmonogram CWU nie steruje ogrzewaniem pomieszczeń ani ich celami.
- Wartości temperatur są walidowane względem urządzenia.

### Do doprecyzowania

- Strefa czasowa i zmiana czasu, granice przedziałów, edycja/kopiowanie dni.
- Stan początkowego harmonogramu i uzgadnianie po restarcie lub przerwie łączności.
- Edycja harmonogramu przy aktywnym nadpisaniu i brak następnej zmiany w całym tygodniu.

Powiązania: [US13](#us13), [US07](#us07)

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
- Encja nastawy PC musi być wskazana już podczas konfiguracji, również dla obserwacji; jej brak uniemożliwia zakończenie konfiguracji.
- Minimalna konfiguracja zawiera encję nastawy PC, temperaturę zewnętrzną i co najmniej jedną aktywną strefę z termometrem oraz celem.
- Zawory i demand wymagają wyjść tylko po włączeniu tych funkcji.
- Brak opcjonalnego źródła nie blokuje podstawowych funkcji ani nie oznacza wartości zero.
- Utrata skonfigurowanego źródła jest widoczna wraz z wpływem na działanie.
- Integracja korzysta z encji/integracji HA, bez wymogu konkretnej marki sprzętu.
- Moc/energia PC i temperatury zasilania/powrotu pozostają opcjonalną diagnostyką.
- Prognozy pogody, nasłonecznienia i PV przeniesiono do odłożonej US21; bieżący program ich nie konfiguruje ani nie używa.
- Zakres nastawy czytamy z pompy; użytkownik może go wyłącznie zawęzić. Bieżący outdoor pozostaje wymagany, domyślnie średnia 2 h, konfigurowalna średnia/mediana i okno 30 min–6 h co 30 min.

### Do doprecyzowania

- Progi świeżości, jednostki, zastępowanie źródeł, niedostępność oraz wiarygodność limitów/odczytu PC.
- Profile danych prognoz wrócą w przyszłym wydaniu w US21.

Powiązania: [US09](#us09), [US15](#us15)

<a id="us17"></a>

## US17 — Konfigurowalna krzywa grzewcza A, B i Tref

Obszar: [E01](https://github.com/marcin-bugala/ha-HeatPumpSteering/issues/3). Dyskusja i status: [#24](https://github.com/marcin-bugala/ha-HeatPumpSteering/issues/24).

> Jako użytkownik chcę ustawiać przesunięcie, nachylenie i punkt odniesienia krzywej grzewczej.

### Wstępne kryteria akceptacji

- Bazą jest Tbase = A + B × (Tref − Ta).
- A, B i Tref są ustawiane osobno; początkowa propozycja to 20°C, 0,2 i 20°C.
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

### Do doprecyzowania

- Zakresy walidacji parametrów, potwierdzanie poleceń i zachowanie po zmianie granic urządzenia — dalsze rundy.
- Brak stref kwalifikujących się do korekty i dokładne zachowanie po przerwach danych.

Powiązania: [US04](#us04), [US16](#us16), [US19](#us19)

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

### Do doprecyzowania

- Zachowanie przy braku kwalifikujących się stref, niepełnych danych i zmianie zestawu stref — dalsze rundy.

Powiązania: [US16](#us16), [US17](#us17), [US19](#us19)

<a id="us19"></a>

## US19 — Przeniesienie doświadczeń POC do produktu

Obszar: [E01](https://github.com/marcin-bugala/ha-HeatPumpSteering/issues/3). Dyskusja i status: [#26](https://github.com/marcin-bugala/ha-HeatPumpSteering/issues/26).

> Jako użytkownik chcę zachować sprawdzone mechanizmy POC i oceniać nowy regulator względem prototypu.

### Wstępne kryteria akceptacji

- Wymagania obejmują filtry, trendy, krótkie zakłócenia, konflikt stref i ograniczenia zmian.
- Oceniane są kompletność danych, jednostki i rozgrzewanie filtrów.
- Pamięć zachowuje potrzebne próbki i czasy; braki obserwacji nie stają się fikcyjnymi pomiarami.
- Polecenie, raport HA i niezależne potwierdzenie urządzenia są rozróżnione.
- Scenariusze POC służą testom porównawczym, ale konkretne progi nie są bez oceny kopiowane.
- Auto STOP CO1 z POC nie przechodzi automatycznie do konfiguracji produktu bez demandu.
- Przyjęte wartości początkowe i odstępstwa od POC określa runda 3; ustalenia produktu są nadrzędne wobec prototypu.
- Oddzielamy bazę, moduły korekt i zabezpieczenia (US20). Prognozy są poza bieżącą wersją (US21).

### Do doprecyzowania

- Docelowe filtry, progi, format pamięci i obsługa długich przerw.
- Minimalna wersja HA i niezależny mechanizm potwierdzania HiMitII.
- Uzgodnienie zachowania przy CWU/defrost oraz granic odpowiedzialności.

Powiązania: [US03](#us03), [US06](#us06), [US08](#us08)


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

### Do doprecyzowania

- Kontrakty modułów, zależności, konfiguracja/migracje i stany gotowości — runda architektury.
- Zachowanie wyłączonego/niedostępnego modułu przy restarcie i brakach danych — runda awarii.

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
