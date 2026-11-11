# I03 — własność wyjść i trwałe bindingi encji

Nadawca: Tech Lead / Orchestrator. Odbiorca: Developer → Reviewer → Tester →
Tech Lead / właściciel. Data: 11 listopada 2026.
Repozytorium: marcin-bugala/ha-HeatPumpSteering.
Gałąź implementacji: `feat/16-output-ownership`, PR do main.
Baza: `3068903a802aec6853403daedfb69a3ef5faf907` albo nowszy main
zawierający ten commit oraz przyjęte przekazanie I03. Developer zapisuje
rzeczywisty bazowy i końcowy SHA w raporcie.

## Podstawa i Definition of Ready

Projekt PR #36 / `e27621281d119f802e263d427ef9b9d36f6a135e`
został scalony przez właściciela; następnie zlecono etap implementacji.
I02 w PR #40 jest scalone; [raport sprawdzenia](i02-verification.md)
wiąże kod, zaakceptowany raport Reviewer/Tester i CI z konkretnymi SHA.
Nie utożsamiamy COMMENTED z formalnym APPROVED.

Bieżące polecenie właściciela: „Jako Tech Lead sprawdź I02, wyniki review
oraz testów. Przygotuj konkretne przekazanie I03 dla Developera, zgodnie
z planem implementacji. Nie rozpoczynaj kodowania”.
To upoważnienie do przygotowania dokumentacji, nie rozpoczęcia implementacji w tej sesji.
Brak nowego pytania produktowego: P04/D93 i P12/D101 już rozstrzygnięto.

Przeczytaj AGENTS.md, rolę Developera, workflow/standardy/CI,
[plan](../../technical/implementation-plan.md), model danych/kontrakty HA/lifecycle
oraz odpowiednie wymagania. Odczytaj Issues wraz z aktualnymi komentarzami.
Nie ponawiaj I00–I02, nie korzystaj z poc.

| Źródło | Część realizowana w I03 |
| --- | --- |
| US01 / #8, US09 / #16, US16 / #23 | Trwałe bindingi, opcjonalne wyjścia, walidacja i bezpieczna edycja |
| US15 / #22, US10 / #17 | Własność wielu wyjść strefy, NC/NO i polaryzacja w konfiguracji |
| D08/D20–D21/D69–D70/D72/D74 | Opcjonalność, jeden CO, trwałość, observation |
| D84–D87/D93/D101 | Unieważnienie, tożsamość, ostrzeżenie odłączenia, rezerwacje i nowe bindingi |
| A01–A04, B04/B06/B09/B10, C05/C13 | Wyłącznie konfiguracja/tożsamość/obserwacja; pełne wykonanie pozostaje później |

Nie zmieniaj statusów ani nie zamykaj całych US przy tym częściowym zakresie.

## Wynik i granice

Po zapisie żadna rozpoznawalna encja wykonawcza nie może należeć do dwóch funkcji
ani konfiguracji produktu. Rename źródła z rejestrem zachowuje binding;
usunięcie/replacement nie przejmuje po cichu nowego urządzenia.
Przed odłączeniem użytkownik widzi bieżący raport HA i informację, że ostatni
stan pozostanie. Reconfigure i wybór NC/NO/polaryzacji niczego nie przełącza.

I03 dodaje tylko konfigurację opcjonalnych zaworów/demandu potrzebną do sprawdzenia
pełnego D87. I12 wykonuje zawory, I13 sekwencjonuje demand.
Nie dodawaj regulatora, usług, retry/ACK/timerów ruchu, aktywacji control,
Store/Recordera/okien, encji produktu, panelu/karty ani nowej zależności.
I04/I05/I10–I13/I16 pozostają osobnymi pakietami. Nie dodawaj drugiego CO.

## Kontrakt konfiguracji i migracji

I02 ma ConfigEntry VERSION=2/MINOR=1, payload schema=2 i stringi entity_id.
I03 wprowadza VERSION=3/MINOR=1 i payload schema=3: starszy parser nie może
po cichu zignorować nowej semantyki własności. Jedna kanoniczna reprezentacja
w ConfigEntry.data, bez równoległych stringów i map w options/Store.

