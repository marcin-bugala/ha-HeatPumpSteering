# Standardy lekkiego kodu i bezpieczeństwa

## Projekt i czytelność

- Czyste, typowane funkcje obliczeniowe; wejście, wynik i powód decyzji jawne.
  Czas i efekty uboczne podawane przez małe kontrakty. Nazwy domenowe, krótka ścieżka
  od danych do decyzji, komentarze wyjaśniające powód. Bez nadmiarowych fabryk,
  bazowych klas, globalnego busa ani frameworka pluginów na zapas.
- Wspólne reguły obiegów bez hardkodowania nazw pomieszczeń/encji; przewidź identyfikator
  obiegu w modelu, ale nie implementuj drugiego CO. Każda nowa zależność wymaga
  uzasadnienia, licencji i oceny kosztu; preferuj HA i bibliotekę standardową.
- Konfiguracja i encje zgodne z publicznymi API wybranej wersji HA: ConfigEntry,
  config/options flow, runtime_data, lifecycle, rejestry, tłumaczenia i diagnostyka
  tam, gdzie odpowiadają projektowi. Nie narzucaj DataUpdateCoordinator, gdy wystarczą
  zdarzenia encji. Nie odczytuj wewnętrznej bazy Recordera własnym SQL.
- Nie blokuj pętli zdarzeń: asynchroniczne API HA; synchroniczne I/O tylko w executorze,
  gdy rzeczywiście potrzebne. Właściwości encji nie wykonują I/O. Subskrypcje,
  timery i zadania muszą zostać odpięte/anulowane podczas unload.
- Obsługuj konkretne wyjątki na granicach. Nie maskuj awarii szerokim `except`,
  nie stosuj `sleep` do koordynacji ani nieskończonych pętli ponowień.

## Walidacja i polecenia

Waliduj jednostki, zakresy, krok, dostępność i świeżość. `unknown`, `unavailable`,
NaN i brak historii nie są zerem. Limity producenta są nadrzędne. Zmiana ustawień
waliduje cały zakres przed zapisem. Nie wybieraj nowych domyślnych parametrów
bez odnośnika do przyjętej decyzji.

Każde wykonanie i ponowienie sprawdza aktualny tryb, właściciela wyjścia, żądanie
i gotowość. Stare działania unieważnia zmiana konfiguracji, celu, trybu i unload.
Powtórzenie tego samego żądania nie jest kolejnym krokiem regulatora. Wywołanie
usługi HA nie jest dowodem wykonania. Testuj opóźnione/obce potwierdzenia i wyścigi.
Nie testuj przez przełączanie prawdziwych encji domu.

## Dane i prywatność

Nie zapisuj tokenów, prywatnych adresów, konfiguracji `.storage`, kopii HA ani danych
domowników w repo/artefaktach. Stosuj syntetyczne fixtures. Diagnostyka na żądanie
anonimizuje spójnie nazwy i encje; testuj również zagnieżdżone pola i tekst błędów.
Brak automatycznej telemetrii/wysyłki. Sekret wykryty w diff usuń przed publikacją,
a ujawniony token zgłoś właścicielowi do unieważnienia, bez powielania jego treści.

Migracje zachowują tożsamość, timery i nadpisania. Niezgodny starszy kod zgłasza błąd
bez resetu danych i bez sterowania. Nie kasuj historii, nie obchodź retencji HA.
Zmiany formatu wymagają testów zachowania danych i procedury zgodnego rollbacku.

## Bezpieczeństwo procesu

CI: `pull_request` i `push`, uprawnienia tylko `contents: read`, bez sekretów, prywatnej
sieci, runnera w domu i `pull_request_target`. Akcje przypinaj do SHA, zależności
narzędzi do wersji. Nie wykonuj kodu z komentarzy ani instalatorów `curl | sh`.
Aktualizacje zależności przechodzą PR i te same kontrole. Prawdziwy odbiór sprzętowy
planuj osobno z właścicielem, limitem zakresu i sposobem przerwania testu.

## Źródła techniczne

Zweryfikowane 11 listopada 2026; przed implementacją sprawdź zgodność z wybranym
minimum HA, nie kopiuj bez oceny kodu z ruchomego `dev`:

- [Config entries](https://contributors.home-assistant.io/core/integrations/config-entries/)
- [Blokujące operacje](https://contributors.home-assistant.io/core/internals/blocking-operations/)
- [Testowanie HA](https://contributors.home-assistant.io/core/development/testing/)
- [Testy custom components](https://github.com/MatthewFlamm/pytest-homeassistant-custom-component)
- [Hassfest action](https://github.com/home-assistant/actions/tree/86d4564712fa02543c808e3a693dd04f9d3f8361/hassfest)

Te praktyki wspierają jakość custom integration; nie są deklaracją uzyskania poziomu
oficjalnej skali jakości HA ani certyfikacji sprzętu.
