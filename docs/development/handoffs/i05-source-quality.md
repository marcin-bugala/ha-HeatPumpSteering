# I05 — jakość źródeł i raporty HA

Nadawca: Tech Lead / Orchestrator.
Odbiorca: Developer → Reviewer → Tester → Tech Lead / właściciel.
Data: 22 listopada 2026.
Repozytorium: marcin-bugala/ha-HeatPumpSteering.
Gałąź implementacji: `feat/23-source-quality`, PR do main.
Baza produktu: `5f49b2eebc9665f6f181cbbd78c8571d55bb28e5` lub nowszy main zawierający I04.
Developer zapisuje rzeczywistą bazę i końcowy SHA.

To przekazanie przygotowuje etap.
Ta sesja nie rozpoczyna jego implementacji.

## Definition of Ready i źródła

Projekt [PR #36](https://github.com/marcin-bugala/ha-HeatPumpSteering/pull/36) scalono jako
`e27621281d119f802e263d427ef9b9d36f6a135e`.
Plan wyznacza I05 jako adaptery wartości, jednostek i świeżości raportów.
I02/I03 dostarczyły konfigurację i trwałe bindingi.
[Odbiór I04](i04-verification.md) potwierdza Store i granice lifecycle.

Przed implementacją:
1. Uzyskaj zatwierdzenie tego przekazania od właściciela.
2. Sprawdź aktualny main i wynik jego CI.
3. Przeczytaj AGENTS.md, rolę Developera, workflow, standardy i ci.md.
4. Odczytaj Issues #8 i #23 razem z komentarzami.
5. Przeczytaj produkt, US01/US16, decyzje oraz rundy 3–6.
6. Przeczytaj [kontrakty HA](../../technical/ha-contracts.md), [model](../../technical/data-model.md),
   [lifecycle](../../technical/lifecycle.md), [trwałość](../../technical/persistence.md)
   i [macierz](../../technical/verification.md).

Issues #8/#23 odczytano podczas przygotowania.
Nie miały komentarzy.
Nie zmieniono statusów całych historii.

| Źródło | Część I05 |
| --- | --- |
| US01 / #8 | Jakość termometrów i jawna dostępność poszczególnych źródeł |
| US16 / #23 | Jednostki, skończone wartości, świeżość, zakresy number i niezależne zależności |
| D46–D47 | Częściowa utrata termometrów i świeżość od raportu |
| D50/D68/D90 | Oddzielenie jakości źródła, raportu HA i dowodu fizycznego; walidacja min/max/step |
| D97 / P08 | Brak fikcyjnego heartbeat i wstecznego pokrycia historii |
| D101 | Istniejące number/switch oraz obie przypięte wersje HA |
| A30/A32/A35 | Tylko jakość bieżących danych i zależne przyczyny niedostępności |
| B04/B06/B11 | Regresja lifecycle, bindingów i izolacji zależności; bez pełnego wykonawcy |

## Wynik i granice

Adapter to mała funkcja przekształcająca stan HA w zwalidowany odczyt.
Snapshot to niemutowalny obraz odczytu i jego jakości.
I05 dostarcza wspólny kontrakt dla przyszłych okien I06 i potwierdzeń I10.
Nie tworzy historii ani potwierdzenia polecenia.

Zakres obejmuje:
- typowane odczyty temperatur sensor, nastaw number i raportów switch;
- normalizację temperatur i zakresów do °C;
- jawne przyczyny brakujących, błędnych i nieaktualnych danych;
- raporty zmienionej i niezmienionej wartości dla wybranych encji;
- wygasanie świeżości bez oczekiwania na następne zdarzenie encji;
- odczyty zgodne z kanoniczną tożsamością bindingów I03;
- integrację jakości odczytów z runtime bez usług urządzeń.

Poza zakresem:
- Recorder, okna, agregacja historyczna, pokrycie 80% i trendy;
- regulator, grace utraty strefy, awaryjne otwarcie i demand;
- D90 provisional/confirmed, retry, polecenia i wykonawca;
- planner CWU, nadpisania, higiena i harmonogram;
- encje produktu, karta, panel i ustawienia zaawansowane UI;
- nowe opcjonalne pola telemetrii, profile producentów, prognozy i drugi CO;
- zmiana schema ConfigEntry/Store, pełne archiwum i zapis raportów w Store.

Nie dodawaj pustych modeli przyszłych funkcji.
Opcjonalne liczniki nie są warunkiem gotowości CO/CWU.
Nie rozbudowuj konfiguracji mocy/energii tylko dla tego etapu.

## Kontrakt odczytu i jakości

Użyj małych niemutowalnych rekordów z jawnymi typami.
Rekord odróżnia source/output ID, lokalizację entity_id, wartość, jednostkę,
czas raportu HA, jakość i stabilne reason codes.
Czas fizycznego pomiaru pozostaje nieznany bez udokumentowanego profilu.
Nie wyprowadzaj go automatycznie z last_changed, last_updated ani last_reported.

Czyste funkcje otrzymują stan, parametry i jawny czas.
Warstwa HA obsługuje odczyty, zdarzenia i anulowanie.
Nie twórz ogólnego frameworka adapterów ani globalnego busa.

| Wejście | Oczekiwany wynik |
| --- | --- |
| Sensor temperatury °C / °F | Skończona wartość w °C; zero i ujemna temperatura są poprawnymi liczbami |
| Brak stanu, unknown, unavailable | None z konkretną przyczyną od razu |
| NaN, infinity, tekst, bool w danych liczbowych, nieznana jednostka | Niepoprawny odczyt; brak zastępowania zerem |
| Number temperatury | Bieżąca wartość i osobno poprawność min/max/step |
| Brak lub błędny min/max/step | Zależna nastawa niedostępna; brak własnego zakresu domyślnego |
| Number w °F | Konwersja min/max jako temperatur; konwersja step jako różnicy temperatur |
| Bieżąca nastawa poza poprawnym zakresem | Zachowaj odczyt i granice oraz jawny konflikt; korekta D99 dopiero I09 |
| Switch on/off | Jawny raport logiczny; brak raportu nie jest OFF |
| Zmiana jednostki lub zakresu | Ponowna walidacja bieżącego snapshotu |

Poprawne min/max/step encji HA wystarczają zgodnie z D90.
Nie wymagaj dowodu ich pochodzenia.
Nie dodawaj własnego fallbacku zakresu pompy.
Zachowaj rozdział raportu switch od fizycznego położenia zaworu.
I05 nie oblicza ruchu zaworu ani potwierdzenia D90.

## Raporty i czas

Świeżość oznacza czas od poprawnego raportu HA.
Domyślne limity wynoszą 120 min dla termometrów stref i 30 min dla outdoor.
Parametry przyjmuj jawnie w warstwie obliczeń.
Nie dodawaj nowych wartości domyślnych dla pozostałych ról bez podstawy projektu.

Subskrybuj wyłącznie encje konfiguracji przez publiczne helpery HA.
Obsłuż state_changed oraz filtrowane state_reported dla jednakowych raportów.
Zweryfikuj kontrakt obu helperów na przypiętych wersjach HA.
Jeden raport nie może utworzyć dwóch niezależnych obserwacji tej samej chwili.
Nie wymagaj zmiany wartości, aby odświeżyć świeżość.

Odczyt cache HA nie jest nowym raportem urządzenia.
Nie odświeżaj czasu raportu podczas zwykłego przeliczenia lub upływu timera.
Nie zapisuj heartbeat do Store.
Po setup odczytaj dostępny stan z jego rzeczywistym timestampem HA.
Nie przypisuj czasu setup jako czasu raportu.
Nie rekonstruuj raportów przez przerwę procesu.

Zapewnij zmianę jakości po przekroczeniu limitu bez nowego raportu.
Użyj kontrolowanego zegara i standardowych anulowalnych callbacków HA.
Timer przelicza jakość bieżącego odczytu.
Nie tworzy próbki.
Testuj dokładną granicę oraz chwilę po limicie.
A32 określa utratę po przekroczeniu limitu.

Unload i zmiana konfiguracji odpinają wszystkie listenery i callbacki.
Stary callback nie publikuje snapshotu nowej konfiguracji.
Zachowaj ochronę generation oraz brak auto-reload po unload z I04.
Rename podąża za registry identity.
Replacement pod dawnym entity_id nie przejmuje tożsamości.

## Zależności i gotowość

Zachowaj osobne wyniki jakości źródeł.
Nie zastępuj ich jednym globalnym błędem instalacji.
Utrata jednego termometru pozostawia pozostałe poprawne źródła dostępne.
Wynik zawiera liczbę poprawnych i skonfigurowanych źródeł strefy.
Agregacja czasowa i reakcja na skok zestawu pozostają I06/I07.

Brak outdoor lub niepoprawna nastawa ogranicza zależną ocenę CO.
Nie przenoś tej przyczyny do niezależnego CWU.
Nie dodawaj wykonywania zaworów lub demandu dla demonstracji izolacji.
Gotowość bieżącego odczytu nie oznacza gotowości przyszłego okna historycznego.
Restore zapisanych trybów nadal respektuje gotowość i brak usług I04.
Nie dodawaj użytkowej aktywacji control.

## Macierz odbioru — plan, nie wynik

| Test / źródło | Wymagany dowód na końcowym SHA |
| --- | --- |
| Jednostki / D101 | °C/°F; number min/max/step; brak/zmiana jednostki; poprawne różnice temperatur |
| Błędne dane / D47/D50 | None, unknown, unavailable, NaN, infinity, tekst, brak zakresu; brak fałszywego zera/OFF |
| A32/D47/D68 | Stała wartość z nowymi raportami pozostaje świeża; sama zmiana zegara nie tworzy raportu |
| A32 — timer | Wnętrze 120 min i outdoor 30 min; utrata po przekroczeniu limitu bez zdarzenia stanu |
| D97 | Setup/reload nie dopisuje raportów w przerwie; cache i timer nie są pomiarem fizycznym |
| A30/D46 | Jeden z dwóch termometrów utracony: drugi poprawny, licznik 1/2; bez fałszywej wartości utraconego |
| A35/D50 | Brak outdoor, number lub zakresu ma właściwą przyczynę; CWU zachowuje niezależne dane |
| D90/D99 | Poprawny zakres bez bramki pochodzenia; nastawa poza zakresem zachowana z konfliktem, bez korekty lub usługi |
| B06 — binding | Rename zachowuje ID; replacement nie jest adoptowany; stare zdarzenie nie zmienia nowego snapshotu |
| B04 / lifecycle | Powtarzany reload nie mnoży listenerów/timerów; unload usuwa je i blokuje późne callbacki |
| Warianty | Samo CO, samo CWU, oba oraz wyłączony moduł; zero usług we wszystkich ścieżkach |
| Regresja I04 | Pełne dotychczasowe 139 testów zachowane; Store, runtime publication, recovery i unload/cancel nadal PASS |

Testy muszą przechodzić przez załadowany runtime i rzeczywiste zdarzenia HA.
Same testy czystej funkcji nie dowodzą poprawnej subskrypcji.
Steruj zegarem i barierami zamiast sleep.
Blokuj sieć urządzeń.
Nie osłabiaj asercji I04, aby dopasować nowy kod.

A30 pozostaje częściowe bez okien i ochrony nagłego spadku.
A35 pozostaje częściowe bez wykonawcy, zaworów i demandu.
A32 dotyczy jakości raportów HA, bez dowodu fizycznego pomiaru.
B04/B06/B11 pozostają częściowe w granicach pakietu.
Pełne A43/B05 i odbiór sprzętu nie należą do I05.

## Definition of Done i przekazanie

Uruchom komendy z ci.md dla końcowego SHA.
Wymagane: Ruff check/format, bootstrap, check_repository, diff-check,
oba ha-tooling/pip check, oba pytest integration, hassfest i agregat ci.
Oczekiwane CI: 7/7 PASS.
Podaj rzeczywistą liczbę testów oraz skip/xfail i ostrzeżenia.
Nie deklaruj PASS na podstawie wcześniejszego SHA.

Reviewer niezależnie sprawdza czas raportu, jednostki, zakres, binding identity,
granice lifecycle i rozdział od fizycznego dowodu.
Tester odtwarza macierz na obu wersjach HA i tym samym SHA.
Po poprawkach ponów dotknięte kontrole.
Autor nazywa własną kontrolę samokontrolą.

Raport zawiera rolę, bazę/head, US/D/A/B, wynik, ograniczenia i następnego odbiorcę.
Nie zamykaj US01/US16 po samym pakiecie I05.
Rollback kodu I05 nie może kasować ani cofać danych I04.
Zmiana schematu wymaga osobnego uzasadnienia i testów.

Następnie Tech Lead ocenia I05 i przygotowuje I06.
I06 wymaga odebranych I04 i I05.
Nie rozpoczynaj I06, merge, wydania, deploy ani testów na instalacji domu.
