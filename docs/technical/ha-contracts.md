# Kontrakty HA i zweryfikowane źródła

D101 (P12): przyjęta domena `heat_pump_steering`.
T01/T03: minimum HA Core 2026.10.4, bieżący cel macierzy 2026.11.1.
Ograniczona macierz zmniejsza koszt testowania nowego produktu; starsze wersje
nie są deklarowane jako wspierane. Po scaleniu PR #36 właściciel zlecił krok 3;
konkretne zakresy są w [przekazaniach](../development/handoffs/README.md).
Python narzędzi bootstrap nie wyznacza minimum produktu.

## Odczyt źródeł 11 listopada 2026

| Źródło | Tag / commit | Sprawdzony kontrakt |
| --- | --- | --- |
| [HA Core minimum](https://github.com/home-assistant/core/tree/357cae5c598dfcd7a0ea7dc5b1facccd4ec6037b) | 2026.10.4 / 357cae5c598dfcd7a0ea7dc5b1facccd4ec6037b | pyproject wymaga Python >=3.14.2; config_entries.runtime_data, Store, track state change/report, API historii, statyczne zasoby, panel |
| [HA Core bieżący](https://github.com/home-assistant/core/tree/d8a0dc698c8946b44e455d904000db563cfbf1ba) | 2026.11.1 / d8a0dc698c8946b44e455d904000db563cfbf1ba | Te same potrzebne API; również Python >=3.14.2 |
| [HA Core pośredni](https://github.com/home-assistant/core/tree/74cf5a49c63ed8d4d87717844bf14f79c28c9cea) | 2026.11.0 / 74cf5a49c63ed8d4d87717844bf14f79c28c9cea | Weryfikacja porównawcza, nie dodatkowa obietnica testów |
| [Plugin testowy](https://github.com/MatthewFlamm/pytest-homeassistant-custom-component/tree/0.13.375) | 0.13.375; ha_version, setup.py, requirements_test.txt | Przypina homeassistant==2026.10.4; deklaruje Python >=3.14, HA wymaga >=3.14.2 |
| [HiMitII](https://github.com/danardelean/HiMitII_HomeAssistant/tree/d479827b8b166c9917a025bbb273bd06c8b45333) | d479827b8b166c9917a025bbb273bd06c8b45333 | number.py, switch.py, coordinator.py: optymistyczny zapis, opóźniony refresh, fallback limitów |

Ścieżki kodu Core sprawdzone na minimum i bieżącej wersji:
`pyproject.toml`, `homeassistant/config_entries.py`,
`homeassistant/helpers/event.py`, `homeassistant/helpers/storage.py`,
`homeassistant/components/recorder/history/__init__.py`,
`homeassistant/components/http/server.py`, `homeassistant/components/frontend/__init__.py`.
Linki commitów powyżej są punktami odniesienia, nie ruchomym dev.

Dokumentacja opisowa, odczytana tego samego dnia:
[ConfigEntry](https://contributors.home-assistant.io/core/integrations/config-entries/),
[karty](https://contributors.home-assistant.io/frontend/custom-ui/card/).
Kod tagów jest podstawą oceny API; dokumentacja online nie jest wersjonowaną
gwarancją zgodności. Odczyt kodu nie oznacza uruchomionego testu.

| Docelowy job Linux | Python | HA | Plugin / wynik teraz |
| --- | --- | --- | --- |
| minimum | 3.14.2 lub zgodny patch 3.14 | 2026.10.4 | 0.13.375, zgodny pin odczytany, testy produktu jeszcze nie istnieją |
| current | zgodny patch >=3.14.2 | 2026.11.1 | Brak zgodnego wydania w odczytanej liście; blokada T08 |
| frontend | przypięty Node LTS wybrany z lockfile w PR UI | oba HA | Build/unit/browser; obecnie plan |

T08: przed pierwszym kodem produktu należy uzyskać zgodny plugin dla 2026.11.1
albo przygotować i przejrzeć wersjonowany pakiet fixtures z odpowiadającego Core
na licencji Apache-2.0. Preferowany plugin upstream; drugi wariant zwiększa koszt
utrzymania. Nie instalować 2026.11.1 przez nadpisanie zależności pluginu 0.13.375,
nie wyłączać joba current i nie deklarować zielonej macierzy.
Pierwszy PR kodowy ma przypiąć pełne bezpośrednie zależności z metadanych
dla obu środowisk i zmienić Ruff target na py314.

## Wejścia i wyjścia v1

T04: ograniczony zestaw jawnych adapterów. Brak dowolnych szablonów usług,
skryptów i automatycznego zgadywania znaczenia encji.

| Rola | Platforma źródłowa i usługa | Walidacja / awaria |
| --- | --- | --- |
| Temperatury stref/outdoor/zasilania/powrotu | sensor z °C lub °F | Przeliczenie do °C, skończona liczba, znana jednostka; unknown/unavailable natychmiast nieważne; raport i świeżość osobno |
| Nastawa CO | number → number.set_value | Bieżąca wartość, poprawne min/max/step encji i jednostka temperatury; brak blokuje zapis, pochodzenie zakresu nie jest dodatkową bramką |
| Nastawa CWU | number → number.set_value | Jak CO; brak potwierdzenia temperatury blokuje ON, nie OFF |
| Zawory | switch → switch.turn_on/turn_off | NC/NO strefy + jawna polaryzacja D93; raport elektryczny + czas ruchu; nie fizyczne położenie |
| Demand CO | switch → switch.turn_on/turn_off | Zezwolenie CO, nigdy główne zasilanie; jawna polaryzacja; raportowany OFF i ponowny odczyt D90 przed uznaniem przerwy za wiarygodną |
| Zezwolenie CWU | switch → switch.turn_on/turn_off | Wyłącznie CWU; brak obsługi higieny D94, bez dodatkowych encji/blokad i warunku aktywacji |
| Moc | sensor, W/kW | Normalizacja W, brak to niedostępne; bez wnioskowania o sprężarce |
| Energia | sensor, Wh/kWh | Normalizacja kWh, reset licznika oznaczony; bez własnej całki i okresów dzień/miesiąc D100 |
| Tryb pracy pompy | opcjonalny sensor/binary_sensor z opisanym mapowaniem | Tylko udokumentowany profil; zezwolenie nie jest pracą; bez profilu unknown |
| Potwierdzenie wyjścia | ponowny odczyt tej samej encji zapisu | Wstępne od razu, ostateczne po 2 min D90; dodatkowy czujnik/dowód fizyczny nie jest wymagany |

Climate/water_heater jako wejściowy sterownik nie są obiecaną funkcją v1:
ich adaptery wymagają osobnej oceny zakresów i semantyki. Wybór ograniczonego
kontraktu number/switch przyjęto w D101; inne adaptery wymagają przyszłego
rozszerzenia projektu i testów.

Min/max/step z encji nie zawsze są odczytem PC. HiMitII ma w number.py
fallbacki (np. CO 12–55, CWU 40–65); ich obecność nie dowodzi aktualnego
zakresu urządzenia. Zgodnie z D90 korzystamy z poprawnych min/max/step encji HA,
bez dodatkowego wymogu pochodzenia limitów; ograniczenie fallbacków jest jawne.
Brak lub niepoprawny zakres nadal blokuje zapis D50. Nie dodajemy własnego
fallbacku zakresu pompy.

Siatka temperatur: anchor=min, step>0, wartości min+n×step w dopuszczalnym
przedziale; zawężenie użytkownika musi zawierać co najmniej jeden punkt.
Zmiana jednostek i kroku powoduje ponowną walidację. Decimal na granicy
kwantyzacji pozwala testować połówki w górę bez bankierskiego round().
Usługi zawsze z konkretnym entity_id, nigdy z wildcard/area jako target.

## Encje udostępniane przez produkt

| Platforma | Stan i polecenia użytkownika |
| --- | --- |
| number | Cel strefy 5–35°C co 0,5°C, początkowo podany przez użytkownika D96; zapis trwały przed publikacją sukcesu |
| switch | Osobne CO control / CWU control: OFF=obserwacja, ON=sterowanie po walidacji |
| sensor | Bieżący pomiar, okna, trend, coverage, baza, wkłady, wynik, nastawa wysłana i potwierdzona, demand żądany/raport, predicted valve, retry i deadline |
| binary_sensor | Gotowość, aktywna blokada, ostrzeżenie; brak źródła nie udaje false |
| event | Zmiana decyzji, pojawienie/ustąpienie ostrzeżenia; atrybuty ograniczone, wersjonowane |
| diagnostics | Pobierany na żądanie eksport z anonimizacją |

Brak climate ze sztucznym HVAC action: produkt nie zna faktycznej pracy
sprężarki/stref. Temperatura aktualna jest sensor, cel number; jedna prawda
nastawy w Store. Nieobecny moduł nie tworzy panelu ani encji.
Wyłączony skonfigurowany moduł zachowuje tożsamość i ustawienia; pokazuje nieaktywność.

Event historii i snapshot decyzji w Recorderze mają stabilne reason codes i
wersję atrybutów; tłumaczenie następuje w UI. Nie publikujemy pełnych
buforów, identyfikatorów źródłowych ani nieograniczonego logu w atrybutach.

## Rezerwacje i aktywacja zmienionych powiązań

Wyjścia nie mogą wskazywać encji własnego produktu ani ich odczytu zwrotnego
jako pozornego dowodu fizycznego. Walidacja odrzuca pętlę sterowania i powielenie tego
samego źródłowego wyjścia poprzez alias w rejestrze, jeśli jest rozpoznawalne.
Nie obiecujemy wykrycia dwóch encji różnych integracji sterujących fizycznie
tym samym przekaźnikiem; ostrzeżenie konfliktu pozostaje obowiązkowe.

D101 przyjmuje techniczny mechanizm D84: pamięć armed_binding_revision.
Nowy/zmieniony binding wyjścia nie dziedziczy aktywacji starego. Pozostaje
nieuzbrojony do jawnej aktywacji modułu (observation → control) po pokazaniu
mapowania i stanu. Pozostałe niezmienione bindingi zachowują swoje zezwolenie.
To nie nowy tryb regulatora ani automatyczny zapis przy reconfigure.
Mechanizm przyjęty w P12; wykonanie UI nadal podlega przeglądowi całego projektu.

Konfiguracja zależności manifestu: wymagane config_flow i version;
frontend/http/websocket_api dla dostarczanego UI przez standardowy mechanizm HA.
Recorder pozostaje opcjonalnym źródłem historii; bez niego budowa okien
z raportów live i jawna niepełność. Nie deklarować zależności wymuszającej
instalację nowej bazy ani uruchamianie transportu urządzeń.

## Zlecenie rozwiązania T08 po scaleniu projektu

[I00](../development/handoffs/i00-ha-test-tooling.md) oddziela przygotowanie
narzędzi od I01. Odczyt 11 listopada 2026: najnowsze wydanie pluginu to nadal
0.13.375 (commit f353decb02e28313f1aeeb316a71053f93c76abd); gałąź domyślna
master, commit a5d0326f2bff12642358a2296807c7dd8067cdbc, również wskazuje 2026.10.4.
Wybrana alternatywa dla current: odtwarzalnie generowany pakiet fixtures z
przypiętego Core 2026.11.1, z poprawnymi metadanymi i licencjami, jeśli nadal
nie ma zgodnego wydania upstream. Nie jest to nadpisanie zależności zainstalowanego
pluginu 0.13.375. Generator upstream bez adaptacji wybiera latest — build I00
musi przyjmować konkretny commit. Ta dokumentacja nie wykonała builda/smoke testów;
T08 kończy dopiero wynik obu środowisk dla SHA I00.

### Wykonanie narzędzi I00

Odczyt przypiętego Core w I00 wykazał gotowy samodzielny pakiet
packages/pytest-homeassistant. Zamiast dostosowywać stary generator, który oczekuje
już przeniesionych plików tests/common.py, budujemy ten pakiet z tego samego
SHA d8a0dc698c8946b44e455d904000db563cfbf1ba. Lokalna wersja to
pytest-homeassistant==0.0.0+ha2026.11.1 z dokładnym pinem homeassistant==2026.11.1.
Nie zmienia to D101 ani minimum. Minimum pozostaje z publicznym pluginem 0.13.375.
Fixtures current są w całości kodem Apache-2.0 Core; nie wymagają generatora MIT.

[Implementacja i komendy](../../tools/ha_test_tooling/README.md) opisują kontrolę
SHA, licencji, niezmienionych plików .py i dwóch buildów, a także różne importy
helperów w obu środowiskach. Wyniki dla konkretnego SHA i link do CI są w PR I00.
Sam udany build lub odczyt źródła nie rozwiązuje T08: wymagane są pip check
i rzeczywiste testy hass w obu wierszach. I01 rusza po odbiorze i scaleniu I00.

Weryfikacja I00 dla cce478e88a73dbca7578439acbad8083e2b279ab:
[Linux/Python 3.14.10](https://github.com/marcin-bugala/ha-HeatPumpSteering/actions/runs/43016249992),
HA 2026.10.4/plugin 0.13.375 oraz HA 2026.11.1/lokalny pakiet 0.0.0+ha2026.11.1:
oba pip check PASS i po 3 testy prawdziwych fixtures PASS. Zgodność dwóch buildów,
pliki .py, licencja i metadane current PASS. Szczegóły i hash są w
[CI](../development/ci.md#i00--środowiska-testów-ha). To dowód narzędzi T08,
nie testów produktu; niezależny odbiór oraz scalenie I00 przez właściciela
pozostają warunkami przekazania I01.
