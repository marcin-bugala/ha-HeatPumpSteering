# Wymagania HA HeatPumpSteering

Wersja dokumentacji 0.7 z 11 listopada 2026 obejmuje rundy 1–6, scenariusze odbioru oraz decyzje architektury i wydań. Aktualizacja PR #36 dodaje przyjęte D90–D101 (rozstrzygnięcia P01–P12) i scenariusze C01–C13; cały projekt techniczny pozostaje do przeglądu. To baza do wspólnego dopracowania, nie zamknięta specyfikacja implementacji ani wydanie oprogramowania.

## Dokumenty

| Dokument | Zawartość |
| --- | --- |
| [Produkt](product.md) | Cel, konfiguracja, moduły, wejścia/wyjścia, ograniczenia |
| [User stories](user-stories.md) | US01–US21, kryteria akceptacji, zależności i pytania |
| [Decyzje](decisions.md) | Ustalenia przyjęte, propozycje i kwestie nierozstrzygnięte |
| [Etapy](roadmap.md) | Zakres wydań, testy, migracja i bramki aktywacji |
| [Runda 1](round-01-installation-zones.md) | Uzgodniony model instalacji i stref oraz scenariusze konfiguracji |
| [Runda 2](round-02-daily-operation.md) | Cele CO, tryby CO/CWU, nadpisania i wspólny zapis ustawień CWU |
| [Runda 3](round-03-regulation.md) | Pomiary, progi, korekty, demand, ostrzeżenia i modularność. Prognozy odłożone. |
| [Runda 4](round-04-failures-restarts.md) | Braki danych, zapisy, ponowienia, odtwarzanie historii, timery i CWU po restarcie |
| [Runda 5](round-05-acceptance.md) | Potwierdzanie zapisów, panel i nadpisania CWU, zmiana czasu, czas pracy siłowników oraz scenariusze A01–A59 |

| [Runda 6](round-06-architecture.md) | Niezależne CO/CWU, trwałość danych, cykl życia, interfejs, diagnostyka i kompletne wydanie developerskie |

## Źródło prawdy i sposób pracy

1. Nowe potrzeby zapisujemy jako Issue; historia otrzymuje stabilny identyfikator US. Nie zmieniamy numeracji istniejących historii.
2. Treść wymagania i kryteria akceptacji wersjonujemy w Git. Issue przechowuje dyskusję, status, zależności i dowody odbioru. Kryteria w opisie Issue są migawką do dyskusji; przy zmianach aktualizujemy je razem ze specyfikacją.
3. Status prowadzimy wyłącznie w polu `**Status:**` opisu Issue. Nie kopiujemy go do poniższego indeksu. Otwarty/zamknięty stan GitHub nie zastępuje statusu procesu.
4. Dokumenty zmieniamy na osobnej gałęzi i przez PR do `main`. W opisie PR wskazujemy powiązane Issues; samo scalenie dokumentacji nie zamyka historii funkcji.
5. Przyjęte decyzje oznaczamy osobno od proponowanych parametrów. Nie utożsamiamy zatwierdzenia kierunku z gotowością wszystkich kryteriów do implementacji.

Nie wymagamy niestandardowych etykiet ani GitHub Projects. Tablicę Projects można później dołączyć do tych samych Issues, po ustaleniu synchronizacji statusu. Nie utworzono jej w tej bazie wymagań.

## Statusy

| Status | Warunek |
| --- | --- |
| Do doprecyzowania | Są pytania dotyczące zachowania, zakresu lub odbioru |
| Uzgodnione | Właściciel produktu potwierdził treść i kryteria; kluczowe pytania rozstrzygnięto |
| Zaplanowane | Wymaganie przypisano do konkretnego etapu i rozwiązano zależności potrzebne do realizacji |
| W realizacji | Rozpoczęto implementację z odnośnikiem do gałęzi/PR |
| Do weryfikacji | Implementacja i odpowiednie testy są gotowe do odbioru |
| Zakończone | Kryteria spełnione, wynik weryfikacji zapisany i zmiana zintegrowana |
| Odłożone | Świadomie poza aktualnym etapem; zapisany powód i warunek powrotu |
| Odrzucone | Świadomie zrezygnowano; zapisany powód |

Przy utworzeniu bazy wszystkie historie i obszary były do doprecyzowania. Po kolejnych rundach aktualizujemy statusy w Issues; zakończenie rundy modelu nie oznacza ukończenia funkcji ani wszystkich kryteriów powiązanych historii. Odłożone Issue może pozostać otwarte; odrzucone zamykamy z uzasadnieniem. Wznowienie prac wymaga aktualizacji pola statusu.

## Obszary funkcjonalne

