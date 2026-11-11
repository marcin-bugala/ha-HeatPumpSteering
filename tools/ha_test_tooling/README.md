# I00: izolowane środowiska fixtures HA

Narzędzia wyłącznie developerskie, poza runtime integracji. Zlecenie:
[I00](../../docs/development/handoffs/i00-ha-test-tooling.md), baza projektu
e276212, baza wykonania d696458 (PR #37). Refs #15/#23/#29;
US08/US16/US20, D68/D71/D77/D80/D89/D101. Przygotowanie
A02/A08/B01/B02/B04/C13; nie wykonanie odbioru produktu.

| Środowisko | HA | Fixtures | Python |
| --- | --- | --- | --- |
| minimum | 2026.10.4 | pytest-homeassistant-custom-component 0.13.375 | 3.14 >=3.14.2 |
| current | 2026.11.1 | lokalny pytest-homeassistant 0.0.0+ha2026.11.1 | 3.14 >=3.14.2 |

Każdy wiersz wymaga osobnego venv. Nie instalować obu pluginów razem.
Aktualny publiczny plugin 0.13.375 nadal przypina HA 2026.10.4
([metadane PyPI](https://pypi.org/pypi/pytest-homeassistant-custom-component/0.13.375/json)).

## Źródło current i różnica wobec wstępnej drogi T08

Odczyt i build 11 listopada 2026 ujawniły, że przypięty Core już zawiera
samodzielny pakiet w
[packages/pytest-homeassistant](https://github.com/home-assistant/core/tree/d8a0dc698c8946b44e455d904000db563cfbf1ba/packages/pytest-homeassistant).
Stary generator 0.13.375 oczekuje tests/common.py i pełnego tests/conftest.py;
w tym Core helpers/fixtures przeniesiono do samodzielnego pakietu. Nie wykonujemy
starego generatora ani nie kopiujemy fixtures z poprzedniego HA.

build.py pobiera dokładnie d8a0dc698c8946b44e455d904000db563cfbf1ba i sprawdza
HEAD oraz czystość źródła. Sparse checkout ogranicza pobierane pliki. Kopiuje pakiet
do dwóch świeżych katalogów. Zmienia wyłącznie version i zależność homeassistant
w pyproject.toml. Oryginalne Python, importy, fixtures i asercje pozostają bez zmian.
Nie ma adaptacji generatora MIT: current korzysta wyłącznie z kodu Core Apache-2.0.
Licencja Core trafia do wheel i jest sprawdzana bajtowo, tak jak wszystkie pliki .py.
Minimum zachowuje licencje MIT pluginu i Apache-2.0 jego kopii testów Core.

Build wymaga przypiętych narzędzi z requirements-build.txt (MIT), używa
--no-isolation i nie pobiera backendu według luźnego pinu upstream. Cały wheel,
w tym METADATA i RECORD, porównywany jest po rozpakowaniu. Różnice timestampów
ZIP nie wpływają na porównanie. provenance.json zapisuje SHA źródła, narzędzia,
hash wheel i hashe wszystkich jego plików; raport jest także w logu CI.
Nie publikujemy ani nie commitujemy wheeli lub kopii Core.

## Odtworzenie na Linux

Minimum, z katalogu repozytorium:

```bash
python3.14 -m venv .ha-tooling/minimum-venv
.ha-tooling/minimum-venv/bin/python -m pip install -r tools/ha_test_tooling/requirements-minimum.txt
.ha-tooling/minimum-venv/bin/python -m pip check
HA_TEST_TARGET=minimum .ha-tooling/minimum-venv/bin/python -m pytest tests/ha_tooling -v -s --disable-socket --allow-unix-socket
```

Current, w nowym venv i nowych katalogach core/current:

```bash
python3.14 -m venv .ha-tooling/current-venv
.ha-tooling/current-venv/bin/python -m pip install -r tools/ha_test_tooling/requirements-build.txt
.ha-tooling/current-venv/bin/python tools/ha_test_tooling/build.py --fetch --core .ha-tooling/core --output .ha-tooling/current
.ha-tooling/current-venv/bin/python -m pip install -r tools/ha_test_tooling/requirements-current.txt .ha-tooling/current/wheel-1/*.whl
.ha-tooling/current-venv/bin/python -m pip check
HA_TEST_TARGET=current .ha-tooling/current-venv/bin/python -m pytest tests/ha_tooling -v -s --disable-socket --allow-unix-socket
```

Ponowny build ze sprawdzonego checkoutu: pomiń --fetch i podaj nowy --output.
Skrypt odmawia nadpisania katalogu wyniku. Rozbieżny SHA, zmiany źródła, błąd
builda, zmienione fixtures/licencja/metadane lub różnica między buildami kończą
operację błędem. Nie ma fallbacku do innego HA.

Pytest wyłącza osobny plugin respx zgodnie z README Core, aby alias httpx HA
został załadowany wcześniej. Pozostają dostępne atrapy HTTP pakietu fixtures.
Smoke testy używają prawdziwego hass, enable_custom_integrations, MockConfigEntry,
pętli asyncio i syntetycznej usługi. Kolejny test sprawdza izolację wpisów/usług;
teardown hass i jego kontrole zadań wykonuje niezmieniony plugin upstream.
Połączenia sieciowe podczas testów są zablokowane przez pytest-socket;
dozwolone lokalne sockety Unix służą pętli zdarzeń.

## Przekazanie Developer → Reviewer / Tester / Tech Lead

Wyniki dla konkretnego SHA oraz link do obu jobów ha-tooling zapisuje opis PR.
Log zawiera wersje zainstalowanych pakietów, pip check, wyniki testów i provenance.
To samokontrola Developera, bez niezależnego review i bez odbioru sprzętu.
Reviewer sprawdza dwa zmienione pola metadanych, SHA, licencje i brak obejść
zależności. Tester odtwarza oba wiersze powyższymi komendami. Dopiero oba PASS,
review i decyzja właściciela o scaleniu pozwalają Tech Leadowi przekazać I01.
Nie zmieniono bramki check_repository.py ani statusów US. I01 musi zachować
bramkę produktu i użyć tych samych instalatorów w macierzy testów integracji;
importy MockConfigEntry różnią się między wierszami tak jak w smoke testach.

Wycofanie przed I01: revert tego narzędziowego PR. Bez migracji danych,
zmian konfiguracji domu, usług urządzeń, merge, wydania i deploy.
