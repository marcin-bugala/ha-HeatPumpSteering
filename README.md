# ha-HeatPumpSteering — POC CO1

Pakiet YAML dla Home Assistant analizujący temperatury z HiMitII i dwóch
kondygnacji. Zwykła automatyzacja zapisuje nastawę przez istniejącą integrację
Hisense (`number.set_value`). Nie jest to jeszcze custom integration.

**Po instalacji zapis jest aktywny**, gdy dane i filtry są gotowe.
Nie przełącza trybu pracy pompy: Hisense należy ustawić na stałą temperaturę
CO1. Opcjonalnie może wyłączać i włączać sam obieg CO1 przez jego przełącznik
HiMitII. Nie odcina zasilania urządzenia ani nie zmienia CWU, sprężarki,
pomp obiegowych, zaworów ani demand bezpośrednio.

## Instalacja

1. Sprawdź mapowanie encji na początku `packages/heat_pump_steering_poc.yaml`.
   Oczekiwana nastawa to `number.garaz_pompa_ciepla_circuit_1_setpoint`;
   bramka ogrzewania to `switch.garaz_pompa_ciepla_circuit_1_heating`.
   Zmień wszystkie wystąpienia nazwy, jeśli w Twoim HA jest inna.
   Nastawa musi być encją `number` w °C z krokiem 1 i liczbowymi min/max.
2. Sprawdź, czy istniejąca automatyzacja nie zapisuje tej samej nastawy.
   W danym momencie powinien działać jeden regulator CO1.
3. Skopiuj plik pakietu do `/config/packages/heat_pump_steering_poc.yaml`.
   W `configuration.yaml` użyj istniejącej konfiguracji pakietów, np.:

   ```yaml
   homeassistant:
     packages: !include_dir_named packages
   ```

   Nie twórz drugiej sekcji `homeassistant`. Jeśli używasz innego sposobu
   wczytywania pakietów, zachowaj go.
4. W HA sprawdź konfigurację, a następnie uruchom HA ponownie.
   Pakiet tworzy sensory statystyczne i helpery; nie wystarczy przeładować
   samych automatyzacji. Potrzebna współczesna wersja HA obsługująca
   `default_entity_id` i `last_reported` (projekt przygotowany dla HA 2026.11).
5. Utwórz dashboard i wklej `dashboards/heating_poc.yaml` jako jego surową
   konfigurację. Nie wymaga kart HACS.

Przy pierwszym uruchomieniu cele zostaną ustawione na **21°C / 22°C**.
Późniejsze zmiany z dashboardu są odtwarzane po restarcie. Nie wyłączaj
automatyzacji inicjalizacji przed pierwszym uruchomieniem.

Encja automatyzacji powinna otrzymać nazwę
`automation.ogrzewanie_poc_zapis_co1`; sprawdź ją w swoim HA, zwłaszcza jeśli
wcześniej istniały encje o tych nazwach. Wyłączenie tej automatyzacji zatrzymuje
zapis, ale pozostawia obliczenia i historię. Nie przywraca poprzedniej nastawy.
**Usunięcie pakietu również pozostawia ostatnią nastawę w pompie.**

## Opcjonalny auto STOP CO1 przy przegrzaniu

Nowy przełącznik dashboardu **„auto STOP przy przegrzaniu”**
(`input_boolean.hp_poc_auto_stop_co1`) jest przy pierwszej instalacji wyłączony.
Po włączeniu jego stan jest odtwarzany po restarcie. Moduł działa niezależnie
od automatyzacji zapisu temperatury wody; wyłączenie samego zapisu CO1
nie wyłącza auto STOP.

| Działanie | Warunek |
| --- | --- |
| STOP CO1 | Mediany 3 h **obu** stref ≥ własny cel +0,4°C nieprzerwanie przez 30 min |
| START CO1 | Mediana 3 h **co najmniej jednej** strefy ≤ własny cel −0,2°C przez 30 min; brak nagłego spadku pomiaru o ponad 0,7°C względem mediany |
| Minimalny czas stanu | CO1 musi być w obecnym stanie przez co najmniej 2 h przed zmianą |
| Ponowienie po błędzie | Najwcześniej po 15 min, nie co minutę |
| Utrata danych podczas przerwy POC | Po 30 min nieprawidłowych danych powrót do grzania Hisense, z zachowaniem minimum 2 h przerwy |

