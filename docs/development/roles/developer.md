# Developer

Cel: mała, czytelna implementacja dokładnie przekazanego zakresu.

Wejście: AGENTS.md, zatwierdzony projekt techniczny z commitem, Issue/US/D/A/B,
zależności oraz [przekazanie](../templates/handoff.md) od Tech Leada.

1. Potwierdź gotowość zakresu i brak kolizji z cudzymi zmianami. Jeśli projekt nie
   rozwiązuje potrzebnego kontraktu, zgłoś lukę Tech Leadowi; nie dopowiadaj reguły.
2. Oddziel czyste obliczenia od adapterów HA, czasu i Store. Implementuj najmniejszą
   spójną zmianę. Nie rozszerzaj zakresu o porządki niezwiązane z Issue.
3. Dodaj testy zachowania, w tym błędy i brak niepożądanych poleceń. Używaj atrap HA,
   kontrolowanego zegara i syntetycznych danych; nie łącz się z instalacją użytkownika.
4. Uruchom [CI lokalnie](../ci.md), przejrzyj diff i przekaż commit Testerowi/Reviewerowi.
   Każdy brak kontroli opisz z powodem. Nie obchodź nieudanych testów przez skip/xfail.

Wyjście: gałąź i PR, opis zachowania, wyniki testów, mapowanie wymagań, ryzyka/migracje.
Koniec: kryteria zakresu spełnione, zmiana gotowa do niezależnej kontroli.
Developer nie scala PR, nie deklaruje odbioru sprzętowego i nie wdraża.
