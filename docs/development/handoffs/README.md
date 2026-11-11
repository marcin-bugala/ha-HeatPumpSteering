# Przekazania Tech Lead → Developer

Data: 11 listopada 2026. Podstawa produktu i projektu:
[main e276212](https://github.com/marcin-bugala/ha-HeatPumpSteering/commit/e27621281d119f802e263d427ef9b9d36f6a135e),
po scaleniu [PR #36](https://github.com/marcin-bugala/ha-HeatPumpSteering/pull/36).

Właściciel po scaleniu polecił: „Zgodnie z docs/development/workflow.md Przejdźmy
do punktu 3. Planowanie i implementacja Jako Tech Lead przygotuj projekt dla
Developera”. Ta dyspozycja jest podstawą przejścia do planowania wykonania
zatwierdzonej bazy, a nie sam zielony wynik CI. Nie oznacza wydania/deploy.
P01–P12 / D90–D101 są przyjęte i nie wracają jako pytania produktowe.

Brak niezależnego review pozostaje jawny: PR #36 nie ma zgłoszonego review
GitHub; autor wykonał samokontrolę, właściciel scalił projekt i zlecił następny
etap. Nie przedstawiamy tego jako niezależnego zatwierdzenia przez agenta.
Przegląd kodu każdego pakietu pozostaje osobnym krokiem workflow.

| Kolejność | Zlecenie | Co Developer dostarcza | Warunek następnego zakresu |
| --- | --- | --- | --- |
| 1 | [I00 — macierz testowa HA / T08](i00-ha-test-tooling.md) | Mały PR narzędziowy: zgodne, przypięte środowiska HA 2026.10.4 i 2026.11.1 z rzeczywistymi fixtures i dowodami smoke testów | Oba środowiska działają, Reviewer sprawdził źródła/metadata/licencje, właściciel scalił PR |
| 2 | [I01 — fundament integracji](i01-ha-foundation.md) | Osobny PR pierwszego kodu produktu: prawdziwy setup/unload ConfigEntry, niezależne moduły w obserwacji, testy HA i hassfest | Aktualny main po I00, konkretne SHA i wyniki T08 wpisane w przekazaniu |
| 3 | I02 z [planu](../../technical/implementation-plan.md) | Tech Lead po odbiorze I01 wydaje osobne zlecenie config_flow i modelu instalacji/stref | Nie rozpoczynać automatycznie po I01 |

To kolejność i zależności, nie druga tablica statusów US. Statusy pozostają
w Issues. I00 jest wydzieleniem technicznej zależności zatwierdzonego I01;
nie tworzy nowej funkcji produktu i nie podnosi minimum HA.

Developer zaczyna od I00. I01 jest konkretnym przygotowanym kontraktem, ale
jego kod wolno rozpocząć dopiero po spełnieniu opisanej zależności T08.
Ten PR zawiera wyłącznie dokumentację, nie implementację narzędzi ani integracji.

## Instrukcja rozpoczęcia dla Developera

Pracuj jako Developer repozytorium marcin-bugala/ha-HeatPumpSteering. Przeczytaj
AGENTS.md, docs/development/roles/developer.md i
docs/development/handoffs/i00-ha-test-tooling.md. Zweryfikuj aktualny origin/main,
czystość katalogu i powiązane Issues z komentarzami. Wykonaj wyłącznie I00
na osobnej gałęzi chore/ha-test-matrix i przygotuj PR do main z dowodami dla
konkretnego SHA. Nie dodawaj kodu custom_components ani nie rozpoczynaj I01.
Nie obchodź zależności pluginu/HA i bramek CI. Nie korzystaj z poc, nie wykonuj
merge, wydania, deploy ani operacji na instalacji domu. Wynik przekaż Reviewerowi
i Tech Leadowi według szablonu repozytorium.
