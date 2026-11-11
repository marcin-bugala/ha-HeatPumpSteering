# Trwałość, historia i aktualizacja

Podstawa: D46–D47, D53–D55, D65, D71–D72, D84–D85, D89; US08/US19.
T07: jeden wersjonowany Store na ConfigEntry, bez pełnego archiwum.

## Wersje i zapis

ConfigEntry VERSION=1 / MINOR_VERSION=1; instalacja i powiązania w data,
bez równoległej kopii tych samych pól w options. Options/config flow wywołują
jeden walidator i aktualizują data przez HA. Store key
`heat_pump_steering.{entry_id}`, wersja główna/minor oraz payload_version,
installation_id i configuration_revision w payload.

Payload v1: user_settings, zone_memory, output_memory, overrides, active_warnings,
acknowledgements, saved_at UTC. Pola według [modelu](data-model.md).
Timery: termin UTC + powód + czas potwierdzonego zdarzenia + stan, który go uzasadnia.
Retry: licznik wyjścia i next_retry; nie lista działań.
Nie zapisujemy tasków, callbacków, tokenów, pełnych pomiarów i stanu HA domu.

Ustawienia użytkownika, tryby, plan CWU, nadpisania, zmiany żądań/wyjść i
istotne deadline: await Store.async_save przed potwierdzeniem operacji lub
poleceniem. Snapshot składa się pod blokadą, zapis jest serializowany.
Postęp temperatur checkpoint przy ocenie, z dopuszczalną utratą od ostatniego
udanego zapisu; nie dopisujemy tej straty po restarcie. Częste odczyty nie
uruchamiają zapisu pełnej pamięci.

HA Store zapewnia zapis pliku swoim mechanizmem; nie piszemy ręcznie .storage.
Atomowość CWU oznacza jeden payload plan+mode+temperatura+usunięcie nadpisania,
nie transakcję usług sprzętowych.

ConfigEntry i Store nie mają wspólnej transakcji. Zmiana strukturalna:
walidacja → przygotowany stan migracyjny z from/to revision w Store →
update entry → finalizacja Store. Runtime pozostaje wstrzymany na granicy zmiany.
Restart z przygotowaną zmianą uzgadnia jedynie zgodne rewizje entry/Store;
niejednoznaczność blokuje wykonanie i zgłasza naprawę. Nigdy cichy reset.
Zmiana ustawień CWU nie dotyka ConfigEntry i nie wymaga tego protokołu.

## Recorder i odbudowa

Korzystamy z API `recorder.history.get_significant_states` przez
`recorder.get_instance(hass).async_add_executor_job`, nie własny SQL.
Odczyt selektywny dla skonfigurowanych źródeł, significant_changes_only=false,
minimal_response=false, no_attributes=false. Zwrócone wartości/czasy/jednostki
są normalizowane, nie kopiowane jako niezweryfikowane pomiary fizyczne.
API historii bywa zmienne; izolujemy je w jednej funkcji i testujemy na obu HA.

Start: najpierw subskrypcja + bufor zdarzeń z watermark, potem historia do watermark,
merge z live po (source identity, timestamp, sequence jeśli dostępny), bez duplikatów.
Pobieranie partiami do 6 h na źródło ogranicza chwilową pamięć. Domyślnie 48 h;
T07 proponuje konfigurowalny horyzont od minimalnego potrzebnego okna do 7 dni,
a konkretną granicę należy zatwierdzić jako parametr techniczny.
Brak Recordera lub wyjątek odczytu oznacza jawne odbudowywanie od dostępnych
danych, nie obowiązek posiadania nowej DB.

Recorder zwykle rejestruje zmiany stanów, nie każdy jednakowy raport.
API może też zwrócić stan początkowy przesunięty do granicy zapytania.
Nie traktujemy tej granicy jako chwili nowego raportu; należy odczytać
oryginalną chwilę ostatniej aktualizacji przed oknem albo odrzucić punkt
o nieustalonej świeżości. Brak wierszy nie dowodzi braku fizycznych pomiarów,
a utrzymująca się wartość nie dowodzi ciągłej świeżości.

