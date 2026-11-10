# Runda 1 — model instalacji i stref

Uzgodniono z właścicielem produktu: 10 listopada 2026. Aktualizacja dokumentacji w [PR #27](https://github.com/marcin-bugala/ha-HeatPumpSteering/pull/27). Runda zakończona w zakresie modelu; nie jest to implementacja ani zamknięcie wszystkich user stories.

## Przyjęty model

1. Jeden wspólny obieg grzewczy i jedna nastawa temperatury wody PC dla wszystkich stref. Kilka niezależnych obiegów nie należy do pierwszej wersji.
2. Strefy niezależne: cały Dom albo nazwane kondygnacje/pomieszczenia. Każda aktywna strefa ma własny cel i minimum jeden termometr.
3. Grupy typu Parter służą tylko porządkowaniu prezentacji. Nie mają osobnej nastawy, wyjść ani dodatkowej wagi w regulacji; nie tworzymy nadrzędnych regulatorów.
4. Strefa może mieć jeden lub kilka termometrów. Można wybrać pomiar główny albo agregację średnią/medianą. Kolejność filtracji, dobór domyślny i częściowa niedostępność są na późniejsze rundy.
5. Każde wyjście zaworów należy tylko do jednej strefy. Strefa może mieć wiele wyjść; jedno wyjście może obsługiwać grupę pętli. Przypisanie tego samego wyjścia do drugiej strefy nie jest dozwolone.
6. NC/NO wybieramy osobno dla strefy sterującej zaworami. Typ jest wspólny dla wszystkich jej wyjść; inne strefy mogą mieć inny typ. W strefie bez wyjść nie wymagamy tego wyboru.
7. Opcjonalne pole „część pętli pozostaje otwarta” jest informacją o instalacji. Nie tworzy fikcyjnych wyjść i nie wymaga listy pętli, liczby siłowników ani wpisywania przepływów.
8. Sterowanie zaworami i demandem pozostaje niezależnie opcjonalne. Brak zaworów nie usuwa stref pomiarowych; bez demandu nie przełączamy ON/OFF ogrzewania.

## Minimalna konfiguracja i obserwacja

Wymagane już przy konfiguracji:
- wskazana encja nastawy temperatury PC;
- czujnik bieżącej temperatury zewnętrznej;
- minimum jedna aktywna strefa z termometrem i temperaturą zadaną.

Bez wskazania encji nastawy nie można zakończyć konfiguracji — nie dopuszczamy jej późniejszego dodawania dopiero przed aktywacją. W obserwacji odczytujemy aktualną nastawę i porównujemy z propozycją, bez wysyłania zmian. Późniejsza niedostępność wskazanej encji podlega osobnym wymaganiom awaryjnym.

## Przykład referencyjny

| Strefa | Cel początkowy | Typ | Wyjście | Otwarte pętle poza sterowaniem |
| --- | --- | --- | --- | --- |
| Parter | 21°C | NC | Jeden przekaźnik grupy 5 siłowników | Tak |
| Piętro | 22°C | NC | Jeden przekaźnik grupy 7 siłowników | Tak |

Alternatywa: Salon, Kuchnia i Łazienka jako odrębne strefy z osobnymi wyjściami, zebrane w grupie Parter. Wspólny przekaźnik kilku pętli należy do jednej sterowanej strefy, nie do kilku niezależnie sterowanych pokojów.

## Scenariusze modelu do przyszłych testów

| Przypadek | Oczekiwane zachowanie |
| --- | --- |
| Jedna strefa Dom, jeden termometr, bez zaworów i demandu | Konfiguracja dozwolona przy wskazanej nastawie PC, outdoor i celu |
| Kilka stref w grupie Parter | Osobne cele; grupa bez celu i dodatkowego udziału w regulatorze |
| Kilka termometrów strefy | Wybór głównego albo średniej/mediany; szczegółowy wynik określimy przy regulacji |
| Dwa wyjścia jednej strefy | Wspólna przynależność i typ NC/NO tej strefy |
| Próba użycia wyjścia także w drugiej strefie | Konfiguracja odrzuca współdzielenie i wskazuje konflikt |
| Strefy NC i NO w jednej instalacji | Dozwolone; każda używa własnego typu |
| Pętle częściowo otwarte na stałe | Możliwość zaznaczenia informacji bez rejestru przepływów |
| Brak wskazania nastawy PC, także w obserwacji | Nie można zakończyć konfiguracji |
| Zapis konfiguracji NC/NO lub trybu obserwacji | Sam zapis nie wysyła poleceń do wyjść |

To scenariusze do wdrożenia i weryfikacji w przyszłości, nie testy działającej integracji.

## Co pozostaje na kolejne rundy

- Codzienna obsługa, ustawianie celów, ręczne zmiany i dashboard.
- Agregacja/filtracja termometrów, konflikt stref, wagi i trendy.
- Histerezy, czasy ruchu, potwierdzenia wyjść, polaryzacja przekaźników i sekwencje demandu.
- Awaria/nieświeżość źródeł, restart i zachowanie urządzeń.
- Model encji/API, kompatybilność, migracja i wydania.

Powiązania: [US01](user-stories.md#us01), [US03](user-stories.md#us03), [US05](user-stories.md#us05), [US09](user-stories.md#us09), [US10](user-stories.md#us10), [US15](user-stories.md#us15), [US16](user-stories.md#us16). Decyzje D17–D23 w [rejestrze](decisions.md).
