# Runda 2 — codzienna obsługa

Uzgodniono z właścicielem produktu 10 listopada 2026. Runda codziennej obsługi zakończona; pozostają szczegóły regulacji, awarii oraz technicznego wykonania. To wymagania, nie działająca implementacja.

## CO i CWU — niezależne zezwolenia

Na dashboardzie są dwa osobne przełączniki obserwacja/sterowanie: CO i CWU. Można obserwować regulator CO, gdy harmonogram CWU działa aktywnie, i odwrotnie. Nowa konfiguracja zaczyna w obserwacji zgodnie z US03.

Tryb CWU Wyłączone/Stałe/Harmonogram jest innym ustawieniem niż obserwacja/sterowanie. W obserwacji analizujemy i pokazujemy decyzje; sam zapis ustawień nie zezwala na polecenia urządzenia.

## Cele ogrzewania domu

Ręczna zmiana temperatury zadanej CO dotyczy konkretnej strefy i staje się jej nową trwałą nastawą, zachowaną po restarcie. Nie jest nadpisaniem czasowym. Nie ma harmonogramu CO — harmonogram dotyczy wyłącznie CWU. Cele stref są obsługiwane poza panelem wspólnego zapisu CWU.

## Tryby CWU

| Tryb | Zachowanie przy aktywnym sterowaniu CWU |
| --- | --- |
| Wyłączone | Wyłącza zezwolenie na podgrzewanie CWU, bez wyłączania ogrzewania domu |
| Stałe | Podgrzewanie do jednej ustawionej temperatury, niezależnie od harmonogramu |
| Harmonogram | Stan oraz temperatura z tygodniowego planu, z możliwością ręcznego nadpisania |

W harmonogramie każdy dzień ma 48 logicznych pól 30 min. Pole może oznaczać wyłączone albo włączone z temperaturą docelową. Włączenie oznacza zezwolenie na grzanie; sprężarka i zabezpieczenia pozostają pod kontrolą producenta.

## Ręczne nadpisanie CWU

- W trybie Harmonogram użytkownik może ręcznie nadpisać stan lub temperaturę bez zmiany trybu na Stałe.
- Nadpisanie zaczyna obowiązywać po zatwierdzeniu przyciskiem Zapisz i trwa do następnej rzeczywistej zmiany stanu/temperatury wynikającej z harmonogramu.
- Identyczne sąsiednie pola 30 min tworzą jeden ciągły okres i nie kasują nadpisania.
- Można ręcznie włączyć CWU w okresie zaplanowanego wyłączenia. Podgrzewanie jest dozwolone od zatwierdzenia, nie dopiero od następnego zaplanowanego włączenia.
- Przy ręcznym włączeniu panel podpowiada ostatnią temperaturę zadaną CWU. Można ją zmienić przed zapisem.
- Na następnej zaplanowanej zmianie harmonogram odzyskuje sterowanie i ustawia właściwy stan oraz temperaturę.

Przykład: plan Wyłączone od 12:00 do 16:00, potem Włączone 45°C. Użytkownik zapisuje ręczne włączenie 48°C o 14:00. Do 16:00 obowiązuje zezwolenie i 48°C; granice 14:30, 15:00 i 15:30 nie usuwają nadpisania. O 16:00 harmonogram ustawia 45°C. Nie wymaga to przejścia do Stałe.

## Jeden panel CWU i jeden Zapisz

Panel obejmuje wyłącznie ustawienia CWU: tryb, ręczny stan, temperatury i harmonogram. Cele stref CO oraz dwa przełączniki obserwacja/sterowanie są poza panelem.

Zmiany podczas edycji są robocze. Dopiero jeden Zapisz zatwierdza całość, po sprawdzeniu poprawności wszystkich ustawień. Błąd nie może zapisać części edycji. Spójny zapis konfiguracji nie oznacza gwarancji atomowego wykonania kilku poleceń przez pompę — błędy urządzenia wymagają osobnej polityki.

Przy zamykaniu panelu z niezapisanymi zmianami pojawia się pytanie „Odrzucić niezapisane zmiany?”. Rezygnacja z odrzucenia zachowuje edycję. Nie dodajemy osobnego potwierdzenia wyboru Wyłączone; wybór wymaga zatwierdzenia Zapisz jak inne ustawienia CWU.

## Scenariusze do przyszłego odbioru

| Przypadek | Oczekiwanie |
| --- | --- |
| CO obserwacja, CWU sterowanie | Brak automatycznych poleceń CO; CWU działa zgodnie z zatwierdzonymi ustawieniami |
| CO sterowanie, CWU obserwacja | Regulator CO działa; brak poleceń CWU |
| Zmiana celu Parter | Nowa trwała nastawa Parter; cel Piętro bez zmian |
| Ręczne włączenie CWU podczas zaplanowanego OFF | Po Zapisz zezwolenie obowiązuje do kolejnej zmiany planu |
| Kolejne identyczne pola półgodzinne | Nie kończą nadpisania |
| Ręczna temperatura i następna zmiana planu | W terminie zmiany obowiązuje stan/temperatura harmonogramu |
| Włączenie CWU w panelu | Podpowiedź ostatniej temperatury, edytowalna przed zapisem |
| Zmiana trybu, temperatury i harmonogramu bez zapisu | Brak zmian aktywnych ustawień i poleceń wynikających z edycji |
| Niepoprawna część edycji | Walidacja zatrzymuje zapis całego zestawu |
| Zamknięcie niezapisanej edycji | Pytanie o odrzucenie zmian |
| Wyłączone CWU | Nie wyłącza CO; w obserwacji pozostaje wyłącznie proponowanym działaniem |

Nie wykonano tych scenariuszy na integracji, ponieważ nie ma jeszcze implementacji.

## Tematy pozostawione na dalsze rundy

- Zakresy i krok temperatur oraz zmiana filtrów/potwierdzeń po zmianie celu.
- Ręczne zmiany bezpośrednio na encjach pompy lub w aplikacji producenta; ręczny demand.
- Restart, utrata komunikacji, zmiana czasu i granice tygodnia.
- Brak przyszłej zmiany w całym harmonogramie oraz edycja harmonogramu podczas nadpisania.
- Pierwsza podpowiedź temperatury, gdy nie istnieje ostatnia nastawa.
- Reakcja na częściowe wykonanie poleceń pompy, ochrona producenta i higiena CWU.
- Relacja do F01, opcjonalność/termin wydania CWU oraz technologia panelu.

Powiązania: [US02](user-stories.md#us02), [US03](user-stories.md#us03), [US07](user-stories.md#us07), [US11](user-stories.md#us11), [US13](user-stories.md#us13), [US14](user-stories.md#us14). Decyzje D24–D30 w [rejestrze](decisions.md).