| Element schema 3 | Kontrakt |
| --- | --- |
| source_bindings | Rekordy source_id UUID, entity_registry_id nullable, entity_id jako ostatnia lokalizacja, rola. Referencje outdoor i sensorów stref po source_id; primary należy do listy |
| output_bindings | Rekordy output_id UUID, entity_registry_id nullable, entity_id, funkcja/scope, adapter number/switch, jawna polaryzacja switch i binding_revision |
| Odwołania modułów | Nastawy CO/CWU i zezwolenie CWU wskazują output_id. Opcjonalny demand wskazuje output_id; strefa ma listę valve_output_ids |
| Strefa | Jeden jawnie wybrany NC/NO wspólny wszystkim jej wyjściom, bez wyjątków na bindingach. Strefa pomiarowa bez wyjść pozostaje poprawna |
| Opcje CO | Niezależny wybór konfiguracji zaworów i demandu, domyślnie brak obu przy migracji. Wyłączenie funkcji zachowuje ustawienia i rezerwacje; jawne odłączenie usuwa przypisanie po D86 |
| configuration_revision | Monotoniczny numer aktualizacji konfiguracji. Otwarcie draftu zapamiętuje wersję; przed zapisem porównanie i ponowna pełna walidacja |
| Tożsamość | UUID instalacji/obiegu/CWU/stref/grup/unique_id/cel nie zmieniają się. Rename encji zachowuje source_id/output_id i binding_revision; replacement/polaryzacja zmienia rewizję bindingu |

source_id opisuje logiczne źródło pomiarowe: wymiana termometru tworzy nowy
szereg/tożsamość źródła bez zmiany zone_id; I05/I06 zbudują okna.
Kilka stref może odnosić się do tej samej encji pomiarowej — to nie konflikt.
Output_id identyfikuje przypisanie funkcji; zmiana jego encji/polaryzacji
zachowuje slot funkcji, zwiększa binding_revision i nie dziedziczy uzbrojenia.
Usunięcie i odtworzenie przypisania tworzy nowy output_id.

Migracja v2→v3 tworzy bindingi dla obecnych wyjść i wszystkich źródeł,
ustala registry_id, jeśli aktualnie istnieje; zachowuje brak danych jako brak.
Nie wymaga dostępnego stanu urządzenia, nie fabrykuje celu, nazw ani ustawień
zaworów. Zachowaj również ścieżkę v1→v2→v3, włącznie z neutralną etykietą strefy.
Waliduj kopię przed jedną aktualizacją wpisu; błędny/przyszły schemat zwraca błąd
bez resetu i częściowej migracji. Przy istniejącym konflikcie nie wybieraj zwycięzcy
kolejnością setup; pokaż konflikt, zablokuj zależne użycie wyjścia, zachowaj dane
umożliwiające naprawę. Pozostała poprawna obserwacja nie wymaga usług.

## Rejestr encji i rozpoznawanie konfliktów

