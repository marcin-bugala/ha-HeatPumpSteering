# I06 — zapis wykonania i granice odbioru

Nadawca: Tech Lead / Orchestrator.
Data: 23 listopada 2026.
Repozytorium: marcin-bugala/ha-HeatPumpSteering.
Pakiet: I06, historia temperatur i okna czasowe.

## Zakres i integracja

I06 wykonano w [PR #48](https://github.com/marcin-bugala/ha-HeatPumpSteering/pull/48).
Baza PR: `d3c79551085bd00fe4e687ab5dd13ab0b581c4f2`.
Końcowy head: `fcc61ac9c6358fdce09e039d276ebbc3e1d056c7`.
Właściciel scalił PR do main jako `626c5b5a291029868aceafad42cee9aabf44b3cf`.
Porównanie head i commitu scalenia nie wykazało zmienionych plików.

Pakiet dodaje odtwarzanie do 48 h z Recordera, granicę live watermark, ograniczone bufory oraz okna średniej i mediany ważonej czasem.
Okno wymaga 80% poprawnego pokrycia i świeżego bieżącego pomiaru.
Kontrolowane przeładowanie zachowuje historię niezmienionego źródła.
Nowe źródło otrzymuje własny bufor.
Zwykły unload porzuca bufor i anuluje oczekujące przeładowanie.
I06 nie wysyła usług do urządzeń i nie zmienia formatu ConfigEntry ani Store.

Zakres dotyczy części US01/#8, US06/#13 i US19/#26.
Obejmuje D32–D34, D47, D53, D71 i D97 w warstwie historii i pomiarów.
Całe historie pozostają otwarte.
Ich status jest prowadzony wyłącznie w Issues.

## Dowody dla ocenionego drzewa

[CI #113](https://github.com/marcin-bugala/ha-HeatPumpSteering/actions/runs/45201212442) wykonało testowy merge `bbe046ff5464ccdcd54a94121d0ccd69497b1b5f` z końcowym head.
Testowy merge i scalony commit mają te same pliki co końcowy head.
Wszystkie siedem zadań CI zakończyło się powodzeniem.
HA 2026.10.4: 180 testów integracyjnych PASS.
HA 2026.11.1: 180 testów integracyjnych PASS, pięć ostrzeżeń deprecacyjnych zależności.
W obu zestawach nie zgłoszono skip ani xfail.
Oba środowiska ha-tooling i pip check, quality, hassfest oraz zbiorcze ci przeszły.
Opis PR podaje samokontrolę Developera i wynik Testera.
Lista GitHub review, komentarzy i wątków PR pozostaje pusta.
Nie ma dostępnego pełnego raportu niezależnego Reviewera dla końcowego drzewa.
Wskazanie `bd00aca` w opisie PR nie identyfikuje dostępnego commitu.
Nie przedstawiamy tego wskazania jako audytowalnej akceptacji.

| Scenariusz | Wynik w I06 | Granica |
| --- | --- | --- |
| A09 | Odtworzenie i gotowość okien sprawdzono w testach integracyjnych. | Bez decyzji regulatora. |
| A30 | Utrata jednego termometru zachowuje drugi i licznik 1/2. | Tylko warstwa pomiarów. |
| A41 | Odtworzenie i połączenie raportu live z historią sprawdzono. | Odpowiedzi Recordera kontrolowano; brak próby rzeczywistej bazy po wielu restartach i dalszych decyzji. |
| A42 | Gotowy pomiar zaworów i niegotowe pozostałe okna rozróżniono. | Reguła decyzji zaworów należy do I07. |
| B08 | Sprawdzono luki, błędy odtwarzania, anulowanie i unload. | Rekordy Recordera są syntetyczne. |
| C09 | Średnia/mediana ważona czasem, próg 80%, luki i retencja. | Brak sprzętu i realnej bazy HA domu. |

Nie uruchamiano poleceń na domowej instalacji.
Dostępne API nie ujawnia wszystkich granic pośrednich sesji Recordera ani ręcznych pauz zapisu.
I06 zachowuje lukę, gdy dostępne dane nie uzasadniają pokrycia.

## Uzupełnienie dowodów

Reviewer ma opublikować pełny wynik dla diffu `d3c7955..fcc61ac9` lub identycznego drzewa `626c5b5`.
Raport ma ocenić US/D/A/B, tożsamość źródeł, watermark, luki, limity bufora i reload/unload.
Tester ma opublikować odrębny raport z listą wykonanych przypadków, SHA i granicą symulacji.
Usterka wskazana przez Reviewera wymaga osobnej poprawki i ponowienia dotkniętych kontroli.
Przed rozpoczęciem zależnej implementacji I07 Tech Lead sprawdza te dowody.
Nie oznaczamy US jako Zakończone na podstawie samego I06.
