# Model danych

T02: dataclasses z jawnymi typami, niemutowalne snapshoty; JSON tylko na granicy HA/Store.
Brak ORM i rozszerzalnego systemu pluginów. Powiązania: D17–D21, D69–D72, D84–D87.

| Rekord | Klucz i istotne pola | Miejsce |
| --- | --- | --- |
| InstallationConfig | installation_id UUID, nazwa, enabled_co/dhw, schema_version | ConfigEntry.data |
| CircuitConfig | circuit_id UUID, installation_id, role=co, output_id, outdoor_source_id, zone_ids, optional demand_id | ConfigEntry.data; maksymalnie jeden CO |
| DhwConfig | dhw_id UUID, setpoint_output_id, enable_output_id | ConfigEntry.data; zero lub jeden |
| ZoneConfig | zone_id UUID, circuit_id, nazwa, group_id?, enabled, source_ids, main_source_id?, valve_output_ids, NC/NO, progi, priorytet | ConfigEntry.data |
| GroupConfig | group_id UUID, nazwa, kolejność | ConfigEntry.data; wyłącznie prezentacja |
| SourceBinding | source_id UUID, entity_registry_id?, entity_id, rola, jednostka, profil historii i raportu | ConfigEntry.data |
| OutputBinding | output_id UUID, binding encji, funkcja, adapter, polaryzacja, poziom potwierdzenia i zakres encji HA | ConfigEntry.data |
| ProgramParameters | wspólne funkcje/okna, świeżość, retry, ograniczenia, aktywne korekty | ConfigEntry.data; wersjonowana konfiguracja |
| Schedule | dhw_id, revision, 7 dni × 48 Slot | Store; Slot=off lub on z temperaturą |
| UserSettings | cele zone_id→temperatura; dhw_mode, stała temperatura?, schedule; tryby observation/control | Store |
| ZoneMemory | ostatnie żądanie?, lost_since?, confirmed close time?, postęp warunków, alarmy | Store |
| OutputMemory | ostatni odczyt HA, wartość/czas, provisional_at, verified_at, licznik prób, sent_at, verification_due, next_retry, desired_revision, armed_binding_revision | Store; nie kolejka do odtworzenia |
| Override | dhw_id, stan/temperatura, provenance, created_at, expires_at UTC lub null, plan_revision | Store |
| Measurement | source_id, czas raportu HA, czas fizyczny?, wartość?, jakość, source_set_revision | Bufor; historia przez Recorder |
| WindowValue | wartość?, start/end, valid_duration, coverage, current_fresh, reasons | RAM; gotowość osobno dla każdego okna |
| Decision | decision_id, timestamp, revisions, baza, wkłady, limity, żądania, reasons | Bieżący snapshot, ograniczony ring i encje Recordera |
| Command | command_id, output_id, desired absolute value, generation, desired_revision, attempt, sent_at | Runtime + potrzebna pamięć retry |
| Evidence | output_id, value, observed_at, source_sequence?, provenance, level | Snapshot; brak sekretów |
| Warning | code, scope_id, active_since, cleared_at?, read_at?, cause | Store dla aktywnych/ack; historia encji w Recorderze |

Nazwy i entity_id nie są kluczami stref. Unique_id własnych encji:
`{installation_id}_{scope_id}_{metric}`; scope_id to circuit/zone/dhw albo installation.
Domena platformy nie wchodzi do klucza celu jako niejawna nazwa pomieszczenia.
Zmiana nazwy/grupy/czujnika zachowuje zone_id i unique_id. Usunięcie i ponowne
dodanie nazwy generuje UUID. Encje użytkownika można przemianować w rejestrze HA
bez odtwarzania ich przez integrację.

Binding przechowuje registry_id, jeśli istnieje; entity_id jest odświeżaną lokalizacją.
Zmiana nazwy źródłowej encji aktualizuje binding i rezerwację bez zmiany tożsamości.
Usunięta encja nie jest automatycznie wiązana do nowej o tej samej nazwie.
Dla źródeł bez wpisu rejestru pozostaje jawny entity_id i konieczność reconfigure.
Nie zmieniamy dashboardów użytkownika ani rejestrów cudzych integracji.

## Rewizje i gotowość

`configuration_revision` dla instalacji, `source_set_revision` dla szeregu,
`settings_revision` dla zapisu użytkownika i `generation` runtime do anulowania.
Cel strefy ma 5–35°C co 0,5°C i jest początkowo podany przez użytkownika D96.
Zmiana celu unieważnia zależne polecenia i zeruje zależne potwierdzenia temperatury;
zachowuje terminy zamknięcia/demandu oraz historię pomiarów.
Zmiana czujnika rozpoczyna nowy szereg i odbudowę, nie miesza konfiguracji historycznych.

Readiness jest rekordem `ready: bool, reasons: tuple, coverage?, as_of`,
osobno dla pomiaru zaworów, trendu, komfortu, trendu 12 h, outdoor, wyjścia, demandu,
CWU. Niedostępna wartość to None + przyczyna, nie NaN, 0 ani fałszywy OFF.
Przewidywane położenie zaworu, raport HA oraz provisional/confirmed po kontroli
2 min pozostają oddzielnymi polami; opcjonalny dowód fizyczny nie jest wymagany.
Tryb modułu nie zastępuje enabled: enabled=false zachowuje ustawienia,
enabled=true po wyłączeniu ustawia observation; restart nie zmienia zapisanego trybu.

Przyszłe dwa CO dodają drugi CircuitConfig, a nie zmianę tożsamości obecnych stref.
v1 waliduje liczność <=1; żaden ekran ani działająca ścieżka drugiego CO nie powstaje.
