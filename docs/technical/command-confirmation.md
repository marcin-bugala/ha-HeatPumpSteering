# Polecenia, raporty i potwierdzenia

Podstawa: D51–D52, D56, D60, D66, D68 z doprecyzowaniem D90–D94;
A17, A20, A27, A36–A40, A52–A53. P01–P05 są rozstrzygnięte.
T05: jeden wykonawca dla wszystkich rodzajów wyjść; odróżniamy potwierdzenie
operacyjne regulatora od niezależnego dowodu fizycznego.

## Dwa etapy potwierdzenia D90

| Etap | Warunek | Skutek |
| --- | --- | --- |
| requested | Aktualne żądanie regulatora | Nie dowodzi wysłania |
| sent | Wywołano usługę HA | Sam powrót usługi nie dowodzi wykonania |
| provisional | Poprawny odczyt tej samej encji zgodny z żądaniem bezpośrednio po zapisie | Wstępne potwierdzenie od razu, również przy optymistycznej aktualizacji; nie kończy jeszcze kontroli po 2 min |
| confirmed | Ponowny odczyt aktualnej wartości tej samej encji po domyślnie 2 min od wysłania: dostępny, poprawny i zgodny z aktualnym żądaniem | Ostateczne potwierdzenie dla regulatora, reset serii błędów i koniec retry; następny krok CO dopiero z zachowaniem limitów |
| unconfirmed | Ponowny odczyt jest niezgodny, unknown, unavailable lub niepoprawny | Brak ostatecznego potwierdzenia; aktualnie potrzebny zapis podlega D52 |
| predicted_position | Raport przekaźnika + czas pracy siłownika | Przewidywane położenie; nie fizyczne sprzężenie zwrotne |
| physical_feedback | Opcjonalny niezależny pomiar urządzenia/położenia | Informacja o faktycznie mierzonej wielkości, nie warunek potwierdzenia operacyjnego |

„100%” oznacza ostateczne zatwierdzenie polecenia w procesie regulatora.
Nie oznacza gwarancji fizycznego wykonania. Nie wymagamy drugiej encji,
source sequence, timestampu urządzenia ani znacznika nowego odczytu chmury.
Dwuetapowe potwierdzenie stosujemy do sterowanych wyjść wspólnego wykonawcy;
szczególnie nastawy CO1 i CWU korzystają z tej samej encji zapisu i odczytu.

Po 2 min callback ponownie pobiera bieżący stan encji HA i waliduje wartość,
jednostkę, dostępność, aktualny request, generation i desired_revision.
To odczyt w chwili weryfikacji, nie zapamiętana kopia odczytu wstępnego.
Nie wymagamy zmiany last_reported między etapami i nie wywołujemy bezpośrednio
API producenta ani nie narzucamy wymuszonego refresh chmury.
Samo upłynięcie czasu bez poprawnego odczytu nie jest potwierdzeniem.
Czas kontroli jest wspólny i konfigurowalny zgodnie z D60, domyślnie 2 min.

Przed upływem terminu zgodny raport pozostaje provisional. Po nieudanej kontroli
poprawny późniejszy odczyt aktualnego żądania może zakończyć serię przed retry A39.
Zmiana celu/trybu/bindingu lub unload unieważnia dawny callback, także gdy
stara wartość przypadkiem pokrywa się z nowym celem.

## HiMitII i granice wiedzy

Odczytany [kod źródłowy](ha-contracts.md) HiMitII wykonuje optymistyczną zmianę
coordinatora i późniejszy refresh; przy błędzie może utrzymać cache.
Jest to akceptowane ograniczenie źródła według D90, nie blokada aktywacji produktu.
Jedna encja nastawy CO1 wystarcza. Poprawny ponowny odczyt encji po 2 min kończy
potwierdzenie nawet bez możliwości odróżnienia cache od nowego raportu chmury.
Diagnostyka opisuje confirmed jako potwierdzenie odczytem HA, nie dowód fizyczny.

Min/max/step bierzemy z encji HA i walidujemy ich spójność. Informacja, że źródło
może używać fallbacku, pozostaje w diagnostyce profilu; nie wymagamy dodatkowej
telemetrii pochodzenia limitów jako warunku aktywacji. Brak/niepoprawny zakres
blokuje zależny zapis D50. Nie dodajemy własnego fallbacku zakresu.

