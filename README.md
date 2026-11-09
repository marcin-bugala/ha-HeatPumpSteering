# ha-HeatPumpSteering — POC CO1

Pakiet YAML dla Home Assistant analizujący temperatury z HiMitII i dwóch
kondygnacji. Zwykła automatyzacja zapisuje nastawę przez istniejącą integrację
Hisense (`number.set_value`). Regulacja pozostaje w automatyzacjach YAML.
Mały moduł `hp_poc_history` wyłącznie odczytuje historię HA przy starcie.

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
3. Skopiuj oba pakiety do `/config/packages/`:
   `heat_pump_steering_poc.yaml` i `heat_pump_steering_memory.yaml`.
   Skopiuj też `custom_templates/hp_poc_memory.jinja` do
   `/config/custom_templates/hp_poc_memory.jinja`.
   Skopiuj cały folder `custom_components/hp_poc_history/` do
   `/config/custom_components/hp_poc_history/`. Pakiet pamięci zawiera
   `hp_poc_history: {}`, więc nie trzeba dopisywać osobnej sekcji konfiguracji.
   W `configuration.yaml` użyj istniejącej konfiguracji pakietów, np.:

   ```yaml
   homeassistant:
     packages: !include_dir_named packages
   ```

   Nie twórz drugiej sekcji `homeassistant`. Jeśli używasz innego sposobu
   wczytywania pakietów, zachowaj go.
4. Przy pierwszej instalacji sprawdź konfigurację, a następnie uruchom HA ponownie.
   Pakiet tworzy sensory statystyczne i helpery; nie wystarczy przeładować
   samych automatyzacji. Potrzebna współczesna wersja HA obsługująca
   `default_entity_id` i `last_reported` (projekt przygotowany dla HA 2026.11).
5. Skopiuj `home-assistant/www/hp-poc-readonly-card.js` do
   `/config/www/hp-poc-readonly-card.js`. W zasobach dashboardów HA dodaj
   `/local/hp-poc-readonly-card.js?v=1` jako **moduł JavaScript**. Jeśli zasoby
   są zarządzane w YAML, dodaj ten adres z `type: module` do istniejącego
   `lovelace.resources`. Nie tworzy się drugiej sekcji `lovelace`.
6. POC jest zakładką `co1` wspólnego dashboardu Historia w pliku
   `home-assistant/dashboards/dashboard_historia.yaml`. Zaktualizuj tę zakładkę
   w surowej konfiguracji dashboardu, zachowując istniejące widoki historii
   i diagnostyki HiMitII oraz ich zasoby. Sam widok POC nie wymaga HACS.
   Po dodaniu zasobu odśwież przeglądarkę.

Przy pierwszym uruchomieniu cele zostaną ustawione na **21°C / 22°C**.
Późniejsze zmiany z dashboardu są odtwarzane po restarcie. Nie wyłączaj
automatyzacji inicjalizacji przed pierwszym uruchomieniem.

Encja automatyzacji powinna otrzymać nazwę
`automation.ogrzewanie_poc_zapis_co1`; sprawdź ją w swoim HA, zwłaszcza jeśli
wcześniej istniały encje o tych nazwach. Wyłączenie tej automatyzacji zatrzymuje
zapis, ale pozostawia obliczenia i historię. Nie przywraca poprzedniej nastawy.
**Usunięcie pakietu również pozostawia ostatnią nastawę w pompie.**

## Porównanie krótszych filtrów — tryb obserwacyjny

W działającym HA moduł porównania jest zarządzany przez interfejs konfiguracji:
dwa helpery `input_text.hp_poc_porownanie_dane` / `pamiec`, dziewięć sensorów
Template Helper `sensor.hp_poc_porownanie_*` i automatyzacja
`automation.ogrzewanie_poc_porownanie_filtrow_bez_sterowania`.
Nie trzeba kopiować plików do HA ani wykonywać restartu. Nie twórz drugiej
kopii tych samych obiektów w pakietach YAML.

