# Workflow od wymagań do PR

## 1. Przygotowanie zakresu — Tech Lead

Odśwież `origin/main`, sprawdź lokalne zmiany i instrukcje. Utwórz osobną gałąź.
Czytaj specyfikację i Issue razem z komentarzami. Zapisz commit źródłowy, US/D/A/B,
zakres, wyłączenia i pytania. Zachowuj istniejące identyfikatory i statusy.

Jeżeli brakuje reguły zachowania, przedstaw właścicielowi rekomendację i jej wpływ.
Można kontynuować niezależne części projektu; zależnej implementacji nie rozpoczynaj
przed rozstrzygnięciem. Nie dodawaj własnych wymogów biznesowych.

## 2. Projekt techniczny — Tech Lead → Reviewer → właściciel

Wykonaj [brief](technical-design-brief.md) jako dokumentacyjny PR.
Każde wymaganie pierwszego wydania musi mieć komponent, dane, kontrakt HA,
zachowanie awaryjne i plan weryfikacji. Oznacz propozycje oraz nierozstrzygnięte punkty.
Reviewer sprawdza zgodność z produktem. Właściciel zatwierdza projekt przed kodowaniem.
Samo zielone CI lub scalenie tego środowiska nie oznacza zatwierdzenia projektu.

## 3. Planowanie i implementacja — Tech Lead → Developer

Podziel projekt na małe PR-y z zależnościami, testami i mierzalnym kryterium końca.
Do przekazania użyj [szablonu](templates/handoff.md). Developer pracuje wyłącznie nad
przekazanym zakresem, dodaje testy zachowania i zgłasza luki projektu.
Pierwszy PR kodowy dodaje też prawdziwe testy HA i zależności CI; nie omija bramek.

Statusy zmienia upoważniony opiekun w istniejącym Issue: Uzgodnione → Zaplanowane →
W realizacji → Do weryfikacji → Zakończone, tylko po spełnieniu definicji z indeksu.
Nie twórz drugiej listy statusów. Zmiana dokumentacji nie zamyka US implementacji;
w PR dokumentacyjnym używaj `Refs #N`, nie `Closes #N`.

## 4. Weryfikacja — Tester i Reviewer

Tester sprawdza kryteria na konkretnym commicie i zapisuje wynik/zakres symulacji.
Reviewer niezależnie ocenia diff, źródła wymagań, bezpieczeństwo, czytelność i testy.
W jednej sesji nazwij drugi przebieg samokontrolą; nie podszywaj się pod niezależnego
recenzenta. Brak niezależnej osoby/roli ujawnij w PR i pozostaw review właścicielowi.
Po poprawkach ponów dotknięte kontrole na nowym commicie.

## 5. PR i integracja — właściciel

PR do `main` opisuje zachowanie, US/D/A/B, wyniki komend, ryzyka i sposób wycofania.
Obowiązują kontrole z [CI](ci.md); wyniki „skipped” nie dowodzą testów HA.
Reviewer nie zatwierdza własnego PR jako niezależnego. Właściciel rozstrzyga
pozostałe pytania i sam podejmuje decyzję o merge. Agenci nie wykonują merge.

Rekomendowane ustawienie GitHub po pierwszym poprawnym przebiegu: ochrona `main`,
wymagane `quality` i `ci`, zatwierdzenie PR przez człowieka, unieważnianie zatwierdzeń
po nowym commicie, bez force-push. Ta zmiana nie modyfikuje ustawień repozytorium;
ich dostępność zależy od planu GitHub. Przy jednym właścicielu nie wymagaj niemożliwego
self-approval — zachowaj ręczną decyzję i jawną informację o braku niezależnego review.

## 6. Wydanie — Release/Deployment → właściciel

Scalenie PR nie jest wydaniem ani wdrożeniem. Rola przygotowuje wersję testową,
changelog, zgodność, instrukcje PL/EN, dowody i rollback. Wydanie, instalacja,
restart HA i uruchomienie sterowania wymagają osobnego zlecenia właściciela.
W tym środowisku nie ma automatycznego publish/deploy ani dostępu CI do domu.
