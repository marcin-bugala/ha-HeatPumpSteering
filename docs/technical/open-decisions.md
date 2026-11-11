# Rozstrzygnięcia P01–P12

Właściciel: Marcin Bugała. Przyjęte 11 listopada 2026 w rozmowie projektu,
wprowadzone do PR #36. P01/P02/P05/P10 przyjęto w wersji skorygowanej przez
właściciela; poprzednie rekomendacje nie obowiązują.
Źródło prawdy: [D90–D101](../requirements/decisions.md).
To rejestr decyzji produktu, nie statusów realizacji US.

| P | Przyjęta reguła | Konsekwencja / powiązanie |
| --- | --- | --- |
| P01 | Potwierdzenie operacyjne jest dwuetapowe: po zapisie zgodny odczyt tej samej encji HA daje potwierdzenie wstępne; ponowny poprawny, zgodny odczyt po domyślnie 2 min daje potwierdzenie ostateczne i kończy serię ponowień. Nie wymagamy drugiej encji, dowodu nowego raportu transportowego ani fizycznego wykonania. Doprecyzowuje D51/D56/D60/D68 i zastępuje wymóg niezależnego dowodu jako warunku aktywacji. | D90; US03–US05, US09–US10, US13, US16–US19 |
| P02 | Każda zmiana ustawienia CWU niewynikająca z działania naszego algorytmu jest external i ma reguły zmiany użytkownika D27/D63/D64. Nie ma kategorii ambiguous ani blokady zapisów z powodu nieustalonego pochodzenia. | D91; US07, US13–US14 |
| P03 | Ręczna zmiana demandu nie zatrzymuje regulatora: następna dozwolona ocena uzgadnia bieżące zapotrzebowanie. Trwałe oddanie kontroli przez obserwację CO. OFF nie resetuje liczników błędów ani terminów ponowień; brak dodatkowej zwłoki logicznej nie obchodzi polityki retry. | D92; US07, US09 |
| P04 | Jawna polaryzacja każdego bindingu wyjścia jest niezależna od wspólnego dla strefy NC/NO. Zmiana mapowania nie wysyła sama polecenia. | D93; US05, US09–US10 |
| P05 | Produkt nie obsługuje higieny CWU: bez wykrywania, dedykowanych encji, blokad i warunku aktywacji. Higiena pozostaje po stronie pompy. Zmiany nastaw niewynikające z naszego algorytmu są external według D91. | D94; US13, US19 |
| P06 | CWU bez wcześniejszych nastaw zaczyna jako Nieskonfigurowane; użytkownik jawnie podaje temperaturę Stałe/ON i zatwierdza cały plan. Szkic 7×48 OFF nie jest zapisanym planem i nie powoduje OFF urządzenia. Kopiowanie dni dotyczy draft. | D95; US13–US14 |
| P07 | Cel strefy 5–35°C co 0,5°C, początkowo podany przez użytkownika. Zmiana celu zeruje zależne potwierdzenia temperatury, zachowuje terminy zamknięcia i demandu oraz historię pomiarów. | D96; US02, US05–US06, US11, US18 |
| P08 | Niepewna historia pozostaje luką; nie przedłużamy ważności poza świeżość i nie odtwarzamy heartbeat z niezmiennych stanów Recordera. Mediana jest ważona czasem; dokładne 50% między wartościami daje średnią dwóch środkowych. | D97; US01, US06, US16, US19 |
| P09 | Przypadek mieszany bez stref kwalifikowanych do korekty: baza outdoor bez korekt pokojowych, z pozostałymi blokadami. Nadal wszystkie poprawne zamknięte → utrzymanie nastawy; wszystkie utracone po grace → baza i wycofanie demandu. | D98; US17–US18 |
| P10 | Gdy bieżąca nastawa jest poza obowiązującym zakresem, obcinamy ją do najbliższej dopuszczalnej granicy i oznaczamy konflikt. Korekta graniczna ma pierwszeństwo przed zwykłym limitem kroku/odstępu i blokadą wzrostu utrzymującą wartość poza zakresem; nie wyłącza obserwacji ani walidacji wyjścia i retry. Doprecyzowuje wyjątek od D42; nie blokujemy korekty samym konfliktem. | D99; US16–US17 |
| P11 | v1 pokazuje energię z istniejącego licznika, bez własnej całki mocy i okresów dobowych/miesięcznych. Ostrzeżenie nieskutecznego zamknięcia gaśnie przy wiarygodnym ustąpieniu któregokolwiek warunku lub otwarciu; brak danych wstrzymuje ocenę, sam nie kasuje ostrzeżenia. Przeczytanie nie kasuje przyczyny. | D100; US04–US05, US12 |
| P12 | Domena heat_pump_steering, minimum HA 2026.10.4 i macierz z 2026.11.1, cel strefy number, frontend TypeScript/Lit, źródła sterujące number/switch v1 oraz jawna aktywacja nowych bindingów wyjść przyjęte. T08 (zgodny plugin macierzy) pozostaje technicznym zadaniem, a projekt czeka na przegląd właściciela. | D101; US02–US03, US08, US11–US14, US16, US20 |

P01: potwierdzenie ostateczne jest „100%” dla procesu regulatora, nie deklaracją
niezależnego fizycznego wykonania. Po 2 minutach ponownie czytamy bieżącą
wartość tej samej encji HA; nie wymagamy osobnego czujnika, source sequence
ani znacznika nowego odczytu chmury. Samo upłynięcie czasu bez poprawnego odczytu
nie wystarcza. Ponowienia po niezgodnym/niedostępnym odczycie pozostają D52.

P10: przykład 40°C przy nowym zakresie 23–35°C daje żądanie 35°C oraz konflikt,
także gdy zwykły limit pozwalałby tylko na zmianę o 1°C. Analogicznie 20°C
przy minimum 23°C daje 23°C. Dla nieleżących na siatce granic wybieramy najbliższy
dopuszczalny punkt wewnątrz zakresu. W obserwacji pokazujemy propozycję bez zapisu.
Nie zmieniamy dotychczasowych początkowych A/B/Tref z product.md; korekta P10
dotyczy zachowania na granicy zakresu.

## Co pozostaje przed implementacją

- Przegląd całego projektu dla wskazanego SHA przez właściciela i Reviewera.
- T08: zgodny plugin/fixtures dla obu przyjętych wersji HA, bez obchodzenia pinów.
- Zatwierdzony SHA i dowody przeglądu w przekazaniu Developerowi.

P01–P12 nie są już otwartymi pytaniami produktowymi. Nie uruchomiono kodowania,
merge, wydania ani deploy. Przyszłe F01/prognozy/dwa CO pozostają poza zakresem.
