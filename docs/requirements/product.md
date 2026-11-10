# Specyfikacja produktu — projekt v0.3

Stan wymagań: 10 listopada 2026. Uzgodnienia i propozycje rozróżnia [rejestr decyzji](decisions.md). Statusy realizacji znajdują się w [Issues](README.md). Brak implementacji produktu.

## Cel i użytkownicy

Publiczna integracja niestandardowa HA ma powoli regulować ogrzewanie z uwzględnieniem komfortu stref oraz dużej bezwładności budynku. Ma ograniczać przegrzewanie, tłumić krótkie zakłócenia i wyjaśniać decyzje. Nie gwarantujemy oszczędności, dokładności predykcji ani niezależnych temperatur tam, gdzie instalacja nie daje niezależnego sterowania.

Odbiorca ma istniejące integracje pompy, termometrów i ewentualnie wyjść wykonawczych. Produkt korzysta z encji HA, nie wymaga jednego producenta sterowników, własnej chmury ani danych logowania Hisense. Hisense/HiMitII to pierwsza konfiguracja referencyjna, nie zamknięty zakres marek.

PC zachowuje sterowanie sprężarką, defrostem, ochroną urządzenia i pompami obiegowymi. Demand oznacza zezwolenie na ogrzewanie, nie odcięcie zasilania pompy. Nie planujemy sterowania sprężarką ani zastępowania zabezpieczeń sprzętowych.

## Podstawa i wybór możliwości

Regulacja nastawy temperatury PC jest podstawą produktu. Początkowe preferencje niezależnych modułów zostają doprecyzowane późniejszą decyzją: nie obiecujemy w v1 produktu działającego wyłącznie jako sterownik zaworów bez regulatora PC. Osobny produktowy tryb F01 bez CO1 pozostaje pytaniem.

Dwie niezależne opcje konfiguracji: sterowanie strefami oraz sterowanie demandem. Dopuszczamy wszystkie cztery kombinacje. Bez demandu nie przełączamy ogrzewania ON/OFF, także przez encję obiegu CO1; pompa decyduje o pracy według swoich zasad i nastawy wody.

| Wejście/wyjście | Warunek wymagania |
| --- | --- |
| Temperatura wnętrza | Co najmniej jeden czujnik na aktywną strefę |
| Cel komfortu | Własny cel każdej aktywnej strefy |
| Bieżąca temperatura zewnętrzna | Wymagana dla regulacji CO1; sama prognoza jej nie zastępuje |
| Nastawa PC | Obowiązkowo wskazana już podczas konfiguracji, również dla obserwacji; bez wskazania nie można jej zakończyć |
| Wyjścia zaworów | Tylko przy włączeniu sterowania zaworami danej strefy; NC/NO wybierane osobno dla tej strefy |
| Wyjście demand | Tylko po włączeniu funkcji demand |
| Prognozy pogody, nasłonecznienia/PV | Opcjonalne |
| Moc/energia PC, zasilanie i powrót | Opcjonalna diagnostyka |
| Sterowanie i nastawa CWU | Warunki opcjonalności modułu do uzgodnienia przed aktywacją CWU |

Brak opcjonalnego źródła nie oznacza zera ani awarii całego produktu. Niedostępność uprzednio wybranego źródła jest jawna. Szczegółowe progi świeżości i zachowanie awaryjne nie zostały jeszcze zatwierdzone.

## Model instalacji i stref — ustalenia rundy 1

Pełny zapis uzgodnień i scenariuszy: [runda 1](round-01-installation-zones.md).

- Pierwsza wersja obsługuje jeden wspólny obieg grzewczy i jedną nastawę temperatury wody PC dla wszystkich stref. Wiele niezależnych obiegów nie należy do jej zakresu.
- Wymagane minimum konfiguracji: wskazana encja nastawy PC, czujnik bieżącej temperatury zewnętrznej oraz co najmniej jedna aktywna strefa z termometrem i celem.
- W obserwacji odczytujemy nastawę PC i porównujemy z propozycją, bez wysyłania zmian. Późniejsza niedostępność encji należy do rundy awarii.
- Strefy są niezależne. Grupy porządkowe, np. Parter, służą prezentacji; nie mają odrębnych celów, wyjść ani dodatkowego udziału w regulacji.
- Strefa może mieć jeden lub kilka termometrów, z wyborem pomiaru głównego albo agregacji średnią/medianą. Dokładne reguły filtracji i braków danych pozostają na rundy regulacji i awarii.
- Wyjście zaworów należy do dokładnie jednej strefy i nie może być współdzielone z inną. Strefa może mieć kilka wyjść; jeden przekaźnik może obsługiwać grupę pętli.
- NC/NO wybieramy osobno dla każdej strefy sterującej zaworami, wspólnie dla wszystkich jej wyjść. Typy mogą różnić się między strefami.
- Opcjonalna informacja „część pętli pozostaje otwarta” nie tworzy wyjść ani obowiązku wpisywania liczby pętli i przepływów.

