# ha-HeatPumpSteering — POC CO1

Pakiet YAML dla Home Assistant analizujący temperatury z HiMitII i dwóch
kondygnacji. Zwykła automatyzacja zapisuje nastawę przez istniejącą integrację
Hisense (`number.set_value`). Nie jest to jeszcze custom integration.

**Po instalacji zapis jest aktywny**, gdy dane i filtry są gotowe.
Nie przełącza trybu pracy pompy: Hisense należy ustawić na stałą temperaturę
CO1. Nie zmienia CWU, sprężarki, pomp, zaworów ani demand.

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
- Wynik ogranicza do przecięcia zakresu HiMitII z zakresem POC **27–35°C**.
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

Jeśli minimum wynosi 27°C, baza 25°C przy −5°C zostanie obcięta do 27°C.
Dashboard pokaże ograniczenie. Przy przegrzewaniu mimo minimum potrzebne
będą kolejne etapy projektu; POC nie obchodzi minimum ani nie odcina pompy.

## Sprawdzenie lokalne

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
