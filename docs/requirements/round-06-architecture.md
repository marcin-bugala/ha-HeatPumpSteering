# Runda 6 — architektura, trwałość danych i wydania

Uzgodnienia właściciela produktu z 11 listopada 2026. Runda jest zamknięta na poziomie decyzji produktu. Dokument nie oznacza implementacji ani zakończenia projektu technicznego. Aktualny zakres zastępuje wcześniejsze zapisy o obowiązkowym CO1 dla każdej konfiguracji, osobnym późniejszym wydaniu CWU/demandu i obowiązkowej migracji z POC.

## Zakres i model instalacji

- Czytamy i sterujemy przez encje HA. Komunikację z urządzeniami zapewniają istniejące integracje, bez osobnego połączenia produktu do chmury producenta. D90 przyjmuje wstępne potwierdzenie od razu i ostateczne po zgodnym ponownym odczycie tej samej encji po 2 min; nie utożsamiamy tego z fizycznym wykonaniem.
- Jedna konfiguracja obejmuje jedną pompę, maksymalnie jeden obieg CO i jedno CWU. CO i CWU są niezależnie opcjonalne: samo CO, samo CWU albo oba.
- W CO wymagamy nastawy CO1 także dla obserwacji, outdoor i aktywnej strefy z temperaturą oraz celem. Wyjścia zaworów i demand wymagane są wyłącznie po włączeniu tych funkcji.
- Przy samym CWU wymagamy tylko jego encji. Nie wymagamy nastawy CO1, outdoor ani stref; panel i encje nieskonfigurowanego modułu nie są udostępniane.
- Od początku model danych i podział modułów przewidują dwa przyszłe obiegi CO jednej pompy. Strefy, np. piętra, są przypisane osobno do obiegów. Każdy obieg ma niezależną nastawę wody i opcjonalny Demand 1/2; te same reguły algorytmu działają niezależnie dla jego stref. Nie jest to funkcja pierwszego wydania.
- Kolejna pompa może w przyszłości mieć osobną konfigurację. Nie rozszerzamy tym zakresu pierwszego wydania o sprawdzoną obsługę wielu pomp.

## Przechowywanie i historia

| Rodzaj danych | Mechanizm |
| --- | --- |
| Konfiguracja instalacji, modułów, stref i encji | Standardowe wpisy konfiguracji HA, z wersjonowaniem i migracjami |
| Cele, harmonogramy, nadpisania, potrzebny stan działania, terminy blokad i ponowień | Wersjonowany mechanizm HA Store, trwała pamięć w .storage |
| Historia temperatur oraz encji decyzji i diagnostyki | Istniejący Recorder HA, zgodnie z ustawieniami użytkownika |
| Bieżące okna średnich, median i trendów | Pamięć operacyjna, odbudowa z dostępnej historii, domyślnie 48 h |

Nie wymagamy dodatkowej bazy danych. Nie duplikujemy pełnego archiwum pomiarów w Store. Konkretne schematy danych, wielkości buforów i częstotliwość zapisu określi projekt techniczny.

Aktualizacja musi zachować konfigurację, cele, harmonogramy, historię pomiarów i decyzji, tożsamość encji, potrzebny stan działania, timery, nadpisania i ponowienia. Nie może resetować działania, powodować nieplanowanych przełączeń ani wymuszać zbierania dostępnej historii od zera. Zachowujemy powiązania dashboardów i automatyzacji. Restart oznacza przerwę wykonania programu; po niej przywracamy stan i sprawdzamy bieżące dane oraz ważność decyzji.

Nie usuwamy danych przy aktualizacji. Retencja i filtry Recordera nadal obowiązują; nie gwarantujemy odtworzenia nieprzechowywanych danych. Braki są jawne i nie są fikcyjnymi próbkami ani dowodem ciągłego spełniania warunku.

