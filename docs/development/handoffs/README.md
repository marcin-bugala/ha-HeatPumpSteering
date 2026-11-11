# Przekazania Tech Lead → Developer

Aktualizacja: 11 listopada 2026. Baza:
[main 3068903](https://github.com/marcin-bugala/ha-HeatPumpSteering/commit/3068903a802aec6853403daedfb69a3ef5faf907),
po scaleniu I02 w [PR #40](https://github.com/marcin-bugala/ha-HeatPumpSteering/pull/40).
Projekt PR #36 i D90–D101 pozostają podstawą. I00/I01 wykonano w PR #38.

Właściciel zlecił sprawdzenie I02, review i testów oraz przygotowanie konkretnego
I03 dla Developera, bez kodowania. Ta sesja przygotowuje dokumentację;
implementacja rozpoczyna się dopiero na osobne zlecenie.

| Zakres | Dokument / rezultat |
| --- | --- |
| Sprawdzenie I02 | [Dowody i ograniczenia](i02-verification.md): raport Reviewer/Tester dla 060c0f0, cztery rozwiązane P1, CI head/main po 53 testy HA |
| Aktualne przekazanie I03 | [Własność wyjść i trwałe bindingi](i03-output-ownership.md), feat/16-output-ownership; nadal observation |
| Kontrakt I02 | [Kreator i model](i02-installation-model.md), wykonany w PR #40; nie ponawiaj |
| Sprawdzenie I00/I01 | [Dowody](i00-i01-verification.md), baza 552ea42 i opis braku formalnego review |
| Pierwotne I00/I01 | [Narzędzia](i00-ha-test-tooling.md), [fundament](i01-ha-foundation.md); historia kontraktu |
| Kolejne pakiety | [Plan](../../technical/implementation-plan.md); I04 i dalsze po osobnym odbiorze/przekazaniu |

To indeks dokumentów, nie druga tablica statusów. Statusy US pozostają w Issues.
Raport Reviewer/Tester dla I02 został opublikowany jako COMMENTED z konta autora;
podaje akceptację końcowego SHA, nie formalne APPROVED. Bieżąca kontrola Tech Leada
nie zastępuje niezależnego odtworzenia. Szczegóły są w raporcie I02.

## Instrukcja rozpoczęcia dla Developera

Pracuj jako Developer repozytorium marcin-bugala/ha-HeatPumpSteering.
Przeczytaj AGENTS.md, docs/development/roles/developer.md,
docs/development/handoffs/i02-verification.md i
docs/development/handoffs/i03-output-ownership.md.
Pobierz aktualny main zawierający 3068903a802aec6853403daedfb69a3ef5faf907
oraz zatwierdzone przekazanie I03. Sprawdź czystość i aktualne Issues z komentarzami.
Wykonaj wyłącznie I03 na feat/16-output-ownership i przygotuj PR do main.
Dodaj atomową własność, bindingi registry, migrację, obsługę rename i ostrzeżenia D86;
konfiguracja zaworów/demandu bez wykonania. Zachowaj UUID i observation bez usług.
Przetestuj oba istniejące środowiska HA, wyścigi, anulowanie i brak przejęcia
nowej encji o starej nazwie. Nie otwieraj ponownie P01–P12/T08.
Nie dodawaj Store, okien, wykonawcy ani frontendu. Nie korzystaj z poc,
nie wykonuj merge, wydania, deploy lub operacji na instalacji domu.
Raport z konkretnym SHA przekaż Reviewerowi → Testerowi → Tech Leadowi/właścicielowi.

W tej sesji nie rozpoczęto kodowania I03.