Użyj publicznych API entity_registry odczytanych na obu przypiętych wersjach:
[minimum](https://github.com/home-assistant/core/blob/357cae5c598dfcd7a0ea7dc5b1facccd4ec6037b/homeassistant/helpers/entity_registry.py)
i [current](https://github.com/home-assistant/core/blob/d8a0dc698c8946b44e455d904000db563cfbf1ba/homeassistant/helpers/entity_registry.py).
RegistryEntry.id jest trwałym ID rejestru; unique_id/platform/domain pozwalają
rozpoznać tę samą rejestrację, nie fizyczną równoważność urządzeń.
Registry aliases są nazwami wyszukiwania, nie listą fizycznie wspólnych przekaźników.

- Gdy registry_id istnieje, rozwiąż je przez registry.async_get(id) i sprawdź
  aktualny entity_id/domenę/platformę. Sam async_resolve_entity_id ze stringiem
  entity_id zwraca string i nie dowodzi istnienia wpisu rejestru.
- Klucz własności: registry_id, gdy znany; dla encji bez rejestru jawny entity_id.
  Porównuj też aktualne/ostatnie lokalizacje, aby nie ominąć konfliktu mieszając
  draft stringowy, stary payload i binding po registry_id.
- Odrzuć powielenie CO↔CWU, demand↔zezwolenie CWU, zawór↔demand/CWU i zawór↔inna
  strefa/entry, również dla wyłączonych modułów/stref i disabled/not loaded entry.
  Jedna strefa może mieć kilka różnych wyjść; identyczny duplikat na liście jest błędem.
- Odrzuć wyjście należące do heat_pump_steering (platform/config entry), również
  po rename. Czujniki wolno współdzielić. Bez heurystyki po podobnej nazwie,
  device_id lub zewnętrznej automatyzacji.
- Nie obiecuj wykrycia dwóch różnych integracji sterujących fizycznie jednym
  przekaźnikiem. Informacja o jednym regulatorze pozostaje obowiązkowa;
  produkt nie wyłącza innych automatyzacji.
- EVENT_ENTITY_REGISTRY_UPDATED: update z old_entity_id aktualizuje lokalizację
  bindingu, rezerwację i subskrypcje; remove unieważnia resolution.
  Gdy zapisany registry_id nie istnieje, nie przechodź na nowy wpis o starej nazwie.
  Tylko jawne reconfigure może zaakceptować inną tożsamość.
- Dla źródeł bez rejestru rename wymaga reconfigure; nie zgaduj. Niedostępny
  odczyt/disabled entity to jakość danych, a nie utrata własności.
- Obsługa rename dotyczy także zapisanych, niezaładowanych wpisów: przy setup/
  ponownym flow uzgodnienie według registry_id. Nie zmieniaj cudzych rejestrów,
  dashboardów ani automatyzacji i nie operuj na .storage.

## Atomowość i lifecycle

Zastąp modułowy _FINALIZE_LOCK jednym małym serwisem własności per instancja HA.
Źródłem prawdy są zapisane ConfigEntry plus jawne krótkotrwałe rezerwacje finalizacji;
cache w pamięci nie jest osobną trwałą bazą. Wszystkie drogi używają tej samej
walidacji: create/reconfigure, migracja/setup i aktualizacja bindingu po registry event.

Pod wspólną blokadą: sprawdź aktualną rewizję, rozwiąż bindingi, sprawdź wszystkie
entries, zarezerwuj cały nowy zestaw i zatwierdź zmianę jako jedną operację logiczną.
Nie zwalniaj starych wyjść przed walidacją całego nowego zestawu.
Błąd/cancel przywraca poprzednią własność i dane; brak częściowych rezerwacji.
Nie trzymaj blokady przez reload ani przyszłe usługi urządzeń.

Samo zwrócenie CREATE_ENTRY z flow nie jest dowodem, że ConfigEntry już widnieje
w kolekcji. Rezerwacja musi obejmować tę granicę aż HA zarejestruje wpis; abort,
błąd i anulowanie finalizacji nie pozostawiają wycieku. Nie polegaj wyłącznie na
szczęśliwej kolejności asyncio.gather. Zaplanuj test z kontrolowaną barierą.
To atomowość w procesie, nie obietnica transakcyjnego fsync HA na dysku.

Unload/wyłączenie entry kończy callbacki, tasks i zwiększa generation.
Zapisane przypisania pozostają zarezerwowane, także gdy runtime nie działa.
Dopiero zatwierdzone odłączenie/usunięcie wpisu zwalnia odpowiednie rezerwacje.
Zamiana A→B po poprawnym zapisie nie daje starym callbackom prawa do B.
Na granicach await ponowna kontrola generation/revision. Obecne I02 nie ma
wykonawcy/retry — testuj dostępne zasoby, nie dodawaj atrapującego frameworka komend.

D101: nowe/zmienione wyjście jest nieuzbrojone; reconfigure nie oznacza aktywacji.
Kontrakt binding_revision musi pozwolić I04/I11 zapisać i porównać
armed_binding_revision. Teraz wszystkie moduły nadal observation; nie zapisuj
fikcyjnego control ani nowego Store. Nieaktywowane wyjście nie jest OFF urządzenia.

## UI i ostrzeżenia D86

Rozszerz istniejący draft/config flow, bez osobnego frontendu. Typowane selektory,
walidacja błędów przy właściwym polu, wszystkie nowe etykiety/opcje/komunikaty PL/EN.
Cztery konfiguracje zawory/demand są dostępne tylko dla CO; samo CWU nie pyta o CO.

Przed zmianą encji, usunięciem bindingu/strefy lub wyłączeniem skonfigurowanej
funkcji pokaż listę odłączanych wyjść, raportowaną wartość z HA albo jawne
nieznane/niedostępne oraz informację: ostatni stan pozostaje, produkt go nie cofnie,
użytkownik może zmienić go ręcznie przed zatwierdzeniem.
Raport HA nie jest fizycznym położeniem zaworu ani potwierdzeniem D90.
Przy włączeniu konfiguracji zaworów pokaż uzgodnione ostrzeżenie o przepływie
z rundy 3. Wyświetl mapowanie NC/NO→zasilanie→stan encji z polaryzacją.

Ostrzeżenie poprzedza zmianę danych, nie jest dopisanym komunikatem po reload.
Końcowe confirm musi być dokładnie true; false i cancel niczego nie zapisują
ani nie zwalniają. Obecna luka confirm=false z I02 jest opisana w raporcie.
Przed ostatecznym zapisem odśwież listę zmian/stany i sprawdź rewizję;
nowy zestaw odłączeń wymaga ponownego pokazania, nie cichego rozszerzenia zgody.

## Minimalna macierz odbioru I03 — plan, nie wyniki

| Test / źródło | Wymagany dowód |
| --- | --- |
| A01–A04/C05: konfiguracja | Cztery kombinacje zawory/demand; CWU-only; NC/NO wspólne strefie, polaryzacja per binding, wiele wyjść; zero usług po edycji |
| B09: konflikty | W obrębie stref/funkcji i między entries; disabled/unloaded/observation też blokują; sensory współdzielone |
| B09: wyścigi | Dwa create, dwa reconfigure i create↔reconfigure na tym samym wyjściu; bariera przed rejestracją wpisu; najwyżej jeden sukces, bez wycieku |
| B09/B10: rollback | Błąd walidacji/zapisu, cancel, anulowanie finalizacji; poprzedni zestaw nadal zajęty, nowy wolny; brak częściowego commit |
| B06: registry rename | Outdoor, primary i aggregate sensory oraz number/switch wyjścia; zachowane UUID/cele/rewizja bindingu; zapis i reload/restart używają nowej lokalizacji |
| B06/B10: usunięcie | Nowa encja o tym samym entity_id z innym registry_id nie jest przejmowana; jawny replacement zmienia rewizję i nie uzbraja |
| D87: alias/tożsamość | Ten sam registry_id przez różne lokalizacje jest konfliktem; aliases display nie tworzą fałszywej tożsamości fizycznej; własne encje odrzucone |
| B04/D86: odłączenie | Stan/unknown i ostrzeżenie przed zapisem; true/false/cancel; usunięcie strefy i zmiana wyjścia; zero OFF/usług; stary runtime nie reaguje |
| B04/B10/C13: lifecycle | Unload nie zwalnia zapisanej własności; usunięcie entry zwalnia; reload bez dublowania listenerów; stary callback po await nie zmienia nowego bindingu |
| D72/B07: migracja | V1→v3 i v2→v3, brak registry/stanów, disabled, błąd/przyszła wersja bez resetu; cele i UUID identyczne |
| D101/C13: aktywacja | Nowy/replaced/polarity-changed binding nie dziedziczy uzbrojenia; rename tej samej tożsamości go nie redefiniuje; nadal observation |
| Regresja I02 | Flow, migracje, selektory PL/EN, primary/aggregate, disabled/re-enable, revision conflict, setup/unload i brak usług zachowane |

Dla testów race użyj zdarzeń/barier zamiast sleep. Mocki HA i syntetyczny registry;
sieć zablokowana. Nie wymagaj dokładnie 53 testów: zachowaj ich intencję,
dostosuj fixtures do v3 i dodaj nowe scenariusze. Nie przenoś braków do I19.
C05 nie oznacza testu ruchu, C13 nie oznacza gotowego Lit lub number celu.

## Definition of Done i przekazanie

Developer raportuje SHA, diff, US/D/A/B/C, migrację, ograniczenia i dokładne wyniki
komend z ci.md: Ruff check/format, 12 bootstrap (lub uzasadnione rozszerzenie),
check_repository i git diff --check. Wymagane oba ha-tooling/pip check,
oba pytest tests/integration, hassfest oraz zbiorcze ci; wszystkie 7 jobów PASS.
Użyj istniejącej macierzy HA 2026.10.4/2026.11.1 i Linux/Python 3.14 >=3.14.2.
Nie aktualizuj zależności/fixtures jako ubocznego zakresu i nie omijaj bramek.

Reviewer sprawdza całość krytycznej sekcji, granicę CREATE_ENTRY, źródło własności,
trwałość identity, ostrzeżenia oraz brak usług. Tester odtwarza macierz na końcowym
SHA i publikuje wynik z brakami; komentarz/CI nie dowodzi odbioru sprzętowego.
Autor własną kontrolę oznacza jako samokontrolę. Po poprawkach nowe SHA i kontrole.

Rollback: schema 3 jest nieczytelne dla I02. Sam revert kodu nie jest powrotem danych;
potrzebna zgodna kopia HA albo osobno przetestowana migracja odwrotna.
Nie kasuj wpisów, celów ani danych, żeby starszy kod zaczął działać.

Kolejność pracy w jednym zakresie I03: model/migracja → własność i registry/lifecycle →
UI ostrzeżeń + testy zachowania. Jeśli diff wymaga podziału PR, zgłoś granicę Tech Leadowi,
nie publikuj przejściowego schematu omijającego D87. Następny pakiet I04 wymaga
osobnego odbioru i przekazania. Bez merge, auto-merge, release, deploy i domu.