Podstawa techniczna zweryfikowana podczas rundy: [konfiguracja i migracje HA](https://developers.home-assistant.io/docs/config_entries_index/), [Store](https://github.com/home-assistant/core/blob/dev/homeassistant/helpers/storage.py), [odtwarzanie historii w Statistics](https://github.com/home-assistant/core/blob/dev/homeassistant/components/statistics/sensor.py), [retencja i filtry Recordera](https://www.home-assistant.io/integrations/recorder/). Odnośniki do dev wskazują przykład mechanizmu; wersję implementacyjną dobierzemy do minimum HA.

## Cykl życia i zmiany konfiguracji

- Wyłączenie lub usunięcie integracji zatrzymuje jej polecenia i ponowienia, pozostawiając urządzenia w ostatnim stanie. Nie przywraca automatycznie wcześniejszych nastaw.
- Wyłączenie modułu zachowuje przypisania, cele, parametry i harmonogramy. Ponowne włączenie zaczyna w obserwacji, od odczytania stanów i odbudowy okien. Użytkownik świadomie aktywuje sterowanie. Zwykły restart i aktualizacja odtwarzają zapisany tryb zgodnie z rundą 4.
- Zapis zmian najpierw waliduje cały zmieniany zakres; po zatwierdzeniu unieważnia nieaktualne oczekujące polecenia i ponownie ocenia dane. Zachowuje nadal pasującą historię i stan. Nie omija ograniczeń i nie aktywuje samoczynnie sterowania.
- Zmiana termometru odbudowuje okna ze źródła nowego bez mieszania ze starym. Zachowana historia nie oznacza użycia niepasujących pomiarów w algorytmie.
- Trwały identyfikator strefy nie zależy od nazwy, grupy ani czujnika. Ich zmiana nie tworzy nowych encji. Usunięcie i odtworzenie tej samej nazwy oznacza nową tożsamość.
- Przed usunięciem strefy lub odłączeniem wyjścia pokazujemy bieżący stan oraz informację: „Po odłączeniu to wyjście pozostanie w obecnym stanie. Integracja przestanie nim sterować”. Użytkownik może wcześniej zmienić stan ręcznie. Anulujemy oczekujące polecenia i ponowienia odłączonego wyjścia.
- Blokujemy współdzielenie encji wykonawczych między niezależnymi funkcjami i konfiguracjami produktu. Jedno wyjście zaworu należy do jednej strefy; strefa może mieć kilka wyjść. Czujniki można współdzielić.
- Wycofano propozycję dopuszczenia współdzielonego zaworu z ostrzeżeniem i agregacji jego żądań OR. Obowiązuje blokada, nie ta propozycja.
- Przy aktywacji informujemy o potrzebie jednego regulatora danego wyjścia. Nie gwarantujemy wykrycia innych automatyzacji i ich nie wyłączamy.
- Błąd jednego modułu lub urządzenia ogranicza zależne działania: awaria CWU nie zatrzymuje sprawnego CO, brak licznika ogranicza diagnostykę, awaria strefy stosuje jej reguły awaryjne. Wspólne zależności nadal mogą blokować kilka funkcji.

## Interfejs i diagnostyka

Od pierwszego wydania developerskiego dostarczamy encje do własnych dashboardów i automatyzacji, gotową kartę produktu, panel CWU z edycją roboczą i jednym Zapisz oraz osobny ekran konfiguracji zaawansowanej. Karta pokazuje strefy, cele, zawory, stan pompy, dostępną moc/energię i przyczyny decyzji. Karta i panel są częścią dostarczanego produktu bez wymagania kart innych autorów.

Interfejs, komunikaty oraz instrukcje instalacji i konfiguracji są w PL/EN. Nazwy stref nadaje użytkownik. Dokładny wybór platform encji i realizacja frontendu pozostają w projekcie technicznym.

Diagnostykę użytkownik pobiera na żądanie standardową funkcją HA i sam decyduje o udostępnieniu. Eksport zawiera wersję, parametry algorytmu, jakość danych, ostatnie decyzje, blokady i błędy poleceń. Nazwy własne i identyfikatory encji zastępujemy spójnymi oznaczeniami; nie zawiera haseł ani tokenów. Brak automatycznej wysyłki.

Ostrzeżenie ustępuje automatycznie po usunięciu przyczyny i spełnieniu warunków powrotu. Oznaczenie jako przeczytane nie kasuje trwającego problemu i blokady. Historia zachowuje wystąpienie i ustąpienie. Podejrzenie niesprawnego zaworu pozostaje podejrzeniem, nie potwierdzeniem awarii.

## Wydania, odbiór i wycofanie

Pierwsze kompletne wydanie developerskie obejmuje CO i strefy, opcjonalne zawory i demand oraz opcjonalne CWU z harmonogramem. Ma umożliwiać pełne działanie uzgodnionego zakresu w konfiguracjach samo CO, samo CWU i obu modułów. Funkcje można implementować etapami, ale pierwsze kompletne wydanie nie jest tylko demonstratorem obserwacyjnym.

Prognozy i ogrzewanie odpływu pozostają na późniejsze wersje. Odpływ jest wstępnie kolejnym rozszerzeniem; ostateczną kolejność ustalimy później.

Warunki wydania:
- przejście testów algorytmu, konfiguracji, awarii, restartów i aktualizacji;
- odbiór sterowania na instalacji referencyjnej, zapis wyników i wskazanie konfiguracji sprawdzonych wyłącznie w symulacji;
- gotowa instrukcja instalacji, konfiguracji i aktualizacji w PL/EN.

Dystrybucja przez HACS jako repozytorium niestandardowe oraz ręcznie. Wydania developerskie oznaczone jako testowe, np. 0.1.0-beta.1; aktualizację wybiera użytkownik. Każde wydanie podaje wymagane minimum HA, sprawdzone wersje, zmiany oraz procedurę powrotu. Minimum ustalimy przed implementacją na podstawie potrzebnych mechanizmów; jego podniesienie jest jawne. Zgłoszenie do domyślnego katalogu HACS po stabilizacji.

Powrót zachowuje dane, jeśli starsza wersja umie je odczytać. Przy niezgodnym formacie pokazuje błąd, nie resetuje danych i nie rozpoczyna sterowania. Wtedy powrót wymaga odtworzenia właściwej kopii HA zgodnie z instrukcją wydania. Nie obiecujemy dowolnej zgodności wstecznej przyszłych formatów.

POC pozostaje całkowicie osobny, nie jest ścieżką uruchomienia produktu ani wymaganiem wobec przyszłych użytkowników. Brak importera POC i obowiązkowej instrukcji migracji. Doświadczenia i dane POC mogą wspierać projektowanie i testy; instrukcja przejścia dla instalacji właściciela jest osobnym materiałem.

## Dodatkowe kryteria odbioru

To scenariusze przyszłej implementacji, nie wykonane testy. Rozszerzają [A01–A59](round-05-acceptance.md#scenariusze-odbioru).

| ID | Warunek | Oczekiwany wynik |
| --- | --- | --- |
| B01 | Konfiguracja tylko CWU | Brak wymagań CO1, outdoor i stref; harmonogram działa przy poprawnych encjach CWU |
| B02 | Samo CO / samo CWU / oba | Każdy wariant jest konfigurowalny; nieobecne moduły nie pokazują paneli i encji |
| B03 | Ponowne włączenie wcześniej wyłączonego modułu | Ustawienia zachowane, początek w obserwacji po odczytach i odbudowie okien |
| B04 | Wyłączenie/usunięcie integracji lub odłączenie wyjścia | Koniec poleceń i ponowień, ostatni stan pozostaje; przy odłączeniu uprzednia informacja |
| B05 | Aktualizacja przy aktywnych blokadach, nadpisaniu i ponowieniach | Stan, terminy i tryby zachowane; brak nieplanowanych przełączeń i zerowania historii |
| B06 | Zmiana nazwy/grupy/czujnika oraz usunięcie i odtworzenie nazwy | Pierwsze zachowują tożsamość; nowe źródło ma własne okna; odtworzona strefa ma nową tożsamość |
| B07 | Powrót do wersji niezgodnej z danymi | Jawny błąd bez resetu danych i aktywacji; udokumentowane odtworzenie kopii |
| B08 | Recorder nie zachował pełnych 48 h | Jawna niepełność, reguły gotowości okien, brak fikcyjnych próbek |
| B09 | Jedna encja wykonawcza przypisana drugiej niezależnej funkcji/konfiguracji | Zapis odrzucony; współdzielenie czujnika dozwolone |
| B10 | Błędna konfiguracja lub zmiana unieważniająca stare polecenie | Walidacja zakresu przed zatwierdzeniem; stare polecenie nie jest odtwarzane |
| B11 | Awaria CWU, licznika lub jednej strefy | Działają funkcje z poprawnymi zależnościami; widoczna przyczyna ograniczeń |
| B12 | Eksport oraz trwające/ustępujące ostrzeżenie | Anonimizacja, brak sekretów i wysyłki; przeczytanie nie kasuje problemu; historia ma początek i koniec |
| B13 | Instalacja na czystym HA bez POC | Konfiguracja i pełne działanie bez znajomości POC; karta/panel i PL/EN dostarczone z produktem |

## Projekt techniczny przed kodowaniem

Do przygotowania: podział modułów, model danych i przyszłych obiegów, domena, minimalna wersja HA i macierz testowa, platformy i kontrakty encji, dwuetapowe potwierdzanie D90 oraz rozpoznawanie zmian zewnętrznych D91, schematy/migracje Store, dostęp do historii i jakość jej raportów, technologia frontendu, plan implementacji i testów. Zachowania ręcznego demandu, logiki odwróconej i inicjalizacji CWU bez wcześniejszej nastawy wymagają jawnego rozstrzygnięcia w tym projekcie.

To zapis wymagań. Nie rozpoczynamy kodowania w ramach tego PR.

Aktualizacja po P01–P12: D90–D101 rozstrzygają pytania produktowe powyżej;
domena/minimum/macierz i kontrakty P12 są przyjęte. Higieny CWU nie obsługujemy.
Cały projekt nadal wymaga przeglądu, T08 wymaga zgodnych zależności testowych.
Dodatkowy odbiór: C01–C13 w rundzie 5; żaden test nie został tu wykonany.
