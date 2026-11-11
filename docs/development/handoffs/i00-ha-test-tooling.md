# I00 — narzędzia testów HA i domknięcie T08

## Kontrakt przekazania

- Nadawca / odbiorca / data: Tech Lead → Developer, 11 listopada 2026.
- Repozytorium: marcin-bugala/ha-HeatPumpSteering.
- Zatwierdzona baza projektu: e27621281d119f802e263d427ef9b9d36f6a135e; PR #36 scalony przez właściciela.
  Dyspozycja właściciela przejścia do kroku 3: [zapis](README.md).
- Gałąź wykonania: chore/ha-test-matrix od aktualnego origin/main.
- Commit wyniku: Developer wpisuje rzeczywisty SHA swojego PR i wyniki.
  Nie używaj SHA niniejszej dokumentacji jako dowodu testów narzędzi.
- Refs #15, #23, #29; US08/US16/US20 w części narzędziowej, nie realizacja
  całych historii. D68/D71/D77/D80/D89/D101.
- Scenariusze: przygotowanie środowisk dla A02/A08, B01/B02/B04, C13.
  Smoke tests I00 nie są wykonaniem tych scenariuszy produktu.
- Projekt: [kontrakty HA](../../technical/ha-contracts.md),
  [cykl życia](../../technical/lifecycle.md), [CI](../ci.md).
- Zakres już upoważniony: przygotowanie narzędzi według przyjętej alternatywy T08,
  bez pytań o ponowne zatwierdzenie P12 i bez zmiany wersji HA.

## Problem i wynik

Plugin pytest-homeassistant-custom-component 0.13.375 przypina
homeassistant==2026.10.4. Przed kodem integracji potrzebujemy dwóch prawdziwych,
izolowanych środowisk zgodnych z HA 2026.10.4 i HA 2026.11.1.
Nie instalujemy nowego HA nad pluginem wymagającym innej wersji.
Nie oznaczamy current jako skipped i nie zmieniamy D101, aby dopasować testy.

Wybrana droga T08: minimum używa wydanego pluginu; dla current preferuj dokładnie
zgodne wydanie upstream, jeśli pojawi się przed rozpoczęciem pracy. W przeciwnym
razie przygotuj odtwarzalny pakiet fixtures wygenerowany z przypiętego Core,
z zgodną od początku metadanymi zależności. To narzędzia testowe, poza runtime
integracji. Nie wymagają chmury, źródeł POC ani instalacji HA użytkownika.

## Zweryfikowane wejście techniczne

Odczyt źródeł 11 listopada 2026; brak uruchomionych środowisk w tym przekazaniu.

| Źródło | Dokładne odniesienie | Ustalenie |
| --- | --- | --- |
| Core minimum | 2026.10.4 / 357cae5c598dfcd7a0ea7dc5b1facccd4ec6037b | Projekt wymaga Python >=3.14.2 |
| Core current | 2026.11.1 / d8a0dc698c8946b44e455d904000db563cfbf1ba | Projekt wymaga Python >=3.14.2 |
| Plugin wydany | 0.13.375 / f353decb02e28313f1aeeb316a71053f93c76abd | ha_version i requirements_test.txt wskazują 2026.10.4 |
| Plugin gałąź domyślna | master / a5d0326f2bff12642358a2296807c7dd8067cdbc | ha_version nadal 2026.10.4; nie jest kompatybilnym wydaniem current |
| Generator pluginu | generate_phacc/generate_phacc.py, ha.py, const.py z 0.13.375 | Bez parametryzacji wybiera najnowszy tag Core; tej ruchomej selekcji nie wolno użyć w naszym buildzie |

