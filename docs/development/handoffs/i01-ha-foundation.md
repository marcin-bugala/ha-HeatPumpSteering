# I01 — fundament integracji w obserwacji

## Kontrakt przekazania

- Nadawca / odbiorca / data: Tech Lead → Developer, 11 listopada 2026.
- Repozytorium: marcin-bugala/ha-HeatPumpSteering.
- Zatwierdzony projekt: main e27621281d119f802e263d427ef9b9d36f6a135e, po PR #36.
  Podstawa przejścia do kroku 3 i jawny brak niezależnego review: [zapis](README.md).
- Gałąź wykonania: feat/10-ha-foundation od aktualnego origin/main **po scaleniu I00**.
- Commit wejściowy wykonania: rzeczywisty SHA main po I00, do wpisania przez Tech Leada.
  Musi zawierać zatwierdzony projekt oraz udane środowiska T08.
- Commit wyniku: SHA PR-a kodowego Developera, nie commit projektu.
- Refs #10 (US03, główne), #15 (US08), #23 (US16), #29 (US20).
- D09/D23/D24/D68–D74/D80/D85/D88/D101; D90–D100 pozostają wiążące, lecz
  wykonawca poleceń i reguły algorytmu nie są implementowane w tym pakiecie.
- Odbiór: A02 i części A08, B01/B02/B04 oraz C13; dokładne części poniżej.
- Projekt: [architektura](../../technical/architecture.md),
  [model](../../technical/data-model.md), [lifecycle](../../technical/lifecycle.md),
  [HA](../../technical/ha-contracts.md), [weryfikacja](../../technical/verification.md).
- Gotowość: kontrakt jest przygotowany; **nie zaczynaj kodu I01 przed wynikami I00**.
  Rozwiązanie T08 musi być dowodem testów, nie samym opisem alternatywy.

## Jeden mały rezultat

Prawdziwa custom integration heat_pump_steering ładuje poprawny ConfigEntry,
tworzy runtime_data, rozróżnia CO/CWU i odłącza zasoby przy unload.
W całym zakresie I01 pozostaje obserwacyjna i nie wywołuje usług źródeł.

Dla utrzymania małego diffu oddzielamy fundament od użytkowego kreatora:
I01 testuje setup/unload na syntetycznych, ale strukturalnie poprawnych
ConfigEntry. Pełny config_flow, dodawanie stref, opcjonalne wyjścia, grupy
i reconfigure są I02/I03. Nie dodawaj pustego kreatora zapisującego niekompletny
wpis, fikcyjnego manifestu ani stubów algorytmu udających wynik.
To częściowa implementacja fundamentu, nie gotowa instalacja produktu dla użytkownika.
Pierwszy kompletny release nadal wymaga wszystkich funkcji D76/D101.

## Kontrakt danych wejściowych

I01 używa podzbioru modelu v1 z data-model.md i jawnych typów.
Nie tworzy drugiego formatu pomiarów, celu ani schedule na potrzeby testów.
Identyfikatory UUID są tworzone raz podczas przygotowania konfiguracji,
nie na każdym setup. Runtime nie przepisuje danych wpisu tylko dlatego,
że został przeładowany.

| Wariant poprawnego ConfigEntry | Wymagane powiązania strukturalne |
| --- | --- |
| CO-only | installation_id, jeden circuit_id, encja nastawy CO number, outdoor sensor, co najmniej jedna aktywna strefa z zone_id, sensor i celem 5–35°C co 0,5°C |
| CWU-only | installation_id, dhw_id, nastawa CWU number i zezwolenie switch; bez pól CO/outdoor/stref |
| CO+CWU | Oba powyższe zakresy, niezależne logicznie; nowe moduły observation |
| Żaden moduł | Niepoprawny wariant — bez poprawnego setup |

Rozdziel „brak skonfigurowanego bindingu” od „wybrana encja jest teraz
unknown/unavailable/nie pojawiła się jeszcze w HA”. Pierwszy jest błędem
struktury; drugi jest niegotowością zależnej funkcji, nie powodem wysłania
OFF ani awarii sprawnego modułu. Nie rozszerzaj w I01 walidatora o okna,
historię, profile sprzętu i cały zestaw parametrów zaawansowanych.
Nie wpisuj fikcyjnego celu pokojowego ani nastawy CWU.
Syntetyczne źródła testów mają jawne jednostki, min/max/step i nazwy bez danych domu.

