# Małe PR-y i przekazanie Developerowi

Po scaleniu PR #36 i jawnej dyspozycji właściciela przejścia do kroku 3
konkretne zlecenia określa [indeks przekazań](../development/handoffs/README.md).
Najpierw I00 domyka T08, potem I01; pozostałe pakiety wymagają osobnego handoffu.
Baza analizy main: 6891b473a646c3d9e0783edf6cd437eb27a9b758.
Gałęzie każdego pakietu od aktualnego origin/main po scaleniu zależności.
Każdy PR do main, bez auto-merge, deploy i automatycznego zamykania US.
Numer pakietu to kolejność techniczna, nie status Issue.
P01–P12 w tabeli są odnośnikami do przyjętych D90–D101, nie otwartymi blokerami.
Baza projektu przyjęta do dalszych prac: e27621281d119f802e263d427ef9b9d36f6a135e.
Właściciel scalił PR #36 i zlecił krok 3; brak niezależnego review jest jawny
w indeksie przekazań. Nie utożsamiamy samego merge z wynikiem testu produktu.

## Definition of Ready

Podstawa przejścia do wykonania i brak niezależnego review są zapisane
w indeksie przekazań; decyzję właściciela wiążemy z konkretną bazą SHA.
Przed kodem produktu I01 wymagane rozwiązanie T08 w I00. I00 jako zadanie
narzędziowe nie wymaga wyniku samego siebie przed rozpoczęciem.
Tech Lead wpisuje zatwierdzony SHA oraz link odpowiedzi właściciela w handoff.
Treść wymagań i powiązanych Issues zsynchronizowana; bez nowych statusów w docs.
Developer odświeża main, czyta Issue z komentarzami, sprawdza instrukcje i
lokalne zmiany. Zakres ma mierzalny wynik i syntetyczne dane, bez urządzeń domu.
Nie wystarcza samo zielone CI dokumentacji.

## Pakiety implementacyjne

