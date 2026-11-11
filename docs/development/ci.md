# CI i lokalna weryfikacja

## Co działa teraz

`CI` uruchamia się na PR do `main`, push do gałęzi produktu i ręcznie. Bez filtrów
ścieżek, więc wymagany check nie znika przy zmianie samej dokumentacji.

| Job | Kontrola |
| --- | --- |
| quality | Ruff lint/format, testy bramek CI, lokalne cele linków Markdown i gotowość testów HA |
| ha-tests | Pytest z pluginem HA, automatycznie po pojawieniu się manifestu/kodu |
| hassfest | Walidacja struktury HA, automatycznie po pojawieniu się integracji |
| ci | Zbiorcza bramka: quality musi przejść; z integracją także oba zadania HA |

Obecnie `ha-tests` i `hassfest` są jawnie pomijane: nie ma jeszcze integracji.
Testy `tests/bootstrap` dotyczą narzędzi CI, nie regulacji pompy. Zielony wynik nie
oznacza realizacji US ani wykonania A/B. Kontrola Markdown sprawdza lokalne pliki,
nie kotwice, dostępność zewnętrznych stron ani semantyczną spójność wymagań.

## Uruchomienie lokalne

Python 3.13+ dla narzędzi; standardowe środowisko wirtualne. W PowerShell:

```powershell
python -m venv .venv
.venv/Scripts/python -m pip install -r requirements-dev.txt
.venv/Scripts/python -m ruff check .
.venv/Scripts/python -m ruff format --check .
.venv/Scripts/python -m unittest discover -s tests/bootstrap -v
.venv/Scripts/python tools/check_repository.py
git diff --check
```

Linux: zamiast `.venv/Scripts/python` użyj `.venv/bin/python`.
Kontrole wymagają tylko repo i danych syntetycznych, bez konfiguracji HA domu.

## Pierwszy PR implementacji — bramka HA

Nie tworzymy pustego manifestu ani fikcyjnego testu produktu w dokumentacyjnym etapie.
Gdy pojawi się `custom_components/**/*.py` lub `custom_components/*/manifest.json`,
`check_repository.py` wymaga jednego manifestu produktu, przypiętego
`pytest-homeassistant-custom-component` w `requirements-ha-test.txt` oraz plików
`tests/integration/test_*.py`. Kod bez manifestu nie omija kontroli. Pytest zwraca
błąd przy braku zebranych testów; nie dodawaj `continue-on-error`, `|| true` ani
akceptacji pustego zestawu. Nazwy plików nie dowodzą jakości testów — to ocenia Reviewer.

W tym samym PR:
1. Wybierz domenę, minimum HA i wersje testowe zgodnie z zatwierdzonym projektem.
2. Utwórz `requirements-ha-test.txt` z dokładną wersją pluginu HA dopasowaną do HA;
   przypnij też pozostałe bezpośrednie zależności testowe. Nie instaluj losowo
   `homeassistant==latest` obok pluginu, który wymaga innej wersji HA.
3. Zastąp pojedyncze środowisko `ha-tests` macierzą minimum HA i aktualnej wspieranej
   stabilnej wersji, jeśli są różne. Dla każdej dobierz plugin i Python na podstawie
   metadanych wydań. Obecne 3.14 to przygotowanie joba, nie deklaracja minimum produktu.
   Dostosuj też Ruff target-version do najstarszego wspieranego Pythona.
4. Dodaj testy HA konfiguracji/setup/unload i braku poleceń w obserwacji z fixture
   `enable_custom_integrations`; mockuj encje/usługi. Przy zmianie zachowania dodawaj
   testy algorytmu, czasu, awarii i migracji z mapowaniem A/B.
5. Uruchom na Linux/WSL lub CI: `python -m pip install -r requirements-ha-test.txt`
   i `python -m pytest tests/integration`. Testy HA mogą nie wspierać natywnego Windows.
6. Sprawdź działający hassfest dla rzeczywistego manifestu; konfigurację HACS i jej
   walidację dodaj wraz z metadanymi dystrybucji. Nie obchodź reguł dla custom integration.

Frontend jest jeszcze bez wybranej technologii. Pierwszy PR frontendu musi dodać
lint/build/test jego stosu do CI i zbiorczej bramki: PL/EN, edycja/odrzucenie/zapis
CWU, dostępność i komunikaty awarii. Obecne CI nie testuje przyszłej karty.

## Utrzymanie i granice

Akcje są przypięte do odczytanych SHA, Ruff do wersji. Oficjalna akcja hassfest
uruchamia aktualny obraz upstream `ghcr.io/home-assistant/hassfest`; SHA akcji nie
przypina obrazu. Wynik może zmienić się po aktualizacji walidatora. Przy pierwszej
integracji zapisz wersję/digest walidatora, jeśli potrzebna jest pełna odtwarzalność.
CI nie potwierdza fizycznego wykonania, poprawności hydrauliki ani bezpieczeństwa
konkretnej instalacji. Dowody sprzętowe i wydanie pozostają osobnymi etapami.

Nie włączamy ochrony `main` automatycznie. Po poprawnym przebiegu właściciel może
wskazać `quality` i `ci` jako wymagane kontrole zgodnie z [workflow](workflow.md).
