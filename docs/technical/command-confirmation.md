# Polecenia, raporty i potwierdzenia

Podstawa: D51–D52, D56, D60, D66, D68; A17, A20, A27, A36–A40, A52–A53.
T05: jeden wykonawca dla wszystkich rodzajów wyjść; dowód ma poziom i pochodzenie.

| Poziom | Co wiadomo | Co wolno z niego wnioskować |
| --- | --- | --- |
| requested | Aktualny wynik regulatora | Żądanie, bez dowodu wysłania |
| sent | Zakończyło się wywołanie usługi HA | Przyjęcie w HA; nie wykonanie |
| reported/optimistic | Encja HA ma wartość zgodną | Raport HA; nie resetuje serii błędów bez wiarygodnego profilu |
| independently_reported | Udokumentowany raport urządzenia po zapisie | Potwierdzenie przekaźnika/nastawy zgodnie z profilem; nie hydrauliki |
| predicted_position | Wiarygodny raport elektryczny + czas siłownika | Przewidywane otwarcie/zamknięcie |
| physical_feedback | Oddzielny udokumentowany czujnik położenia | Tylko rzeczywiście mierzoną wielkość; opcjonalny |

State.last_reported mówi o raporcie w HA; context może pomóc skorelować
własną akcję, ale nie dowodzi odczytu z urządzenia.
`homeassistant.update_entity`, upływ 2 minut, inny entity_id i zgodny cache
nie stanowią samodzielnie dowodu. Nie wywołujemy transportu poza integracją źródłową.

## Profil dowodu

Profil jest małym zweryfikowanym rekordem możliwości, nie plugin frameworkiem:
source integration/version, pole stanu, czy setter jest optymistyczny,
co oznacza świeży raport, czy dostępne jest sequence/device_timestamp,
jakie limity są rzeczywiście z urządzenia, jakie ograniczenia ma potwierdzenie.
Użytkownik nie może samym checkboxem przemienić cache w dowód.
Przykładowo dla przekaźnika można uznać raport elektryczny urządzenia
po wysłaniu, jeśli kod integracji zapewnia jego niezależność;
ruch termicznego siłownika pozostaje tylko przewidywany.

Evidence pasuje do output_id, bieżącej generation i desired_revision,
znormalizowanej wartości na siatce i wiarygodnego odczytu nie starszego od
wysłania. Timestamp/sequence urządzenia porządkuje opóźnione raporty.
Sama późniejsza chwila odbioru bez ustalonej semantyki profilu nie rozwiązuje
opóźnionego echa starej komendy. Gdy profilu nie da się zweryfikować:
`cannot_confirm`, nie `confirmed`.
Po restarcie bieżący wiarygodny stan służy uzgodnieniu, nie odtwarzaniu
dawnego ACK. Bieżący niezależny odczyt zgodny z żądaniem pozwala uniknąć zbędnego zapisu.

## Stwierdzona luka HiMitII

Kod referencyjny w [źródłach](ha-contracts.md):
async_set_property → API set_device_property → _optimistic_update →
async_set_updated_data → delayed refresh.
Przy tolerowanych błędach odczytu coordinator może oddać poprzednie self.data.
Number i switch czytają ten sam coordinator; number stosuje fallback min/max.
Brak publicznego znacznika rozróżniającego optimistic od niezależnego refresh
i brak pochodzenia limitów na encjach. Opóźniony odczyt chmury dodatkowo nie
jest automatycznie dowodem fizycznego wykonania przez pompę.

Wniosek techniczny: obecny odczyt encji HiMitII nie spełnia sam z siebie
kontraktu potwierdzeń. Nie deklarujemy gotowości sterowania referencyjnego.
P01 proponuje wymagać telemetrii odczytu/limitów od integracji źródłowej
lub innego wiarygodnego źródła HA. Ewentualna poprawka upstream jest osobnym
zleceniem poza tym PR. Nie obchodzimy D68 przez bezpośrednie API chmury.

## Życie pojedynczego wyjścia

Stan serii: desired value/revision, last_sent, attempt_count, confirm_deadline,
next_retry, last_evidence, last_error. Jedno aktualne żądanie, nie FIFO komend.
Pierwsze wysłanie t0, timeout domyślnie t0+2 min, kolejne t0+5 i t0+10 min.
Błąd po trzecim timeout t0+12 min; następnie t0+20, +35, +60, +100,
+165, +270, +390 min. Odstępy od wysłania poprzedniej próby.
Późny poprawny dowód o t0+3 min kończy serię przed próbą +5 min.

Zmiana wartości anuluje dawny request, ale nie resetuje licznika błędów wyjścia.
Nowe żądanie respektuje aktualny termin ponowienia; OFF demandu bez dodatkowej
zwłoki algorytmicznej nie omija istniejącego ograniczenia błędów transportu.
Tę interpretację należy objąć przeglądem właściciela przy P03; nie wprowadzać
nowego minimum ON. Sukces z niezależnego odczytu resetuje serię.
CO retry dotyczy tej samej absolutnej nastawy, nie następnego kroku o 1°C.

Potwierdzenie przekaźnika uruchamia ruch zaworu; dopiero potem czas pracy.
Demand ON wymaga jednej potrzebującej strefy gotowej (wszystkie jej
przypisane wyjścia wiarygodnie otwarte + ruch) albo wirtualnego zapotrzebowania
strefy bez wyjść. Brak pomiaru po grace nie tworzy wirtualnego demandu.
OFF timer demandu liczony od wiarygodnego raportu OFF, nigdy od wysłania.

## Zmiany zewnętrzne

P02: nie każdy odmienny state_changed jest zmianą użytkownika.
Klasyfikator porównuje aktualny request, własny context, device sequence i
udokumentowane raporty źródła. Kandydat: own_echo / external / ambiguous.
external w Harmonogram tworzy nadpisanie do następnej rzeczywistej
zmiany pary stan/temperatura albo zapisu panelu; nie do następnego półgodzinnego pola.
Identyczny raport nie jest zmianą ustawienia.
ambiguous wymaga polityki P02; nie zastępujemy jej cichym nadpisaniem.

Dla CO ręczna nastawa nie dezaktywuje regulatora i nie dodaje pauzy D61.
Demand nie ma jeszcze przyjętej polityki ręcznej zmiany: P03.
Dla CWU inicjalizacja i higiena: P05/P06. Nie nazywamy zmian higienicznych
nadpisaniem użytkownika bez rozpoznanego źródła.
