# Przekazania Tech Lead → Developer

Aktualizacja: 11 listopada 2026. Aktualna baza:
[main 552ea42](https://github.com/marcin-bugala/ha-HeatPumpSteering/commit/552ea427086786e3b3411d95ed0305dc35ba80c0),
po scaleniu I00/I01 w [PR #38](https://github.com/marcin-bugala/ha-HeatPumpSteering/pull/38).
Projekt i D90–D101 pochodzą z PR #36, pierwotne przekazania z PR #37.

Właściciel zlecił: „Jako Tech Lead sprawdź scalone I00 i I01, wyniki review
oraz testów. Przygotuj konkretne przekazanie I02 dla Developera, zgodnie
z planem implementacji. Nie rozpoczynaj kodowania”.
To podstawa aktualnego przekazania, bez automatycznego uruchamiania implementacji.

| Zakres | Dokument / rezultat |
| --- | --- |
| Sprawdzenie I00/I01 | [Dowody review/testów i ograniczenia](i00-i01-verification.md), baza 552ea42; oba środowiska HA i pełny CI PASS |
| Aktualne przekazanie I02 | [Kreator HA i model instalacji/stref](i02-installation-model.md), gałąź kodu feat/8-installation-model |
| Pierwotny kontrakt I00 | [Narzędzia testów HA](i00-ha-test-tooling.md); droga narzędziowa wykonana w PR #38 jest opisana w tools/ha_test_tooling/README.md |
| Pierwotny kontrakt I01 | [Fundament integracji](i01-ha-foundation.md); wykonany w tym samym PR po dyspozycji właściciela, nie ponawiaj go |
| Kolejne pakiety | [Plan implementacji](../../technical/implementation-plan.md); I03 dopiero po odbiorze I02 i osobnym przekazaniu |

To indeks dokumentów i zależności, nie druga tablica statusów US.
Statusy pozostają wyłącznie w Issues; I02 nie zamyka całych historii.

I00/I01 mają dowody CI na main. PR #38 nie ma formalnych reviews ani komentarzy;
opis raportuje samokontrolę i akceptację I00 przez Testera w rozmowie.
Nie nazywamy tego formalnym niezależnym review końcowego SHA.
Właściciel scalił PR i zlecił dalszy etap; kod I02 nadal wymaga review i testów.

## Instrukcja rozpoczęcia dla Developera

Pracuj jako Developer repozytorium marcin-bugala/ha-HeatPumpSteering.
Przeczytaj AGENTS.md, docs/development/roles/developer.md,
docs/development/handoffs/i00-i01-verification.md oraz
docs/development/handoffs/i02-installation-model.md. Bazą jest main
552ea427086786e3b3411d95ed0305dc35ba80c0 lub nowszy main zawierający ten commit.
Sprawdź gałąź, czystość katalogu i aktualne Issues z komentarzami.
Wykonaj wyłącznie I02 na feat/8-installation-model i przygotuj PR do main.
Zachowaj obserwację bez usług urządzeń, UUID i zgodną migrację danych I01.
Dodaj testy kreatora/reconfigure/modelu/migracji w obu istniejących środowiskach HA.
Nie otwieraj ponownie T08 ani P01–P12. Nie dodawaj aktywnego sterowania,
Store/historii/frontendu ani pełnej własności wyjść I03. Nie korzystaj z poc,
nie wykonuj merge, wydania, deploy lub operacji na instalacji domu.
Raport dla konkretnego SHA przekaż Reviewerowi → Testerowi → Tech Leadowi.

Niniejsze przekazanie jest dokumentacją. W tej sesji nie rozpoczęto kodowania I02.
