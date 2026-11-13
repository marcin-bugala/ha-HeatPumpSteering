# I04 — wersjonowany Store i granica ConfigEntry/Store

Nadawca: Tech Lead / Orchestrator. Odbiorca: Developer → Reviewer → Tester →
Tech Lead / właściciel. Data: 13 listopada 2026.
Repozytorium: marcin-bugala/ha-HeatPumpSteering.
Gałąź implementacji: `feat/15-versioned-store`, PR do `main`.
Baza: `74f326baa6eb6347672125f49ac9ec1929e6f345` albo nowszy main zawierający
ten commit i przyjęte przekazanie I04. Developer zapisuje rzeczywisty bazowy
i końcowy SHA w raporcie.

## Podstawa i Definition of Ready

Projekt techniczny z PR #36, commit projektu
`e27621281d119f802e263d427ef9b9d36f6a135e`, został scalony przez właściciela.
Plan określa I04 jako mały pakiet Store v1, celów/trybów, walidacji i protokołu
rewizji ConfigEntry/Store. I03 jest zintegrowane na main; [raport I03](i03-verification.md)
wiąże końcowy kod, review, testy i CI z konkretnymi SHA.

Bieżące polecenie właściciela: „Przygotuj I04”. Upoważnia ono do przygotowania
przekazania, nie do implementacji w tej sesji. Implementacja rozpoczyna się po
osobnym zleceniu Developera.

Przeczytaj AGENTS.md, rolę Developera, workflow/standardy/CI, ten dokument,
[trwałość](../../technical/persistence.md), [model danych](../../technical/data-model.md),
[lifecycle](../../technical/lifecycle.md), [plan](../../technical/implementation-plan.md)
oraz wymagania. Odczytaj Issues #9, #15 i #26 z komentarzami. Na dzień przekazania
wszystkie trzy są otwarte, mają status `Do doprecyzowania` i nie mają komentarzy.
Nie zmieniaj statusów ani nie zamykaj całych US w tym częściowym zakresie.

| Źródło | Część realizowana w I04 |
| --- | --- |
| US02 / #9 | Trwały cel strefy jako ustawienie Store i zachowanie po reload/restart |
| US08 / #15 | Wersjonowanie, walidacja, odmowa niezgodności i bezpieczny powrót |
| US19 / #26 | Trwała pamięć potrzebnego stanu bez POC i bez fikcyjnych danych |
| D24–D25/D54/D71–D72/D74/D89/D96/D101 | Niezależne tryby, cele, Store, ciągłość, observation po ponownym włączeniu, niezgodny rollback |
| A07, A43, B05–B07, C08 | Warstwa trwałości A07/C08; A43/B05 tylko kontrakt zapisu i restartu, bez wykonawcy |

Nie ma nowego pytania produktowego blokującego I04. Parametry i zachowania urządzeń
pozostają w późniejszych pakietach. Jeżeli implementacja wymaga reguły wykraczającej
poza poniższy kontrakt, zgłoś ją Tech Leadowi zamiast dobierać zachowanie.

## Wynik i jawne wyłączenia

Po I04 każda ConfigEntry ma jeden Store HA o kluczu
`heat_pump_steering.{entry_id}`. Store jest jedynym źródłem bieżących celów stref
i zapisanych trybów modułów. Istniejące `target_temperature` w ConfigEntry schema v3
jest wartością bootstrap/migracyjną; po inicjalizacji Store nie wolno używać jej
jako cichego fallbacku ani synchronizować jako drugiej bieżącej kopii.

I04 dodaje typed persistence API, walidację, serializację zapisów oraz protokół
uzgodnienia rewizji przy zmianach strukturalnych. Setup może odtworzyć zapisany
tryb dopiero po gotowości modułu. Nadal nie istnieje użytkowa aktywacja control,
regulator ani wykonawca, więc żaden przebieg I04 nie wywołuje usług urządzeń.

Poza zakresem:

- encja `number` celu, dashboard, WS API, karta/panel i frontend;
- Recorder, historia, okna, pomiary, źródłowa świeżość i fikcyjne heartbeat;
- algorytm CO/stref/CWU, polecenia, D90, retry, timery ruchu i demand;
- harmonogram/nadpisania CWU, aktywne ostrzeżenia i diagnostyka użytkowa;
- uzbrajanie wyjść i aktywacja control przez użytkownika;
- reverse migration, backup/restore domu, wydanie i test sprzętowy.

Nie twórz atrap tych funkcji ani ogólnego frameworka event sourcing. Nie zapisuj
pełnych pomiarów, tasków, callbacków, nazw domu ani konfiguracji `.storage` w repo.

