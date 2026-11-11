# I02 — kreator HA i model instalacji/stref

## Kontrakt Tech Lead → Developer

- Data: 11 listopada 2026; repo: marcin-bugala/ha-HeatPumpSteering.
- Baza wykonania i sprawdzony main: 552ea427086786e3b3411d95ed0305dc35ba80c0.
- Projekt: e27621281d119f802e263d427ef9b9d36f6a135e po PR #36,
  przyjęte D90–D101 i przekazania po PR #37.
- Zależności: I00 i I01 scalone razem w PR #38. [Dowody i ograniczenia
  review/testów](i00-i01-verification.md). T08 nie otwieramy ponownie.
- Upoważnienie: właściciel po scaleniu zlecił Tech Leadowi przygotowanie I02,
  zgodnie z planem; ten dokument nie uruchamia Developera automatycznie.
- Gałąź kodu: feat/8-installation-model od aktualnego origin/main zawierającego
  powyższą bazę. Przed startem sprawdź nowe commity, diff i Issues z komentarzami.
- Refs #8 (US01, główne), #22 (US15), #16 (US09 — część strukturalna),
  #23 (US16), #9 (US02 — cel początkowy); regresje #10/#15.
- D07/D17–D21/D23/D32/D46/D69–D74/D84–D89/D95–D96/D101.
- Odbiór: A01/A02/A05/A09/A30, B01/B02/B03/B06/B09/B10/B11,
  C07/C08/C13 w dokładnie ograniczonych częściach z tabeli niżej.
- Wynik: mały PR do main z rzeczywistym SHA i dowodami testów;
  bez Closes całych US, merge, auto-merge, wydania, deploy i instalacji domu.

Przeczytaj AGENTS.md, rolę Developera, workflow, standardy, ci.md,
[model](../../technical/data-model.md), [HA](../../technical/ha-contracts.md),
[lifecycle](../../technical/lifecycle.md) oraz US01/02/09/15/16 i rundy 1/3–6.
P01–P12 są rozstrzygnięte; nie redefiniuj ich przy doborze implementacji.

## Rezultat widoczny dla użytkownika

Z UI HA można utworzyć poprawną konfigurację jednej pompy: samo CO, samo CWU
albo oba. CO ma jeden obieg i dowolnie nazwane strefy, opcjonalne grupy
porządkowe, własny początkowy cel i jeden/kilka termometrów strefy.
Użytkownik może później edytować tę konfigurację i wyłączyć strefę/moduł.
Całość nadal działa wyłącznie w obserwacji i nie wysyła poleceń urządzeń.

Nie dodawaj w I02 zaworów/demandu ani ich pól aktywacji: przypisania i własność
tych opcjonalnych wyjść są I03, wykonanie I12/I13. Brak ich pól w tym częściowym
pakiecie nie zmienia pełnego zakresu wydania i nie jest końcem US09.
CWU obejmuje na razie tylko przypisania źródeł; nie ma panelu/temperatury
stałej/harmonogramu ani obsługi higieny.

## Co istnieje i co należy rozszerzyć

| Plik / stan w main | Zlecenie I02 |
| --- | --- |
| config_flow.py rejestruje tylko VERSION/MINOR_VERSION | Rzeczywisty async_step_user i reconfigure, współdzielony draft/walidator; nie zastępuj istniejącej klasy inną domeną |
| manifest.json bez config_flow | Ustaw config_flow=true dopiero razem z działającym kreatorem, strings/translations i testami |
| models.py: InstallationConfig/co/dhw/ZoneConfig i parse_config | Rozszerz małe jawne typy o nazwy, grupy i listy termometrów, bez frameworka i bez drugiego modelu na potrzeby UI |
| ZoneConfig ma temperature_entity_id i target_temperature | Obsłuż zgodną migrację do wielu termometrów; zachowaj cel i UUID istniejących wpisów I01 |
| refresh_readiness korzysta z jednej temperatury strefy | Subskrybuj wszystkie nowe źródła; dla agregacji rozpoznaj dostępne źródła, dla głównego używaj tylko wybranego. Brak jednego nie udaje awarii pozostałych źródeł/stref |
| setup/unload mają generation i unsubscribe | Reconfigure odłącza stare źródła i tworzy świeży runtime; żadnych starych callbacków ani usług wyjściowych |
| 13 testów setup/unload i dwa środowiska CI | Zachowaj regresje zachowania i dodaj testy przepływów/modelu/migracji w obu wierszach |

