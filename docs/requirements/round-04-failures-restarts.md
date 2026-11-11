# Runda 4 — awarie, braki danych i restarty

Uzgodnienia z 10 listopada 2026. Przypadki odbioru opisują oczekiwane zachowanie produktu.

## Pomiary i gotowość okien

| Sytuacja | Zachowanie |
| --- | --- |
| Część termometrów strefy jest niedostępna lub nieaktualna | Kontynuuj z przynajmniej jednym poprawnym termometrem. Pokaż liczbę dostępnych źródeł, np. „Dostępny 1 z 2 termometrów”. |
| Utrata lub powrót termometru zmienia skład pomiaru strefy | Pokaż zmianę jakości. Sam skok wynikający ze zmiany zestawu czujników nie uruchamia zabezpieczenia nagłego spadku. |
| Brak nowego raportu temperatury wnętrza | Domyślny limit 120 min. |
| Brak nowego raportu temperatury zewnętrznej | Domyślny limit 30 min. |
| Jawna niedostępność albo niepoprawna wartość | Uznaj pomiar za utracony od razu. |
| Poprawna, niezmienna temperatura | Nadal jest poprawna przy aktualnych raportach. |

Limity świeżości są wspólne dla programu i edytowalne w konfiguracji zaawansowanej. Odliczanie odnosi się do raportu źródła, a nie zmiany wartości. Diagnostyka odróżnia dostępny raport w HA od dowodu nowego fizycznego pomiaru.

Każde okno jest gotowe osobno przy co najmniej 80% pokrycia czasu poprawnymi danymi i świeżym bieżącym pomiarze. Próg pokrycia jest wspólny i konfigurowalny. Gdy pomiar zaworów jest gotowy, a trend jeszcze się uzupełnia, obowiązują progi dla trendu niejasnego. Dashboard pokazuje „Brak danych do oceny trendu”. Komfort i trend długoterminowy wymagają gotowości własnych okien.

Nagły spadek oznacza bieżący pomiar strefy niższy od temperatury komfortowej o ponad 0,7°C. Próg jest ustawieniem strefy. Przy rozpoznanym spadku otwarcie wymaga uzgodnionego potwierdzenia niedogrzania przez 30 min poprawnych obserwacji. Zmiana składu czujników sama nie jest nagłym spadkiem.

## Utrata temperatury strefy

Po utracie ostatniego poprawnego termometru oznacz temperaturę i komfort jako niedostępne. Wyklucz strefę z ważonej korekty komfortu i trendu. Wstrzymaj jej potwierdzenia zależne od temperatury. Domyślnie przez 30 min zachowaj ostatnie żądanie zaworów i zapotrzebowania oraz pokaż ostrzeżenie. Okres przejściowy liczy się od uznania ostatniego pomiaru za utracony i jest konfigurowalny wspólnie dla programu.

Po okresie przejściowym strefa przechodzi w awaryjne otwarcie przypisanych zaworów. Jej brak pomiaru nie tworzy dodatkowego zapotrzebowania demand ani korekty pokojowej. Może odbierać ciepło wynikające z pracy pompy. Regulacja bazuje na poprawnych strefach i temperaturze zewnętrznej.

Po utracie temperatur wszystkich stref i upływie okresu przejściowego:
- zawory przechodzą w awaryjne otwarcie;
- integracja wycofuje dodatkowe żądanie demand, jeśli obsługuje to wyjście;
- CO1 wynika z krzywej pogodowej przy poprawnym outdoor, bez korekt pokojowych;
- pompa zachowuje własną pracę. Integracja nie wydaje osobnego STOP CO1.

Jeżeli wszystkie aktywne strefy mają poprawne pomiary i zamknięte zawory, utrzymujemy aktualną nastawę CO1 i wyłączamy demand przy braku zapotrzebowania. Ponowna możliwość odbioru ciepła uruchamia ocenę z aktualnych danych.

## Utrata outdoor lub nastawy PC