## Życie pojedynczego wyjścia

Stan: desired value/revision, last_sent, provisional_at, verification_due,
verified_at, attempt_count, next_retry, ostatni odczyt i błąd.
Jedno aktualne żądanie, nie FIFO komend. Pierwsze wysłanie t0, wstępny odczyt
od razu, ostateczna kontrola t0+2 min; przy niepowodzeniu kolejne wysłania
t0+5 i t0+10 min i kontrole +7/+12 min. Błąd po trzecim niepowodzeniu do +12 min.
Następne wysłania +20, +35, +60, +100, +165, +270, +390 min.
Odstępy od wysłania poprzedniej próby, nie od końca kontroli.
Zgodny odczyt po nieudanej kontroli, np. o t0+3 min, kończy serię przed +5 min.

Zmiana wartości anuluje dawny request, nie resetuje licznika błędów wyjścia.
Nowe żądanie respektuje aktualny termin retry. OFF demandu nie ma dodatkowej
zwłoki logicznej, ale nie resetuje liczników ani terminów D92.
Ostatecznie potwierdzony sukces resetuje serię.
CO retry dotyczy tej samej absolutnej nastawy, nie kolejnego kroku o 1°C.
Korekta nastawy spoza zakresu do granicy ma osobne pierwszeństwo D99.

Ruch zaworu liczymy od zgodnego raportu przekaźnika; kontrola po 2 min nie
rozpoczyna ponownie już trwającego ruchu. Gotowość do ON demandu wymaga
ostatecznej weryfikacji otwarcia i upływu czasu siłownika co najmniej jednej
potrzebującej strefy (wszystkie jej wyjścia) albo wirtualnego zapotrzebowania.
Przy raporcie otwarcia 10:05 i poprawnej weryfikacji 10:07 gotowość ruchu
z czasem 3 min przypada 10:08, zgodnie z A27.
OFF demandu jest datowany zgodnym raportem OFF, a kontrola po 2 min potwierdza
jego utrzymanie; nie przesuwa początku 15-minutowej przerwy.
Niezgodna kontrola unieważnia założenie zgodnego stanu i blokuje zależną gotowość.
Niepotwierdzony raport nie jest podstawą odtworzenia blokad przez restart D55.

CWU ON po nowym zapisie temperatury czeka na jej ostateczny zgodny odczyt po 2 min.
OFF pozostaje niezależne od temperatury. Bieżąca zgodna, poprawna nastawa,
której nie trzeba zmieniać, nie wymusza zbędnego zapisu. Jeśli trwa kontrola
po właśnie wykonanym zapisie, zgodny stan/no-op nie kończy jej przed terminem 2 min.

## Zmiany zewnętrzne D91–D94

Każda rzeczywista zmiana ustawienia CWU niewynikająca z naszego algorytmu jest
external, jak zmiana użytkownika. Własny request/context i rejestr wysłanych
działań rozpoznają własne zmiany oraz ich echo; brak takiego powiązania oznacza
external, bez próby rozpoznania aplikacji/użytkownika/higieny.
Nie ma kategorii ambiguous ani blokady z powodu nieustalonego pochodzenia.
Identyczny raport nie jest zmianą ustawienia; opóźnione echo naszego polecenia,
jeżeli jest rozpoznawalne, nie tworzy ręcznego nadpisania.

W Harmonogramie external nadpisuje do następnej rzeczywistej zmiany pary
stan/temperatura albo zapisu panelu w Harmonogram. Identyczne pola nie kończą
nadpisania; jednakowy tydzień daje brak terminu i jawny komunikat D64.
Zapis panelu kończy nadpisanie także przy identycznym planie.
Ręczna zmiana CO1 nie dezaktywuje regulatora ani nie dodaje pauzy D61.
Ręczny demand uzgadniamy przy następnej dozwolonej ocenie; trwałe oddanie
kontroli przez obserwację CO D92.
Higieny CWU nie obsługujemy: brak encji, wykrywania, specjalnych blokad i wymogu
aktywacji. Zmiana nastaw przez mechanizm PC też jest external, jeśli nie
pochodzi od naszego algorytmu. Nie sterujemy higieną ani zabezpieczeniami PC.