## ConfigEntry schema v4 i bootstrap Store

I04 podnosi `CONFIG_ENTRY_VERSION` i `CONFIG_SCHEMA_VERSION` z 3 do 4. Schema v4
zachowuje wszystkie UUID, bindingi I03 i `configuration_revision`, a dodaje jawny
znacznik `state_store_initialized: bool`. Migracja v3→v4 nie zmienia semantyki
bindingów ani celów bootstrap i nie wymaga stanów encji lub dostępnego urządzenia.

Znacznik rozróżnia pierwszy bootstrap od utraty/uszkodzenia istniejącego Store:

1. Dla `state_store_initialized=false` setup ładuje Store. Jeżeli istnieje poprawny,
   zgodny payload pozostawiony po przerwanym bootstrapie, używa go idempotentnie.
2. Jeżeli Store nie istnieje, tworzy v1 z celów bootstrap ConfigEntry, trybami
   `observation`, pustą pamięcią i bieżącą `configuration_revision`.
3. Dopiero po udanym, awaited `Store.async_save` ustawia marker na true.
4. Crash po zapisie Store, ale przed markerem jest bezpieczny: następny setup
   waliduje istniejący Store i kończy marker bez resetu.
5. Przy markerze true brak/None, uszkodzony, obcy albo nieobsługiwany Store jest
   błędem setup. Nie twórz wtedy nowego payloadu i nie nadpisuj danych bootstrapem.

Użyj publicznego `homeassistant.helpers.storage.Store` na obu przypiętych wersjach,
z `version=1`, `minor_version=1`, `atomic_writes=True` i domyślnym
`max_readable_version=1`. Nie czytaj ani nie zapisuj ręcznie plików `.storage`.
HA może zwrócić None po obsłudze uszkodzonego JSON; marker ConfigEntry ma zapobiec
potraktowaniu takiego wyniku jako pierwszej konfiguracji.

Migracja v1/v2/v3 ConfigEntry kończy w schema v4 i zachowuje dotychczasowe testy
atomowości. Przyszła lub błędna ConfigEntry nie tworzy Store. Nie zwiększaj
`configuration_revision` tylko z powodu technicznego podniesienia schema.

## Store v1 — kanoniczny payload

Payload jest zwykłym JSON na granicy HA i typowanymi, niemutowalnymi snapshotami
w runtime. Liczby temperatur serializuj w kanonicznej postaci zachowującej krok
0,5°C; po odczycie waliduj przez ten sam kontrakt D96. Czasy są UTC aware ISO 8601.

Wymagane pola root:

| Pole | Kontrakt I04 |
| --- | --- |
| payload_version | Dokładnie integer 1; bool/string/float i przyszła wersja są błędem |
| installation_id | Musi być równe ConfigEntry; nigdy adopcja obcego Store |
| configuration_revision | Dodatni integer zgodny z committed stanem ConfigEntry |
| settings_revision | Dodatni, monotoniczny integer dla zmian ustawień Store |
| phase | `committed`; przejście strukturalne jest w `pending_config_change` |
| user_settings | `zone_targets` po zone_id oraz `co_mode`/`dhw_mode` dla istniejących modułów |
| pending_config_change | null albo kompletny rekord from/to + następny snapshot ustawień |
| zone_memory/output_memory | Puste mapy w I04; pola i producenci powstają w pakietach algorytmu/wykonawcy |
| overrides/active_warnings/acknowledgements | Puste mapy w I04; bez fikcyjnych rekordów przyszłych funkcji |
| saved_at | Czas udanego snapshotu do diagnostyki; nie jest dowodem stanu urządzenia |

Walidator odrzuca brak pól, nieznane enumy, nieprawidłowe UUID/revisions/czasy,
cele spoza 5–35°C lub kroku 0,5°C, cele obcych/brakujących zone_id oraz tryby
dla nieistniejących modułów. Cel jest wymagany dla każdej zapisanej strefy,
również czasowo disabled. Brak modułu oznacza brak jego pola trybu, nie null.

I04 dopuszcza wartości trybu `observation` i `control`, aby odtworzyć przyszły
zapisany stan, ale nie dodaje ścieżki użytkowej ustawiającej control. Efektywny
runtime zaczyna observation; zapisany control staje się efektywny dopiero po
gotowości modułu. Brak gotowości pozostawia działanie w observation bez kasowania
zapisanego zamiaru. Żadna z tych zmian nie wysyła usługi HA.

Nie akceptuj dowolnych dodatkowych pól „na przyszłość”. Rozszerzenia I07/I11/I14
podnoszą minor/payload i dodają własne migracje. Puste kolekcje I04 dowodzą granicy,
nie implementacji blokad, retry, nadpisań lub ostrzeżeń.