## Moduły

| ID | Moduł | Zakres |
| --- | --- | --- |
| F00 | Konfiguracja | UI HA, wybór encji, stref i możliwości, późniejsza edycja |
| F01 | Skropliny | Osobna logika grzałki odpływu i diagnostyka, późniejszy etap |
| F02 | CO1 | Krzywa, komfort, trendy, ograniczone korekty i kontrola poleceń |
| F03 | Strefy | Cele, zapotrzebowanie, grupy wyjść, stan polecony/przewidywany/potwierdzony |
| F04 | Demand | Opcjonalne zezwolenie na ogrzewanie, agregacja i sekwencje do dopracowania |
| F05 | Obsługa i diagnostyka | Dashboard, wyjaśnienia, obserwacja, historia i ręczna kontrola |
| F06 | CWU | Praca stała lub tygodniowy harmonogram z temperaturą na przedział |
| F07 | Prognozy | Opcjonalne korekty pogody i słońca/PV; zakres wydania do ustalenia |

### F02 — regulacja CO1

- PC pracuje w trybie stałej nastawy zasilania kontrolowanej przez HA; aktywna pogodówka producenta nie powinna równolegle nadpisywać tej samej nastawy.
- Baza: `Tbase = A + B × (Tref − Ta)`. A, B i Tref konfigurowane oddzielnie. Propozycja początkowa: A=20°C, B=0,2, Tref=20°C, Ta jako średnia 2 h.
- Komfort pomieszczeń jest istotnym wejściem, a nie wyłącznie dodatkiem do dokładnej krzywej Hisense. Osobno pokazywane są baza i korekty komfortu, trendu oraz prognoz.
- Krótkie gotowanie/słońce i wietrzenie mają ograniczony wpływ na CO1. Nie wolno bezterminowo ignorować trwałego wzrostu temperatury.
- Szybszy odporny pomiar strefy dla zaworów, wolniejszy filtr komfortu oraz trend są odrębnymi sygnałami.
- Konflikt stref bez fizycznego odcięcia wymaga jawnego kompromisu. Jedna chłodna strefa nie może bez ograniczeń wymuszać przegrzewania innych; dokładna reguła i wpływ wag pozostają do uzgodnienia.
- Temperatura jest ograniczona zakresem urządzenia i instalacji. Osiągnięcie limitu jest pokazywane; nie omijamy go przez nieuzgodnione przełączanie PC.
- Martwa strefa ±0,2°C, filtry 3–6 h, trend 12–24 h, korekta ±2°C i zmiany 1°C/około 120 min to kandydaci do kalibracji, nie uniwersalne obietnice produktu.
- POC opisuje minimum encji HiMitII MB 20°C; wcześniejsze przypuszczenie 27°C nie jest uniwersalnym limitem produktu. Zakres realnej pompy i wiarygodność raportowanych limitów wymagają weryfikacji.
- Natychmiastowa zmiana encji po zapisie może być optymistyczna. Potrzebny jest niezależny dowód odczytu; zwykłe zdarzenie stanu, last_reported lub upływ czasu nie dowodzą wykonania.

### F03/F04 — strefy, zawory i demand

Strefa może oznaczać dom, kondygnację albo pomieszczenie. Strefy mają niezależne cele; grupy są wyłącznie porządkowe i nie tworzą hierarchii regulatorów. Dopuszczamy jeden lub kilka termometrów, z pomiarem głównym albo średnią/medianą. Szczegóły obliczeń pozostają do ustalenia. Nie narzucamy trzech pięter jako limitu produktu.

Strefa może mieć jeden przełącznik grupy pętli albo kilka wyjść; każde wyjście należy tylko do jednej strefy. Pętle stale dostępne i ręcznie zdławione pozostają poza sterowaniem; opcjonalnie oznaczamy ich obecność przy strefie bez tworzenia pełnego rejestru pętli i przepływów. Otwarcie siłownika nie usuwa nastawy przepływu na rotametrze.

NC: zasilanie otwiera, brak zasilania zamyka. NO: odwrotnie. Typ wybierany jest osobno dla każdej strefy i dotyczy wszystkich jej wyjść; nie stosujemy globalnego typu ani wyjątków NC/NO na pojedynczych wyjściach. Ewentualne odwrócenie logiki przekaźnika musi być rozróżnione od typu siłownika. Bez sprzężenia zwrotnego stan zaworu jest przewidywany, po uwzględnieniu czasu ruchu, nie sprzętowo potwierdzony.

