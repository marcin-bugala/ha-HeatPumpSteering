# Frontend, karta i atomowy zapis CWU

Podstawa D29–D30, D62–D65, D79–D83. T04: TypeScript + Lit, jeden lokalny
bundle ES module dostarczany w custom_components/heat_pump_steering/frontend.
Lit (BSD-3-Clause) jako mała zależność UI, bez bibliotek kart innych autorów.
Dev: przypięty bundler, lint, testy komponentów i przeglądarkowe, lockfile.
Nie używać prywatnych globalnych HA klas jako bazy ani CDN.

Karta `custom:heat-pump-steering-card` implementuje setConfig, hass i
getCardSize/getGridOptions. Panel produktu rejestrowany przez standardowy
frontend HA; obejmuje widok CWU i osobny ekran zaawansowany.
Statyczne pliki przez async_register_static_paths, wersjonowany URL bundle.
Dokumentacja PL/EN podaje dodanie zasobu karty do Lovelace oraz przykładową
konfigurację entry_id. Integracja nie nadpisuje dashboardów użytkownika.
Panel i zasób współdzielone przez wpisy, rejestrowane raz; unload jednego entry
nie usuwa frontendu pozostałym. Po unload ostatniego panel znika, dostępny
statyczny bundle bez runtime nie może sterować.

## Odczyt i zapis

Karta czyta własne standardowe encje i ograniczony snapshot przez uwierzytelnione
HA WebSocket. Nie przechowuje własnego modelu algorytmu.
Backend jest jedynym walidatorem i właścicielem trwałych nastaw.
Cele stref przez number.set_value; tryby przez switch standardowych encji.
Żadne UI nie wywołuje usług źródłowych wyjść bezpośrednio.

Proponowane komendy WS v1, z walidowanym entry_id, uwierzytelnieniem HA i
sprawdzeniem uprawnień użytkownika do danej instalacji:
- get_snapshot: revision, module availability, decisions, warnings;
- get_dhw_settings: komplet edycji i settings_revision;
- save_dhw_settings: expected_revision, mode, constant_temperature?, 7×48 slots;
- get/save_advanced_settings: tylko admin, expected_revision i pełny zmieniany zakres;
- mark_warning_read: warning_id, bez skasowania przyczyny.

Zmiana konfiguracji urządzeń przez flow HA; WS zaawansowane nie omija rezerwacji
wyjść ani ostrzeżeń odłączenia. Payloady rozróżniają błędy walidacji pól,
conflict_revision, storage_failed, module_disabled i unconfirmed_output.
Uprawnienia zapisu celów/trybów jak dla encji HA, nie anonimowy dostęp.

## Transakcja CWU

Otwórz → pobierz snapshot → utwórz draft w UI.
Wyłączone blokuje temperaturę i plan; Stałe tylko temperaturę; Harmonogram
tylko plan. Niedostępne pola zachowują wcześniejsze dane, nie są automatycznie kasowane.
Kopiowanie dnia jest operacją draft, bez usług urządzeń.

Zapisz wysyła cały zestaw i expected_revision. Backend pod blokadą:
sprawdza rewizję → waliduje wszystkie aktywne pola i zgodność zachowanych danych
z zakresem → zapisuje jeden Store payload → publikuje nową rewizję →
zleca bieżącą ocenę. Nieudany zapis: stary stan obowiązuje i błąd UI.
Konflikt dwóch kart: brak last-write-wins, odświeżenie/ponowna edycja.
Nie ma kilku niezależnych usług ustawiania trybu i planu, które mogłyby zapisać połowę.

Zapis Harmonogram kończy nadpisanie również przy identycznym planie;
dlatego identyczny payload jest zdarzeniem użytkownika, nie no-op.
Sukces zapisu ustawień i potwierdzenie ich wykonania w PC to odrębne komunikaty.
W observation sukces nie uruchamia CWU.
Częściowe wykonanie sprzętowe nie cofa atomowego zapisu ustawień.

Zamknięcie draft z różnicami wymaga potwierdzenia odrzucenia. Brak osobnego
potwierdzenia Wyłączone. Przy odświeżeniu/nawigacji najlepsze dostępne
ostrzeżenie przeglądarki; nie obiecujemy zachowania niezapisanego draft po crashu.

## Prezentacja i język

Karta: strefy i cele, aktywne tryby CO/CWU poza edycją CWU, pomiar/komfort,
predicted valve i poziom dowodu, demand, dostępny stan pompy, moc/energia,
decyzja i przyczyny. Brak licznika to „Brak danych”, nie 0.
Nieobecny moduł nie ma pustego panelu. Oczekiwanie na historię, observation,
wyłączony moduł i nieznany stan wyjścia mają odrębne oznaczenia.
Techniczne UUID/sequence nie są podstawową treścią użytkownika.

Reason codes i błędy mają komplet PL/EN. Język z hass.language, fallback EN,
bez mieszania języków wewnątrz komunikatu. Nazwy użytkownika nie są tłumaczone.
Test spójności kluczy backend strings/translations i bundle locale.
Instrukcje instalacji, konfiguracji, aktualizacji/wycofania PL/EN w PR wydania.

Klawiatura, focus trap panelu, etykiety pól, czytelny kontrast i komunikaty
niewyłącznie kolorem. Test desktop i telefon, 7×48 bez poziomego wymuszenia
całego tygodnia; wybór dnia, przyciski kopiowania i lista zmian w draft.
Testy A44–A56 obejmują backend oraz interakcję UI.
