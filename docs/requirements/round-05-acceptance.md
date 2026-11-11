# Runda 5 — scenariusze odbioru

Uzgodnienia z 11 listopada 2026. Zestaw konkretyzuje rundy 1–4 i doprecyzowania przyjęte w rundzie 5. Oczekiwane wyniki są kryteriami przyszłej implementacji. Scenariusze opisano przy aktywnym odpowiednim module, poprawnych danych i ustawieniach domyślnych, chyba że wiersz wskazuje inaczej. T w regułach zaworów oznacza obliczony pomiar do zaworów, a ΔT różnicę punktów trendu.

## Doprecyzowania rundy 5

- Czas potwierdzenia zapisu wynosi domyślnie 2 minuty i jest konfigurowalny wspólnie dla programu. Odstępy ponowień liczymy od wysłania poprzedniej próby. Późniejsze poprawne potwierdzenie nadal aktualnego polecenia kończy serię przed kolejnym ponowieniem.
- Ręczna zmiana nastawy wody na pompie lub w jej aplikacji pozostawia regulator CO1 aktywny. Bieżąca wartość jest odczytywana, a następny dozwolony zapis zmierza do aktualnego wyniku algorytmu. Nie wprowadzamy dodatkowej pauzy za samą taką zmianę.
- Panel CWU udostępnia pola zależnie od trybu. W Wyłączone temperatura i harmonogram są niedostępne. W Stałe dostępna jest temperatura, w Harmonogram dostępny jest plan. Dzięki temu jedna edycja nie łączy ręcznej temperatury i harmonogramu.
- Zapis w trybie Harmonogram kończy wcześniejsze nadpisanie i natychmiast stosuje aktualny przedział zapisanego planu. Dotyczy również ponownego zapisania identycznego planu.
- Tymczasowe nadpisania CWU dotyczą ręcznych zmian poza panelem, np. na encji lub w aplikacji PC. Trwają do kolejnej zmiany planu albo zapisu panelu w Harmonogram. Bez następnej zmiany trwają do ręcznej zmiany lub tego zapisu, z komunikatem „Nadpisanie ręczne — brak zaplanowanej zmiany”.
- Harmonogram używa strefy czasowej HA. Przy przeskoku zegara stosujemy aktualny lokalny przedział. Przy cofnięciu powtarzają się te same lokalne pola. Blokady i ponowienia mierzą rzeczywisty upływ czasu. Nadpisanie kończy następna rzeczywista zmiana ustawienia wynikającego z planu.
- Jeden globalny parametr „Czas pracy siłowników”, domyślnie 3 minuty, obejmuje otwieranie i zamykanie. Jest ustawieniem zaawansowanym programu. Po raporcie przełączenia przekaźnika pokazujemy Otwieranie/Zamykanie, a po upływie czasu przewidywany stan końcowy. Dopiero wtedy zaczynamy ocenę 120-minutowego warunku ostrzeżenia o zamknięciu.

## Scenariusze odbioru

### Konfiguracja