Kod źródłowy obliczeń jest w `templates/shadow_observation.jinja`.
`python tools/build_shadow.py` generuje `deploy/shadow_api.json` z pełnymi
definicjami obiektów dla API oraz `deploy/shadow_automation.yaml` do edytora
automatyzacji. Generator jedynie tworzy pliki lokalnie, nie łączy się z HA.
Przy instalacji na nowej instancji utwórz najpierw `storage_helpers`, potem
`helpers`, a na końcu `automation`, zachowując wskazane identyfikatory.
Makro jest wklejone do jednej zmiennej automatyzacji: aktualizacja tego
modułu nie wymaga zmiany `custom_templates` ani kodu Python integracji.

Porównanie obejmuje mediany 2 h i 45 min, krótki trend 2 h oraz dwa cele CO1:
z medianą 2 h albo dotychczasową 3 h. Oba cele porównawcze mają kontrolę
aktualnego kierunku zmian: składnik wzrostu 12 h danej kondygnacji wchodzi
do korekty tylko przy jej krótkim trendzie >0,03°C/h. Gdy krótkiego trendu
brakuje, dodatkowej korekty za wzrost nie stosujemy. Obecny regulator nadal
używa swoich niezmienionych reguł. Porównawcze cele CO1 nie są poleceniami
zapisu i nie oznaczają zezwolenia na podwyższenie temperatury wody.

Krótki trend porównuje medianę ostatnich 30 min z medianą fragmentu od
120 do 90 min temu; różnicę dzieli przez 1,5 h. Nie jest regresją ani
wyuczonym modelem bezwładności. Próg 0,03°C/h jest propozycją do oceny.
Szybki START/STOP wykorzystuje medianę 45 min i te same progi komfortu,
30 min potwierdzenia, blokadę wietrzenia, minimum 2 h stanu CO1 i 15 min
między próbami. Sprawdza również włączenie istniejącego auto STOP.
Nie kopiuje awaryjnego START po utracie danych; brak danych w porównaniu
zawsze oznacza brak zalecenia. To ocena względem rzeczywistego stanu CO1,
nie niezależna symulacja całego wirtualnego cyklu pompy.

Automatyzacja co minutę ocenia istniejący bufor próbek 5-minutowych.
Licznik rośnie wyłącznie przy nowej obserwacji, nie przy każdym renderze.
Krótka przerwa nie dolicza offline minut; ponad 20 min przerywa potwierdzenie.
Zmiana celu zeruje licznik. Oba JSON-y są ograniczone do 255 znaków,
temperatury i trendy zaokrąglone, a brak danych zapisany jako `null`.
Sensory odrzucają stan starszy niż 10 min zamiast pokazywać stare zalecenie.

Jedynymi akcjami modułu są dwa `input_text.set_value` kierowane do jego
własnej pamięci i wyniku. Nie wywołuje `number.set_value`, `switch.turn_*`,
nie zmienia automatyzacji regulacji ani nie przejmuje sterowania CO1.
Dashboard pokazuje nowe linie, wartości, potwierdzenia i zalecenie START/STOP.
Historia nowych sensorów zaczyna się w chwili ich utworzenia.

Cofnięcie: wyłącz automatyzację porównania i usuń z dashboardu jej linie
i opisy. Po 10 min sensory uznają dane za nieaktualne. Pozostawienie helperów
nie wpływa na ogrzewanie; nie wymaga usuwania encji ani historii.

## Układ dashboardu

Na szerokim ekranie panel ma trzy stałe sekcje:

- **Po lewej — Historia i temperatury.** Osobne wykresy parteru, piętra,
  wody CO1, temperatury zewnętrznej i pracy/przerw obiegu. Wszystkie legendy
  mają czytelne nazwy zamiast identyfikatorów `hp_poc_*`.