## Przebieg UI i zapis

1. user: nazwa instalacji i wybór CO/CWU. Pierwsza konfiguracja wymaga co
   najmniej jednego modułu. Instalacja ma własny UUID, nie slug nazwy i nie
   identyfikator pierwszej encji.
2. Dla CO: number nastawy i sensor outdoor. Wybór encji także w obserwacji.
   Następnie menu zarządzania strefami/grupami w roboczym draft.
3. Strefa: nazwa użytkownika, enabled, grupa lub brak, jeden/kilka sensor,
   cel 5–35°C co 0,5°C. Przy wielu: główny (musi należeć do listy) albo
   agregacja. Funkcja agregacji mean/median jest wspólna dla programu,
   domyślnie mean; nie twórz indywidualnych wag termometrów.
4. Grupa: UUID i nazwa, tylko porządek. Bez temperatury, celu, wyjść i
   dodatkowego udziału w regulacji. Strefa bez grupy jest poprawna.
5. Dla CWU: number nastawy i switch zezwolenia. CWU-only pomija całe CO,
   outdoor i strefy. Stan startowy nastaw/planów CWU pozostaje Nieskonfigurowane D95.
6. Podsumowanie i finalne zatwierdzenie całego poprawnego draft. Dopiero
   wtedy utwórz ConfigEntry albo zastąp dane edytowanego wpisu i przeładuj runtime.
   Wcześniejsze kroki, błędne pola i anulowanie nie zmieniają zapisanego wpisu.
7. Reconfigure: ten sam mechanizm draft/walidacji, z zachowaniem UUID i entry_id.
   Nazwa/grupa/termometry nie tworzą nowych tożsamości strefy. Usunięcie i
   ponowne dodanie tej samej nazwy daje nowy zone_id.
   Nie identyfikuj stref po indeksie listy.

Nowa konfiguracja ma co najmniej jedną aktywną strefę, jeśli CO jest włączone.
Nie wolno zapisać CO enabled bez aktywnej strefy, źródła i celu.
Wyłączenie już skonfigurowanego modułu zachowuje jego strukturę/ustawienia;
oba wcześniej skonfigurowane moduły mogą pozostać wyłączone bez kasowania
konfiguracji. Ponowne enabled=true zaczyna w observation. Przy wyłączonym CO
można przechowywać wyłączone strefy; ich ponowna aktywacja waliduje minimum CO.
Nie zamieniaj disabled modułu na brak jego zapisanej konfiguracji.

## Walidacja i współdzielenie

Dwa poziomy: struktura konfiguracji oraz bieżąca dostępność.
Brak bindingu, nieprawidłowa domena/UUID, zduplikowane zone_id/group_id,
pusta lista źródeł aktywnej strefy, obcy main_sensor, nieskończony/niezgodny
z krokiem cel i nieistniejąca grupa są błędami draft.
Walidacja liczb odrzuca bool, NaN i Infinity; schema_version=True nie jest
wersją 1. Żaden błąd nie klamruje celu do nowej wartości ani nie zapisuje połowy danych.

Poprawnie przypisana encja, która chwilowo nie raportuje/ma unavailable,
to niegotowość źródła, nie brak skonfigurowanego bindingu. Nie stosuj
testowego zapisu do number/switch ani błędu cannot_connect dla całej pompy.
Znane niepoprawne jednostki lub możliwości sygnalizuj konkretnie przy źródle;
nie prezentuj niedostępnej wartości jako 0 i nie wymagaj dodatkowej telemetrii D90.

D87 obowiązuje również dla już istniejących podstawowych wyjść CO/CWU:
nie przyjmuj tej samej nastawy number jako CO i CWU ani tego samego wyjścia
drugiej konfiguracji. Uwzględnij również zapisane nieaktywne wpisy.
Zapisy współbieżne nie mogą przejść check-then-act i utworzyć konfliktu.
Współdzielenie sensor jest dozwolone.
I02 obejmuje minimalną kontrolę konfliktów zapisanych entity_id przy finalizacji,
konieczną przed wystawieniem kreatora. Pełne wiązanie registry_id, rezerwacje
dla zaworów/demandu, aliasy i śledzenie rename encji pozostają I03.
Nie dodawaj globalnego single_instance jako obejścia konfliktów.

