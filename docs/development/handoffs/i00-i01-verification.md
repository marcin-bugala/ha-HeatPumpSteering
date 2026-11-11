# Weryfikacja wejścia do I02 — I00/I01

Rola: Tech Lead / Orchestrator. Data: 11 listopada 2026.
Sprawdzona baza main: [552ea427086786e3b3411d95ed0305dc35ba80c0](https://github.com/marcin-bugala/ha-HeatPumpSteering/commit/552ea427086786e3b3411d95ed0305dc35ba80c0).
Ten raport sprawdza źródła, opis i logi CI; nie jest niezależnym review ani
ponownym lokalnym uruchomieniem HA/sprzętu. Nie zmienia statusów US.

## Scalenie i identyfikatory

| Element | Dowód |
| --- | --- |
| Przekazania I00/I01 | PR #37, merge d6964581a573dd28fbaf548bc738c24c774b5b62 |
| Kod I00 | cce478e88a73dbca7578439acbad8083e2b279ab |
| Kod I01 po poprawkach | 9eff42fd634bb21b3ced096f153131a1a10b1edc |
| Końcowy head PR #38 | 40d5a4228b827bb1f68ce6581c45d422c05fe8dd |
| Merge I00/I01 | [PR #38](https://github.com/marcin-bugala/ha-HeatPumpSteering/pull/38), merge 552ea427086786e3b3411d95ed0305dc35ba80c0 |
| Odstępstwo od dwóch PR-ów | Opis PR #38 dokumentuje jawne polecenie właściciela wykonania I01 w tym samym PR po akceptacji I00 przez Testera w rozmowie |

Odczytano model, parser, lifecycle, manifest i minimalną platformę wersji
config_flow oraz testy setup/unload i fixtures. I01 nie reklamuje kreatora:
manifest nie zawiera config_flow=true; istniejąca klasa rejestruje VERSION=1,
MINOR_VERSION=1. To wejście do właściwego kreatora I02, nie gotowy formularz.

## Wyniki z GitHub Actions

| SHA / przebieg | Co odczytano | Wynik |
| --- | --- | --- |
| I00 cce478e / [43016249992](https://github.com/marcin-bugala/ha-HeatPumpSteering/actions/runs/43016249992) | Wyniki jobów ha-tooling minimum/current, quality i ci; opis odtworzenia w tools/ha_test_tooling/README.md | Wszystkie wymagane joby PASS; opis raportuje po 3 smoke tests; produkt wtedy nie istniał, ha-tests/hassfest skipped |
| Head 40d5a42 / [43023929564](https://github.com/marcin-bugala/ha-HeatPumpSteering/actions/runs/43023929564) | Joby oraz logi ha-tests minimum/current | quality, oba tooling, oba ha-tests, hassfest i ci PASS; pip check PASS; po 13 testów integracji PASS |
| Main 552ea42 / [43025762094](https://github.com/marcin-bugala/ha-HeatPumpSteering/actions/runs/43025762094) | Joby oraz logi ha-tests minimum/current po merge | Wszystkie 7 jobów PASS; pip check PASS; po 13 testów integracji PASS |

Logi obu wierszy head i main odczytano bezpośrednio. Środowisko Linux /
Python 3.14.10; minimum HA 2026.10.4 + plugin 0.13.375, current HA 2026.11.1 +
samodzielny pytest-homeassistant 0.0.0+ha2026.11.1 z przypiętego Core.
Current ma 5 ostrzeżeń deprecacyjnych upstream HA/backoff, bez xfail/skip
i bez wpływu na wynik. Nie są odbiorem sprzętowym.

T08 ma dowód zgodnych środowisk w scalonym kodzie. Nie zlecaj ponownie starego
generatora ani przebudowy alternatywy z pierwotnego handoffu I00.
Aktualna procedura: [narzędzia testowe](../../../tools/ha_test_tooling/README.md).
Nie instalować obu pluginów w tym samym środowisku.

## Review i granice dowodu

API PR #38 zwróciło: brak formalnych reviews, brak komentarzy Conversation,
brak komentarzy liniowych. Nie ma opublikowanego raportu niezależnego Reviewera
ani Testera dla końcowego SHA. Opis PR zawiera samokontrolę Developera
i informację o akceptacji I00 przez Testera w rozmowie — to różne źródła dowodu.
Nie twierdzimy, że brak review oznacza brak przeglądu poza GitHub.

Właściciel scalił PR #38 i w bieżącym zadaniu zlecił przygotowanie I02.
To jest podstawa kontynuowania, bez przedstawiania merge lub samokontroli
jako niezależnej recenzji. Kod I02 nadal przechodzi Reviewer → Tester → właściciel.

I01 pokrywa podstawę obserwacji, warianty CO/CWU, walidację struktury,
izolację gotowości między modułami, brak usług i sprzątanie listenera przy unload.
Nie kończy całych A02/A08/B01/B02/B04/C13 ani US03/08/16/20.
Brakuje kreatora, nazw/grup, wielu termometrów strefy, reconfigure i migracji
rozszerzonego modelu — są przedmiotem I02. Store, historia, wykonawca i aktywne
sterowanie pozostają późniejsze.

## Wniosek Tech Leada

Przygotowanie I02 ma wystarczającą bazę wykonawczą: oba pakiety są scalone,
CI działa na main, T08 nie jest już blokerem. Brak formalnego niezależnego
odbioru pozostaje jawną luką procesu; nie zmieniamy z tego powodu produktu
ani nie prosimy ponownie o przyjęte P01–P12.

[Konkretny kontrakt I02](i02-installation-model.md) określa zakres i testy.
Nie wykonano tu kodowania ani aktywacji urządzeń.