## Pliki i odpowiedzialności

| Zakres | Minimalna odpowiedzialność |
| --- | --- |
| custom_components/heat_pump_steering/manifest.json | Rzeczywisty manifest HA z domain/version i poprawnymi metadanymi; zgodność hassfest, bez zależności transportu producenta |
| const.py | Domena i przyjęte stałe strukturalne; bez parametrów regulatora na zapas |
| models.py | Małe typy konfiguracji fundamentu i runtime, trwałe identyfikatory, osobny enabled/mode/readiness CO i CWU |
| __init__.py | async_setup_entry/async_unload_entry, runtime_data i pełne sprzątanie własnych zasobów |
| tests/integration/conftest.py | enable_custom_integrations, poprawne MockConfigEntry i syntetyczne źródła |
| tests/integration/test_setup.py | Trzy warianty, wymagania CO/CWU, niezależna gotowość, brak usług |
| tests/integration/test_unload.py | Sprzątanie, ponowny setup, brak starych callbacków i brak OFF |
| requirements-ha-test.txt + zestaw current I00 | Dokładne piny i faktyczne środowiska; brak konfliktów pip |
| .github/workflows/ci.yml, pyproject.toml | Prawdziwe ha-tests minimum/current i hassfest w ci; Ruff target py314 |
| strings.json/translations gdy pojawia się tekst użytkownika | PL/EN; bez pustych atrap ekranów |

ConfigEntry VERSION/MINOR_VERSION i klucze zgodne z przyjętym modelem.
Nie przenoś produkcyjnej konfiguracji do fixtures. Nie dodawaj osobnego DB,
Store z udawanymi danymi, custom frameworka runtime ani DataUpdateCoordinator,
jeżeli nie ma tu zewnętrznego pollingu do koordynowania.

Nie deklaruj config_flow=true, dopóki nie istnieje prawdziwy kreator — I02
doda go wraz z kompletną walidacją. To rozdzielenie pakietów nie zmienia
docelowej konfiguracji UI produktu. Nie reklamuj I01 jako wydania do HACS.
Jeśli hassfest wymaga dodatkowego pliku/metadanych, dodaj je w realnej formie,
bez omijania walidatora i bez deklarowania niewdrożonych funkcji.

## Lifecycle i błędy

- Setup waliduje obsługiwany schemat oraz strukturę obecnych modułów,
  tworzy runtime dopiero z poprawnych danych. Nowa konfiguracja observation.
- Każda subskrypcja/callback/task powstały w setup ma jawnego właściciela
  i funkcję anulowania; nie twórz timerów i listenerów tylko dla liczby testów.
- Unload unieważnia generation, odłącza istniejące subskrypcje, anuluje zadania,
  usuwa aktywny runtime i platformy, jeśli zostały rzeczywiście utworzone.
  Stan źródeł pozostaje. Nie ma przywracania poprzednich nastaw ani OFF.
- Błąd setup po częściowym utworzeniu zasobów sprząta wyłącznie własne zasoby.
  Nie maskuj błędu szerokim except i nie wpisuj pustego stanu jako „naprawy”.
- Brak odczytu modułu oznacza jawne readiness=false z przyczyną;
  gotowość drugiego modułu niezależna. Brak opcjonalnej telemetrii nie blokuje wpisu.
- Nie wdrażaj jeszcze aktywacji control, usług wykonawcy, retry, potwierdzeń,
  planera CWU ani fizycznego działania. Brak tych funkcji jest jawnym zakresem,
  nie funkcją, która po cichu zwraca sukces.
- Nieobsługiwany schemat odmawia setup bez resetu danych i bez usług urządzeń.
  Pełne migracje i Store pozostają I04; odmowa nie dowodzi wykonania B07 w całości.

## Wymagane testy dla rzeczywistego SHA kodu