Po zmianie źródeł lista subskrypcji i rewizja konfiguracji muszą być aktualne.
Strefa zachowuje zone_id; źródła otrzymują nową rewizję zestawu. Nie ma jeszcze
historii/filtrów do odbudowy — nie dodawaj ich tylko dla pokazania B06.
Nie obliczaj w I02 komfortu/trendów; gotowość struktury i odczytów nie jest
gotowością przyszłych okien. Testy częściowej dostępności dotyczą tylko tej warstwy.

## Wersjonowanie i dane po I01

Zaplanuj realną migrację I01: ConfigEntry VERSION 1/MINOR 1 i schema_version=1
do rozszerzonego schematu 2 / ConfigEntry VERSION 2/MINOR 1.
Nowy parser ma mieć jeden kanoniczny format; stary payload jest wejściem
funkcji migracji, nie drugim stale aktualizowanym źródłem prawdy.

Przekształcenie: scalar temperature_entity_id → lista jednego termometru,
tryb źródła równoważny staremu; nazwy/grupy nowe opcjonalne, groups puste.
Nazwa instalacji zachowuje entry.title. Jeśli stara strefa nie miała nazwy,
pokaż neutralną lokalizowaną etykietę ze stabilnym skrótem UUID, nie zgaduj
pomieszczenia. Zachowaj installation/circuit/zone/dhw UUID, enabled, cele,
bindings i unique_id. Nie generuj nowych ID przy zwykłym setup/migracji.
Nie zmieniaj istniejących wartości na podstawie bieżących odczytów urządzeń.

Migruj i waliduj kopię całego payload przed async_update_entry. Błąd/nieznana
wersja odmawia bez pustego resetu i bez usług. Stare testy I01 dla nowszej
wersji mają sprawdzać nową VERSION+1, a nie uznawać wersję 2 za zawsze błędną.
Dodaj osobny test poprawnej migracji wpisu v1, nie usuwaj jego fixture.
Starszy kod I01 odmawia odczytu nowej wersji, zgodnie z D89.

Cel początkowy pozostaje bootstrap wartością ConfigEntry odziedziczoną po I01.
Nie dodawaj drugiej równoległej kopii w options/Store. Codzienna encja celu,
autorytatywny Store i przeniesienie tej wartości bez resetu są I04/I16.
Reconfigure I02 zachowuje podany cel; docelowe wydanie nadal realizuje D71.
Nie dodawaj planu CWU ze sztuczną temperaturą ani pełnych schematów Store na zapas.

Na minimum i current sprawdzono kontrakt publicznego
ConfigFlow.async_update_reload_and_abort(entry, data=...) w config_entries.py
(tag 2026.10.4 i 2026.11.1; odczyt 11 listopada 2026). Używaj pełnego
zwalidowanego data przy zastąpieniu, aby usunięte klucze nie wracały
po płytkim data_updates. Wersję wpisu aktualizuje migracja HA.
Nie zapisuj tych samych pól raz w data, raz w options. Wybór UI ConfigFlow
i natywnego reconfigure nie wymaga osobnego ekranu web produktu.

## PL/EN i testy

Wszystkie nowe kroki, opisy, błędy i abort reasons w strings.json oraz
translations/pl.json/en.json; spójne klucze i parametry. Nazwy użytkownika
nie są tłumaczone. Nie umieszczaj schema_version, UUID i szczegółów bootstrap
jako podstawowych pytań użytkownika.