- Brak outdoor wstrzymuje obliczanie i zapisy nowych nastaw CO1. Zawory i demand mogą nadal działać na poprawnych temperaturach stref, zgodnie z timerami. CWU jest niezależne.
- Brak outdoor razem z utratą wszystkich temperatur stref pozostawia ostatnią nastawę w pompie. Zawory i demand przechodzą w uzgodniony stan awaryjny po okresie przejściowym.
- Brak encji nastawy PC lub wiarygodnego zakresu urządzenia blokuje zapisy CO1. Można pokazać niewykonywalną propozycję, jeśli dane wystarczają do obliczenia. Pozostałe funkcje wymagają swoich poprawnych źródeł i wyjść.
- Po powrocie odczytaj aktualną nastawę i limity. Przelicz decyzję i respektuj ograniczenie 1°C / 120 min. Odczyty nie służą do odtwarzania zaległych poleceń.

## Zawory i demand przy błędzie wyjścia

Po błędzie przełączenia lub utracie sterownika pokaż nieznany stan zaworu i ostrzeżenie. Gotowość wymaga raportu przełączenia przekaźnika oraz upływu czasu otwierania. Raport elektryczny nie jest dowodem fizycznego ruchu zaworu. Zapotrzebowanie strefy z niepotwierdzonym otwarciem nie wystarcza do ON demandu. Gotowość może zapewnić inna poprawna strefa. Po nieudanym zamknięciu nadal uwzględniaj strefę w ocenie przegrzewania. Sprawne strefy działają dalej.

Dla demandu pokazuj stan żądany i raportowany. Awaria wyjścia nie przełącza zasilania pompy ani CO1 inną encją. Po zmianie zapotrzebowania ponawiamy tylko obecnie potrzebny stan. Przerwę 15 min liczymy od potwierdzonego raportowanego OFF. Jeżeli zapotrzebowanie zanika przy oczekiwaniu na ON, aktualne polecenie dotyczy OFF.

## Zapisy i ponowienia

Rozróżniamy polecenie wysłane, potwierdzone niezależnym odczytem, brak potwierdzenia i brak możliwości potwierdzenia. Optymistyczna aktualizacja encji nie daje dowodu wykonania. Runda 5 ustala domyślnie 2 minuty oczekiwania, konfigurowalne dla programu. Odstępy prób są liczone od wysłania. Poprawne spóźnione potwierdzenie nadal aktualnego polecenia kończy serię przed kolejną próbą.

Wspólna polityka zapisów obejmuje CO1, zawory, demand i CWU:
1. Pierwsza próba i maksymalnie dwie dalsze w odstępach 5 min.
2. Po trzeciej nieudanej próbie zgłoszenie błędu zapisu.
3. Następne odstępy wynoszą 10, 15, 25, 40, 65, 105, 120, 120… min. Odstępy rosną według ciągu Fibonacciego do limitu 120 min.
4. Licznik i termin są osobne dla sterowanego wyjścia. Potwierdzony sukces zeruje serię. Zmiana żądanej wartości sama nie zeruje licznika.
5. Przed każdą próbą sprawdź aktualną potrzebę, dane, zakres, blokady i zezwolenie na sterowanie. Anuluj nieaktualne polecenie i zakończ próby po przejściu do obserwacji. Po odzyskaniu komunikacji uzgodnij raportowany stan z aktualną decyzją.

Ponowienie CO1 dotyczy tej samej bezwzględnej nastawy, np. 28°C. Niepotwierdzony zapis nie stanowi podstawy kolejnego kroku o 1°C. Ograniczenie zmiany 1°C / 120 min dotyczy nowych zmian nastawy.

## Uruchomienie i historia

Przy pierwszym starcie, restarcie lub przeładowaniu odczytaj bieżące źródła i dostępną historię pomiarową, domyślnie 48 h wstecz. Zakres jest konfigurowalny. Zbuduj pomiary stref, średnie, mediany i trendy według aktualnych ustawień, łącząc historię z pamięcią bez podwójnego uwzględniania próbek. Agregacja uwzględnia czas obowiązywania odczytów. Luki pozostają lukami, a wystarczająca historia od razu przygotowuje filtry. Dashboard pokazuje postęp odbudowy i braki.

Zachowujemy cele, ustawienia, harmonogramy, potrzebne próbki, potwierdzone stany i czasy zmian, liczniki i terminy ponowień oraz postęp potwierdzeń temperatury. Dane historyczne przygotowują filtry. Bieżące stany urządzeń sprawdzamy przed uzgadnianiem wyjść.

Pierwsza konfiguracja zaczyna w obserwacji. Po restarcie przywracamy niezależne zapisane tryby CO i CWU. Sterowanie wznawia się po przygotowaniu wymaganych danych i ocenie aktualnego stanu. Regulator podejmuje bieżącą decyzję bez odtwarzania kolejki.

