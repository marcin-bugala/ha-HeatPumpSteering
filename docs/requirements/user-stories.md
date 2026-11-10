# User stories

Baza v0.1 z 10 listopada 2026. Treść poniżej zawiera wstępne kryteria do uzgodnienia; status procesu znajduje się w powiązanym Issue. Identyfikatory są trwałe. [Indeks i zasady](README.md) · [Produkt](product.md) · [Decyzje](decisions.md).

<a id="us01"></a>

## US01 — Dodawanie i konfiguracja stref

Obszar: [E02](https://github.com/marcin-bugala/ha-HeatPumpSteering/issues/4). Dyskusja i status: [#8](https://github.com/marcin-bugala/ha-HeatPumpSteering/issues/8).

> Jako użytkownik chcę dodać strefę i wybrać jej czujnik temperatury bez edytowania YAML.

### Wstępne kryteria akceptacji

- Strefę można dodać, nazwać, edytować i wyłączyć przez UI integracji.
- Aktywna strefa wymaga co najmniej jednego poprawnie skonfigurowanego źródła temperatury.
- Brak skonfigurowanego sterowania zaworami nie uniemożliwia obserwacji strefy ani wykorzystania jej w regulacji PC.
- Konfiguracja nie zawiera narzuconych nazw pomieszczeń ani identyfikatorów encji.

### Do doprecyzowania

- Jak agregować kilka termometrów w jednej strefie i jak traktować częściową niedostępność?

Powiązania: [US15](#us15), [US16](#us16)

<a id="us02"></a>

## US02 — Nastawa komfortu i pamięć ustawień

Obszar: [E02](https://github.com/marcin-bugala/ha-HeatPumpSteering/issues/4). Dyskusja i status: [#9](https://github.com/marcin-bugala/ha-HeatPumpSteering/issues/9).

> Jako użytkownik chcę zmieniać temperaturę zadaną strefy na dashboardzie i zachować ją po restarcie.

### Wstępne kryteria akceptacji

- Każda aktywna strefa ma własny cel temperatury.
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
- Tryb można zmienić z dashboardu i jest on wyraźnie widoczny.
- W obu trybach widoczne są proponowana decyzja, jej powód i rzeczywisty stan instalacji.
- Powrót do obserwacji zatrzymuje następne automatyczne polecenia i nie cofa ostatnich nastaw.
- Aktywacja ponownie ocenia aktualne dane; nie odtwarza kolejki decyzji z obserwacji.
- Niespełnione warunki i brak danych blokują odpowiednie działania również w trybie aktywnym.

### Do doprecyzowania

- Czy wspólny tryb obejmuje również CWU i późniejsze F01?
- Czy tryb jest wspólny dla wszystkich wyjść CO, czy dopuszczamy osobne uprawnienia?
- Czy i jak odtwarzać aktywny tryb po restarcie?

Powiązania: brak dodatkowych powiązań.

<a id="us04"></a>

## US04 — Wyjaśnianie decyzji regulatora

Obszar: [E01](https://github.com/marcin-bugala/ha-HeatPumpSteering/issues/3). Dyskusja i status: [#11](https://github.com/marcin-bugala/ha-HeatPumpSteering/issues/11).

> Jako użytkownik chcę wiedzieć, dlaczego regulator proponuje lub wykonuje zmianę CO1.

### Wstępne kryteria akceptacji

- Diagnostyka rozdziela bazę krzywej, korekty komfortu/trendu/prognoz i wynik po ograniczeniach.
- Widać proponowaną, wysłaną i potwierdzoną nastawę; brak dowodu potwierdzenia jest jawny.
- Widoczne są blokady, jakość danych, osiągnięcie limitów i najwcześniejszy kolejny zapis.
- Obserwacja i aktywne sterowanie mają porównywalny zapis przyczyn decyzji.

### Do doprecyzowania

- Zakres i czas przechowywania dziennika decyzji oraz format eksportu.

Powiązania: [US03](#us03), [US17](#us17), [US19](#us19)

<a id="us05"></a>

## US05 — Niezależne ograniczanie grzania przegrzanej strefy

Obszar: [E02](https://github.com/marcin-bugala/ha-HeatPumpSteering/issues/4). Dyskusja i status: [#12](https://github.com/marcin-bugala/ha-HeatPumpSteering/issues/12).

> Jako użytkownik chcę zamknąć sterowane pętle przegrzanej strefy bez zatrzymania ogrzewania innych stref.

### Wstępne kryteria akceptacji

- Polecenia dotyczą wyłącznie wyjść przypisanych do danej strefy.
- Jedno wyjście może obsługiwać grupę pętli; strefa może mieć kilka wyjść.
- Zachowane są histereza, czasy ruchu i minimalne czasy zmian ustalone dla instalacji.
- Bez wyjść zaworów widoczna jest tylko ocena zapotrzebowania i ograniczenie możliwości regulacji.
- Stan zamknięcia strefy nie oznacza odcięcia pętli pozostających poza sterowaniem.

### Do doprecyzowania

- Progi zamknięcia/otwarcia i minimalne czasy.
- Zachowanie wyjść przy braku termometru, restarcie i utracie komunikacji.
- Zasady agregacji demandu i kolejność otwarcia zaworów oraz żądania ciepła.

Powiązania: [US09](#us09), [US10](#us10), [US15](#us15)

<a id="us06"></a>

## US06 — Odporność na wietrzenie i krótkie zyski ciepła

Obszar: [E01](https://github.com/marcin-bugala/ha-HeatPumpSteering/issues/3). Dyskusja i status: [#13](https://github.com/marcin-bugala/ha-HeatPumpSteering/issues/13).

> Jako użytkownik chcę, aby krótkie wietrzenie, gotowanie i słońce nie wywoływały agresywnych zmian CO1.

### Wstępne kryteria akceptacji

- Nagły spadek nie powoduje natychmiastowego podnoszenia CO1 ani bezwarunkowego otwierania strefy.
- Krótkie piki mają ograniczony wpływ na długoterminową korektę wody.
- Trwałe przegrzewanie i niedogrzanie nie są bezterminowo odrzucane jako zakłócenie.
- Szybki sygnał dla zaworów jest odrębny od wolniejszej oceny komfortu i trendu.

### Do doprecyzowania

- Definicje zakłóceń, końca zakłócenia, długości okien i wymaganej jakości danych.

Powiązania: [US19](#us19)

<a id="us07"></a>

## US07 — Sterowanie ręczne i oddawanie kontroli

Obszar: [E01](https://github.com/marcin-bugala/ha-HeatPumpSteering/issues/3). Dyskusja i status: [#14](https://github.com/marcin-bugala/ha-HeatPumpSteering/issues/14).

> Jako użytkownik chcę zachować kontrolę ręczną i znać zasady powrotu do automatyki.

### Wstępne kryteria akceptacji

- Ręczna zmiana jest rozpoznawana w zakresie pozwalającym na to przez encje HA.
- Dashboard pokazuje obowiązujący tryb i ewentualne nadpisanie.
- Reguły pierwszeństwa są jawne i spójne dla danego modułu.
- Odzyskanie kontroli nie wykonuje nieaktualnych poleceń.

### Do doprecyzowania

- Nadpisanie do odwołania, do terminu czy do kolejnego przedziału harmonogramu?
- Czy zmiana poza dashboardem integracji wstrzymuje regulator i na jak długo?
- Zachowanie przy ręcznym OFF demandu i CWU.

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

- Podstawą produktu pozostaje regulacja nastawy temperatury PC.
- Obsługiwane są cztery kombinacje: bez stref/bez demandu, strefy/bez demandu, bez stref/z demandem, strefy/z demandem.
- Wyjścia zaworów wymagane są tylko przy ich sterowaniu; wyjście demand tylko przy włączonym demandzie.
- Bez demandu integracja nie przełącza ogrzewania ON/OFF, także przez encję CO1.
- Można później dołączyć te możliwości bez ponownego tworzenia całej konfiguracji.
- Zmiana konfiguracji sama nie aktywuje nowych wyjść.

### Do doprecyzowania

- Interfejs demandu: zewnętrzny przekaźnik, logiczna encja obiegu lub oba warianty jako jawne profile.
- Reguły zapotrzebowania, braku danych, polaryzacji, timerów i potwierdzania demandu.

Powiązania: [US03](#us03), [US15](#us15), [US16](#us16)

<a id="us10"></a>

## US10 — Konfiguracja siłowników NC i NO

Obszar: [E02](https://github.com/marcin-bugala/ha-HeatPumpSteering/issues/4). Dyskusja i status: [#17](https://github.com/marcin-bugala/ha-HeatPumpSteering/issues/17).

> Jako użytkownik chcę podczas konfiguracji wybrać NC albo NO, aby integracja poprawnie otwierała i zamykała pętle.

### Wstępne kryteria akceptacji

- Krok jest wymagany tylko przy konfiguracji wyjść zaworów i wyjaśnia znaczenie NC/NO.
- NC: zasilanie otwiera, brak zasilania zamyka; NO: zasilanie zamyka, brak zasilania otwiera.
- Dashboard przedstawia polecenie i przewidywany stan hydrauliczny niezależnie od ON/OFF przekaźnika.
- Bez sprzężenia zwrotnego przewidywany stan nie jest oznaczany jako potwierdzony.
- Sam wybór lub zmiana typu nie wysyła poleceń.

### Do doprecyzowania

- Typ globalny, na strefę czy na wyjście; czy dopuszczamy instalacje mieszane?
- Niezależna konfiguracja odwróconej logiki wyjścia przekaźnika i czasu ruchu.

Powiązania: [US09](#us09)

<a id="us11"></a>

## US11 — Dashboard temperatur i celów stref

Obszar: [E02](https://github.com/marcin-bugala/ha-HeatPumpSteering/issues/4). Dyskusja i status: [#18](https://github.com/marcin-bugala/ha-HeatPumpSteering/issues/18).

> Jako użytkownik chcę na dashboardzie widzieć temperaturę aktualną i zadaną oraz zmieniać cel każdej strefy.

### Wstępne kryteria akceptacji

- Dostępne są odczyt i edycja celu każdej aktywnej strefy.
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

### Do doprecyzowania

- Okresy zużycia energii, integracja mocy do energii i źródła wiarygodnego trybu pracy.

Powiązania: [US04](#us04), [US16](#us16)

<a id="us13"></a>

## US13 — CWU stale lub według harmonogramu

Obszar: [E03](https://github.com/marcin-bugala/ha-HeatPumpSteering/issues/5). Dyskusja i status: [#20](https://github.com/marcin-bugala/ha-HeatPumpSteering/issues/20).

> Jako użytkownik chcę w panelu sterowania wybrać stałe podgrzewanie CWU albo pracę według harmonogramu.

### Wstępne kryteria akceptacji

- Tryb stały używa jednej ustawionej temperatury CWU niezależnie od harmonogramu.
- Tryb harmonogramu korzysta z aktualnego przedziału.
- Włączenie CWU oznacza zezwolenie na podgrzewanie; pompa zachowuje własną regulację i zabezpieczenia.
- Dashboard pokazuje aktualny tryb, nastawę i najbliższą zmianę.
- Temperatury są ograniczone zakresem obsługiwanym przez urządzenie.

### Do doprecyzowania

- Opcjonalność modułu i wydanie docelowe.
- Współpraca z obserwacją US03, ręczne nadpisanie, brak danych i funkcje higieniczne producenta.
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
- Harmonogram CWU nie steruje ogrzewaniem pomieszczeń ani ich celami.
- Wartości temperatur są walidowane względem urządzenia.

### Do doprecyzowania

- Strefa czasowa i zmiana czasu, granice przedziałów, edycja/kopiowanie dni.
- Stan początkowego harmonogramu i uzgadnianie po restarcie lub przerwie łączności.
- Zakres ręcznego nadpisania harmonogramu.

Powiązania: [US13](#us13), [US07](#us07)

<a id="us15"></a>

## US15 — Dom, kondygnacje lub pomieszczenia jako strefy

Obszar: [E02](https://github.com/marcin-bugala/ha-HeatPumpSteering/issues/4). Dyskusja i status: [#22](https://github.com/marcin-bugala/ha-HeatPumpSteering/issues/22).

> Jako użytkownik chcę odwzorować cały dom, kondygnacje lub pomieszczenia bez narzuconej struktury pięter.

### Wstępne kryteria akceptacji

- Dopuszczalna jest jedna strefa Dom z jednym termometrem albo wiele nazwanych stref.
- Każda aktywna strefa ma co najmniej jeden termometr oraz cel.
- Czujnik i obliczane zapotrzebowanie mogą istnieć bez fizycznego zaworu.
- Pętle bez siłowników pozostają poza sterowaniem; ich odbiór ciepła jest jawnym ograniczeniem modelu.
- Przyszła trzecia kondygnacja nie wymaga zmiany kodu.

### Do doprecyzowania

- Czy model dopuszcza jednocześnie nadrzędne kondygnacje i podrzędne pokoje oraz jak unika podwójnego ważenia?
- Liczba stref w v1 i przypisanie współdzielonych wyjść.

Powiązania: [US01](#us01), [US09](#us09)

<a id="us16"></a>

## US16 — Wybór wymaganych i opcjonalnych źródeł

Obszar: [E04](https://github.com/marcin-bugala/ha-HeatPumpSteering/issues/6). Dyskusja i status: [#23](https://github.com/marcin-bugala/ha-HeatPumpSteering/issues/23).

> Jako użytkownik chcę dodać tylko dostępne czujniki, prognozy i sterowniki, aby konfiguracja pasowała do instalacji.

### Wstępne kryteria akceptacji

- Aktywna strefa wymaga temperatury; regulacja CO1 wymaga bieżącej temperatury zewnętrznej.
- Aktywny zapis CO1 wymaga encji nastawy; zawory i demand wymagają wyjść tylko po włączeniu tych funkcji.
- Prognoza pogody, nasłonecznienia/PV, moc/energia i temperatury zasilania/powrotu są opcjonalne.
- Brak opcjonalnego źródła nie blokuje podstawowych funkcji ani nie oznacza wartości zero.
- Utrata skonfigurowanego źródła jest widoczna wraz z wpływem na działanie.
- Integracja korzysta z encji/integracji HA, bez wymogu konkretnej marki sprzętu.

### Do doprecyzowania

- Profile dostawców prognoz i formaty/horyzonty danych.
- Progi świeżości, jednostki, zastępowanie źródeł oraz zachowanie po ich utracie.
- Kiedy brak encji PC pozwala zapisać konfigurację obserwacyjną?

Powiązania: [US09](#us09), [US15](#us15)

<a id="us17"></a>

## US17 — Konfigurowalna krzywa grzewcza A, B i Tref

Obszar: [E01](https://github.com/marcin-bugala/ha-HeatPumpSteering/issues/3). Dyskusja i status: [#24](https://github.com/marcin-bugala/ha-HeatPumpSteering/issues/24).

> Jako użytkownik chcę ustawiać przesunięcie, nachylenie i punkt odniesienia krzywej grzewczej.

### Wstępne kryteria akceptacji

- Bazą jest Tbase = A + B × (Tref − Ta).
- A, B i Tref są ustawiane osobno; początkowa propozycja to 20°C, 0,2 i 20°C.
- Ta jest przefiltrowaną bieżącą temperaturą zewnętrzną, a nie prognozą.
- Korekty komfortu, trendów i prognoz są oddzielone od bazy i widoczne diagnostycznie.
- Zmiana współczynników nie omija limitów temperatury, kroku ani częstotliwości zapisu.

### Do doprecyzowania

- Zakresy/kroki parametrów, okno Ta i dokładna kolejność korekt/ograniczeń.
- Potwierdzanie limitów pompy i niezależnego odczytu nastawy.

Powiązania: [US04](#us04), [US16](#us16), [US19](#us19)

<a id="us18"></a>

## US18 — Wagi stref i opcjonalnych prognoz

Obszar: [E04](https://github.com/marcin-bugala/ha-HeatPumpSteering/issues/6). Dyskusja i status: [#25](https://github.com/marcin-bugala/ha-HeatPumpSteering/issues/25).

> Jako użytkownik chcę ustawiać znaczenie stref i siłę korekt prognoz, aby dopasować regulator do domu.

### Wstępne kryteria akceptacji

- Wagi stref i siła korekt pogody oraz słońca/PV są konfigurowane osobno.
- Wagi nie zastępują temperatur zadanych ani reguł ochrony przed przegrzewaniem.
- Prognoza PV jest pomocniczym wskaźnikiem słońca, nie bezpośrednią prognozą ciepła w pomieszczeniach.
- Zyski słoneczne nie są liczone podwójnie z PV i nasłonecznienia.
- Brak PV nie oznacza braku słońca; niska jakość prognozy ogranicza jej wpływ.
- Każda korekta jest ograniczona i wyjaśniona; brak prognoz pozwala regulować na podstawie pomiarów.

### Do doprecyzowania

- Normalizacja wag, priorytety konfliktów, jednostki i zakresy korekt.
- Czy w v1 stosujemy korekty ręcznie parametryzowane, czy dopiero później model uczony?
- Horyzont prognozy, dobór ekspozycji, walidacja i archiwizacja prognoz.

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

### Do doprecyzowania

- Docelowe filtry, progi, format pamięci i obsługa długich przerw.
- Minimalna wersja HA i niezależny mechanizm potwierdzania HiMitII.
- Uzgodnienie zachowania przy CWU/defrost oraz granic odpowiedzialności.

Powiązania: [US03](#us03), [US06](#us06), [US08](#us08)