Planowana agregacja demandu: OR zapotrzebowań aktywnych stref, ze stanem niepewności zamiast uznawania braku danych za brak zapotrzebowania. Progi, czasy i kolejność zaworów/demandu wymagają specyfikacji. Stałe otwarte pętle nie oznaczają automatycznie ciągłego zapotrzebowania; decyzja o ich wpływie na model pozostaje otwarta.

### F06 — CWU

Uzgodnienia codziennej obsługi: [runda 2](round-02-daily-operation.md).

- Trzy tryby: Wyłączone (bez podgrzewania CWU, bez wyłączania CO), Stałe (jedna nastawa) i Harmonogram.
- Harmonogram dotyczy wyłącznie CWU; nie wprowadza harmonogramu ogrzewania pomieszczeń.
- Każdy dzień tygodnia ma 48 logicznych przedziałów 30 min; przedział wyłączony albo włączony z własną temperaturą.
- Włączenie oznacza zezwolenie na podgrzewanie; pompa zachowuje swój cykl pracy i zabezpieczenia.
- Ręczne nadpisanie stanu lub temperatury w trybie Harmonogram działa po zatwierdzeniu do następnej zaplanowanej zmiany stanu/temperatury; identyczne półgodzinne pola nie kasują nadpisania. Tryb pozostaje Harmonogram.
- Można ręcznie włączyć CWU w zaplanowanym okresie wyłączenia. Przy włączeniu panel podpowiada ostatnią temperaturę zadaną z możliwością edycji przed zapisem.
- Jeden panel CWU obejmuje tryb, temperatury, ręczny stan i harmonogram. Zmiany są robocze do jednego „Zapisz”; walidacja dotyczy całości i nie dopuszcza częściowego zapisu ustawień. Nie oznacza to atomowego wykonania kilku poleceń przez pompę.
- Zamknięcie panelu z niezapisanymi zmianami wymaga potwierdzenia ich odrzucenia. Nie wprowadzamy dodatkowego potwierdzenia samego wyboru Wyłączone.
- Panel nie obejmuje celów CO ani przełączników obserwacja/sterowanie.
- CO i CWU mają oddzielne przełączniki obserwacja/sterowanie. Zapis ustawień CWU w obserwacji nie zezwala na wykonanie poleceń urządzenia.
- Restart, zmiana czasu, opcjonalność modułu i wydanie, inicjalizacja temperatury bez wcześniejszej nastawy, błędy wykonania i higiena pozostają do dopracowania. Nie zastępujemy programów higienicznych producenta.

### F07 — prognozy i wagi

- Konfigurujemy znaczenie stref oraz osobno siłę wpływu pogody i słońca/PV. Nie definiujemy wag mieszania zewnętrznych źródeł celów komfortu.
- Dane prognoz muszą mieć rozpoznane jednostki, czas wydania/ważności, zasięg i luki.
- PV jest wskaźnikiem słońca, nie miarą ciepła domu. Ekspozycja paneli i okien może się różnić; zachmurzenie, rolety, zacienienie i ograniczenia falownika mogą zaburzać zależność.
- Nie liczymy dwukrotnie tych samych zysków z PV i prognozy nasłonecznienia. Brak PV nie oznacza braku słońca.
- Korekty mają ograniczony wpływ i są wyjaśniane. Zanik jakości prognozy nie może utrzymywać trwałej redukcji ogrzewania.
- Dokument POC proponuje analizę godzinową do 48 h, okna 24/48 h, prognozy temperatur wnętrza 1/3/6 h, uczenie opóźnienia i osobnych zysków stref. To kierunki do oceny, nie zatwierdzony zakres v1.
- Model uczony, jeśli zostanie przyjęty, najpierw pracuje obserwacyjnie. Należy archiwizować prognozę dostępną w chwili decyzji i oddzielić uczenie od walidacji. Nie oceniamy dawnych decyzji później skorygowaną prognozą.

### F01 — skropliny, późniejszy etap

Ustalona potrzeba: grzać przy temperaturze zewnętrznej poniżej −5°C i potwierdzonej pracy pompy; minimum 30 min pracy grzałki; co najmniej 20 min po zatrzymaniu; ponowne uruchomienie pompy anuluje poprzedni wybieg.

Wymagane są histereza temperatury, diagnoza faktycznego poboru, obsługa restartów i zaników odczytów. Nie ustalono progu mocy klasyfikującego pracę. A2W_SW_ON nie jest potwierdzonym stanem sprężarki.

