# I07 — decyzje stref bez wykonywania poleceń

Nadawca: Tech Lead / Orchestrator.
Odbiorca: Developer → Reviewer → Tester → Tech Lead / właściciel.
Data: 23 listopada 2026.
Repozytorium: marcin-bugala/ha-HeatPumpSteering.
Proponowana gałąź: `feat/12-zone-decisions`, PR do main.
Baza produktu przy przygotowaniu: `626c5b5a291029868aceafad42cee9aabf44b3cf`.
Developer zapisuje rzeczywisty aktualny main i końcowy SHA.

Właściciel zlecił implementację I07 z subagentami 26 listopada 2026.
Rzeczywista baza implementacji: `5fb7b0a036c527c19c347003a1368b1786090aa2`.
Tech Lead zwolnił warunek dowodowy I06 po zapisaniu niezależnych raportów.

## Warunek rozpoczęcia i źródła

Zatwierdzony projekt techniczny scalono w [PR #36](https://github.com/marcin-bugala/ha-HeatPumpSteering/pull/36), commit `e27621281d119f802e263d427ef9b9d36f6a135e`.
I04 i I06 znajdują się na main.
Niezależne raporty I06 uzupełniono zgodnie z [zapisem I06](i06-verification.md).
Zgłoś Tech Leadowi każdą usterkę blokującą I06.
Reviewer wydał ACCEPT, a Tester PASS w zakresie pakietu I06.

Przeczytaj AGENTS.md, [plan](../../technical/implementation-plan.md), [macierz](../../technical/verification.md), produkt, decyzje, US05/US06/US18 i rundy 3–6.
Sprawdź Issues [#12](https://github.com/marcin-bugala/ha-HeatPumpSteering/issues/12), [#13](https://github.com/marcin-bugala/ha-HeatPumpSteering/issues/13) i [#25](https://github.com/marcin-bugala/ha-HeatPumpSteering/issues/25) z komentarzami.
Sprawdź [workflow](../workflow.md), [standardy](../standards.md), [CI](../ci.md) i opis roli.
Stosuj przyjęte D35–D39, D46, D48, D55, D57–D59 oraz D96/D100 tam, gdzie dotyczą postępu i ostrzeżeń.
Nie przenoś do I07 zachowania fizycznych wyjść.

## Zakres

I07 dodaje czyste, typowane decyzje stref na podstawie okien I06, bieżącego pomiaru, celu i jawnego czasu.
Decyzja zawiera żądanie otwarcia, zamknięcia lub zachowania, przyczynę i gotowość danych.
Stan pamięci zawiera poprzednie wiarygodne żądanie, terminy blokad, postęp niedogrzania, utratę źródeł i zmianę zestawu źródeł.
Oddziel czyste obliczenia od odczytu HA, czasu, zapisu Store i przyszłego wykonawcy.
Integracja z runtime może publikować wynik decyzji wewnętrznie, bez usług urządzeń.
Nie twórz globalnego busa ani pustego frameworka przyszłych modułów.

| Reguła | Oczekiwanie |
| --- | --- |
| D35 / A10–A13 | Trend rosnący zamyka od celu; malejący otwiera do celu; niejasny używa progów ±0,2°C. Między progami zachowaj wiarygodne żądanie. |
| D58 / A14 | Bez poprzedniego żądania między progami zachowaj odczytany stan. Nie zgłaszaj demandu przed warunkiem otwarcia. |
| D36/D57 / A15 | Nagły spadek to bieżący pomiar ponad 0,7°C poniżej komfortowego. Otwarcie wymaga domyślnie 30 min poprawnych obserwacji utrzymanego niedogrzania. Ustąpienie zeruje postęp. |
| D36/D55 / A16 | Po zamknięciu obowiązuje domyślnie 30 min minimum. Obie blokady otwarcia biegną równolegle; obowiązuje późniejszy termin. |
| D46/D96 | Nowy cel i zmiana dostępnego zestawu termometrów nie tworzą fałszywego nagłego spadku. Zachowaj historię oraz niezależne terminy. |
| D48 / A31 | Po utracie wszystkich termometrów zachowaj żądanie 30 min. Następnie wyznacz awaryjne otwarcie bez własnego demandu. |
| D59 / A42 | Gotowe okno zaworów bez gotowego trendu używa progów niejasnego trendu i jawnej przyczyny. |
| D38 / A21 | Dla strefy bez wyjść wyznacz blokadę wzrostu CO przy ≥cel+0,5°C przez 60 min. Zwolnij przy ≤cel+0,2°C przez 30 min. Nie zmieniaj nastawy CO. |
| D39/D100 | Wyznacz ostrzeżenie nieskutecznego zamknięcia tylko z wiarygodnych warunków. Brak danych wstrzymuje ocenę i sam nie kasuje ostrzeżenia. |

Konfigurowalne progi i czasy strefy muszą przejść walidację zgodną z modelem.
D37 przekazuje priorytet i kwalifikację strefy do późniejszego I08.
I07 nie oblicza ważonego błędu E ani nastawy CO.
Pełny stan zaworu po fizycznym ruchu, potwierdzenie przekaźnika i czas pracy siłownika należą do I12.
I07 może użyć wiarygodnego stanu wejściowego.
Nie udawaj fizycznego potwierdzenia na podstawie żądania.

## Granice i awarie

Bez pomiaru nie naliczaj czasu potwierdzenia temperatury.
Wiarygodne blokady czasowe mogą upłynąć podczas przerwy.
Zmiana celu zeruje tylko zależny postęp temperatury.
Zmiana source_set_revision nie może wyglądać jak nagły spadek.
Po restarcie użyj wiarygodnego zapisanego stanu i dostępnej historii I04/I06.
Nie dopisuj brakujących próbek ani czasu potwierdzenia za przerwę.
Observation nie wysyła poleceń.
Unload i zmiana konfiguracji unieważniają zależną pracę runtime.

Poza zakresem pozostają: wywołania usług, przekaźniki, wykonawca, demand, fizyczne zawory, korekty CO, encje produktu, UI, CWU, prognozy i drugi CO.
Nie zmieniaj schematu ConfigEntry/Store bez osobnego uzasadnienia, migracji i testu rollbacku.
Nie używaj aktywnego sprzętu w testach.

## Odbiór

Testy mają pokazać A10–A16, A21, A31 i A42 na deterministycznym zegarze.
Sprawdź równość na progach, moment przed i po terminie, ustąpienie warunku oraz równoległość blokad.
Sprawdź pierwszy start, restart, nowy cel, utratę i powrót źródeł oraz zmianę source_set_revision.
Sprawdź wariant bez wyjść i blokadę wzrostu CO bez wysłania nastawy.
Sprawdź ostrzeżenie przy niepełnych danych i jego wiarygodne ustąpienie.
Test integracyjny przechodzi przez załadowany runtime z syntetycznymi encjami HA.
Każda ścieżka asertuje brak usług do urządzeń.
A21 jest w I07 tylko decyzją blokady; zastosowanie jej w CO należy do I09.
A31 nie wykonuje fizycznego otwarcia; I12/I13 odbiorą wykonanie.
D39/D100 pozostają częściowe do I12/I16.

Przed PR uruchom pełne komendy z [ci.md](../ci.md).
Oba środowiska HA, ha-tooling, pip check, hassfest i zbiorcze ci mają przejść dla końcowego SHA.
Zapisz liczby testów, skip/xfail, ostrzeżenia i zakres symulacji.
Reviewer ocenia diff, zegar, trwałość postępu, granice żądań i brak usług.
Tester niezależnie odtwarza scenariusze na obu wersjach HA.
Autor nazywa własną kontrolę samokontrolą.
Po poprawkach ponów dotknięte testy na nowym SHA.

Raport podaje bazę, head, US/D/A/B, wynik, braki i następnego odbiorcę.
Nie zmieniaj statusu pełnych US na Zakończone po samym I07.
Nie scalaj automatycznie, nie publikuj wydania i nie wdrażaj na produkcję.
