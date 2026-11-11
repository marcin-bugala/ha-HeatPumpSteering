# Sprawdzenie scalonego I02

Rola: Tech Lead / Orchestrator. Data: 11 listopada 2026.
Wynik: I02 daje bazę do przekazania I03; poniższy odbiór dotyczy tylko
części konfiguracji i obserwacji, nie całych US ani działającego sterowania.
Bieżące polecenie właściciela zleca przygotowanie I03, bez kodowania.

## Commity i źródła

- [PR #40](https://github.com/marcin-bugala/ha-HeatPumpSteering/pull/40)
  scalony 11 listopada 2026, 19:10:20 czasu Warszawy.
- Końcowy head: `060c0f06b5936129089a91afde26c6b502b5c92c`.
- Main po merge: `3068903a802aec6853403daedfb69a3ef5faf907`.
- Drzewo head i main: `111ba02bfcb8a72a8d5892f736f4e72928dc7a16`.
- Kontrakt: [przekazanie I02](i02-installation-model.md), przyjęte w PR #39;
  projekt PR #36, D90–D101 pozostają wiążące.
- Sprawdzono modele, config_flow, migrację/setup/unload, tłumaczenia i testy.
  Odczytano Issues #8/#16/#17/#22/#23 i ich puste listy komentarzy.
  Nie zmieniono statusów, nie czytano gałęzi poc.

## Review i testy

[Raport Reviewer/Tester dla pierwszej wersji](https://github.com/marcin-bugala/ha-HeatPumpSteering/pull/40#pullrequestreview-5862935552)
wymagał zmian na `85eed4092e87f6c08f93f2b78eb99ef72c9534f0`.
[Raport ponownego odbioru](https://github.com/marcin-bugala/ha-HeatPumpSteering/pull/40#pullrequestreview-5863365691)
dla końcowego `060c0f0` podaje **akceptację, bez blokujących uwag**.

| Uwagi pierwszego review | Dowód w końcowym kodzie/testach |
| --- | --- |
| P1: błędy bindingów dopiero na końcu flow | Walidacja przy polach CO/CWU; parametryzowane testy domen i pustych/błędnych ID |
| P1: niejawny cel nowej strefy 21°C | Nowa strefa bez default; test formularza, zapisany cel nadal widoczny przy edycji |
| P1: obcy primary w aggregate | Walidacja przynależności także w modelu; primary→aggregate czyści primary; testy modelu/flow |
| P1: angielskie opcje i etykieta migracyjna | Natywne selektory i PL/EN; test kluczy oraz polskiej etykiety |
| Brakujące przypadki odbioru | Disabled/re-enable w observation, odtworzenie nazwy z nowym UUID, równoległe konfliktujące finalizacje |

Wszystkie cztery wątki liniowe mają `is_resolved=true`.
Raport roli Reviewer/Tester został opublikowany jako COMMENTED, z tego samego
połączonego konta co autor; nie ma formalnego APPROVED. Zapisujemy treść
i SHA raportu, nie wywodzimy niezależności osoby z konta ani z merge.
Bieżąca kontrola Tech Leada nie jest nowym niezależnym review lub odtworzeniem Testera.

[CI końcowego head](https://github.com/marcin-bugala/ha-HeatPumpSteering/actions/runs/43071707226):
wszystkie 7 jobów PASS: quality, hassfest, ha-tooling minimum/current,
ha-tests minimum/current i ci. Drugi przebieg head:
[43071697192](https://github.com/marcin-bugala/ha-HeatPumpSteering/actions/runs/43071697192).

Bezpośrednio odczytane logi jobów 130701882899 i 130701883038:
Linux/Python 3.14.10, HA 2026.10.4 i 2026.11.1, oba `pip check` PASS,
po 53 zebrane i zaliczone testy; bez skip/xfail. Current: 5 ostrzeżeń
deprecacyjnych upstream HA/backoff. Testy blokują sieć i rejestrują brak
usług urządzeń. Raport Reviewer/Tester podaje również PASS Ruff, 12 bootstrap,
check_repository, pip check dev i diff check; nie przedstawiamy tych cudzych
lokalnych wykonań jako własnych.

CI merge: [43075194676](https://github.com/marcin-bugala/ha-HeatPumpSteering/actions/runs/43075194676).
Wszystkie 7 jobów PASS. Bezpośredni odczyt logów 130713896283/130713896364
potwierdza oba pip check PASS i po 53 testy PASS (current: 5 ostrzeżeń).

## Co rzeczywiście dostarcza I02

User/reconfigure obsługuje CO-only/CWU-only/oba, nazwy/grupy, strefy
i listy termometrów, primary/aggregate oraz mean/median. ConfigEntry
VERSION=2/MINOR=1 i payload schema=2 mają migrację z I01, zachowującą
UUID, cele, enabled i bindingi. Cały draft jest walidowany przed zastąpieniem;
konflikt edycji nie nadpisuje nowszych danych. Reload usuwa stary runtime
i subskrypcje. Nadal wyłącznie observation.

Pokrycie jest częściowe: US01/02/09/15/16; A01/A02/A05/A09/A30,
B01/B02/B03/B06/B09/B10/B11 oraz C07/C08/C13 według tabeli I02.
Testy setup/unload wspierają A08/B04. Nie potwierdzają pełnych okien,
Store, algorytmu, fizycznych wyjść lub kompletnego UI.

## Granica przekazania I03

I02 blokuje duplikaty stringów entity_id dla trzech podstawowych wyjść,
skanuje zapisane entries i używa modułowego _FINALIZE_LOCK. Nie ma jeszcze
registry identity, pełnego rejestru właścicieli/setup guard, wyjść zaworów/demandu,
ostrzeżenia D86 ani protokołu aktywacji nowych bindingów.
To zakres [I03](i03-output-ownership.md), nie rzekomo wykonane testy I02.

Dodatkowa obserwacja Tech Leada: async_step_confirm sprawdza obecność user_input,
ale nie prawdziwość confirm. Samo wysłanie confirm=false może zatwierdzić draft.
I03 musi usunąć tę lukę w ramach jawnego potwierdzenia D86 i przetestować
false/cancel; nie wolno oprzeć ostrzeżenia na dotychczasowej bramce.
Nie wykonano nowego testu reprodukującego: jest to wniosek z odczytu kodu.

Nie znaleziono potrzeby nowej decyzji produktowej. Istniejące D84–D87,
D93 i D101 rozstrzygają zachowanie. Warianty techniczne i testy są w I03.
Następny odbiorca dokumentacji: właściciel/Reviewer; następnie Developer
na zakresie I03. Brak merge, implementacji, wydania i deploy w tej sesji.