- **Pośrodku — Sterowanie i stan.** Cele kondygnacji, automatyczna nastawa
  wody, auto STOP, ręczne ON/OFF obiegu i ręczna nastawa wody. Pod nimi
  znajdują się nieedytowalne tabele bieżących odczytów, gotowości danych
  i diagnostyki. Znaczniki prób zapisu nie są już polami do edycji.
- **Po prawej — Jak działa POC.** Bieżąca decyzja wyrażona po polsku,
  składniki obliczenia, słownik temperatur i reguły STOP/START. Progi w opisie
  uwzględniają aktualne cele kondygnacji.

Na węższym ekranie sekcje układają się kolejno pod sobą. Kolumny nie mieszają
kart automatycznie. Panel korzysta z bieżącego motywu HA.

Karty tylko do odczytu nie otwierają okien ani nie przełączają encji.
Wykresy zachowują podgląd po najechaniu. Mała lokalna karta
`hp-poc-readonly-card` otacza natywne wykresy HA i blokuje kliknięcia,
podwójne kliknięcia, aktywację klawiaturą i zdarzenia more-info; nie wywołuje
żadnych usług i nie zmienia danych. Tabele są natywnymi kartami Markdown.

Jeśli aktualizujesz wyłącznie układ panelu, wystarczy dodać powyższy plik
JavaScript i zasób, podmienić YAML dashboardu i odświeżyć stronę.
**Pakiet automatyzacji pozostaje ten sam — nie trzeba restartować HA ani
ponownie rozgrzewać filtrów.** Komunikat „Custom element doesn't exist:
hp-poc-readonly-card” oznacza, że zasób nie został załadowany.

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

Przy włączonej opcji auto STOP **POC może wznowić także ręcznie wyłączony
CO1**, gdy temperatury spełnią warunek START. Pochodzenie wyłączenia nie
blokuje wznowienia według temperatur. Nadal obowiązują świeże dane,
potwierdzenie 30 min, minimum 2 h przerwy i odstęp od ostatniej próby.

Ręczne OFF jest więc przerwą tymczasową. Aby pozostawić CO1 wyłączony
bez automatycznego wznowienia, wyłącz auto STOP i CO1. Wyłączenie opcji
**pozostawia bieżący stan CO1**; ponowne jej włączenie ponownie zezwala
na START według temperatur, również gdy obieg już jest wyłączony.

Flaga „CO1 wstrzymany przez POC” pozostaje informacyjna dla zwykłego START.
Ogranicza tylko powrót awaryjny przy utracie danych: ten powrót jest dozwolony
wyłącznie po przerwie rozpoczętej przez POC. Brak danych po ręcznym OFF sam
w sobie nie uruchomi ogrzewania. Ręczne włączenie CO1 lub wyłączenie opcji
kasuje flagę; nie trzeba jej ustawiać ręcznie.

Brak danych stref blokuje nowe wyłączenie. Obsługa ON/OFF opiera się na
temperaturach wnętrza, niezależnie od dostępności outdoor i temperatury wody,
żeby postój obiegu nie blokował wznowienia. Nieudana próba OFF nie oznacza
przejęcia sterowania: flagę ustawiamy dopiero po powrocie akcji i stanie OFF
encji HA. To nadal nie jest niezależne potwierdzenie z chmury — HiMitII
może aktualizować optymistycznie. Dziennik opisuje wysłane polecenia.

Pamięć POC odtwarza potwierdzenia temperatury, czasy zmiany CO1 i nastawy.
Krótki restart nie rozpoczyna od nowa 2 h blokady ani 30 min potwierdzenia.
Minuty bez obserwacji nie powiększają potwierdzenia. Luka ponad 20 min
powoduje ostrożne rozpoczęcie potwierdzeń i blokad czasowych od nowa.
Usunięcie pakietu nie włącza CO1, jeżeli moduł wcześniej go wyłączył.

Aktualizacja działającego POC: patrz procedura pamięci poniżej. Opcja
auto STOP pozostaje niezależnym przełącznikiem i zachowuje ustawienie użytkownika.

## Pamięć odporna na krótkie restarty

