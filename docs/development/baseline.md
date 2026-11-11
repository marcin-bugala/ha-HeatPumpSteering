# Ocena istniejącej bazy — 11 listopada 2026

Przegląd wykonano na `main`, commit `02ee6d337a2de1cb30fc0430621679130a72d3a0`.
[PR #33](https://github.com/marcin-bugala/ha-HeatPumpSteering/pull/33) jest scalony.
Wcześniejsza informacja o otwartym PR w lokalnym handoffie jest historyczna.

## Istniejące ustalenia

- README, MIT i podstawowy `.gitignore`; 11 plików w `docs/requirements/`.
- Dokumentacja v0.7: 21 US, D01–D89 (z jawnymi zastąpieniami), A01–A59 i B01–B13.
- Issues #3–#7 to obszary; US01–US19 to #8–#26, US20 #29, US21 #30.
  Odczytano ich opisy. Dyskusję konkretnego Issue trzeba odświeżyć przy jego realizacji.
- Obowiązuje słownik statusów i wyłączne pole `**Status:**` w Issue. Kopie kryteriów
  w Issues oraz ich historyczne linki do gałęzi nie zastępują aktualnego Git.
- [Roadmapa](../requirements/roadmap.md): P1 projekt techniczny przed P2 budową.
- Lokalny `handoff-projekt-techniczny.md` był dostępny i został odczytany. Jego
  przenośny zakres zadania zapisano w [briefie](technical-design-brief.md), bez
  uzależniania środowiska od ścieżki na komputerze autora.

## Braki przed tą zmianą

Brak AGENTS.md, ról, workflow, CI, konfiguracji lintera, kodu integracji, manifestu,
frontendu i wykonywalnych testów produktu. Nie ma ustalonej domeny ani minimum HA.
72 scenariusze są przyszłym odbiorem, nie wynikami wykonanych testów.

## Wnioski z analizy wymagań

| Obszar | Konsekwencja dla środowiska |
| --- | --- |
| US01/02/08/15, D71–D85 | Projekt tożsamości, Store/migracji i historii przed kodem |
| US03/07/09/10/16, D68–D74/D87 | Test braku poleceń, anulowania i właściciela wyjścia; bez testów na domu |
| US04/05/06/17/18/19/20 | Deterministyczny czas, obliczenia i niezależny dowód potwierdzenia |
| US11/12/13/14, D79–D82 | Projekt dostarczanego UI, PL/EN i testy edycji atomowej CWU |
| US21/F01/drugi CO | Zachować miejsce w projekcie, nie dodawać funkcji do pierwszego wydania |

Otwarte blokery: domena/minimum HA, kontrakty wejść i wyjść, niezależne potwierdzenia,
zmiany zewnętrzne CWU, ręczny demand, polaryzacja, inicjalizacja CWU/higiena,
schematy Store/Recorder i technologia frontendu. Tech Lead ma wskazać rekomendacje,
źródła i konsekwencje, a nie wybierać po cichu brakujące reguły produktu.

Zmiana dodaje środowisko i odnośnik w README. Nie przepisuje wymagań, statusów Issues,
nie ustala parametrów produktu i nie korzysta z gałęzi POC.