Źródła:
[plugin i generator](https://github.com/MatthewFlamm/pytest-homeassistant-custom-component/tree/f353decb02e28313f1aeeb316a71053f93c76abd),
[Core minimum](https://github.com/home-assistant/core/tree/357cae5c598dfcd7a0ea7dc5b1facccd4ec6037b),
[Core current](https://github.com/home-assistant/core/tree/d8a0dc698c8946b44e455d904000db563cfbf1ba).

## Do wykonania w tym PR

1. Przygotuj dwa rozłączne zestawy zależności testowych i dokładne wersje
   bezpośrednich zależności. Zapisz zgodność Python/HA/plugin i sposób instalacji.
   Zachowaj requirements-dev.txt dla lekkiego quality.
2. Dla minimum zachowaj publiczny plugin 0.13.375 z HA 2026.10.4.
   Dla current, jeśli nadal nie ma zgodnego wydania, przygotuj w tools/ha_test_tooling
   wersjonowane źródło/adaptację generatora i metadane pakietu fixtures.
   Buduj wheel lokalnie w CI; nie publikuj na PyPI i nie commituj binarnych wheeli.
   Nadaj odrębną wersję lokalną, np. 0.13.375+ha2026.11.1, z zależnością
   homeassistant==2026.11.1 w METADATA, a nie zmienionym HA po instalacji.
   Nazwa przykładowa nie jest istniejącą wersją upstream.
3. Pobieraj jawne commity z tabeli i sprawdzaj ich SHA; generator ma przyjmować
   konkretny katalog/commit Core, bez wyboru latest, pobierania wszystkich tagów
   i wykonywania ruchomego master/dev. Dostosowania przepisywania importów
   i fixtures zachowaj w małym audytowalnym diffie, bez przepisywania asercji HA.
   Nie uruchamiaj wprost upstream generatora, dopóki nie usuniesz jego selekcji
   najnowszego tagu i nie sprawdzisz efektów plikowych.
4. Dołącz licencje i pochodzenie generowanych plików: MIT narzędzia pluginu,
   Apache-2.0 kodu testów Core. Przypnij także narzędzia budowania i generowania;
   nie kopiuj starych wymagań generatora bez oceny zgodności.
5. Dodaj tests/ha_tooling/test_environment.py z rzeczywistym fixture hass,
   MockConfigEntry i enable_custom_integrations. Test potwierdza wersję HA,
   zgodność wersji fixtures, uruchomienie event loop oraz działanie atrap usług.
   Rejestruje syntetyczną usługę w domenie testu i sprawdza jej rezultat;
   nie korzysta z encji domu ani custom_components produktu.
   Fixture ma działać i zostać posprzątany, nie tylko dać się zaimportować.
6. Dodaj jawny job ha-tooling z obiema wersjami, działający już przed istnieniem
   integracji. Zbiorcza bramka ci wymaga jego sukcesu dla obu wierszy.
   Istniejące quality i warunkowe ha-tests/hassfest zachowują znaczenie.
   Żadnych pustych zestawów, continue-on-error, xfail ani skip całego current.
7. Uruchom pip check i smoke tests w obu środowiskach na Linux/WSL/CI.
   Zapisz wersje faktycznie zainstalowane, SHA źródeł i hash wheel current.
   Powtórz build z tych samych źródeł; wymagaj równoważnych metadanych i treści
   fixtures. Różne timestampy archiwum nie są same błędem semantycznej zgodności.
8. Zaktualizuj docs/development/ci.md i ha-contracts.md wynikiem dla swojego SHA,
   z kompletnymi komendami instalacji. Dopiero udane wyniki obu wierszy domykają T08.
   I01 musi móc użyć tych samych instalatorów bez ręcznych poprawek.

## Granice zakresu

Bez manifestu i plików custom_components, algorytmu, usług produktu, wyjść,
Store, Recordera produktu, config_flow i frontendu. To nie fikcyjna integracja
ani dowód działania regulatora. Nie zmieniaj check_repository.py tak, aby
słabszy test lub brak właściwych zależności przechodził jako test produktu.
W I01 dotychczasowe bramki manifestu, dokładnego pinu pluginu i realnych
tests/integration/test_*.py nadal obowiązują.

Nie przenoś wygenerowanego pluginu do zależności runtime. W runnerze może być
sieć do pobrania przypiętych źródeł/pakietów, nigdy dostęp do sieci domu.
Niedopasowane źródło lub uszkodzony build kończy job błędem, bez fallbacku
na inną wersję HA. Konflikt selekcji wersji nie jest decyzją produktową.

## Weryfikacja i mierzalny koniec

| Kontrola | Wymagany wynik |
| --- | --- |
| Ruff, format, 7+ testów bootstrap, lokalne linki, git diff --check | PASS według ci.md |
| pip check dla obu izolowanych środowisk | PASS, bez wymuszonego konfliktu zależności |
| Pytest smoke tests HA minimum/current | Zebrane i wykonane realne testy; oba PASS |
| Faktyczna wersja HA i fixtures | Dokładnie przyjęta para w każdym wierszu |
| Build i pochodzenie current | Jawne commity, metadane, hash, licencje i odtwarzalne treści |
| Pełny CI | quality, ha-tooling oba wiersze i ci PASS; ha-tests/hassfest pominięte wyłącznie dlatego, że nadal brak produktu |

Nie wpisuj PASS, dopóki nie istnieje wynik dla konkretnego SHA.
Przekazanie dokumentacyjne nie uruchomiło tych smoke testów.

## Migracje, wycofanie i odbiorca

Brak danych produktu i migracji domu. Wycofanie: revert narzędziowego PR
przez kolejny PR, przed rozpoczęciem zależnego I01; po I01 najpierw oceń zależności.
Nie usuwaj oryginalnych testów bootstrap i nie obniżaj istniejących bramek.

Odbiorca: Reviewer sprawdza zgodność metadanych, rzeczywiste źródło fixtures,
licencje, brak obejścia zależności i CI; Tester odtwarza oba środowiska z instrukcji.
Autor nazywa własne sprawdzenie samokontrolą. Tech Lead po wynikach i scaleniu
wpisuje commit I00 do przekazania I01; Developer nie uruchamia kolejnych pakietów
automatycznie i nie scala własnego PR.