Propozycja łączenia timerów: wyłączenie nie wcześniej niż późniejszy z terminów start grzałki+30 min i ostatni stop pompy+20 min, jeśli nie powstało nowe zapotrzebowanie. Ta reguła, zachowanie po ociepleniu i przy nieznanym stanie wymagają zatwierdzenia.

## Obserwacja, diagnostyka i niezawodność

- Start nowej konfiguracji w obserwacji. Wyjścia objęte obserwacją nie otrzymują poleceń; algorytm nadal oblicza decyzje.
- Użytkownik sam aktywuje sterowanie. Powrót do obserwacji zatrzymuje kolejne polecenia i nie cofa ostatnich nastaw.
- Przy aktywacji ponowna ocena aktualnych danych zamiast wykonywania historycznej kolejki.
- CO i CWU mają dwa niezależne przełączniki obserwacja/sterowanie; włączenie jednego nie aktywuje drugiego. Relacja do F01 i odtwarzanie trybów po restarcie pozostają do uzgodnienia.
- Pamięć zachowuje cele i potrzebny stan; nie dopisuje fikcyjnych pomiarów ani potwierdzeń podczas przerw.
- Wymagane jawne reguły dla restartu, przeładowania, wyłączenia/usunięcia integracji, braku termometrów, chmury i ręcznej zmiany.
- Ograniczone ponowienia; brak dwóch aktywnych regulatorów na tym samym wyjściu.
- Rozróżniamy zezwolenie na grzanie, raport HA, rzeczywistą pracę sprężarki i fizyczne wykonanie polecenia.
- Dashboard: cele i pomiary, zawory, dostępny stan pompy, moc i energia, jakość danych, filtry/trendy, decyzje, nastawy proponowane/wysłane/potwierdzone, limity i timery.
- Encje produktu mają umożliwiać także własny dashboard. Nie rozstrzygnięto wyboru climate/number ani konieczności własnej karty.
- Diagnostyka bez sekretów; bez obowiązkowej telemetrii produktu.

## Codzienna obsługa CO

Zmiana celu CO jest nową, trwałą nastawą konkretnej strefy, zachowaną po restarcie. Nie jest czasowym nadpisaniem i nie ma harmonogramu CO. Obsługa celu jest poza panelem zbiorczego zapisu CWU; nie omija ograniczeń regulatora.

## Referencyjna instalacja użytkownika — nie ograniczenie produktu

Hisense Hi-Therma 8 kW monoblok, podłogówka i bufor jako sprzęgło rozdzielający obieg pompy ciepła i obieg podłogówki. Dwie kondygnacje, docelowo trzecia.

| Element | Ustalenie |
| --- | --- |
| Parter | Cel początkowy 21°C; 8 pętli, 5 planowanych siłowników |
| Piętro | Cel początkowy 22°C; 8 pętli, 7 planowanych siłowników |
| Siłowniki | SALUS T30NC230, NC, M30×1,5, 230 V — ostatnia korekta użytkownika |
| Pozostałe pętle | Bez siłowników, planowany przepływ ręcznie do 1 l/min na pętlę; nie pełny przepływ |
| Wyjścia | Rozważane po jednym Shelly 1PM Mini Gen3 na grupę; KinCony A8v3+ESPHome jako alternatywa wielokanałowa |
| Dodatkowe pomiary | Rozważane sondy zasilania/powrotu; nie uznajemy ich za zainstalowane |
| Demand | Planowany suchy styk; połączenie i znaczenie wejścia Hisense do weryfikacji |

Pompa wtórna i zapewnienie przepływu zostały przez użytkownika odłożone do osobnego zadania. Nie dobieramy ich tutaj i nie traktujemy tego odłożenia jako potwierdzenia gotowości hydraulicznej do uruchomienia wyjść. Jednego konkretnego przepływu nie przedstawiamy jako gwarantowanego zabezpieczenia wszystkich instalacji.

## Publiczna dystrybucja

Plan: instalacja ręczna i HACS jako custom repository, jedna integracja w repozytorium, PL/EN, wersjonowane wydania, opis kompatybilności i ograniczeń, instrukcje migracji/wycofania. Zgłoszenie do katalogu domyślnego HACS jest późniejszym zadaniem, nie warunkiem rozpoczęcia.

Domena techniczna, minimalna wersja HA i kontrakty encji zostaną ustalone przed pierwszym kodem. Kandydat domeny: heat_pump_steering. Nie ustalamy jeszcze usług ani schematów API, których zachowanie nie jest uzgodnione.