| Test / źródło | Asercja w I01 | Co pozostaje później |
| --- | --- | --- |
| A02 — część strukturalna | Wpis z CO bez przypisanej nastawy nie ładuje poprawnego runtime; brak usług i resetu danych | Komunikat kreatora w I02 |
| B01 | CWU-only przechodzi setup bez nastawy CO, outdoor i stref | Działający harmonogram w I14/I15 |
| B02 | Trzy warianty konfiguracji ładują wyłącznie obecne moduły; enabled/mode/gotowość osobno | Encje i panel w I16–I18 |
| A08 — fundament observation | Setup, ponowny setup i obsługa odczytów nie wywołują żadnej usługi źródła | Aktywacja i anulowanie realnego wykonawcy I11 |
| B04 — unload | Żadnego switch.turn_off/number.set_value ani przywracania; własne zadania/listenery odłączone | Anulowanie realnych retries I11 |
| C13 — część kontraktu | Domena i oba środowiska HA przyjęte w D101 | Karta Lit i aktywacja bindingów I03/I18 |
| D85 | Identyfikatory instalacji/stref/obiegu zachowane po unload/setup tego samego wpisu | Reconfigure/rename w I02/I03 |
| B11 — zależności fundamentu | Wybrana, niedostępna encja CWU nie zmienia gotowości sprawnych źródeł CO i odwrotnie | Awarie przy rzeczywistych poleceniach I15/I19 |

Mockuj konkretne usługi źródeł i sprawdzaj zero ich wywołań; nie blokuj
hass.services.async_call globalnie w sposób niszczący wewnętrzny setup HA.
Nie opieraj wszystkich asercji wyłącznie na liczbie wywołań: sprawdź runtime,
tożsamość, readiness i brak pozostawionych zasobów.
Użyj rzeczywistego fixture hass i MockConfigEntry. Test z samym importem domeny
nie spełnia zakresu. Zestaw nie może być pusty, pominięty ani xfail.

## CI i DoD

W tym samym PR pierwszy kod musi mieć manifest, dokładny pin pluginu minimum,
zgodny zestaw current, realne tests/integration/test_*.py i enable_custom_integrations.
Skorzystaj z instalatorów i dowodów I00; przed implementacją Tech Lead wpisuje
ich konkretny merge SHA. Nie zastępuj macierzy jednym zielonym środowiskiem.

Wymagane: wszystkie komendy [ci.md](../ci.md), pip check obu środowisk,
python -m pytest tests/integration na minimum/current oraz rzeczywisty hassfest.
ha-tests/hassfest nie mogą być skipped po pojawieniu się kodu.
Zbiorczy ci wymaga quality, obu ha-tests, obu ha-tooling I00 i hassfest.
Zapisz wersję/digest hassfest, jeśli dostępny. Nie zmieniaj nazw wymaganych
quality/ci ani uprawnień CI na zapis i nie dodawaj sekretów.

Developer w opisie PR podaje zakres części A/B/C powyżej, SHA,
środowiska/komendy/wyniki/linki CI, braki i ryzyko. To nie ukończenie US03/08/16/20.
DoD: wszystkie asercje zakresu mają wykonane testy, poprawny hassfest,
brak aktywnego sterowania i gotowy mały diff do niezależnego review.

## Wyłączenia, migracje i odbiorca

Bez algorytmu, krzywej, zaworów/demandu, CWU planu, D90/D99 wykonawcy, Store,
Recordera, frontendu, HACS wydania, POC/importera, prognoz i skroplin.
Nie dodawaj aktywnych placeholderów przyszłych modułów.

Brak migracji danych istniejącego produktu, bo to pierwszy kod; tożsamość
nowego wpisu musi jednak być trwała. Przy niezgodnych danych odmowa bez resetu.
Wycofanie przez revert małego PR przed wydaniem; nie usuwać historii HA
ani wykonywać usług na urządzeniach przy wycofaniu.

Następny odbiorca: Reviewer → Tester → Tech Lead / właściciel.
Reviewer ocenia kontrakty, bezpieczeństwo i testy, Tester potwierdza podany SHA
w obu środowiskach. Autor nie nazywa własnej samokontroli niezależnym review.
Nie scalać, nie publikować, nie wdrażać i nie rozpoczynać automatycznie I02.
W razie nowej luki opisz konkretny kontrakt i rekomendację Tech Leadowi;
nie wracaj do już przyjętych pytań P01–P12.
