# Runda 3 — reguły regulacji

Uzgodnienia z 10 listopada 2026. Runda reguł zakończona na poziomie wymagań. Dokument nie opisuje działającej implementacji. Awarie, restarty i braki danych opisuje [runda 4](round-04-failures-restarts.md). Interfejsy modułów pozostają na rundę architektury.


Aktualizacja 11 listopada 2026 po P01–P12: D90–D101 mają pierwszeństwo w
doprecyzowanym zakresie. D99 wprowadza wyjątek od zwykłego kroku/odstępu:
nastawę poza obowiązującym zakresem obcinamy do dopuszczalnej granicy i oznaczamy
konflikt. D90 określa wstępne potwierdzenie od razu i ostateczny odczyt tej samej
encji po 2 min. D96/D97/D98/D100 ustalają cel strefy, jakość historii, przypadki
mieszane i ustępowanie ostrzeżenia. Pozostałe reguły rundy zachowujemy.

## 1. Podział ustawień i brak modelu hydrauliki

Codzienny dashboard służy odczytom, celom komfortu i trybom pracy. Szczegółowe funkcje, okna, współczynniki i programy są w osobnym oknie konfiguracji zaawansowanej.

- Funkcje i okna pomiarowe są wspólne dla programu.
- Strefy mają własne progi reakcji, priorytety i wskazane niżej czasy zabezpieczeń.
- NC/NO pozostaje wyborem strefy z rundy 1.
- Runda 5 określa jeden globalny „Czas pracy siłowników” dla otwierania i zamykania.
- Nie ma pola ani logiki stale otwartych pętli, przepływów lub częściowego odcięcia hydraulicznego. To założenia sprzętowe użytkownika.

Przy konfiguracji sterowania zaworami wyświetlamy:

> Pompa ciepła lub pompa obiegowa może pracować mimo zamknięcia wszystkich sterowanych stref. Instalacja musi zapewniać wymagany przepływ również w takim stanie. Zapewnienie drogi przepływu jest obowiązkiem użytkownika lub instalatora.

To zastępuje D22 i odpowiednie fragmenty rundy 1; nie oznacza rozpoznawania ani sprawdzania hydrauliki przez program.

## 2. Pomiary, funkcje i okna

Najpierw tworzymy jeden pomiar strefy: wybrany termometr główny albo agregacja kilku termometrów, domyślnie średnia ich odczytów. Funkcja agregacji średnia/mediana jest wspólna dla programu; termometry mają równy udział. Następnie z historii pomiaru strefy liczymy okna czasowe.

| Zastosowanie | Funkcja | Zakres okna | Domyślnie |
| --- | --- | --- | --- |
| Temperatura do zaworów | Średnia lub mediana | 30 min–6 h, co 30 min | Średnia, 30 min |
| Temperatura komfortowa do CO1 | Średnia lub mediana | 30 min–6 h, co 30 min | Mediana, 3 h |
| Krótszy punkt trendu zaworów | Wspólna funkcja dla obu punktów: średnia lub mediana | 15 min–2 h, co 15 min | Średnia, 30 min |
| Dłuższy punkt trendu zaworów | Ta sama funkcja co dla krótszego punktu | 2–12 h, co 30 min | Średnia, 4 h |
| Outdoor do krzywej PC | Średnia lub mediana | 30 min–6 h, co 30 min | Średnia, 2 h |

Dla trendu niezależne są czasy, nie funkcje. Krótsze okno musi być krótsze od dłuższego; 2 h / 2 h jest niedozwolone. Funkcje agregacji termometrów i agregacji w czasie są odrębnymi ustawieniami.

Trend zaworów: ΔT = wartość krótszego okna − wartość dłuższego. Domyślny próg osobno dla strefy: 0,2°C. ΔT ≥ +próg oznacza rosnący, ΔT ≤ −próg malejący, pomiędzy — niejasny/stabilny. To wskaźnik różnicy okien, nie pomiar pochodnej w °C/h.

## 3. Reguły stref i zakłócenia

T oznacza temperaturę do zaworów, S cel strefy.

