# Przekazania Tech Lead → Developer

Aktualizacja: 13 listopada 2026. Baza:
[main 74f326b](https://github.com/marcin-bugala/ha-HeatPumpSteering/commit/74f326baa6eb6347672125f49ac9ec1929e6f345),
po scaleniu domknięcia I03 w [PR #43](https://github.com/marcin-bugala/ha-HeatPumpSteering/pull/43).
Projekt PR #36 i D90–D101 pozostają podstawą. I00/I01 wykonano w PR #38,
I02 w PR #40, a I03 w PR #42 i #43.

Właściciel zlecił przygotowanie I04. Ta sesja przygotowuje dokumentację;
implementacja rozpoczyna się dopiero na osobne zlecenie.

| Zakres | Dokument / rezultat |
| --- | --- |
| Sprawdzenie I03 | [Dowody i ograniczenia](i03-verification.md): zaakceptowany 1b452bd, merge 74f326b, niezależne role Reviewer/Tester i CI main 7/7 po 91 testów HA |
| Aktualne przekazanie I04 | [Wersjonowany Store](i04-versioned-store.md), feat/15-versioned-store; cele/tryby i protokół rewizji, nadal bez usług |
| Kontrakt I03 | [Własność wyjść i trwałe bindingi](i03-output-ownership.md), wykonany w PR #42/#43; nie ponawiaj |
| Sprawdzenie I02 | [Dowody i ograniczenia](i02-verification.md): raport Reviewer/Tester dla 060c0f0, cztery rozwiązane P1, CI head/main po 53 testy HA |
| Kontrakt I02 | [Kreator i model](i02-installation-model.md), wykonany w PR #40; nie ponawiaj |
| Sprawdzenie I00/I01 | [Dowody](i00-i01-verification.md), baza 552ea42 i opis braku formalnego review |
| Pierwotne I00/I01 | [Narzędzia](i00-ha-test-tooling.md), [fundament](i01-ha-foundation.md); historia kontraktu |
| Kolejne pakiety | [Plan](../../technical/implementation-plan.md); I05 i dalsze po osobnym odbiorze/przekazaniu |

To indeks dokumentów, nie druga tablica statusów. Statusy US pozostają w Issues.
Końcowy review I03 został opublikowany jako COMMENTED z połączonego konta autora,
ale pochodzi z osobnej roli i przebiegu; nie stanowi formalnego self-approval GitHub.
Tester i CI dotyczą dokładnie końcowego SHA. Szczegóły są w raporcie I03.

## Instrukcja rozpoczęcia dla Developera

Pracuj jako Developer repozytorium marcin-bugala/ha-HeatPumpSteering.
Przeczytaj AGENTS.md, docs/development/roles/developer.md,
docs/development/handoffs/i03-verification.md i
docs/development/handoffs/i04-versioned-store.md.
Pobierz aktualny main zawierający 74f326baa6eb6347672125f49ac9ec1929e6f345
oraz zatwierdzone przekazanie I04. Sprawdź czystość i Issues #9/#15/#26 z komentarzami.
Wykonaj wyłącznie I04 na feat/15-versioned-store i przygotuj PR do main.
Dodaj Store v1, cele/tryby, walidację, bootstrap marker i protokół rewizji
ConfigEntry/Store. Zachowaj bindingi I03, UUID i observation bez usług.
Przetestuj oba środowiska HA, awarie zapisu, cancel, race oraz crash na granicach
prepare→ConfigEntry→finalize. Nie otwieraj ponownie P01–P12/T08.
Nie dodawaj Recordera, okien, wykonawcy, encji produktu ani frontendu. Nie korzystaj z poc,
nie wykonuj merge, wydania, deploy lub operacji na instalacji domu.
Raport z konkretnym SHA przekaż Reviewerowi → Testerowi → Tech Leadowi/właścicielowi.

W tej sesji nie rozpoczęto kodowania I04.
