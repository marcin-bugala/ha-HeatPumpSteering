# Projekt techniczny do przeglądu

Rola: Tech Lead / Orchestrator. Data: 11 listopada 2026. Baza produktu:
`6891b473a646c3d9e0783edf6cd437eb27a9b758` (main, po PR #35).
To dokumentacyjna propozycja, nie zgoda na implementację ani wykonany odbiór.
Wiążące pozostają [wymagania v0.7](../requirements/README.md) i D01–D89
z jawnymi zastąpieniami. Nie zmieniono kryteriów ani statusów Issues.

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
| [Potwierdzenia](command-confirmation.md) | Co stanowi dowód i czego brakuje HiMitII |
| [Trwałość i historia](persistence.md) | Store, Recorder, okna, migracje i powrót |
| [Frontend](frontend.md) | Karta, CWU, edycja atomowa i PL/EN |
| [Weryfikacja](verification.md) | Każda US i każdy A/B: komponent, dane, awaria, test |
| [Plan i przekazania](implementation-plan.md) | Małe PR-y z zależnościami i DoR/DoD |
| [Decyzje do właściciela](open-decisions.md) | Pytania, rekomendacje i blokowane zakresy |

Propozycje techniczne (prefiks T) podlegają przeglądowi projektu. Pytania produktowe
(prefiks P) wymagają decyzji Marcina Bugały; nie są nowymi przyjętymi D.
Żadna proponowana wartość w tych dokumentach nie staje się domyślną przez sam PR.
Po odpowiedzi należy zaktualizować wymagania i powiązane Issues spójną zmianą.

Pierwsze kompletne wydanie nadal zawiera CO, strefy, opcjonalne zawory/demand i CWU,
kartę, panel oraz PL/EN; warianty samo CO / samo CWU / oba. Przyszłe dwa CO
mają miejsce w identyfikatorach, bez drugiego regulatora, prognoz, skroplin i importera.

Następny odbiorca: właściciel produktu i niezależny Reviewer. Autor wykona
samokontrolę, nie niezależne review. Pakiety Developera są warunkowe:
wymagają wskazania zatwierdzonego SHA projektu i rozstrzygnięcia ich zależnych pytań.
Wyniki kontroli dokumentacyjnego commitu będą w PR; A01–A59/B01–B13 pozostają planem.