| ID | Powiązane historie | Warunki i zdarzenia | Oczekiwany wynik |
| --- | --- | --- | --- |
| A01 | [US01](user-stories.md#us01), [US09](user-stories.md#us09), [US15](user-stories.md#us15), [US16](user-stories.md#us16) | Jedna strefa Dom, termometr, outdoor i encja nastawy PC, zawory i demand wyłączone | Konfiguracja może zakończyć się w obserwacji. Strefa uczestniczy w regulacji pomiarowej. |
| A02 | [US09](user-stories.md#us09), [US16](user-stories.md#us16) | Włączony moduł CO, brak wskazanej encji nastawy PC przy konfiguracji obserwacji | Kreator wskazuje brak i wymaga wyboru encji. |
| A03 | [US09](user-stories.md#us09) | Sprawdzenie czterech kombinacji obsługi zaworów i demandu | Wymagane są tylko wyjścia włączonych funkcji. Bez demandu wynik zapotrzebowania jest diagnostyczny. |
| A04 | [US10](user-stories.md#us10), [US15](user-stories.md#us15) | Dwie strefy NC/NO, kilka wyjść strefy, próba przypisania tego samego wyjścia kolejnej strefie | Typ strefy obejmuje jej wyjścia. Współdzielenie wyjścia zostaje odrzucone. |
| A05 | [US01](user-stories.md#us01), [US15](user-stories.md#us15), [US18](user-stories.md#us18) | Pokoje zebrane w grupie Piętro | Cele i priorytety mają strefy. Grupa służy prezentacji i nie jest dodatkowo liczona w regulacji. |
| A06 | [US06](user-stories.md#us06), [US17](user-stories.md#us17) | Wybór trendu 2 h / 2 h oraz parametrów poza uzgodnionymi zakresami | Zapis konfiguracji wskazuje błędy. Dla trendu jedna funkcja obejmuje oba punkty. |

### Obserwacja i UI

| ID | Powiązane historie | Warunki i zdarzenia | Oczekiwany wynik |
| --- | --- | --- | --- |
| A07 | [US02](user-stories.md#us02), [US03](user-stories.md#us03), [US11](user-stories.md#us11) | CO w obserwacji, CWU aktywne, zmiana celu Parter z 21 na 21,5°C | Nowy cel jest trwały, cel Piętro pozostaje aktualny. CO pokazuje decyzję bez poleceń, CWU zachowuje własny tryb. |
| A08 | [US03](user-stories.md#us03), [US07](user-stories.md#us07) | Przejście CO z obserwacji do sterowania i ponownie do obserwacji | Aktywacja ocenia aktualne dane i ograniczenia. Obserwacja zatrzymuje kolejne polecenia i ponowienia. |

### Pomiary i strefy

| ID | Powiązane historie | Warunki i zdarzenia | Oczekiwany wynik |
| --- | --- | --- | --- |
| A09 | [US01](user-stories.md#us01), [US06](user-stories.md#us06) | Kilka termometrów w strefie, globalna średnia domyślna | Powstaje średnia strefy, potem historia jej okien. Okna i funkcje są wspólne dla programu, progi stref niezależne. |
| A10 | [US05](user-stories.md#us05) | Cel 21°C, T do zaworów 21°C, ΔT trendu +0,2°C, dane gotowe | Żądanie zamknięcia strefy. |
| A11 | [US05](user-stories.md#us05) | Cel 21°C, T 21°C, ΔT −0,2°C, blokady otwarcia upłynęły | Żądanie otwarcia strefy. |
| A12 | [US05](user-stories.md#us05) | Cel 21°C, trend niejasny, T 21,2°C albo 20,8°C | Odpowiednio żądanie zamknięcia albo otwarcia po spełnieniu blokad. |
| A13 | [US05](user-stories.md#us05) | Temperatura między progami, wiarygodne poprzednie żądanie | Zachowujemy poprzednie żądanie. |
| A14 | [US05](user-stories.md#us05), [US09](user-stories.md#us09) | Pierwszy start, gotowe pomiary między progami, brak poprzedniego żądania | Zawory pozostają w odczytanym stanie. Strefa czeka ze zgłoszeniem zapotrzebowania na warunek otwarcia. |
| A15 | [US05](user-stories.md#us05), [US06](user-stories.md#us06) | Bieżący pomiar jest niższy od komfortowego o 0,8°C i utrzymuje się warunek niedogrzania | Otwarcie czeka na 30 min poprawnych obserwacji. Ustąpienie warunku przed terminem zeruje potwierdzenie. |
| A16 | [US05](user-stories.md#us05) | Minimalne zamknięcie i potwierdzenie niedogrzania kończą się odpowiednio 10:30 i 10:20 | Najwcześniejsze otwarcie 10:30 przy nadal spełnionych warunkach. Czasów nie sumujemy. |
| A17 | [US05](user-stories.md#us05), [US10](user-stories.md#us10), [US12](user-stories.md#us12) | Przekaźnik potwierdził zamknięcie o 10:00, czas pracy siłowników 3 min | Do 10:03 stan Zamykanie, potem przewidywane zamknięcie. Przy ciągłym spełnieniu warunków ostrzeżenie najwcześniej 12:03. |

### CO1

| ID | Powiązane historie | Warunki i zdarzenia | Oczekiwany wynik |
| --- | --- | --- | --- |
| A18 | [US17](user-stories.md#us17), [US18](user-stories.md#us18) | Parter e=−0,4°C, priorytet 1, Piętro e=+0,4°C, priorytet 2 | E=(−0,4+0,8)/3≈+0,133°C, w martwej strefie komfortu. Równe priorytety dają równe udziały. |
| A19 | [US17](user-stories.md#us17) | E=+0,6°C, martwa strefa 0,2°C, mnożnik 1,5 | Korekta komfortu +0,6°C przed sumą, ograniczeniami i zaokrągleniem. |
| A20 | [US05](user-stories.md#us05), [US17](user-stories.md#us17), [US18](user-stories.md#us18) | Przegrzana strefa ma wszystkie przypisane wyjścia zamknięte zgodnie z raportem i czasem ruchu | Jej odchylenie wypada z korekty CO1. Temperatura i warunki ostrzeżenia są nadal monitorowane. |
| A21 | [US17](user-stories.md#us17), [US18](user-stories.md#us18) | Strefa bez wyjść ma komfort ≥cel+0,5°C przez 60 min | Wzrost CO1 jest zablokowany także przy dodatnim E. Zwolnienie wymaga ≤cel+0,2°C przez 30 min. |
| A22 | [US06](user-stories.md#us06), [US17](user-stories.md#us17) | Ważony wzrost komfortu 0,35°C przez 12 h, brak ważonego niedogrzania | Korekta trendu −0,25°C. Przy wzroście 0,2°C daje 0, a przy ≥0,5°C osiąga −0,5°C. |
| A23 | [US17](user-stories.md#us17), [US20](user-stories.md#us20) | Suma modułów przekracza skonfigurowany limit | Suma jest ograniczona. Zwiększenie limitu zachowuje zakres PC, ograniczenie komfortu, blokady i szybkość zmian. |
| A24 | [US16](user-stories.md#us16), [US17](user-stories.md#us17) | Pompa ma zakres 20–55°C, użytkownik zawęża do 23–35°C | Wykonywalne nastawy mieszczą się w 23–35°C. Próba rozszerzenia poza zakres pompy jest odrzucona. |
| A25 | [US17](user-stories.md#us17) | Krok PC 1°C, wynik 27,4°C albo 27,5°C, bieżąca nastawa 30°C | Docelowo odpowiednio 27°C albo 28°C. Najbliższy nowy zapis wynosi najwyżej 29°C, po wymaganym odstępie. |
| A26 | [US07](user-stories.md#us07), [US17](user-stories.md#us17) | Rozpoznana ręczna zmiana nastawy w pompie przy aktywnym CO | Regulator pozostaje aktywny i przy najbliższym dozwolonym zapisie zmierza do własnej bieżącej nastawy z zachowaniem ograniczeń. |

### Demand

| ID | Powiązane historie | Warunki i zdarzenia | Oczekiwany wynik |
| --- | --- | --- | --- |
| A27 | [US09](user-stories.md#us09), [US10](user-stories.md#us10) | Demand OFF potwierdzony 10:00, żądanie i potwierdzenie przekaźnika otwarcia strefy o 10:05 | Strefa przewidywanie gotowa o 10:08. Najwcześniejsze ON demandu 10:15, jeśli zapotrzebowanie trwa. |
| A28 | [US09](user-stories.md#us09) | Warunki A27, lecz ostatnie zapotrzebowanie zanika 10:12 | Oczekujące ON jest anulowane. Żądany demand pozostaje OFF. |
| A29 | [US09](user-stories.md#us09) | Potrzebująca strefa jest już otwarta albo ma tylko zapotrzebowanie wirtualne | Nie rozpoczynamy nowego oczekiwania na ruch zaworów. Nadal obowiązuje minimalna przerwa demandu. |

### Awarie i historia

| ID | Powiązane historie | Warunki i zdarzenia | Oczekiwany wynik |
| --- | --- | --- | --- |
| A30 | [US01](user-stories.md#us01), [US16](user-stories.md#us16) | Jeden z dwóch termometrów strefy jest utracony | Działa pozostały poprawny pomiar z ostrzeżeniem 1 z 2. Zmiana zestawu sama nie jest nagłym spadkiem. |
| A31 | [US05](user-stories.md#us05), [US09](user-stories.md#us09) | Ostatni termometr strefy staje się jawnie niedostępny o 10:00 | Do 10:30 zachowujemy żądania. Korekty pokojowe są pomijane. Potem awaryjne otwarcie bez własnego demandu. |
| A32 | [US16](user-stories.md#us16) | Brak nowego raportu wnętrza przez ponad 120 min albo outdoor przez ponad 30 min | Źródło jest nieaktualne. Niezmienna wartość z aktualnymi raportami pozostaje poprawna. |
| A33 | [US09](user-stories.md#us09), [US17](user-stories.md#us17) | Wszystkie temperatury stref utracone, okresy przejściowe minęły, outdoor poprawny | Awaryjne otwarcie, wycofanie demandu i CO1 z samej krzywej. |
| A34 | [US09](user-stories.md#us09), [US17](user-stories.md#us17) | Wszystkie aktywne strefy poprawnie mierzone i zamknięte | Utrzymanie bieżącego CO1 oraz OFF demandu przy braku zapotrzebowania. |
| A35 | [US16](user-stories.md#us16), [US17](user-stories.md#us17) | Utrata outdoor albo aktualnej nastawy/wiarygodnego zakresu PC | Odpowiednie zapisy CO1 wstrzymane. Sprawne zawory, demand i CWU działają według własnych danych. |
| A36 | [US05](user-stories.md#us05), [US09](user-stories.md#us09) | Błąd przekaźnika otwierania albo zamykania | Stan nieznany i ponowienia. Niepotwierdzone otwarcie nie wystarcza do ON demandu. Nieudane zamknięcie zachowuje strefę w ochronie przegrzewania. |
| A37 | [US04](user-stories.md#us04), [US17](user-stories.md#us17), [US19](user-stories.md#us19) | Zapis CO1 wysłany 10:00 bez niezależnego potwierdzenia | Próba niepotwierdzona o 10:02. Kolejne wysłania 10:05 i 10:10. Błąd zapisu po braku potwierdzenia do 10:12. |
| A38 | [US04](user-stories.md#us04), [US17](user-stories.md#us17), [US19](user-stories.md#us19) | Seria A37 nadal bez sukcesu | Dalsze próby 10:20, 10:35, 11:00, 11:40, 12:45, 14:30, 16:30, potem co 120 min. Przed każdą aktualna ocena potrzeby. |
| A39 | [US04](user-stories.md#us04), [US17](user-stories.md#us17) | Po limicie 10:02 poprawne potwierdzenie aktualnego polecenia dociera 10:03 | Koniec ponowień i reset serii błędów. Próba 10:05 nie jest wysyłana. |
| A40 | [US03](user-stories.md#us03), [US09](user-stories.md#us09), [US17](user-stories.md#us17) | Oczekujące ponowienie, lecz użytkownik przechodzi w obserwację albo aktualne żądanie się zmienia | Przed kolejną próbą obowiązuje bieżący tryb i decyzja. Poprzednie polecenie nie jest odtwarzane z kolejki. |
| A41 | [US03](user-stories.md#us03), [US19](user-stories.md#us19) | Start z dostępną historią 48 h i świeżymi źródłami | Odtworzone pomiary, okna i gotowość pozwalają działać bez ponownego zbierania pełnej historii. Zachowane tryby przywracamy po sprawdzeniu bieżących stanów. |
| A42 | [US05](user-stories.md#us05), [US19](user-stories.md#us19) | Pomiar zaworów gotowy, trend niegotowy; okno komfortu ma mniej niż 80% poprawnego pokrycia | Zawory używają progów niejasnego trendu z komunikatem. Korekta komfortu czeka na gotowość własnego okna. |
| A43 | [US09](user-stories.md#us09), [US19](user-stories.md#us19) | OFF demandu potwierdzony 10 min przed restartem, przerwa 2 min, aktualny raport nadal OFF | Pozostają 3 min blokady. Potwierdzenia temperatury nie doliczają przerwy w obserwacji. |

### CWU

| ID | Powiązane historie | Warunki i zdarzenia | Oczekiwany wynik |
| --- | --- | --- | --- |
| A44 | [US13](user-stories.md#us13), [US14](user-stories.md#us14) | Wybór Wyłączone, Stałe albo Harmonogram w panelu | Wyłączone blokuje temperaturę i plan. Stałe udostępnia temperaturę, blokuje plan. Harmonogram udostępnia plan, blokuje temperaturę stałą. |
| A45 | [US13](user-stories.md#us13) | Zmiana pól panelu i próba zamknięcia bez Zapisz | Edycja jest robocza. Zamknięcie wymaga potwierdzenia odrzucenia. Jeden Zapisz zatwierdza poprawny zestaw. |
| A46 | [US13](user-stories.md#us13) | Aktywne CWU, tryb Wyłączone zapisany w panelu | Wykonujemy żądanie OFF CWU. Obsługa ogrzewania domu pozostaje zależna od własnych reguł. |
| A47 | [US07](user-stories.md#us07), [US13](user-stories.md#us13), [US14](user-stories.md#us14) | Zewnętrzne ręczne ON 48°C o 14:00 podczas planu OFF do 16:00, potem ON 45°C | Podgrzewanie może działać według nadpisania do 16:00. Pola 14:30/15:00/15:30 nie kasują go. O 16:00 obowiązuje 45°C. |
| A48 | [US07](user-stories.md#us07), [US13](user-stories.md#us13), [US14](user-stories.md#us14) | Warunki A47, o 14:30 zapis panelu w Harmonogram, plan bieżący OFF | Nadpisanie kończy się o 14:30 i obowiązuje OFF z bieżącego pola. Dotyczy również zapisu identycznego planu. |
| A49 | [US07](user-stories.md#us07), [US13](user-stories.md#us13), [US14](user-stories.md#us14) | Nadpisanie aktywne, zapis zmienionego planu o 14:30, którego obecny przedział to ON 46°C, następna zmiana 15:00 | O 14:30 obowiązuje 46°C z zapisanego planu. Nie czekamy do 15:00. |
| A50 | [US13](user-stories.md#us13), [US14](user-stories.md#us14) | Cały tydzień ma jednakowy stan i temperaturę, potem zewnętrzne nadpisanie | Nadpisanie trwa do ręcznej zmiany lub zapisu panelu w Harmonogram. Widoczny komunikat o braku zaplanowanej zmiany. |
| A51 | [US13](user-stories.md#us13), [US14](user-stories.md#us14) | Restart podczas ważnego nadpisania albo po jego terminie | Odtwarzamy ważne nadpisanie. Po upływie terminu stosujemy bieżący przedział bez wydłużania i bez kolejki pominiętych zmian. |
| A52 | [US13](user-stories.md#us13) | Żądanie ON wymaga nowej temperatury, zapis temperatury zawodzi | ON czeka na potwierdzenie temperatury. Ponawiamy aktualnie potrzebny zapis zgodnie z polityką. |
| A53 | [US13](user-stories.md#us13) | Aktualne żądanie zmienia się na OFF podczas niepotwierdzonej temperatury | OFF jest wykonywane bez oczekiwania na temperaturę. Zachowujemy zatwierdzone ustawienia i pokazujemy wynik operacji. |
| A54 | [US14](user-stories.md#us14) | Zmiana zegara do przodu pomija lokalne pola planu | Po zmianie stosujemy aktualny lokalny przedział. Pominiętych pól nie odtwarzamy. |
| A55 | [US14](user-stories.md#us14) | Cofnięcie zegara powtarza godzinę planu | Ponownie obowiązują te same lokalne pola. Polecenie jest potrzebne przy różnicy stanu/temperatury. |
| A56 | [US09](user-stories.md#us09), [US14](user-stories.md#us14), [US19](user-stories.md#us19) | Zmiana czasu podczas blokady lub ponowień i przy nadpisaniu | Timery mierzą rzeczywisty upływ. Nadpisanie kończy następna rzeczywista zmiana ustawienia z lokalnego planu. |

### Moduły i migracja

| ID | Powiązane historie | Warunki i zdarzenia | Oczekiwany wynik |
| --- | --- | --- | --- |
| A57 | [US20](user-stories.md#us20), [US21](user-stories.md#us21) | Wyłączony moduł korekty lub bieżąca wersja bez prognoz | Wkład modułu odpowiada jego aktywności, a wspólne limity i obserwacja obowiązują. Prognozy pozostają poza bieżącym programem. |
| A58 | [US08](user-stories.md#us08), [US19](user-stories.md#us19) | Uruchomienie produktu na HA bez POC | Instalacja nie wymaga POC ani importera. Ogólne ostrzeżenie o konflikcie regulatorów pozostaje. Runda 6 zastępuje wcześniejszy scenariusz migracji. |
| A59 | [US04](user-stories.md#us04), [US12](user-stories.md#us12) | Dowolna decyzja, ograniczenie, awaria lub niedostępny opcjonalny licznik | Widać przyczynę, jakość danych i dostępny stan. Brak licznika nie jest prezentowany jako zerowy pobór. |

## Pokrycie i dalsza specyfikacja

Każdy US01–US21 ma co najmniej jeden odnośnik w tabeli. Obszar F01 skroplin jest przewidziany na późniejszy etap i wymaga odrębnego dopracowania przed jego implementacją. US21 prognoz pozostaje odłożone.

Odbiór powinien zapisywać wersję, ustawienia, wejścia, stany, czasy i wyniki scenariusza. Techniczne źródło dowodu potwierdzenia, odtworzenie historii i realizacja timerów należą do rundy architektury. Parametry różne od domyślnych muszą zachowywać reguły w dopuszczalnych zakresach.

Dalsze decyzje obejmują minimalną wersję HA, domenę, kontrakty modułów i źródeł, trwałość pamięci, rozpoznawanie zmian zewnętrznych, kasowanie ostrzeżeń oraz zachowanie po usunięciu integracji. Wyłączenie integracji i dowody poprawności na urządzeniu zostaną ujęte przy migracji i wydaniach.

## Aktualizacja po rundzie 6

[Ustalenia architektury](round-06-architecture.md) zawężają wymagania A01/A02 do modułu CO i dodają konfigurację tylko CWU. A58 zastąpiono uruchomieniem bez POC. Dalsze decyzje o trwałości, cyklu życia, diagnostyce i wydaniach są w rundzie 6; minimum HA, domena i kontrakty techniczne pozostają do projektu. Kryteria B01–B13 rozszerzają tabelę bez zmiany identyfikatorów A.