## API pamięci i zwykłe zapisy ustawień

Dodaj małą usługę per entry, posiadaną przez runtime, z jedną `asyncio.Lock` dla
snapshotu i zapisu. Nazwa klasy/pliku może być idiomatyczna dla repo; kontrakt:

- `async_load_or_initialize(config)` zwraca zwalidowany immutable snapshot;
- odczyt snapshotu nie udostępnia mutowalnego słownika z granicy JSON;
- zmiana celu/trybu przyjmuje oczekiwane `settings_revision`, waliduje całość,
  składa nowy snapshot pod lockiem i wykonuje awaited `async_save`;
- dopiero udany save publikuje snapshot runtime i zwiększoną rewizję;
- wyjątek lub anulowanie zachowuje poprzedni snapshot i rewizję;
- zapis ustawień nie aktualizuje ConfigEntry i nie wywołuje reload;
- dwa równoległe zapisy tej samej rewizji: najwyżej jeden sukces, drugi otrzymuje
  jawny konflikt; nie stosuj last-write-wins;
- w I04 nie używaj opóźnionego zapisu dla celów/trybów. Operacja nie jest
  potwierdzona przed trwałym zapisem.

Runtime przechowuje bieżące cele osobno od bootstrapowego `ZoneConfig` albo przez
jednoznaczny widok settings; przyszli konsumenci nie mogą przypadkiem czytać
`ZoneConfig.target_temperature` jako aktualnego celu po inicjalizacji Store.

## Protokół ConfigEntry/Store przy zmianie strukturalnej

ConfigEntry i Store nie mają wspólnej transakcji. Wszystkie drogi zmieniające
`configuration_revision` po I04 — reconfigure oraz registry reconciliation I03 —
muszą użyć jednego koordynatora, nie bezpośredniego `async_update_entry`.

Pod wspólną blokadą per entry:

1. Sprawdź oczekiwaną rewizję ConfigEntry i Store oraz pełną poprawność kandydata.
2. Zbuduj następny stan Store: cele istniejących stref zachowane po `zone_id`,
   nowa strefa dostaje jawny cel z draftu, usunięta znika; disable/re-enable modułu
   zapisuje jego tryb jako observation. Rename/grupa/czujnik nie zmienia celu.
3. Zapisz `pending_config_change` z `from_revision`, `to_revision`, dotychczasowym
   committed snapshotem i kompletnym następnym snapshotem.
4. Dopiero po udanym prepare zaktualizuj ConfigEntry jako jedną zmianę logiczną.
5. Zapisz Store jako committed dla `to_revision`, usuń pending i dopiero wtedy
   zakończ sukcesem/reload. Nie trzymaj locka przez reload ani usługi urządzeń.

Odzyskanie podczas setup jest deterministyczne:

- entry na `from_revision` + poprawny pending → wycofaj pending, zachowaj stary
  committed stan;
- entry na `to_revision` + poprawny pending → dokończ commit następnego stanu;
- inna rewizja, niespójne from/to, installation_id lub payload → jawny błąd,
  bez zgadywania zwycięzcy i bez resetu;
- awaria prepare nie zmienia ConfigEntry; awaria finalizacji po aktualizacji entry
  pozostawia odzyskiwalny pending i nie uruchamia runtime na nieuzgodnionym stanie.

Registry rename zachowuje Store settings i tylko uzgadnia nową
`configuration_revision`. Replacement/polaryzacja nadal nie uzbraja bindingu;
I04 nie dodaje `armed_binding_revision` ani aktywacji. Nie osłabiaj własności I03.

## Setup, reload, disable i unload

Kolejność setup: walidacja/migracja ConfigEntry → load/recovery Store → własność
I03 → utworzenie runtime → subskrypcje/readiness → ewentualne odtworzenie zapisanego
trybu po gotowości. Błąd Store kończy setup przed runtime i bez usług.

Reload używa tego samego Store i nie zwiększa rewizji. Restart z poprawnym committed
snapshotem odtwarza cele i zapisane tryby. Ponowne włączenie modułu po `enabled=false`
zaczyna observation zgodnie z D74; zwykły restart włączonego modułu nie resetuje
zapisanego trybu. Moduły są niezależne.

Unload anuluje zasoby jak w I03 i nie usuwa Store. Ponieważ zapisy I04 są awaited,
nie powinno być ukrytego dirty snapshotu do dopisania. Usunięcie ConfigEntry i
kasowanie Store zaplanuje osobny lifecycle, gdy HA remove hook zostanie wprowadzony;
I04 nie usuwa danych przy unload/disable.

## Minimalna macierz odbioru I04 — plan, nie wyniki

