# Przekazania Tech Lead → Developer

Aktualizacja: 23 listopada 2026.
Baza: [main 626c5b5](https://github.com/marcin-bugala/ha-HeatPumpSteering/commit/626c5b5a291029868aceafad42cee9aabf44b3cf).
Właściciel scalił I05 w PR #47 i I06 w PR #48.
Projekt PR #36 oraz D90–D101 pozostają podstawą.

| Zakres | Dokument / rezultat |
| --- | --- |
| Wykonany I06 | [Zapis i ograniczenia](i06-verification.md): head fcc61ac, merge 626c5b5, CI #113; brak dostępnego pełnego raportu review |
| Przygotowane I07 | [Decyzje stref](i07-zone-decisions.md): tylko decyzje; implementacja po uzupełnieniu dowodów I06 |
| Wykonany I05 | [Kontrakt jakości źródeł](i05-source-quality.md), PR #47 |
| Odbiór I04 | [Dowody i ograniczenia](i04-verification.md), PR #45 |
| Kontrakt I04 | [Wersjonowany Store](i04-versioned-store.md) |
| Odbiór I03 | [Dowody](i03-verification.md), PR #42/#43 |
| Kontrakt I03 | [Własność i bindingi](i03-output-ownership.md) |
| Odbiór I02 | [Dowody](i02-verification.md), PR #40 |
| Odbiór I00/I01 | [Dowody](i00-i01-verification.md), PR #38 |
| Kolejne pakiety | [Plan](../../technical/implementation-plan.md) |

To indeks dokumentów.
Statusy US pozostają wyłącznie w Issues.
Scalenie pakietu nie zamyka całej historii.

## Instrukcja dla Developera

Przeczytaj AGENTS.md, opis roli, zapis I06 i przekazanie I07.
Przed implementacją I07 uzyskaj audytowalny pełny wynik niezależnego review I06 i odrębny raport Testera.
Sprawdź aktualny main, jego CI oraz Issues #12/#13/#25 z komentarzami.
Po spełnieniu warunku użyj gałęzi `feat/12-zone-decisions` od aktualnego main.
Zapisz rzeczywisty SHA bazy i końcowy SHA.
Implementuj tylko czyste decyzje stref i testy określone w I07.
Nie czytaj poc i nie uruchamiaj urządzeń domu.
Przekaż końcowy SHA Reviewerowi, Testerowi i Tech Leadowi.