Dla celów 21/22°C STOP oznacza mediany ≥21,4/22,4°C. START oznacza
≤20,8°C na parterze lub ≤21,8°C na piętrze. Progi są startowymi parametrami
POC; edytuje się je w szablonach nowych `binary_sensor`. Reguła „obie strefy”
chroni chłodniejszą kondygnację przed wyłączeniem przez cieplejszą. Przy
wznowieniu z powodu jednej strefy druga może być cieplejsza — nadal jest to
wspólny obieg bez zaworów.

Polecenia idą wyłącznie do
`switch.garaz_pompa_ciepla_circuit_1_heating` (w HiMitII: `c1_SW_ON`).
Nie używamy wyłącznika licznika Tuya ani nadrzędnego wyłącznika pompy.
Hisense zachowuje własną obsługę sprężarki, CWU i ochrony urządzenia.

POC wznawia tylko przerwę, którą sam zarządził i odnotował pomocniczą flagą.
Ręcznie wyłączonego wcześniej CO1 nie uruchamia. Ręczne włączenie CO1
kasuje tę flagę i uruchamia nowy minimalny czas pracy. Wyłączenie opcji
auto STOP kasuje flagę i **pozostawia bieżący stan CO1**; w razie potrzeby
włącz ogrzewanie ręcznie przełącznikiem CO1 na dashboardzie. Ponowne
włączenie opcji nie przejmuje automatycznie już wyłączonego obiegu.
Nie ustawiaj ręcznie flagi „CO1 wstrzymany przez POC”. Samo naciśnięcie OFF,
gdy CO1 już jest OFF, nie jest rozpoznawalnym nowym zdarzeniem — do przejęcia
sterowania służy wyłączenie opcji auto STOP.

Brak danych stref blokuje nowe wyłączenie. Obsługa ON/OFF opiera się na
temperaturach wnętrza, niezależnie od dostępności outdoor i temperatury wody,
żeby postój obiegu nie blokował wznowienia. Nieudana próba OFF nie oznacza
przejęcia sterowania: flagę ustawiamy dopiero po powrocie akcji i stanie OFF
encji HA. To nadal nie jest niezależne potwierdzenie z chmury — HiMitII
może aktualizować optymistycznie. Dziennik opisuje wysłane polecenia.

Po restarcie lub przeładowaniu szablonów potwierdzanie 30-minutowe zaczyna
się ponownie. Flaga własności i czas ostatniej próby są odtwarzane; stan CO1
musi ponownie być stabilny przez 2 h. Usunięcie pakietu nie włącza CO1,
jeżeli moduł wcześniej go wyłączył.

Po aktualizacji skopiuj zarówno pakiet, jak i dashboard; sprawdź konfigurację
i wykonaj pełny restart HA. Dopiero potem włącz opcję auto STOP, jeśli chcesz
z niej korzystać.

## Algorytm

- Co 5 minut pobiera równo ważone próbki; nie używa temperatury ogrodu.
- Outdoor Hisense: średnia czasowa 2 h. Wnętrza: mediana 3 h. Mediana tłumi
  krótkie piki bez trwałego blokowania nowych temperatur.
- Baza: `20 + 0.2 × (20 − Ta_2h)`.
- Błąd strefy: `cel − mediana`. Przy przegrzaniu którejkolwiek kondygnacji
  o ponad 0,2°C wybiera bardziej ujemny błąd; inaczej średnią obu błędów.
- Martwa strefa ±0,2°C; poza nią korekta 1,5°C wody na 1°C pozostałego błędu.
  Łączna korekta ograniczona do ±2°C.
- Po zebraniu 12 h historii median dodaje wyłącznie łagodną korektę w dół
  za trend wzrostowy: do −0,5°C. Nie jest to samouczący regulator ani PID.
- Nagły spadek >0,7°C względem mediany lub bieżące przegrzanie strefy
  blokuje **podnoszenie** CO1; obniżanie pozostaje możliwe.
- Minimum wyniku pobiera bezpośrednio z atrybutu `min` encji HiMitII
  (w obecnej wersji MB dla CO1: **20°C**). Nie narzuca własnego minimum 27°C.
  Maksimum to mniejsza z wartości: `max` encji i górny limit POC **35°C**.
  Parametry POC edytuje się w bloku zmiennych drugiej sekcji `template`.
  Następnie zaokrągla do pełnego stopnia, połówki w górę.

Mediana 3 h nie ignoruje dowolnie długiego gotowania/słońca. Zakłócenie
trwające około połowy okna może wpłynąć na wynik. To celowy prosty POC,
który reaguje także na trwałe przegrzewanie. Bez zaworów nie zapewni
niezależnego utrzymywania obu temperatur.

## Zapis do HiMitII