Jeżeli brakuje wiarygodnego poprzedniego żądania strefy, stosujemy zwykłe progi po przygotowaniu pomiarów. Między progami zawory pozostają w odczytanym stanie, a strefa czeka z zapotrzebowaniem na spełnienie warunku otwarcia. Strefa bez zaworów również czeka na ten warunek. Przy wiarygodnej pamięci poprzednie żądanie pozostaje ważne do kolejnej decyzji.

## Odliczanie po restarcie

Blokady czasu między zmianami CO1, przerwy demandu i minimalnego zamknięcia strefy mogą upływać podczas przerwy, jeśli mamy zapisany czas i odczyt jest zgodny z zapisanym stanem. Przy niepewności odliczanie zaczyna się od ponownego wiarygodnego ustalenia stanu.

Potwierdzenia zależne od temperatury zachowują postęp bez doliczania czasu przerwy w poprawnej obserwacji. Odbudowa historii sama nie odtwarza decyzji ani potwierdzeń.

Przykład z demandem. OFF potwierdzono 10 min przed restartem. Po 2 min przerwy nadal raportuje OFF. Do końca blokady pozostają 3 min.

## CWU po awarii i restarcie

Przywróć zapisany tryb CWU. Nadpisanie wraca, jeśli jego termin jeszcze nie upłynął. Gdy termin minął podczas przerwy, zastosuj aktualny przedział harmonogramu. Przerwa nie wydłuża nadpisania. Odczytaj stan urządzenia, unikaj zbędnych zapisów i zastosuj przywrócony tryb obserwacji oraz politykę ponowień.

Włączenie CWU wymaga wcześniejszego zapisu i potwierdzenia temperatury docelowej. Wyłączenie CWU wysyłamy bez czekania na wynik zapisu temperatury. Przy częściowym wykonaniu zachowujemy zatwierdzone ustawienia, pokazujemy przyjęte polecenia i ponawiamy tylko brakujące, nadal potrzebne działanie. Każda próba sprawdza aktualny tryb i harmonogram.

## Scenariusze do odbioru

- Utrata jednego z dwóch termometrów pozwala kontynuować na drugim i zgłasza ograniczoną dostępność.
- Po utracie wszystkich termometrów strefy 30 min okresu przejściowego poprzedza otwarcie awaryjne bez własnego demandu.
- Wszystkie temperatury stref utracone i outdoor poprawny prowadzą do krzywej bez korekt oraz wycofania demandu.
- Wszystkie strefy poprawnie mierzone, ale zamknięte pozostawiają aktualne CO1 i OFF demandu.
- Utrata outdoor lub limitów PC wstrzymuje odpowiednie zapisy. Poprawne zawory i niezależny demand mogą działać.
- Przekaźnik z niepotwierdzonym otwarciem nie wystarcza do włączenia demandu.
- Błąd po trzeciej próbie uruchamia odstępy 10, 15, 25, 40, 65, 105, 120… min. Udany odczyt potwierdzający zeruje licznik.
- Restart odtwarza 48 h dostępnych pomiarów, gotowość poszczególnych okien, tryby, timery i terminy ponowień.
- Brak gotowego trendu przy gotowym pomiarze zaworów używa progów niejasnego trendu, z informacją diagnostyczną.
- W CWU wygaśnięcie nadpisania podczas przerwy stosuje bieżący przedział. Przy częściowym wykonaniu wysyłane jest tylko nadal potrzebne polecenie.

Runda 5 ustala potwierdzenie 2 min, wspólny czas pracy siłowników 3 min i zasady zmiany czasu harmonogramu. Kontrakty źródeł i pozostałe szczegóły techniczne należą do rundy architektury. [Tabela odbioru A01–A59](round-05-acceptance.md) konkretyzuje oczekiwane wyniki.

Powiązania [US01](user-stories.md#us01), [US03](user-stories.md#us03), [US04](user-stories.md#us04), [US05](user-stories.md#us05), [US06](user-stories.md#us06), [US09](user-stories.md#us09), [US13](user-stories.md#us13), [US14](user-stories.md#us14), [US16](user-stories.md#us16), [US17](user-stories.md#us17), [US19](user-stories.md#us19).