`sensor.hp_poc_pamiec` jest trigger-based template sensor, którego stan
i atrybuty HA odtwarza. Przechowuje ograniczony bufor pełnych próbek
co 5 min (także przy stałej temperaturze), historię median do trendu oraz
czasy zmian i potwierdzeń. Obliczenia są współdzielone w makrach
`custom_templates/hp_poc_memory.jinja`.

Dotychczasowe sensory Statistics pozostają do porównania. Sterowanie
i zakładka POC korzystają teraz z sensorów z końcówką `_trwaly`,
wyliczanych z bufora regularnych próbek. Przy starcie brakujące sloty może
uzupełnić Recorder: z uwzględnieniem czasu obowiązywania stanów, zamiast
traktowania każdej zmiany temperatury jako jednej próbki. Identyfikatory
istniejących urządzeń i automatyzacji zachowano.

- Krótki restart zachowuje ostatnio utrwalone próbki i czasy zamiast
  wymuszać ponowne 2,5–3 h zbierania oraz 2 h stabilnej nastawy.
- Brak danych nie jest zastępowany zerem. Luka ponad 20 min blokuje gotowość
  danego okna do czasu jej wyjścia z okna. Progi pokrycia 80% i 29/29/20
  slotów z odczytem lub odtworzonym stanem historycznym nadal obowiązują.
- Potwierdzenia STOP/START gromadzą 30 min poprawnych obserwacji. Przy
  krótkiej przerwie czas jest zachowany i wstrzymany, a nie powiększany
  o całą przerwę. Zmiana celów zeruje potwierdzenie, ale zachowuje pomiary.
- Przy luce ponad 20 min POC nie zakłada, że stan urządzenia pozostał
  niezmieniony: zaczyna blokadę czasową ostrożnie od nowego odczytu.
- Odtwarzanie korzysta z punktu zapisu HA. Nagła utrata procesu/zasilania
  może utracić najnowszy fragment od ostatniego zapisu. Bufor nie zastępuje
  niezależnego zasilania ani ochrony sprzętowej.

### Uzupełnianie historii — instalacja i aktualizacja

1. Zachowaj kopie aktualnych plików. Skopiuj folder
   `custom_components/hp_poc_history/`, podmień makro `.jinja` i pakiet
   `heat_pump_steering_memory.yaml`. Główny pakiet regulacji nie zmienia się.
2. Wykonaj `homeassistant.check_config` i usuń ewentualne błędy przed
   przeładowaniem.
3. Przy pierwszej instalacji modułu historii potrzebny jest pełny restart HA
   po poprawnym sprawdzeniu konfiguracji. Nie uruchamiaj go automatycznie
   bez decyzji administratora. Przy kolejnych zmianach tylko makra/pakietu
   wystarcza `homeassistant.reload_custom_templates`, potem `template.reload`
   i akcja `hp_poc_history.refresh`. Zmiana kodu Python wymaga restartu.
4. Zaktualizuj tylko zakładkę POC w swoim wspólnym dashboardzie Historia.
   Karta JavaScript pozostaje bez zmian.
5. Sprawdź `sensor.hp_poc_pamiec` (atrybut `payload`, wersja 1) i nowe
   sensory z końcówką `_trwaly`. `payload.history_generated_at > 0` oznacza
   przyjęty wynik odczytu historii, nie gwarancję gotowości wszystkich okien.
   Przy wystarczającej historii obliczenia są dostępne po najbliższym cyklu
   POC (do 5 min), bez ponownego czekania 2,5 h. START/STOP nadal wymaga
   potwierdzenia warunków względem aktualnych celów przez 30 min.

Moduł czyta ostatnie **15 h** trzech temperatur, przełącznika CO1 i nastawy:
3 h potrzebne do początkowych median oraz 12 h trendu. Czyta przez Recorder
w jego executorze, bez tokena, żądań do chmury i bez bezpośredniego otwierania
pliku bazy. Nie wysyła poleceń urządzeniom. Działa przy starcie HA; akcja
`hp_poc_history.refresh` pozwala powtórzyć odczyt po przeładowaniu szablonów.
Błąd startowy powoduje maksymalnie 3 próby co minutę. Zwykłe próbkowanie
działa również, jeśli odczyt historii się nie powiedzie.