Automatyzacja sprawdza wynik co 5 min, 15 s po obliczeniu. Jeśli zaokrąglony
cel jest równy aktualnej nastawie, **nic nie wysyła**. W przeciwnym razie
wykonuje najwyżej **jeden krok 1°C co 120 min** w kierunku celu. Na przykład:
aktualnie 30°C, cel 27°C → zapis 29°C, po co najmniej 2 h następny krok.

Odstęp liczony jest od późniejszego z: ostatniej próby zapisu POC oraz
ostatniej zmiany encji nastawy (także ręcznej). Termin próby zapisywany jest
przed poleceniem, więc błąd chmury nie wywołuje serii szybkich ponowień.
Po restarcie HA obowiązuje ponownie minimum 2 h stabilnej nastawy. Jeżeli
bieżąca nastawa leży daleko poza zakresem POC, pakiet nie wykona kroku poza
tym zakresem — wymaga doprowadzenia nastawy do zakresu ręcznie.

Zapis wymaga włączonego CO1, kompletnego wyniku nie starszego niż 10 min,
świeżych źródeł (wnętrza do 2 h, pompa do 30 min), prawidłowych jednostek
i limitów. Przed pierwszym wynikiem filtry potrzebują około **2,5 h** próbek
(pokrycie okna ≥80% oraz co najmniej 29/29/20 próbek). Trend zaczyna działać
później. Recorder powinien przechowywać sensory POC, aby zachować historię.

`last_reported` oznacza świeżość raportu w HA, nie dowód nowego fizycznego
pomiaru ani udanego pobrania danych przez chmurę. HiMitII aktualizuje nastawę
optymistycznie: POC nie ma niezależnego potwierdzenia wykonania. Dziennik
rejestruje wysłanie polecenia, nie potwierdzony stan pompy. Nie dodaje własnego
klienta chmurowego ani nie używa prywatnych struktur integracji.

Temperatura rzeczywista CO1 jest kontrolą dostępności i diagnostyką. Moc
pompy jest wyłącznie pokazywana w diagnostyce — bez zgadywania progu pracy
sprężarki i jednostek licznika. Stan włączonego CO1 nie oznacza pracy sprężarki.
POC nie identyfikuje defrost/CWU; nie steruje ich cyklami, zmienia tylko CO1.

Przy minimum encji 20°C baza 25°C przy −5°C nie jest podnoszona do 27°C.
Jeżeli aktualna integracja zgłosi inne minimum, POC je uwzględni automatycznie.
Brak liczbowego `min` blokuje zapis. Dashboard pokazuje aktualny zakres;
POC nie obchodzi limitów integracji ani nie odcina pompy.

## Sprawdzenie lokalne

### Gdy dashboard pokazuje „Nie znaleziono encji”

To oznacza brak encji pod oczekiwanym identyfikatorem, a nie brak historii.
Pusty sensor Statistics powinien istnieć ze stanem `unknown`.

1. Sprawdź, czy skopiowano **cały** plik pakietu, w tym sekcję `sensor:`
   z ośmioma wpisami `platform: statistics`. Sam YAML dashboardu nie tworzy encji.
2. Sprawdź konfigurację i wykonaj **pełny restart HA**, jeśli dotąd przeładowano
   tylko automatyzacje lub szablony.
3. W Narzędziach deweloperskich → Stany wyszukaj `hp_poc`. Sprawdź, czy
   oczekiwane sensory istnieją pod inną nazwą, np. z końcówką `_2`.
4. Jeśli nadal ich nie ma, w Ustawienia → System → Dzienniki sprawdź błędy
   `statistics`, `sensor`, `template` i nazwy pliku pakietu. Treść błędu jest
   potrzebna do ustalenia przyczyny; samo czekanie 2,5 h nie utworzy encji.

Poprawiony dashboard i `sensor.hp_poc_status` rozróżniają brak encji,
nieprawidłowe wejścia i oczekiwanie na próbki. Status dotyczy obliczeń;
nie jest potwierdzeniem wykonania zapisu. Przy niekompletnych danych
automatyzacja nie wysyła nastawy.

```text
python -m pip install -r requirements-test.txt
python -m unittest discover -s tests -v
```

Testy wykonują szablony Jinja bez połączenia z HA: przegrzewanie, konflikt
stref, trend, zaokrąglanie, kroki, filtry rozruchowe, brakujące/stare dane,
limity, brak zmiany i odstępy zapisu. Nie zastępują sprawdzenia konfiguracji
w docelowym HA ani testu komunikacji z pompą.

Dokumentacja HA: [Statistics](https://www.home-assistant.io/integrations/statistics/),
[Template](https://www.home-assistant.io/integrations/template/),
[Number](https://www.home-assistant.io/integrations/number/).
