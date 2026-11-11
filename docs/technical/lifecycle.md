# Cykl życia i czas

Podstawa: D09, D24, D44, D46–D61, D65, D73–D74, D84–D88.
T06: jedna serializowana sekcja zmiany stanu per entry oraz osobna blokada
wykonania per output. To blokady asyncio, nie blokujące blokady wątków.

## Ocena i wykonanie

Raporty encji odświeżają bufory i UI na bieżąco. Ocena algorytmu co domyślne
5 min, po zmianie celu/trybu/konfiguracji i na deadline blokady/ponowienia/CWU.
Zdarzenia dostępności i dowodu unieważniają zależne działania od razu.
Scalenie kilku zdarzeń w jedną najbliższą ocenę nie przesuwa deadline.
Nie oceniamy po każdym pakiecie telemetrycznym, jeśli wystarczy zaktualizować snapshot.

Runtime trzyma `generation` i rewizje, zadania i funkcje unsubscribe.
Zmiana konfiguracji/trybu/celu, odłączenie wyjścia i unload unieważniają
odpowiednie działania przed uruchomieniem kolejnej usługi.
Na granicy każdego await ponowna kontrola generation. Przed usługą:
aktualny tryb, enabled, właściciel, źródła, zakres, blokady, aktualne żądanie,
brak zbędnego powtórzenia i zgodność rewizji. Usługa nie odbywa się pod
globalną blokadą konfiguracji przez cały timeout.
Nie można cofnąć komendy już przyjętej przez HA; można zatrzymać następne
zapisy, retry i obsługę starego ACK. Nie obiecujemy anulowania fizycznego ruchu.

Timer to pojedynczy callback HA na najbliższy termin; jego treść zleca ponowną
ocenę, nie wykonuje zapamiętanej akcji bez walidacji.
Brak sleep, aktywnego polling loop, nieograniczonej kolejki i odtwarzania zaległości.

## Zdarzenia cyklu życia

| Zdarzenie | Kolejność i efekt |
| --- | --- |
| Pierwszy setup | Walidacja wersji konfiguracji/Store, rezerwacja wyjść, load pamięci, subskrypcje, historia + raporty na żywo, uzgodnienie; oba nowe moduły observation |
| Restart / zwykły reload | Tryby z Store, dostępna historia, świeże odczyty i limity; zachowane terminy tylko przy wiarygodnym stanie; bieżąca ocena, bez replay |
| Aktywacja control | Ostrzeżenie konfliktu, walidacja zależnych możliwości, trwały zapis trybu, nowa ocena; brak danych blokuje tylko zależne działania |
| Powrót do observation | Unieważnienie generation przed oczekiwaniem I/O; anulowanie kolejnych poleceń/retry, trwały tryb; brak cofania nastaw |
| enabled=false | Anulowanie działań modułu; zachowanie ustawień, brak automatycznego OFF |
| Ponowne enabled=true | Zachowane ustawienia/tożsamość, mode=observation; odbudowa i odczyt; bez samoczynnej aktywacji |
| Reconfigure | Walidacja całego zmienianego zakresu i rezerwacji, zapis, anulowanie starych działań, odbudowa tylko zmienionych źródeł; nowe wyjście bez samoczynnej aktywacji |
| Odłączenie / usunięcie strefy | UI pokazuje stan i ostrzeżenie D86; zatwierdzenie anuluje działania, usuwa przypisanie; ostatni stan pozostaje |
| Unload / wyłączenie entry | Ustawienie stopped i nowej generation, unsubscribe i cancel timer/tasks, oczekiwanie zakończenia z ograniczeniem czasu, zapis potrzebnej pamięci, unload platform |
| Usunięcie entry | Jak unload, bez polecenia OFF; zwolnienie własności i usunięcie danych wpisu zgodnie z mechanizmem HA, bez usuwania historii Recordera |

Dwie równoczesne konfiguracje nie przechodzą check-then-act przy rezerwacji:
rejestr właścicieli produktu chroniony blokadą w event loop; commit przypisania
i zwolnienie starego następują jako jedna zmiana. Kontrola obejmuje wpisy
wyłączone i niezaładowane, na podstawie ich zapisanej konfiguracji.

## Dwa rodzaje czasu

Trwanie w uruchomionym procesie według monotonic clock / async_call_later,
terminy odtwarzalne jako UTC aware datetime. Harmonogram według strefy HA;
lokalne daty nie są trwałymi timerami. Zmiana strefy/clock powoduje ponowne
wyznaczenie obecnego pola i następnej rzeczywistej zmiany.

Po restarcie blokada może skrócić się o przerwę tylko z zapisanym terminem
i zgodnym wiarygodnym odczytem (A43). Przy niepewnym czasie lub stanie
odliczanie od ponownego wiarygodnego ustalenia, zgodnie z D55.
Warunki temperatury zapisują accrued_valid_duration oraz moment ostatniej
poprawnej obserwacji. Przerwa nie dopisuje czasu; odtworzenie historii przygotowuje
filtry, nie potwierdzenia. Ustąpienie warunku zeruje jego postęp,
brak danych wstrzymuje zgodnie z rundą 4.

Czas zamknięcia i potwierdzenie nagłego spadku biegną równolegle.
Ruch siłownika rozpoczyna niezależny raport przekaźnika, nie wysłanie.
Przy utracie dowodu w ruchu stan nieznany i brak gotowości do demandu.
Po odzyskaniu odczytu ponownie uzgadniamy stan, bez założenia, że ruch się odbył.

## Sekwencja CWU

Edycja UI nie zmienia stanu. Zatwierdzony plan tworzy nowe żądanie i rewizję.
Dla ON: aktualna temperatura docelowa → niezależny dowód → ON zezwolenia.
Jeżeli temperatura już wiarygodnie odpowiada celowi, bez zbędnego zapisu.
Dla OFF: anulowanie zależnego ON/temperatury, OFF niezależnie od potwierdzenia
temperatury, z polityką błędów wyjścia. Błąd ON nie cofa udanego zapisu temperatury
ani zapisanych ustawień. Przy nowym polu/panelu każda próba ocenia bieżący cel.

Nadpisanie przechowuje next effective transition UTC, nie next slot.
Przy jednakowym tygodniu expires_at=null i jawny komunikat.
Przeskok czasu stosuje obecne pole, cofnięcie powtarza lokalne pola.
Skan najbliższych lokalnych granic mapuje obie instancje powtórzonej godziny
na rzeczywiste UTC; nie tworzy nieistniejącego pola przy przeskoku.
Początkowy plan i higiena pozostają P05/P06.

## Granice trwałości

Błąd zapisu ustawień lub trybu zwraca błąd użytkownikowi, nie sukces.
Observation/stopped odcina wykonanie w pamięci od razu nawet przy awarii dysku.
Jeśli trybu nie udało się utrwalić, UI jawnie wskazuje ryzyko odtworzenia
poprzedniego trybu przy restarcie; zapis starego Store nie jest samowolnie kasowany.
Nie da się zagwarantować trwałości bez działającego nośnika.
Zapis zamiaru wykonania i stan retry są trwałe przed wysłaniem; crash w trakcie
usługi wymaga odczytu urządzenia, nie automatycznego ponowienia.