| Test I02 | Scenariusz / D | Asercja |
| --- | --- | --- |
| Trzy pełne ścieżki user | A01/A02, B01/B02 | CO-only/CWU-only/oba tworzą wpis gotowy do setup; CWU-only nie pyta o CO; brak bindingu daje błąd właściwego pola |
| Wielostrefowość i grupy | A05, US01/15 | Dom lub wiele stref; grupa nie ma celu ani własnych źródeł, trzecia grupa/strefa bez zmiany kodu |
| Wiele termometrów | A09/A30 części, D19/D32/D46 | Tryb główny/lista i wspólna mean/median zapisane; główny musi należeć do listy; utrata części źródeł nie udaje utraty wszystkich |
| Cel | C08 część konfiguracji, D96 | 5 i 35 dozwolone, co 0,5; poza zakresem/bool/NaN/Infinity/krok odrzucone; brak domyślnego celu |
| Disabled/re-enable | B03, D74 | Stan zachowany; brak aktywnych stref odrzucony tylko przy enabled CO; ponowne włączenie observation |
| Nazwa/grupa/czujnik | B06 części, D85 | entry/installation/zone IDs nie zmieniają się; źródła przeładowane bez starych callbacków |
| Usunięcie i odtworzenie nazwy | B06, D85 | Nowy UUID, pozostałe UUID/cele zachowane |
| Anulowanie/błąd/równoczesna edycja | B10, D84 | Brak częściowego zapisu; wykryj zmianę rewizji wpisu podczas draft i nie nadpisuj nowszych danych |
| Konflikt podstawowych wyjść | B09 część, D87 | CO/CWU i dwa wpisy nie dzielą wyjścia, także przy współbieżnym finalnym zapisie; sensor wspólny dozwolony |
| Migracja i wersja nieobsługiwana | B05/B07 części, D72/D89 | V1 → V2 zachowuje dane i setup; błąd/nowsza wersja bez resetu i usług; stary scalar poprawnie przepisany |
| Granice CWU | C07 część, D94/D95 | Brak wymagania higieny/temperatury/planów; przypisania nie uruchamiają CWU |
| Obserwacja po każdej operacji | A08, B04 | Zero number.set_value/switch.turn_on/off przy create/edit/migrate/reload/unload i odczytach |
| PL/EN i manifest | D79/D101, C13 część | Kreator reklamowany dopiero z pełnymi ścieżkami i tłumaczeniami; domena i obie wersje HA zachowane |

To nowy plan testów, nie wykonane wyniki. Dotychczasowe 13 testów I01
muszą zachować intencję regresji; zmienia się wyłącznie asercja braku kreatora
oraz oczekiwane wersje zgodnie z nową funkcją. Nie utrzymuj stałej liczby 13
jako kryterium jakości; dodane przypadki mają rzeczywiście zostać zebrane.
Pełne A03/A04 (opcje wyjść), historia B08, kontrola poleceń, dashboard US02
i aktywne sterowanie nie są odbiorem tego pakietu.

## CI, DoD i przekazanie dalej

Wykonaj komendy ci.md, oba pip check i pełne tests/ha_tooling oraz
tests/integration na HA 2026.10.4 i 2026.11.1. Zachowaj aktualne instalatory
I00 i rozdzielone pluginy, blokadę sieci testów, quality i hassfest.
Wszystkie 7 jobów CI muszą przejść; żadnego skip/xfail w zastępstwie nowej funkcji.
Nie przebudowuj tooling ani nie podnoś HA/Python/deps jako porządków I02.

W PR pokaż: SHA kodu, porównanie do aktualnego main, mapowanie tabeli testów
na konkretne wyniki, PL/EN, migrację v1→v2, ryzyka i jawne ograniczenia.
Reviewer sprawdza atomiczność draft, tożsamość, migrację, granice I03/I04/I05
i brak usług; Tester odtwarza oba środowiska i wszystkie nowe przypadki.
Autor nazywa samokontrolę samokontrolą. Nie zamykaj całych US samym I02.

Wycofanie: nowy ConfigEntry VERSION=2 jest nieczytelny dla I01; downgrade
ma odmówić bez resetu. Po użyciu nowego formatu powrót wymaga zgodnej kopii HA
lub jawnie przygotowanej i przetestowanej migracji odwrotnej. Nie proponuj
samego revert kodu jako gwarantowanego zachowania już zmienionych danych.

Bez zaworów/demandu i ich wykonawcy, rezerwacji I03 poza minimum D87,
Store/Recordera/historii/filtrów/algorytmu, codziennych encji celów/trybów,
harmonogramu i frontendu, POC/importera, drugiego CO, prognoz i skroplin.
Następny odbiorca: Reviewer → Tester → Tech Lead / właściciel.
I03 nie rozpoczyna się automatycznie po I02. Nową lukę zgłoś Tech Leadowi
z rekomendacją; nie dodawaj własnych reguł produktu.
