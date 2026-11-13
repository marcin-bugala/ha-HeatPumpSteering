# Projekt techniczny do przeglądu

Rola: Tech Lead / Orchestrator. Data: 11 listopada 2026. Baza produktu:
`6891b473a646c3d9e0783edf6cd437eb27a9b758` (main, po PR #35).
Projekt scalono w PR #36 jako e27621281d119f802e263d427ef9b9d36f6a135e.
Właściciel następnie zlecił krok 3; konkretne zakresy wykonania i warunki T08
są w [przekazaniach dla Developera](../development/handoffs/README.md).
To nie wynik odbioru produktu ani zgoda na dowolny zakres implementacji.
Wiążące są [wymagania](../requirements/README.md) i D01–D101 z jawnymi
zastąpieniami. Ustalenia P01–P12 właściciela zsynchronizowano z kryteriami;
statusy realizacji pozostają wyłącznie w Issues, bez ich zamykania.

Przeczytano AGENTS.md, rolę Tech Leada, brief, workflow, standardy, CI, produkt,
US01–US21 i rundy 1–6. Odczytano opisy i komentarze Issues #3–#26, #29, #30
(26 Issues wymagań; API zwróciło puste listy komentarzy). Starsze uwagi rund
w opisach Issues nie zastępują późniejszych D69–D89. POC nie odczytywano.

| Dokument | Cel przeglądu |
| --- | --- |
| [Architektura](architecture.md) | Granice i przepływ odpowiedzialności |
| [Model danych](data-model.md) | Tożsamość, dane i gotowość |
| [Kontrakty HA i źródła](ha-contracts.md) | Domena, wersje, encje, dowody API |
| [Cykl życia](lifecycle.md) | Czas, anulowanie, restart i błędy |
| [Potwierdzenia](command-confirmation.md) | Wstępne potwierdzenie i ponowny odczyt po 2 min |
| [Trwałość i historia](persistence.md) | Store, Recorder, okna, migracje i powrót |
| [Frontend](frontend.md) | Karta, CWU, edycja atomowa i PL/EN |
| [Weryfikacja](verification.md) | Każda US i każdy A/B: komponent, dane, awaria, test |
| [Plan i przekazania](implementation-plan.md) | Małe PR-y z zależnościami i DoR/DoD |
| [Rozstrzygnięcia właściciela](open-decisions.md) | Przyjęte P01–P12, D90–D101 i dalszy przegląd |

P01–P12 zostały rozstrzygnięte przez Marcina Bugałę i zapisane jako D90–D101.
Domena, minimum/macierz HA, platformy encji i Lit z P12 są przyjęte.
Pozostałe szczegóły techniczne T podlegają przeglądowi całego projektu;
T08 ma dowód rozwiązania w scalonym I00. Aktualna dyspozycja właściciela
i zakres I04 są w indeksie przekazań.

Pierwsze kompletne wydanie nadal zawiera CO, strefy, opcjonalne zawory/demand i CWU,
kartę, panel oraz PL/EN; warianty samo CO / samo CWU / oba. Przyszłe dwa CO
mają miejsce w identyfikatorach, bez drugiego regulatora, prognoz, skroplin i importera.

Następny odbiorca: Developer dla I04, następnie Reviewer/Tester i Tech Lead.
Autor wykonał samokontrolę, nie niezależne review; brak niezależnego review
PR #36 pozostaje jawny. I00/I01 scalono w PR #38; ich dowody i brak formalnego
review są w raporcie I00/I01.
P01–P12 nie są blokerami produktowymi.
Wyniki kontroli dokumentacyjnego commitu będą w PR; A01–A59/B01–B13 pozostają planem.

## Aktualne przekazanie po I03

[I04 — wersjonowany Store](../development/handoffs/i04-versioned-store.md)
ma bazę main 74f326b po PR #43. [Raport I03](../development/handoffs/i03-verification.md)
zawiera wynik Reviewera i Testera oraz po 91 testów obu HA na końcowym head
i main. I04 nadal nie uruchamia usług urządzeń; dodaje trwałość celów/trybów
i protokół rewizji. Starsze handoffy są historią, nie nowym zleceniem.
