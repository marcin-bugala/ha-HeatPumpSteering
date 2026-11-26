# I07 — trwała pamięć decyzji stref

Tech Lead uzgodnił ten kontrakt z Developerem 26 listopada 2026.
Zakres dotyczy US05, US06 i US18 oraz D36, D38, D39, D48, D55, D96 i D100.

## Powód zmiany

I04 odrzucał niepuste pole `zone_memory` w payload v1.
I07 musi zachować żądanie, wiarygodny termin zamknięcia i postęp poprawnych obserwacji przez restart.
Pamięć wyłącznie w RAM nie spełnia tego kontraktu.
I07 podnosi `payload_version` z 1 do 2.
Wersja wrappera HA Store pozostaje 1.1.
ConfigEntry pozostaje w wersji 4.

## Dane i migracja

Pamięć ma jeden rekord na trwały UUID strefy.
Rekord zawiera żądanie, cel, tożsamości źródeł, terminy i ograniczony postęp warunków.
Rekord zawiera również aktywną blokadę wzrostu CO i ostrzeżenie nieskutecznego zamknięcia.
Nie zawiera historii temperatur, tasków ani callbacków.

Nowy parser odczytuje v1 i v2.
Odczyt v1 nadal wymaga pustych pól zarezerwowanych zgodnie z kontraktem I04.
Migracja zachowuje cele, tryby, UUID, obie rewizje oraz oczekującą zmianę konfiguracji.
Pierwszy udany zapis nowego kodu zapisuje v2.
Nieznana wersja lub błędny rekord powoduje odmowę bez pustego resetu.
Usunięcie strefy usuwa jej pamięć przy finalizacji zmiany konfiguracji.
Zmiana nazwy zachowuje UUID i pamięć.
Ponownie utworzona strefa nie dziedziczy pamięci usuniętego UUID.

Zapis korzysta z istniejącej blokady Store.
Runtime publikuje decyzję dopiero po udanym zapisie i ponownym sprawdzeniu aktualności.
Zmiana celu unieważnia zależny postęp temperatury.
Niezależny termin minimum zamknięcia pozostaje zachowany.
Restart usuwa znacznik ostatniej ciągłej obserwacji.
Restart nie dolicza przerwy do potwierdzenia temperatury.

## Wycofanie

Kod sprzed I07 nie obsługuje payload v2.
Starszy parser odmawia odczytu bez kasowania Store i bez aktywacji wyjść.
Sam revert kodu po zapisie v2 nie jest zgodnym rollbackiem danych.
Powrót wymaga zgodnej kopii HA albo osobnego, przejrzanego narzędzia migracji wstecznej.
Ten PR nie wykonuje backupu, restartu ani odtworzenia domu.

## Parametry i granice

`ZonePolicy` udostępnia typowane parametry czystego API.
Wartości początkowe pochodzą z przyjętych decyzji produktu.
Walidacja odrzuca wartości niefinitywne, niepoprawne czasy i sprzeczne progi.
I07 nie dodaje arbitralnych biznesowych minimów i maksimów.
Konfiguracja zaawansowana użytkownika pozostaje w I16/I18.
Priorytet strefy nie zmienia lokalnych progów ani celu.
Ważony błąd i nastawa CO pozostają w I08/I09.
Wiarygodny stan zaworu pozostaje jawnym wejściem.
Żądanie strefy nie dowodzi wykonania ani fizycznego położenia zaworu.