| ID | Obszar | GitHub |
| --- | --- | --- |
| E01 | Regulator CO1, obserwacja i niezawodność | [#3](https://github.com/marcin-bugala/ha-HeatPumpSteering/issues/3) |
| E02 | Strefy, siłowniki i opcjonalny demand | [#4](https://github.com/marcin-bugala/ha-HeatPumpSteering/issues/4) |
| E03 | CWU i harmonogram tygodniowy | [#5](https://github.com/marcin-bugala/ha-HeatPumpSteering/issues/5) |
| E04 | Źródła danych, prognozy i wagi | [#6](https://github.com/marcin-bugala/ha-HeatPumpSteering/issues/6) |
| E05 | Ogrzewanie odpływu skroplin — późniejszy etap | [#7](https://github.com/marcin-bugala/ha-HeatPumpSteering/issues/7) |

## Indeks historii

| ID | Historia | Obszar | GitHub |
| --- | --- | --- | --- |
| [US01](user-stories.md#us01) | Dodawanie i konfiguracja stref | E02 | [#8](https://github.com/marcin-bugala/ha-HeatPumpSteering/issues/8) |
| [US02](user-stories.md#us02) | Nastawa komfortu i pamięć ustawień | E02 | [#9](https://github.com/marcin-bugala/ha-HeatPumpSteering/issues/9) |
| [US03](user-stories.md#us03) | Obserwacja decyzji i świadome włączenie sterowania | E01 | [#10](https://github.com/marcin-bugala/ha-HeatPumpSteering/issues/10) |
| [US04](user-stories.md#us04) | Wyjaśnianie decyzji regulatora | E01 | [#11](https://github.com/marcin-bugala/ha-HeatPumpSteering/issues/11) |
| [US05](user-stories.md#us05) | Niezależne ograniczanie grzania przegrzanej strefy | E02 | [#12](https://github.com/marcin-bugala/ha-HeatPumpSteering/issues/12) |
| [US06](user-stories.md#us06) | Odporność na wietrzenie i krótkie zyski ciepła | E01 | [#13](https://github.com/marcin-bugala/ha-HeatPumpSteering/issues/13) |
| [US07](user-stories.md#us07) | Sterowanie ręczne i oddawanie kontroli | E01 | [#14](https://github.com/marcin-bugala/ha-HeatPumpSteering/issues/14) |
| [US08](user-stories.md#us08) | Aktualizacje, trwałość danych i możliwość wycofania | E01 | [#15](https://github.com/marcin-bugala/ha-HeatPumpSteering/issues/15) |
| [US09](user-stories.md#us09) | Niezależny wybór sterowania strefami i demandem | E02 | [#16](https://github.com/marcin-bugala/ha-HeatPumpSteering/issues/16) |
| [US10](user-stories.md#us10) | Konfiguracja siłowników NC i NO | E02 | [#17](https://github.com/marcin-bugala/ha-HeatPumpSteering/issues/17) |
| [US11](user-stories.md#us11) | Dashboard temperatur i celów stref | E02 | [#18](https://github.com/marcin-bugala/ha-HeatPumpSteering/issues/18) |
| [US12](user-stories.md#us12) | Dashboard zaworów, pompy, mocy i energii | E01 | [#19](https://github.com/marcin-bugala/ha-HeatPumpSteering/issues/19) |
| [US13](user-stories.md#us13) | CWU stale lub według harmonogramu | E03 | [#20](https://github.com/marcin-bugala/ha-HeatPumpSteering/issues/20) |
| [US14](user-stories.md#us14) | Tygodniowy harmonogram CWU co 30 minut | E03 | [#21](https://github.com/marcin-bugala/ha-HeatPumpSteering/issues/21) |
| [US15](user-stories.md#us15) | Dom, kondygnacje lub pomieszczenia jako strefy | E02 | [#22](https://github.com/marcin-bugala/ha-HeatPumpSteering/issues/22) |
| [US16](user-stories.md#us16) | Wybór wymaganych i opcjonalnych źródeł | E04 | [#23](https://github.com/marcin-bugala/ha-HeatPumpSteering/issues/23) |
| [US17](user-stories.md#us17) | Konfigurowalna krzywa grzewcza A, B i Tref | E01 | [#24](https://github.com/marcin-bugala/ha-HeatPumpSteering/issues/24) |
| [US18](user-stories.md#us18) | Priorytety stref i ważony komfort | E04 | [#25](https://github.com/marcin-bugala/ha-HeatPumpSteering/issues/25) |
| [US19](user-stories.md#us19) | Przeniesienie doświadczeń POC do produktu | E01 | [#26](https://github.com/marcin-bugala/ha-HeatPumpSteering/issues/26) |
| [US20](user-stories.md#us20) | Modułowy regulator i wybór aktywnych korekt | E01 | [#29](https://github.com/marcin-bugala/ha-HeatPumpSteering/issues/29) |
| [US21](user-stories.md#us21) | Prognozy pogody, nasłonecznienia i PV — przyszła wersja | E04 | [#30](https://github.com/marcin-bugala/ha-HeatPumpSteering/issues/30) |

US02 i US11, US01 i US15 oraz US06 i US19 częściowo się uzupełniają. Zachowujemy identyfikatory, a odpowiedzialność rozdzielamy w opisach. Zależności w tej fazie są powiązaniami wymagań, nie ścisłą kolejnością implementacji.

## Źródła i granice

- Ustalenia właściciela produktu w rozmowach projektu, skonsolidowane do 11 listopada 2026.
- [README POC](https://github.com/marcin-bugala/ha-HeatPumpSteering/blob/poc/co1-automation/README.md) i [projekt prognoz](https://github.com/marcin-bugala/ha-HeatPumpSteering/blob/poc/co1-automation/docs/full-integration-forecast.md).
- Przegląd źródeł POC: commit `44efb4e39acb888eb3368ce46b735cd37c6f3b72`. Dalszy rozwój POC nie zmienia automatycznie specyfikacji produktu.
- [Konfiguracja UI HA](https://contributors.home-assistant.io/core/integrations/config-flow/) i [wymagania publikacji HACS](https://www.hacs.xyz/docs/publish/integration/).

Dokumentacja nie potwierdza aktualnego montażu urządzeń, parametrów hydraulicznych ani wersji działającego HA. Nie zawiera danych dostępowych ani prywatnej konfiguracji serwera.



## Zakres po rundzie 3

Prognozy zachowujemy w US21 ze statusem prowadzonym w Issue (Odłożone przy tej decyzji); w bieżącym programie nie są aktywne. US20 wymaga modularności korekt od początku. Pole o stale otwartych pętlach z rundy 1 zostało zastąpione ostrzeżeniem hydraulicznym. Starsze zapisy rund są historyczne, z odnośnikiem do aktualnych reguł.
