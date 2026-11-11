# Następne zadanie: projekt techniczny

Brief przenosi zakres odczytanego lokalnego `handoff-projekt-techniczny.md` do repo.
Aktualizacja stanu 11 listopada 2026: PR #33 jest scalony do `main`; wymagania v0.7
są dostępne bez korzystania z gałęzi roboczej rundy 6. Oryginalny dokument pozostaje
bez zmian na komputerze autora. Poniższy brief nie jest gotowym projektem ani zgodą
na rozpoczęcie kodowania integracji.

## Zlecenie dla Tech Leada

Przygotuj dokumentacyjny PR do `main` na osobnej gałęzi. Czytaj `docs/requirements/`
i aktualne Issues. Nie korzystaj z POC, nie implementuj integracji, nie scalaj PR.
Zachowaj wszystkie wiążące decyzje produktu, w tym D68–D89 i zakres pierwszego
kompletnego wydania z [roadmapy](../requirements/roadmap.md).

Proponowany układ wyników w przyszłym `docs/technical/` (do utworzenia przez Tech Leada):

| Dokument | Wymagana treść |
| --- | --- |
| architecture.md | Granice obliczeń, pomiarów, historii, korekt, ograniczeń, wykonania, CWU, diagnostyki i frontendu; zależności bez własnego frameworka |
| data-model.md | Pompa, obieg, strefa, grupa, źródło, wyjście, harmonogram, decyzja i polecenie; trwała tożsamość i miejsce na przyszłe dwa CO |
| ha-contracts.md | Domena, minimum HA i macierz wsparcia; platformy, jednostki, zakresy, krok, dostępność i identyfikatory wejść/wyjść |
| lifecycle.md | Oceny, zdarzenia, timery, blokady, ponowienia, restart/reload/unload i anulowanie starych działań |
| command-confirmation.md | Żądanie, optymistyczny raport i niezależny odczyt; dowody i ograniczenia integracji źródłowych |
| persistence.md | Konfiguracja, schematy Store, zapis/migracje/rollback; Recorder, pokrycie i luki, odbudowa okien 48 h oraz ograniczenia retencji |
| frontend.md | Technologia dostarczanej karty/paneli, zasoby, PL/EN, robocza edycja i atomowy zapis CWU |
| verification.md | Macierz US/D/A/B → komponent, dane, awaria i test; HA/frontend, migracje, symulacja i osobny odbiór sprzętowy |
| implementation-plan.md | Małe PR-y, zależności, Definition of Ready/Done i przekazania; prowadzą do pełnego wydania, nie samej obserwacji |
| open-decisions.md | Rekomendacja, alternatywy, konsekwencje i właściciel rozstrzygnięcia; odnośniki do wymagań |

## Pytania wymagające jawnego rozwiązania

Minimum HA, domena i testowana macierz nie są jeszcze ustalone. Nie traktuj wersji
Pythona narzędzi CI jako decyzji o wsparciu produktu. Sprawdź oficjalną dokumentację
i kod dla proponowanych wersji; zapisz datę oraz tag/commit źródła.

W szczególności rozstrzygnij: niezależne potwierdzenia integracji źródłowych,
rozpoznawanie zewnętrznych zmian CWU, ręczny demand, polaryzację wyjść, inicjalizację
CWU bez wcześniejszej nastawy i relację do higieny pompy. Uwzględnij także otwarte
pytania przy poszczególnych US, np. zakres celu strefy, jakość historii i ostrzeżenia.
Nie zamykaj ich domyślną wartością bez decyzji. Konflikty zachowania przedstaw
właścicielowi z rekomendacją; można kontynuować niezależne części dokumentacji.

## Warunek przekazania Developerowi

Każde wymaganie pierwszego wydania ma komponent, dane, zachowanie awaryjne i sposób
weryfikacji. Istnieje plan testów A01–A59/B01–B13 bez twierdzenia, że je wykonano.
Propozycje są odróżnione od przyjętych decyzji, blokery implementacji rozwiązane,
a właściciel przejrzał projekt. Dopiero wtedy Tech Lead wydaje konkretne przekazania
do małych PR-ów implementacyjnych.