| Żądanie | Trend | Warunek domyślny |
| --- | --- | --- |
| Zamknij / brak zapotrzebowania | Rosnący | T ≥ S |
| Zamknij / brak zapotrzebowania | Niejasny/stabilny | T ≥ S +0,2°C |
| Otwórz / zapotrzebowanie | Malejący | T ≤ S |
| Otwórz / zapotrzebowanie | Niejasny/stabilny | T ≤ S −0,2°C |

Poza warunkami zachowujemy poprzednie żądanie. Równość celu oznacza osiągnięcie/przekroczenie granicy w odpowiednim kierunku, nie wymaganie identycznego odczytu. Progi reakcji i próg trendu są ustawieniami strefy. Stan początkowy bez poprzedniego żądania określa [runda 4](round-04-failures-restarts.md#uruchomienie-i-historia).

Gotowanie, słońce i wietrzenie nie są całkowicie ignorowane. Lokalny wzrost może zamknąć zawory, bez natychmiastowej dużej korekty CO1. Nagły spadek uruchamia zabezpieczenie otwarcia: potrzeba 30 min utrzymującego się warunku niedogrzania w poprawnych obserwacjach. Jeśli warunek ustąpi, potwierdzenie zerujemy. Czas edytowalny dla strefy. Runda 4 ustala domyślny próg nagłego spadku na ponad 0,7°C względem temperatury komfortowej.

Po zamknięciu strefy obowiązuje minimum 30 min przed ponownym otwarciem, ustawiane dla strefy. Zamknięcie przy spełnionym warunku przegrzewania nie ma analogicznej blokady. Gdy obowiązują obie blokady otwarcia, spełnić trzeba obie, ale czasy mogą biec równolegle — nie sumujemy ich automatycznie do 60 min.

## 4. Ważony komfort i konflikt stref

Priorytety stref: 1–5, domyślnie 3, w konfiguracji zaawansowanej strefy. Są wagami: 4 ma dwukrotnie większy udział niż 2; wszystkie równe oznaczają równy wpływ.

Dla strefy e = cel − temperatura komfortowa. Dodatnie e to niedogrzanie, ujemne przegrzanie. Zbiorczy błąd:

E = suma(w × e) / suma(w)

Wybieramy kompromis z ochroną przed przegrzewaniem. Gdy można sterować przegrzaną strefą, priorytetem jest lokalne zamknięcie jej wyjść. Po zamknięciu wszystkich przypisanych wyjść pomijamy odchylenie strefy w korekcie CO1; nadal monitorujemy temperaturę i ostrzeżenie. Bez czujnika położenia nie nazywamy tego potwierdzonym fizycznym odcięciem.

Strefa bez sterowanych wyjść pozostaje uwzględniana wraz z ochroną przed przegrzewaniem. Nie różnicujemy stref według nieznanych programowi dodatkowych otwartych pętli.

Korekta komfortu:
- martwa strefa E: ±0,2°C;
- poza nią 1,5°C wody na 1°C błędu pozostałego po odjęciu martwej strefy;
- początkowe ograniczenie korekty komfortu ±2°C;
- parametry algorytmu w konfiguracji zaawansowanej programu.

Przykład: E=+0,6°C → (0,6−0,2)×1,5 = +0,6°C korekty przed dalszymi ograniczeniami.

## 5. Ochrona przegrzania i ostrzeżenie

Dla stref bez sterowanych wyjść duże trwałe przegrzanie blokuje podnoszenie CO1, nawet gdy E wskazuje niedogrzanie:
- temperatura komfortowa ≥ cel +0,5°C przez 60 min poprawnych obserwacji;
- zwolnienie przy temperaturze komfortowej ≤ cel +0,2°C przez 30 min poprawnych obserwacji;
- progi i czasy osobno dla strefy;
- blokada pozwala utrzymać lub obniżyć nastawę, nie wyłącza automatycznie demandu;
- zwolnienie tylko pozwala na wzrost według aktualnej decyzji i ograniczeń, nie wymusza go.

Ostrzeżenie nieskutecznego zamknięcia:
- najpierw upływa czas zamykania siłowników;
- następnie przez domyślnie 120 min strefa pozostaje zamknięta, temperatura komfortowa ≥ cel +0,5°C i trend zaworów rośnie;
- czas obserwacji i próg temperatury konfigurowalne dla strefy;
- komunikat: „Strefa nadal się nagrzewa mimo polecenia zamknięcia. Sprawdź zawory i inne źródła ciepła.”;
- ostrzeżenie nie przesądza o awarii i samo nie wyłącza całej pompy.

Program nie uwzględnia otwartych pętli w klasyfikacji ostrzeżenia. Runda 5 ustala wspólny czas pracy siłowników, domyślnie 3 min dla obu kierunków. Potwierdzenie zapisu i awarie opisują rundy 4–5. Techniczne źródło potwierdzenia i kasowanie ostrzeżenia pozostają na dalszy etap.

## 6. Długoterminowa korekta trendu CO1

To inny trend niż trend zaworów. Porównujemy temperaturę komfortową teraz i 12 h wcześniej; uwzględniamy priorytety i ten sam zestaw stref co dla komfortu. Porównujemy temperatury, nie sam błąd względem celu, aby zmiana celu nie udawała zmiany temperatury.

Dla ważonego wzrostu:
- do 0,2°C: korekta 0;
- od 0,2°C do 0,5°C: liniowo od 0 do −0,5°C;
- przy ≥0,5°C: −0,5°C;
- korekta działa dopiero, gdy ważona ocena komfortu nie wskazuje niedogrzania;
- sam spadek nie tworzy dodatkowej dodatniej korekty.

Okres, progi i maksymalna korekta są ustawieniami zaawansowanymi programu. Bez wystarczającej historii wyłączona jest ta dodatkowa korekta; podstawowy regulator może działać po przygotowaniu swoich filtrów.

## 7. Wynik CO1 i wykonanie

1. Krzywa Tbase = A + B × (Tref − Ta), z ustalonym pomiarem outdoor.
2. Osobno obliczone aktywne korekty komfortu i trendu.
3. Suma korekt ograniczona wspólnym limitem, domyślnie ±2°C, konfigurowalnym w programie również na większą wartość.
4. Zakres temperatur czytamy z ustawień pompy udostępnionych przez integrację źródłową. Użytkownik może go opcjonalnie zawęzić, nie rozszerzyć.
5. Obliczenia z pełną precyzją; dopiero wynik zaokrąglamy do najbliższej dozwolonej wartości kroku PC, połówki w górę, bez wyjścia poza dopuszczalny zakres.
6. Do wyniku zbliżamy się najwyżej o 1°C co 120 min w obu kierunkach. Maksymalna zmiana i odstęp konfigurowalne, zgodne z możliwościami PC. Brak zbędnego zapisu identycznej nastawy.
7. Obowiązują blokady przegrzewania i tryb obserwacji; aktywacja modułu nie może ich ominąć.

Przykład limitu sumy: komfort +1,5°C i hipotetyczna przyszła korekta +0,8°C dają +2°C przy limicie 2°C. Nie oznacza to aktywnej obsługi prognoz. Większy limit sumy nie znosi pozostałych limitów ani ograniczenia komfortu.

## 8. Demand

- Zapotrzebowanie strefy wynika z reguł otwarcia/zamknięcia. Bez sterowanych zaworów jest wirtualne.
- Zbiorcze zapotrzebowanie: OR aktywnych stref. Bez skonfigurowanego wyjścia wynik tylko diagnostyczny; nie przełączamy wtedy ON/OFF ogrzewania.
- Przy potrzebie ciepła najpierw wydajemy otwarcie zaworów.
- Demand może się włączyć, gdy co najmniej jedna potrzebująca ciepła strefa ma przewidywane otwarcie. Nie czekamy na wszystkie; już otwarta strefa nie zaczyna oczekiwania od nowa.
- Strefa bez sterowanych zaworów nie wymaga opóźnienia otwierania.
- „Czas pracy siłowników” ma domyślnie 3 min, jest wspólny dla domu i konfigurowalny. Obejmuje otwieranie i zamykanie zgodnie z rundą 5. Upływ czasu oznacza przewidywany stan.
- Brak zapotrzebowania wszystkich stref wyłącza demand bez dodatkowego opóźnienia. Nie wprowadzamy minimalnego czasu ON blokującego to wyłączenie.
- Przed ponownym ON wymagane minimum 15 min od OFF, wspólne dla domu i konfigurowalne. Zawory mogą otworzyć się wcześniej; ON nadal wymaga aktualnego zapotrzebowania i gotowości.
- Nie sterujemy zasilaniem PC ani wybiegiem pomp producenta.
- Nie modelujemy pętli stale otwartych.

## 9. Częstotliwość i modułowość

Regulator domyślnie ocenia temperatury, trendy, zapotrzebowanie i CO1 co 5 min; okres wspólny dla domu i konfigurowalny w programie. Zmiana celu/trybu wywołuje dodatkową ocenę. Timery kończą się według swoich terminów, bez dodatkowego czekania na cykl. Dodatkowa ocena nie omija blokad. Dashboard aktualizuje odczyty zgodnie z raportami źródeł.

Kod ma od początku rozdzielać bazę, moduły korekt, sumowanie i zawsze obowiązujące ograniczenia. Dostępne moduły korekt można wybiórczo uruchamiać w konfiguracji zaawansowanej; diagnostyka pokazuje wkład każdego modułu. Obecnie przewidujemy komfort i trend długoterminowy. Wyłączenie korekty nie wyłącza ochrony, limitów ani obserwacji. Kontrakty techniczne zostaną ustalone w rundzie architektury.

## 10. Prognozy odłożone

Pogoda, nasłonecznienie i PV pozostają wymaganiami przyszłej wersji. Bieżąca wersja nie pobiera ich, nie wymaga ich konfiguracji i nie używa ich do sterowania. Nie implementujemy pustych aktywnych modułów prognoz. Modularność ma umożliwić ich dodanie później. Szczegółowy algorytm prognoz pozostaje nieuzgodniony.

## Scenariusze do przyszłego odbioru

- Równe priorytety dają równy wpływ; 4 ma dwa razy większy wpływ niż 2.
- Agregacja wielu termometrów domyślnie średnią poprzedza okna czasowe; funkcje i czasy są wspólne dla programu, progi stref niezależne.
- Dla trendu wspólna funkcja, niezależne okna; 2 h / 2 h odrzucone.
- Rosnący trend i T=S zamyka; malejący i T=S otwiera po blokadach. Niejasny trend używa ±0,2°C.
- Po nagłym spadku brak otwarcia przed 30 min utrzymującego się niedogrzania; ustąpienie warunku zeruje potwierdzenie.
- Minimalne 30 min zamknięcia i potwierdzenie niedogrzania mogą biec równolegle.
- Zamknięta sterowana strefa nie wpływa na korektę komfortu, ale pozostaje monitorowana; strefa bez wyjść pozostaje w ocenie.
- Przegrzanie +0,5°C/60 min blokuje wzrost; +0,2°C/30 min zwalnia, bez wymuszonego podnoszenia.
- Ostrzeżenie po czasie zamykania i 120 min spełnienia wszystkich warunków; brak automatycznej diagnozy awarii.
- Wzrost komfortu o 0,35°C/12 h daje −0,25°C korekty trendu, jeżeli nie ma ważonego niedogrzania.
- Ograniczenie sumy korekt, zakres pompy i węższy zakres użytkownika oraz kwantyzacja nie są omijane.
- Zapotrzebowanie jednej gotowej strefy wystarcza do ON demandu; brak wszystkich wyłącza bez opóźnienia; ponowne ON wymaga 15 min.
- Brak pola/sterowania pętlami stale otwartymi; ostrzeżenie hydrauliczne przy konfiguracji zaworów.
- Wyłączony moduł korekty nie usuwa ograniczeń; prognozy nie są wykonywane.

Są to scenariusze wymagań, nie wykonane testy oprogramowania. Uzgodnione przypadki niepełnych danych, restartów i zamkniętych stref opisuje [runda 4](round-04-failures-restarts.md).

Powiązania: [US01](user-stories.md#us01), [US04](user-stories.md#us04), [US05](user-stories.md#us05), [US06](user-stories.md#us06), [US09](user-stories.md#us09), [US10](user-stories.md#us10), [US15](user-stories.md#us15), [US16](user-stories.md#us16), [US17](user-stories.md#us17), [US18](user-stories.md#us18), [US19](user-stories.md#us19), [US20](user-stories.md#us20), [US21](user-stories.md#us21).
