# Sprawdzenie i integracja I03

Rola: Tech Lead / Orchestrator. Data: 13 listopada 2026.
Wynik: I03 — własność wyjść i trwałe bindingi — jest odebrane i zintegrowane.
Odbiór dotyczy zakresu I03, nie całych US01/US09/US10/US15/US16 ani
działającego sterowania urządzeniami.

## Commity i źródła

- Implementacja podstawowa: [PR #42](https://github.com/marcin-bugala/ha-HeatPumpSteering/pull/42),
  head `9eeb6331`, merge `d530ee9cbc48ff3d8bcdb3e91fb52f6e9ce4cf8a`.
- Domknięcie luk odbioru: [PR #43](https://github.com/marcin-bugala/ha-HeatPumpSteering/pull/43),
  zaakceptowany head `1b452bd4990bb84a8db3cfef148705d88da36f44`, merge
  `74f326baa6eb6347672125f49ac9ec1929e6f345`.
- Porównanie zaakceptowanego head z merge commitem #43: jeden commit merge,
  zero zmienionych plików. Drzewo produktu jest zgodne z odebranym SHA.
- Kontrakt wejściowy: [przekazanie I03](i03-output-ownership.md), projekt
  techniczny [PR #36](https://github.com/marcin-bugala/ha-HeatPumpSteering/pull/36)
  i przyjęte D90–D101.

## Review, testy i CI

- [Raport Testera](https://github.com/marcin-bugala/ha-HeatPumpSteering/pull/43#issuecomment-6859172549)
  dla `1b452bd4990bb84a8db3cfef148705d88da36f44`: PASS.
- [Końcowy raport Reviewera](https://github.com/marcin-bugala/ha-HeatPumpSteering/pull/43#pullrequestreview-5894803008)
  dla tego samego SHA: ACCEPTED, bez blokujących uwag. GitHub pokazuje
  `COMMENTED`, ponieważ połączone konto jest autorem PR; treść pochodzi z osobnej
  roli i przebiegu review, nie jest formalnym self-approval konta GitHub.
- [CI końcowego head](https://github.com/marcin-bugala/ha-HeatPumpSteering/actions/runs/43464948987):
  wszystkie 7 jobów PASS.
- [CI merge commitu na main](https://github.com/marcin-bugala/ha-HeatPumpSteering/actions/runs/43477638876):
  wszystkie 7 jobów PASS: quality, hassfest, ha-tooling minimum/current,
  ha-tests minimum/current i zbiorczy ci.
- Na main oba joby `ha-tests` wykonały po 91 testów: HA 2026.10.4 —
  91 PASS; HA 2026.11.1 — 91 PASS i 5 znanych ostrzeżeń deprecacyjnych upstream.
  Bez skip/xfail. Testy blokowały sieć urządzeń.

Przed końcową akceptacją zachowano w historii nieudane przebiegi i uwagi review.
Poprawiono między innymi granicę rezerwacji CREATE_ENTRY, rollback błędu/anulowania,
czas życia tymczasowego guarda, separację instancji HA, listener registry oraz
brakujące przypadki D86/D87/D93/D101 i migracji.

## Co dostarcza I03

Schema ConfigEntry v3 ma trwałe `source_bindings` i `output_bindings`, UUID,
registry identity, `binding_revision` i `configuration_revision`. Własność wyjść
obejmuje również disabled/unloaded entry oraz krótkotrwałe rezerwacje finalizacji.
Rename zachowuje tożsamość, replacement jej nie przejmuje. Reconfigure pozostaje
atomowe w zakresie danych i rezerwacji, a jawne odłączenie stosuje ostrzeżenie D86.

Konfiguracja zaworów, demandu, NC/NO i polaryzacji nadal niczego nie przełącza.
Runtime pozostaje w observation. Nie dodano Store, Recordera, algorytmu, wykonawcy,
retry, encji produktu ani frontendu.

## Ograniczenia i następny zakres

Weryfikacja używa syntetycznego HA, rejestru encji i mocków usług. Nie wykonano
testu na instalacji referencyjnej ani fizycznego ruchu urządzeń. Nie jest to
blokada I03, lecz pozostaje ograniczeniem przyszłego odbioru wydania.

Reverse migration schema v3 nie powstała. Powrót do starszego I02 wymaga zgodnej
kopii HA; kod nie może resetować danych. Statusów całych US nie zmieniono.

Następny pakiet: [I04 — wersjonowany Store](i04-versioned-store.md), od main
`74f326baa6eb6347672125f49ac9ec1929e6f345`. I04 ma używać kanonicznych bindingów
schema v3 i nie może cofać modelu do stringów entity_id.