| Pakiet / gałąź | Zakres i rezultat do przeglądu | Refs US / Issues, D, A/B | Zależności / decyzje | Kryterium końca i odbiorca |
| --- | --- | --- | --- | --- |
| I00 chore/ha-test-matrix | Zgodne środowiska i fixtures minimum/current, realne smoke tests oraz odtwarzalny pakiet current, bez custom_components | US08/16/20; #15 #23 #29; D80,D101; przygotowanie A/B/C | Przyjęty projekt i T08 jako zakres do rozwiązania | Oba środowiska i pip check PASS, licencje/źródła sprawdzone; Reviewer → Tester → Tech Lead |
| I01 feat/10-ha-foundation | Rzeczywisty manifest, ConfigEntry/runtime, minimum i macierz CI; setup/unload i observation na poprawnych wpisach, użytkowy config_flow w I02 | US03/08/16/20; #10 #15 #23 #29; D09,D68–D71,D80; A02,A08; B01,B02,B04 | Przyjęty projekt/P12, scalone I00 z dowodami T08 | Prawdziwe testy HA na obu wersjach; mock dowodzi braku usług w observation; hassfest. Reviewer → Tester |
| I02 feat/8-installation-model | Typy i walidacja jednej pompy/jednego CO/CWU, stref/grup, trwałe UUID, bez wykonawcy | US01/09/15; #8 #16 #22; D07,D17–D21,D69–D70,D85; A01,A03–A05; B01,B02,B06 | I01; P07/P12 | UI konfiguruje samo CO/samo CWU/oba; brak pustych modułów i nowych ID przy rename; Reviewer |
| I03 feat/16-output-ownership | Atomowe rezerwacje między wpisami, ostrzeżenia odłączenia, binding registry_id i rename źródła | US01/09/16; #8 #16 #23; D84–D87; A04; B04,B06,B09,B10 | I02; P04 | Dwa równoczesne flow nie współdzielą wyjścia; odłączenie niczego nie przełącza; Reviewer → Tester |
| I04 feat/15-versioned-store | Store v1, cele/tryby, walidacja payload, protokół rewizji ConfigEntry/Store i odmowa niezgodności | US02/08/19; #9 #15 #26; D25,D54,D71–D72,D89; A07,A43; B05–B07 | I02; P07 | Restart zachowuje UUID i ustawienia; błąd zapisu i crash granicy nie resetują; Reviewer |
| I05 feat/23-source-quality | Adaptery wartości, jednostek, świeżości, raportów changed/reported; bez historii i usług | US01/16; #8 #23; D46–D47,D50,D68; A30,A32,A35 | I02; P08 | Jednakowy raport odświeża tylko HA freshness; NaN/unknown/unavailable nigdy 0; Tester |
| I06 feat/26-history-windows | Recorder adapter, 48h rebuild + live watermark, średnie/mediany ważone czasem, pokrycie | US01/06/19; #8 #13 #26; D32–D34,D47,D53,D71; A09,A30,A41,A42; B08 | I04,I05; P08 | Brak duplikatów, fikcyjnego heartbeat i mieszania czujników; test start-state/retencji, limit pamięci; Reviewer → Tester |
| I07 feat/12-zone-decisions | Czyste żądania stref, progi, spadek, równoległe blokady i grace; tylko decyzje | US05/06/18; #12 #13 #25; D35–D39,D46,D48,D55,D57–D59; A10–A16,A21,A31,A42 | I04,I06; P07/P11 | Deterministyczny zegar; nowe cele, brak danych i source-set nie tworzą fałszywego spadku; Tester |
| I08 feat/24-co-calculation | Baza, kwalifikacja i ważony komfort, trend, aktywność modułów; bez usług | US17/18/20; #24 #25 #29; D10,D37,D40–D41,D45,D49; A18–A23,A33,A34,A57 | I06,I07; P09/P10 | Wyniki liczbowe A18–A23; zamknięte vs utracone vs mieszane osobno; Reviewer |
| I09 feat/24-co-constraints | Zakres, siatka, tempo i ochrona wzrostu; nadal obserwacyjnie | US16/17; #23 #24; D38,D42,D50,D61; A21,A24–A26,A35 | I08; P01/P10 | Połówki w górę; D99: clipping do granicy z konfliktem przy nastawie poza zakresem, bez zwykłego limitu kroku/odstępu; inne braki legalnego kroku blokują; ręczna nastawa; Tester |
| I10 feat/11-command-evidence | Dwuetapowy odczyt tej samej encji, provisional/confirmed po 2 min, bez automatycznych usług runtime | US04/16/19; #11 #23 #26; D51,D60,D68; A36,A37,A39 | I03,I05; przyjęte P01/D90 | Wstępny zgodny stan nie kończy kontroli 2 min; zgodny ponowny odczyt, także cache HA, kończy retry bez dodatkowej telemetrii; granice fizycznego dowodu jawne; Reviewer |
| I11 feat/11-command-retries | Jedyny wykonawca, liczniki na wyjście, retry i generation, aktywacja tylko po gotowości | US03/04/17/19; #10 #11 #24 #26; D52,D60,D73–D74,D84; A08,A37–A40; B04,B10 | I04,I09,I10; P01/P03 | Dokładne czasy prób, późny/stary ACK, observation/unload w await; retry nie krokiem CO; Reviewer → Tester |
| I12 feat/17-valve-execution | NC/NO i polaryzacja, raport elektryczny i predicted movement, niezależny eksport stanów | US05/10; #12 #17; D08,D21,D51,D66; A04,A17,A20,A36 | I07,I11; P04 | Brak udawanego physical feedback; błąd close nie usuwa ochrony; Tester |
| I13 feat/16-demand-sequencing | OR, jedna gotowa strefa, brak minimum ON, 15min od OFF, anulowanie ON i ręczny demand | US07/09; #14 #16; D06,D43,D48–D51,D55; A27–A29,A31,A33,A34,A43,A56 | I12; P03 | Cztery kombinacje zawory/demand; bez demandu brak ON/OFF CO; Reviewer → Tester |
| I14 feat/21-dhw-planner | Czysty plan 7×48 i next effective change, DST i override terminy, inicjalizacja | US13/14; #20 #21; D13,D26–D28,D56,D63–D65; A47–A51,A54–A56 | I04; P02/P05/P06 | Bez efektów urządzeń; jednakowe pola nie kończą nadpisania; Tester |
| I15 feat/20-dhw-execution | Temperatura→ponowny odczyt po 2 min→ON, OFF niezależne, każda niealgorytmiczna zmiana external; bez obsługi higieny | US07/13/14; #14 #20 #21; D27,D56,D63–D64,D88; A46–A53; B11 | I10,I11,I14; P01/P02/P05 | Częściowe wykonanie, external bez blokady pochodzenia, restart i brak wymogu encji higieny; brak wpływu awarii na CO; Reviewer → Tester |
| I16 feat/18-product-entities | number celu, switch trybów, sensor/binary/event decyzji, bounded diagnostics i anonimizacja | US02/04/11/12; #9 #11 #18 #19; D79,D81–D83; A07,A59; B12 | I04–I15; P07/P11/P12 | Własne dashboardy bez helperów; testy anonimizacji zagnieżdżeń i PL/EN; Reviewer |
| I17 feat/20-dhw-settings-api | Uwierzytelnione WS odczytu/zapisu, revision conflict, jeden trwały zapis | US13/14; #20 #21; D29–D30,D62–D63; A44,A45,A48,A49 | I14–I16; P06 | Brak częściowego zapisu i last-write-wins; identyczny save kończy override; Tester |
| I18 feat/18-bundled-frontend | Karta, panel CWU, draft/cancel/save i osobny ekran zaawansowany, lint/build/browser CI | US11–14; #18 #19 #20 #21; D29–D30,D62,D79–D81; A44–A56,A59; B02,B13 | I16,I17; P11/P12 | Bundle lokalny, klawiatura/mobile, PL/EN, frontend w zbiorczej bramce CI; Reviewer → Tester |
| I19 fix/15-lifecycle-regressions | Przegląd pełnych restart/reload/unload, reconfigure i aktualizacji na złożonych stanach | US08/19; #15 #26; D54–D55,D71–D74,D84–D89; A41,A43,A51,A56; B03–B12 | I01–I18 | Testy migracji i race bez aktywnego sprzętu; brak nieplanowanych usług; Reviewer → Tester |
| I20 docs/first-developer-release | Materiały wydania beta, instrukcje PL/EN, HACS/manual, macierz, wyniki i rollback | US08/11–14/19; #15 #18–#21 #26; D75–D81,D89; A58; B13 | Całość + osobno autoryzowany odbiór sprzętu | Release/Deployment przygotowuje materiały dla właściciela; żadnego publish/deploy |

