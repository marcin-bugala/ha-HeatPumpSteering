# Przekazania Tech Lead → Developer

Aktualizacja: 22 listopada 2026.
Baza: [main 5f49b2e](https://github.com/marcin-bugala/ha-HeatPumpSteering/commit/5f49b2eebc9665f6f181cbbd78c8571d55bb28e5).
Właściciel scalił I04 w PR #45.
Projekt PR #36 oraz D90–D101 pozostają podstawą.

| Zakres | Dokument / rezultat |
| --- | --- |
| Odbiór I04 | [Dowody i ograniczenia](i04-verification.md): head c00c029, merge 5f49b2e, końcowy Tester/Reviewer i CI #98 |
| Aktualne przekazanie I05 | [Jakość źródeł](i05-source-quality.md): wartości, jednostki i raporty HA; bez historii i usług |
| Kontrakt I04 | [Wersjonowany Store](i04-versioned-store.md), wykonany w PR #45 |
| Odbiór I03 | [Dowody](i03-verification.md), PR #42/#43 |
| Kontrakt I03 | [Własność i bindingi](i03-output-ownership.md) |
| Odbiór I02 | [Dowody](i02-verification.md), PR #40 |
| Kontrakt I02 | [Kreator i model](i02-installation-model.md) |
| Odbiór I00/I01 | [Dowody](i00-i01-verification.md), PR #38 |
| Kontrakty I00/I01 | [Narzędzia](i00-ha-test-tooling.md), [fundament](i01-ha-foundation.md) |
| Kolejne pakiety | [Plan](../../technical/implementation-plan.md); I06 po odbiorze I05 |

To indeks dokumentów.
Statusy US pozostają wyłącznie w Issues.
Odbiór pakietu nie zamyka całej historii.

## Instrukcja dla Developera

Pracuj jako Developer repozytorium marcin-bugala/ha-HeatPumpSteering.
Przeczytaj AGENTS.md, opis roli, odbiór I04 i przekazanie I05.
Po zatwierdzeniu przekazania wykonaj wyłącznie I05 na feat/23-source-quality.
Użyj aktualnego main zawierającego 5f49b2e i zatwierdzone dokumenty.
Zapisz rzeczywisty SHA bazy.
Sprawdź jego CI i Issues #8/#23 z komentarzami.

Dodaj typowane odczyty, normalizację jednostek i jakość raportów HA.
Obsłuż jednakowe raporty oraz utratę świeżości bez nowego zdarzenia.
Zachowaj tożsamość bindingów i granice runtime I04.
Nie twórz historii, okien, poleceń, encji produktu ani frontendu.
Nie odczytuj poc i nie uruchamiaj urządzeń domu.

Przekaż konkretny SHA Reviewerowi, Testerowi i Tech Leadowi.
Ta sesja przygotowała dokumentację.
Nie rozpoczęła implementacji I05.