| Test / źródło | Wymagany dowód na końcowym SHA |
| --- | --- |
| Bootstrap CO/CWU/oba | Store v1 powstaje raz po udanym zapisie; właściwe cele/observation, UUID i bindingi bez zmian, zero usług |
| Migracja v1/v2/v3→v4 | Idempotentna; brak stanów registry/urządzeń nie blokuje; przyszła/błędna wersja nie tworzy ani nie resetuje Store |
| A07/D25/D96/C08 | Zmiana jednego celu przez persistence API zachowuje drugi, granice/krok walidowane; reload/restart czyta Store, nie bootstrap ConfigEntry; CO observation nie wpływa na CWU |
| D54/D74 | Zapisane tryby modułów niezależne; restore dopiero po readiness; re-enable zaczyna observation; zawsze zero usług w I04 |
| Zapis settings | Błąd i CancelledError nie publikują nowego snapshotu; dwa zapisy tej samej rewizji bez lost update |
| Brak/uszkodzenie/future | Marker true + None, malformed, obcy installation_id, przyszła wrapper/payload lub niespójna rewizja: setup error, brak save/reset/runtime/usług |
| Config transaction | Awaria przed prepare, po prepare i po update entry; restart odpowiednio rollback/finalize; powtórzenie jest idempotentne |
| Reconfigure | Rename/grupa/czujnik zachowują cel po zone_id; nowa/usunięta strefa aktualizuje settings; revision conflict odrzucony |
| Registry I03 | Rename encji przechodzi przez koordynator, zachowuje settings i ownership; listener/reload bez duplikacji |
| B05/A43 — część I04 | Syntetyczny committed/pending snapshot i UTC są zachowane przez crash/restart; brak twierdzenia o działającej blokadzie demandu lub postępie temperatury |
| B06 | Trwała tożsamość stref zachowuje cel; odtworzona nazwa z nowym UUID nie dziedziczy celu; okna nowego źródła pozostają I06 |
| B07/D89 | Niezgodny Store/ConfigEntry daje jawny błąd bez zmiany pliku, danych, markerów i bez aktywacji |
| Regresja I03 | Własność/race/D86/registry/migracje/setup/unload i 91 istniejących testów zachowane |

Testy crash wykonuj przez kontrolowane wyjątki/barierę w adapterze Store, nie przez
edycję prawdziwego `.storage` ani `sleep`. Dane wyłącznie syntetyczne, sieć zablokowana.
Sprawdź na obu wersjach HA konkretne zachowanie Store dla unsupported/corrupt load;
mock nie może ukrywać odmiennego publicznego kontraktu.

Niewykonane w I04: pełny A43 z demandem i potwierdzeniami temperatury, pełny B05
z aktywnymi retry/nadpisaniem, encja/UI celu z A07/C08 oraz realny rollback kopii HA.
Raport Testera ma je oznaczyć jako częściowe lub niewykonane, nie jako PASS całego
scenariusza. Wszystkie testy I04 są symulacją HA bez sprzętu.

## Definition of Done i przekazanie

Developer raportuje bazowy/końcowy SHA, diff, US/D/A/B/C, wersje schema/Store,
każdą granicę awarii i niewykonane części. Wymagane komendy z ci.md: Ruff
check/format, bootstrap, check_repository, git diff --check, oba ha-tooling/pip check,
oba pytest integration, hassfest i zbiorcze ci — 7/7 PASS dla końcowego SHA.
Istniejących 91 testów nie wolno osłabiać; liczba końcowa ma wynikać z nowych
przypadków, nie z twardego celu.

Reviewer niezależnie sprawdza model źródła prawdy, marker bootstrap, walidację
future/corrupt, kolejność prepare→entry→finalize, wszystkie bezpośrednie update
`configuration_revision`, brak cichego fallbacku i brak usług. Tester odtwarza
macierz na tym samym SHA, w tym awarie/cancel/race i oba HA. Po poprawkach ponów
dotknięte kontrole; autor nie przedstawia samokontroli jako niezależnego review.

Rollback I04: ConfigEntry schema v4 i Store v1 są nieczytelne dla I03. Sam revert
kodu nie jest bezpiecznym powrotem. Do powrotu potrzebna jest zgodna kopia HA albo
osobno zaprojektowana i przetestowana migracja odwrotna; nie kasuj Store, markerów,
celów lub bindingów, aby starszy kod zaczął działać.

Następne I05/I06/I07/I11/I14 korzystają z API i wersjonowania I04, ale żaden z nich
nie jest implementowany w tym PR. Bez merge, auto-merge, release, deploy, restartu
domu i operacji na prawdziwych encjach.