D97 (przyjęte P08) określa politykę jakości: pokrycie tylko z udokumentowanych
przedziałów ważności, bez przedłużania do następnego odczytu przez luki i restarty.
Od raportu do min(następna utrata, raport+freshness, koniec przedziału).
Dla starych jednakowych wartości bez zachowanego heartbeat pokrycie jest
niepewne. Nie wolno uznać całego 48 h za gotowe tylko dlatego, że ostatni stan
się nie zmienił. Można wykorzystać zapisane raporty czasu fizycznego w
atrybutach źródła, jeżeli profil je wiarygodnie definiuje.
Nie dodajemy własnego archiwum heartbeat w Store.

Agregacja strefy na połączonych granicach ważności termometrów; najpierw
średnia/mediana aktywnych źródeł, potem okna czasowe. Skład jest oznaczony
source_set_revision. Średnia po czasie to suma(value×duration)/valid_duration;
mediana ważona czasem. Gotowość >=80% pełnej długości okna + świeży pomiar teraz.
Przy dokładnie 50% między wartościami mediana to średnia dwóch środkowych D97.
W chwili przekroczenia limitu świeżości przedział staje się luką. Brak danych nie jest sztucznym zerem ani interpolacją.

Live śledzi oba helpery HA: state_changed dla zmian oraz state_reported dla
jednakowych raportów, tylko wybrane encje. last_reported służy świeżości HA,
nigdy potwierdzeniu komendy. Po przerwie procesu nie odtwarzamy heartbeat
z obecnego last_reported wstecz.

## Ograniczenie pamięci i historia decyzji

Propozycje limitów technicznych: horyzont live max 7 dni, 20 000 punktów na źródło,
200 ostatnich decyzji i 200 ostatnich przejść ostrzeżeń w ring RAM.
Przy nadmiarze nie gubimy po cichu jakości: zachowujemy dokładne najnowsze dane,
starsze przycięte obszary są luką. Nie resamplujemy sztucznymi próbkami.
Zmiana limitów i odbiór wydajności w PR historii; limity nie mają być obietnicą
dowolnej liczby encji/raportów.

Temperatury źródeł i własne encje decyzji/ostrzeżeń korzystają z Recordera.
Snapshot decyzji ma reason codes, wkłady, limity, revisions i status dowodu;
bez tablic szeregów, nazw własnych i pełnych wyjątków.
Recorder respektuje filtry i retencję. UI pokazuje brak historii, nie próbuje
omijać wyłączenia encji ani czytać bezpośrednio DB.
Aktywne ostrzeżenia i ich ack są w Store; historyczne wystąpienie/ustąpienie
w Recorderze oraz ograniczonym bieżącym ring.
Nie obiecujemy trwałej historii po jej wykluczeniu przez użytkownika.

## Migracje i powrót

Każda migracja jest funkcją old→new, z walidacją przed zapisem, zachowaniem UUID,
celów, planu, trybów, terminów, nadpisań, liczników i zgodnych źródeł.
Testy obejmują stary poprawny payload, brak pól, nieznaną wersję, uszkodzony JSON,
crash pomiędzy etapami oraz powtórne uruchomienie. Wersja nieobsługiwana lub
nieudana migracja nie zapisuje pustego Store i nie aktywuje wyjść.
Pierwsza wersja nie ma realnej poprzedniej wersji produktu; testy migracji używają
jawnych syntetycznych schematów, nie importera POC.

Release opisuje tabelę odczytu/zapisu wersji schematów.
Powrót zgodny: instalacja starszego pakietu i uzgodnienie stanów po restarcie.
Niezgodny: błąd bez kasowania, wymagane odtworzenie odpowiedniej kopii HA
zgodnie z osobnym planem właściciela. Sam backup pliku Store może nie wystarczyć
przy zmianie ConfigEntry/rejestrów. PR dokumentacyjny nie uruchamia backupu,
restartu ani rollbacku domu.

D90: Store zachowuje provisional_at, verification_due i verified_at osobno.
Restart nie promuje provisional do confirmed samym upływem czasu. Po odtworzeniu
zgodnego aktualnego żądania wykonujemy bieżący odczyt; jeśli termin kontroli minął,
poprawny zgodny odczyt może zakończyć potwierdzenie. Brak/zmiana żądania unieważnia
stary zamiar. Nadpisania CWU przechowują own/external, bez klasy ambiguous i bez
stanu higieny. D95: niezapisany szkic harmonogramu nie jest aktywnym planem.
