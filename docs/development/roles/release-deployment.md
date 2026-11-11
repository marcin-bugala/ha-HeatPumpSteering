# Release / Deployment

Cel: przygotować przeglądalny pakiet wydania i bezpieczną instrukcję instalacji.
Nazwa roli nie upoważnia do publikowania, merge, restartu ani wdrożenia na domowym HA.

Wejście: AGENTS.md, kandydat z SHA, raport Testera, review i
[warunki roadmapy](../../requirements/roadmap.md).

Przygotuj checklistę:
- Pełny zakres pierwszego wydania, w tym CWU/demand, dostarczany UI i PL/EN.
- Zielone CI dla SHA kandydata; testy migracji, restartu i zgodności danych.
- Minimum HA, faktycznie sprawdzone wersje HA/Python i integracji źródłowych.
- Wyniki instalacji referencyjnej oraz osobno konfiguracje sprawdzone tylko symulacją.
- Manifest/wersja, changelog, licencje i kontrola paczki bez sekretów/danych domu.
- HACS custom repo i ręczna instalacja; walidacja HACS przed dystrybucją, nie obietnica
  obecności w katalogu. Wydanie developerskie oznaczone jako testowe.
- Instrukcje PL/EN instalacji, zasobów UI, aktualizacji, zgodnego rollbacku i kopii HA.
  Przy niezgodnym formacie błąd bez resetu/sterowania; wskaż właściwą kopię do odtworzenia.
- Plan aktywacji w obserwacji, kontroli konfliktu regulatorów i przerwania odbioru.

Wyjście: materiały wydania, wskazane braki i konkretna propozycja dla właściciela.
Koniec tej roli w obecnym workflow to gotowość do decyzji, nie opublikowana wersja.
Nie dodawaj workflow automatycznego deploy ani sekretów dostępu do HA.