Jeśli zakres pakietu przestaje być czytelnym diffem, Tech Lead dzieli go według
kontraktu (np. karta, panel CWU i ekran zaawansowany jako osobne PR-y z własnymi
testami). I18 zalecane podzielić na I18a karta+CI, I18b panel CWU, I18c zaawansowane.
Tak samo I16 można podzielić encje i diagnostykę. Nie przenosić brakujących testów
z implementacji do I19; I19 jest dodatkową regresją, nie odroczoną jakością.

Kolejność umożliwia równoległość logiczną I07–I09 i I14 dopiero po wspólnych
kontraktach, ale delegowanie nie jest uruchomione tym planem.
Developer → Reviewer → Tester → Tech Lead / właściciel to kontrakt pracy.
Autor swojej samokontroli nie zgłasza jako niezależnego review.

## Definition of Done pojedynczego PR

Zmiana realizuje tylko przekazany zakres, ma testy właściwych US/D/A/B i brak
nieuzgodnionych reguł. Uruchomione wymagane komendy z CI, dla kodu także pytest HA
na minimum/current i hassfest; frontend od pierwszego PR ma lint/build/test.
Brak testów/symulacja/skipped jawnie opisane. Uzupełnione PL/EN i procedura
powrotu przy zmianie schematów. Reviewer otrzymuje SHA, diff, źródła i dowody.
Tester raportuje wersję i wyniki dla wskazanego SHA; nowe commity ponawiają
dotknięte kontrole. Merge tylko decyzją właściciela.

Wycofanie PR: zanim wydano produkt, revert małego zakresu przez kolejny PR;
po zmianie danych według macierzy schematów i zgodnej kopii HA.
Nigdy revert schematu z cichym czyszczeniem Store.
Scalenie dokumentacji lub części kodu nie zamyka US pełnego zakresu.

## Konkretne przekazania po scaleniu projektu

- [I00 — narzędzia testowe HA](../development/handoffs/i00-ha-test-tooling.md):
  bieżący zakres Developera, domyka techniczną zależność T08 bez kodu integracji.
- [I01 — fundament integracji](../development/handoffs/i01-ha-foundation.md):
  kompletny kontrakt następnego małego PR; start po wynikach i scaleniu I00.
- [Indeks](../development/handoffs/README.md) zapisuje bazę e276212 i dyspozycję
  właściciela przejścia do kroku 3. Commit wykonawczy I01 będzie aktualnym main po I00.

Doprecyzowanie podziału: I01 nie dodaje pustego config_flow. Testuje prawdziwy
setup/unload na poprawnych ConfigEntry; I02 dodaje użytkowy kreator i model stref.
Nie zmienia to docelowego działania produktu ani pierwszego kompletnego wydania.
Reviewer/Tester otrzymują rzeczywiste SHA i wyniki; żaden handoff nie wykonuje merge.

C01–C13 w verification.md uzupełniają testy pakietów I01–I18: C01/C02 I10–I11,
C03/C06 I14–I15, C04 I13, C05 I03/I12, C07 I14/I17/I18, C08 I04/I07/I16,
C09 I06, C10 I08, C11 I09/I11, C12 I07/I16, C13 I01/I03/I18.
Te testy powstają wraz z odpowiednimi zmianami, nie dopiero w I19.
