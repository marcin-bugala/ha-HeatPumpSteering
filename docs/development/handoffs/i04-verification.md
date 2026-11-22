# Sprawdzenie i integracja I04

Rola: Tech Lead / Orchestrator. Data: 22 listopada 2026.
Wynik odbioru: gotowy do scalenia w zakresie I04.
Właściciel już scalił PR #45 o 19:33 czasu Europe/Warsaw.
Ta sesja nie wykonała merge ani implementacji.

## Kandydat i źródła

- Kontrakt: [I04](i04-versioned-store.md), przyjęty przez scalenie [PR #44](https://github.com/marcin-bugala/ha-HeatPumpSteering/pull/44).
- Projekt: [PR #36](https://github.com/marcin-bugala/ha-HeatPumpSteering/pull/36), merge `e27621281d119f802e263d427ef9b9d36f6a135e`.
- Plan: [implementation-plan.md](../../technical/implementation-plan.md).
- Implementacja: [PR #45](https://github.com/marcin-bugala/ha-HeatPumpSteering/pull/45), 16 plików, +1938/-74.
- Baza PR: `4bc949ef009f1bf547389ac2b9821d8e3c2581ee`.
- Oceniony head: `c00c029ee81bf8f8f23e3782436f78a1f3ffc782`.
- Testowy merge CI: `e610cb0fcf210a453a334770904bbabd384cce04`.
- Merge na main: `5f49b2eebc9665f6f181cbbd78c8571d55bb28e5`.
- Porównanie head→main: jeden commit merge i zero zmienionych plików.
- Porównanie testowego merge→merge na main również zwraca zero zmienionych plików.

Lokalny katalog był czysty na feat/15-versioned-store i ocenionym head.
Lokalny origin/main pozostawał na 4bc949e.
Zapis FETCH_HEAD był zablokowany przez uprawnienia katalogu Git.
Aktualny main i porównania sprawdzono przez GitHub.
Gałęzi poc nie odczytywano.

## Powiązanie dowodów z SHA

| Dowód | Wynik i zakres |
| --- | --- |
| [Developer, komentarz 7083612783](https://github.com/marcin-bugala/ha-HeatPumpSteering/pull/45#issuecomment-7083612783) | Samokontrola c00c029; pełne publiczne setup po unload/cancel |
| [Tester, komentarz 7083636891](https://github.com/marcin-bugala/ha-HeatPumpSteering/pull/45#issuecomment-7083636891) | PASS części I04 na c00c029; wcześniejsze wyniki zastąpione |
| [Niezależny Reviewer, review 6013759841](https://github.com/marcin-bugala/ha-HeatPumpSteering/pull/45#pullrequestreview-6013759841) | ACCEPTED dla c00c029; pełny diff od 4bc949e; brak blokujących uwag |
| [CI #98](https://github.com/marcin-bugala/ha-HeatPumpSteering/actions/runs/45054694193) | 7/7 jobów PASS; checkout e610cb0, złożony z właściwych head/base |
| Log ha-tests minimum, job 137307636368 | HA 2026.10.4: 139 PASS; bez skip/xfail |
| Log ha-tests current, job 137307636345 | HA 2026.11.1: 139 PASS; bez skip/xfail; 5 ostrzeżeń upstream |
| Pozostałe joby CI #98 | quality, hassfest, oba ha-tooling/pip check oraz agregat ci: PASS |
| Oddzielny push CI merge commitu main | Niepotwierdzony w tej sesji; nie przypisujemy mu wyniku CI #98 |

Reviewer działał w osobnej roli i przebiegu.
GitHub zapisuje jego wynik jako COMMENTED z konta autora.
To merytoryczna akceptacja niezależnego przebiegu, bez formalnego APPROVE GitHub.
Tech Lead nie zastępuje tego review własną akceptacją.
Lista inline review threads jest pusta.

Tester wykonał lokalne bramki na head.
Pełne wykonania HA pochodzą z Linux CI, nie z lokalnego Windows.
Ta sesja odczytała oba logi HA i wszystkie podsumowania jobów.
Pominięte alternatywne kroki instalacji minimum/current nie są pominiętymi testami HA.

## Kompletność kontraktu I04

Poniższa macierz opisuje odbiór pakietu, nie status całych US.

| Wymaganie / decyzja | Dowód i ocena |
| --- | --- |
| US02/#9; D25/D96; A07/C08 | Trwałe cele po zone_id; zakres 5–35°C co 0,5°C; reload czyta Store. PASS warstwy trwałości |
| US08/#15; D72/D89/D101; B07 | Schema v4, marker bootstrap, Store 1.1/payload v1; migracje v1/v2/v3→v4; odmowa future/foreign/malformed bez resetu. PASS |
| US19/#26; D71–D72 | Store przechowuje ustawienia; kolekcje przyszłej pamięci pozostają puste. Brak fikcyjnych pomiarów i nowej bazy. PASS części I04 |
| D24/D54/D74 | Niezależne tryby CO/CWU; restore po readiness; re-enable zaczyna observation. Zero usług. PASS |
| Settings revision | Wspólny lock; dwa zapisy tej samej rewizji bez utraty zmiany. Save poprzedza publikację runtime. Błąd/cancel zachowuje poprzedni snapshot. PASS |
| ConfigEntry/Store | Prepare→entry→finalize; crash przed/po update odzyskuje właściwą rewizję. Reconfigure i registry zatrzymują stary runtime. PASS |
| B06 | Rename/grupa/czujnik zachowują cel po UUID. Usunięcie i odtworzenie nazwy tworzy nową tożsamość. PASS części trwałości |
| A43/B05 | Syntetyczny pending i zapis/restart bez resetu. PASS wyłącznie granicy trwałości |
| Regresja I03 | Ownership, bindingi, migracje, registry, unload i brak usług pozostają pokryte. PASS |

Końcowy Tester i Reviewer potwierdzili usunięcie dwóch wcześniejszych P1.
Pierwszy P1 dotyczył publikacji udanego snapshotu do załadowanego runtime.
Drugi P1 dotyczył aktywnego runtime przy nieuzgodnionych rewizjach po awarii finalize.
Dodatkowe poprawki usunęły auto-reload po rzeczywistym unload/cancel.
Test końcowy przechodzi przez późniejszy publiczny setup.
Kończy ze zgodnymi rewizjami, pending=None i jednym zestawem listenerów.
Nie pozostawia osieroconych zadań ani usług.

## Ograniczenia i niewykonane przypadki

| Scenariusz | Pozostałe ograniczenie |
| --- | --- |
| A07/C08 | Bez encji number, UI, regulatora i resetowania przyszłych potwierdzeń temperatury |
| A43/B05 | Bez demandu, retry, nadpisania CWU i postępu potwierdzeń temperatury |
| B06 | Bez okien nowego źródła; należy do I06 |
| Corrupt JSON | Symulacja na publicznej granicy Store; bez destrukcyjnej edycji prawdziwego pliku .storage |
| Restart/crash | Syntetyczne HA i kontrolowane wyjątki/bariera; bez restartu serwera domu |
| Rollback | Bez rzeczywistego odtworzenia kopii HA i bez migracji odwrotnej |
| Sprzęt / wydanie | Bez instalacji referencyjnej, fizycznych przełączeń, frontendu, release i deploy |

Wszystkie testy produktu używają syntetycznego HA.
Sieć urządzeń pozostaje zablokowana.
Schema v4 i Store v1 są nieczytelne dla I03.
Sam revert kodu nie zapewnia bezpiecznego rollbacku.
Powrót wymaga zgodnej kopii HA albo osobno przetestowanej migracji odwrotnej.

## Decyzja i odbiorca

Nie stwierdzono otwartych poprawek blokujących I04.
Nie potrzeba ponownego przekazania Reviewera dla tego samego kodu.
Zmiana kodu unieważnia odbiór dotkniętych ścieżek.

Issues #9/#15/#26 odczytano razem z dyskusją.
Wszystkie pozostają otwarte, bez komentarzy i z istniejącym polem Status.
Nie zmieniono ich statusów ani checkboxów.
I04 nie realizuje wszystkich kryteriów tych historii.

Następny pakiet: [I05 — jakość źródeł](i05-source-quality.md).
Właściciel zatwierdza konkretne przekazanie przed zleceniem implementacji.
Developer potwierdza aktualny main i jego CI przed startem.
Następnie raportuje Reviewerowi, Testerowi i Tech Leadowi konkretny SHA.