Wartość niezmienna przez godzinę stanowi godzinę znanego stanu. Odtwarzanie
stosuje schodkowo ostatni zapisany stan, bez interpolacji. `unknown`,
`unavailable`, błędne zakresy i przerwy pracy Recordera pozostają brakami.
To odtworzenie historii stanów HA, nie dowód ciągłych fizycznych pomiarów:
czujnika, który zawiesił się bez zgłoszenia niedostępności, nie da się
rozpoznać wyłącznie po tej historii. Źródła muszą być objęte Recorderem.

Historia przełączeń i zmian nastawy odtwarza również blokadę 2 h. Powtórzony
raport tej samej wartości nie zeruje licznika. Jeśli właściwa zmiana była
przed początkiem okna, używamy początku potwierdzonego fragmentu, a nie
zgadniętej godziny zmiany. Niedostępność i przerwa HA ponad 20 min przerywają
ciągłość; obecny stan musi zgadzać się z historią. Zmiana w trakcie odczytu
historii zachowuje nowszy licznik z działającego POC. Nie odtwarzamy z dawnych
temperatur 30 min potwierdzenia STOP/START, bo cele mogły być wtedy inne.
Odczyt stanu HiMitII nadal nie stanowi niezależnego potwierdzenia sprężarki.

Jeśli zmieniasz identyfikatory źródeł, zmień je w obu pakietach oraz w filtrze
`event_data.entities` w pakiecie pamięci. W sekcji `hp_poc_history` podaj
odpowiednie klucze `ground`, `upper`, `outdoor`, `co1`, `setpoint`.

Cofnięcie odczytu historii: przywróć poprzednie makro i pakiet pamięci bez
sekcji `hp_poc_history`, sprawdź konfigurację i uruchom HA ponownie. Pozostawione
pliki modułu nie są wtedy wczytywane. Nie trzeba usuwać danych historii.
W aktualizacji nie obniżamy
limitów temperatury ani nie wydajemy testowych poleceń pompie.

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
Po krótkim restarcie odliczanie jest kontynuowane z pamięci POC. Jeżeli
bieżąca nastawa leży daleko poza zakresem POC, pakiet nie wykona kroku poza
tym zakresem — wymaga doprowadzenia nastawy do zakresu ręcznie.

Zapis wymaga włączonego CO1, kompletnego wyniku nie starszego niż 10 min,
świeżych źródeł (wnętrza do 2 h, pompa do 30 min), prawidłowych jednostek
i limitów. Bez wystarczającej historii filtry potrzebują około **2,5 h** próbek
(pokrycie okna ≥80% oraz co najmniej 29/29/20 slotów). Przy kompletnej historii
moduł startowy odtwarza te okna i trend. Recorder powinien przechowywać
źródłowe temperatury, CO1, nastawę oraz sensory POC.

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

Testy dashboardu sprawdzają również układ kolumn i renderowanie opisów
przy kompletnych, brakujących i pustych danych. Test karty w prawdziwej
przeglądarce (z lokalną atrapą karty natywnej, bez połączenia z HA):

```text
npm install --no-save playwright
node tests/test_readonly_card.cjs
```

Wymaga zainstalowanego Chrome; dla Edge ustaw `POC_BROWSER_CHANNEL=msedge`.
Sprawdza blokadę aktywacji, pozostawienie podglądu po najechaniu, aktualizację
danych i brak wpływu na przyciski poza kartą. Nie jest wizualnym odbiorem
dashboardu w działającej instancji HA.

Dokumentacja HA: [Statistics](https://www.home-assistant.io/integrations/statistics/),
[Template](https://www.home-assistant.io/integrations/template/),
[Number](https://www.home-assistant.io/integrations/number/).
