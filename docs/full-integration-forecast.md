# Prognozowanie pogody i zysków słonecznych — pełna integracja

Wymagania projektowe z rozmowy 2026-11-10. Funkcja planowana po POC;
ten dokument nie zmienia działającego sterowania ani nie oznacza instalacji
jakiegokolwiek nowego źródła prognozy.

## Cel

Ograniczyć spóźnione podnoszenie i obniżanie CO1 poprzez przewidywanie
strat ciepła oraz zysków słonecznych. Obserwacja użytkownika: pochmurny dzień
nie przyniósł oczekiwanego dogrzania parteru, a piętro również było chłodniejsze.
Traktować to jako informację do modelu; sam przebieg temperatur nie dowodzi
przyczyny ani wielkości wymiany ciepła między kondygnacjami.

## Wejścia i horyzonty

- Godzinowa prognoza temperatury zewnętrznej na maksymalnie 48 h, zależnie
  od rzeczywistego zasięgu dostawcy; czas wydania i ważności, jednostki, luki.
- Porównanie średnich w kolejnych oknach 0–24 i 24–48 h oraz przebiegu nocnego.
  Średnia dobowa jest wskaźnikiem trendu, nie jedynym wejściem sterowania.
- Większa waga horyzontu zgodnego z wyuczonym opóźnieniem domu, początkowo
  rozważyć 3–12 h; dalszy horyzont służy przygotowaniu i ocenie ryzyka.
- Godzinowa prognoza produkcji PV oraz produkcja rzeczywista, jeśli dostępne.
  Preferowane dodatkowe dane: promieniowanie słoneczne, zachmurzenie,
  pozycja słońca. Nie zakładać, że wybrany dostawca udostępnia wszystkie pola.
- Parametry instalacji PV oraz okien: kierunki, zacienienie i rolety.
  Nie zakładać wspólnej ekspozycji paneli i przeszkleń.

## Interpretacja PV

Prognoza PV jest pomocniczym wskaźnikiem nasłonecznienia, nie prognozą ciepła
przenikającego przez okna. kWh elektryczne PV nie są kWh zysków cieplnych domu.
Uwzględnić orientację, porę roku, ograniczenie falownika, zacienienie i śnieg.
Jeśli dostawca umożliwia, rozważyć normalizację względem produkcji przy
bezchmurnym niebie. Uczyć osobną zależność od nasłonecznienia dla każdej
kondygnacji, z opóźnieniem oraz zakresem niepewności. Oddzielić tę funkcję
od przyszłego planowania zużycia energii pod autokonsumpcję PV.

## Zachowanie regulatora

- Nadchodzące ochłodzenie i małe oczekiwane zyski słoneczne mogą uzasadniać
  wcześniejsze, łagodne zwiększenie dostawy ciepła, jeśli model przewiduje
  niedogrzanie. Sam spadek średniej zewnętrznej nie wymusza podniesienia CO1.
- Oczekiwane słońce może zmniejszyć lub odroczyć podniesienie nastawy,
  jeśli prognoza temperatur wnętrza nadal zapewnia komfort.
- Zachmurzenie po okresie słonecznym powinno usuwać wcześniejszą redukcję
  za oczekiwane słońce. Nie zakładać codziennego powtarzania dziennych pików.
- Przy wspólnym CO1 bez zaworów nie blokować grzania całego domu wyłącznie
  dlatego, że parter ma szansę dogrzać się słońcem, gdy piętru grozi niedogrzanie.
  Stosować jawne rozstrzyganie konfliktów komfortu; niezależne sterowanie
  wymaga fizycznych stref. Zawory nadal są elementem planowanym.
- Zachować ograniczenia temperatur, zmiany pełnymi stopniami, odstępy
  zapisów i ochrony pompy. Prognoza jest ograniczoną korektą, nie pozwoleniem
  na dowolne podgrzewanie domu na zapas.

## Uczenie i wiarygodność

Model oddziela straty do otoczenia, ciepło ogrzewania, zyski słoneczne i
wewnętrzne oraz sprzężenie kondygnacji. Początkowo uczy w tle. Nie przypisuje
całego dziennego wzrostu CO ani całego wzrostu PV słońcu w pomieszczeniach.
Moc elektryczna pompy i stan CO1 nie są bezpośrednim pomiarem ciepła dla CO.

Archiwizować prognozę taką, jaka była dostępna w chwili decyzji, wraz
z wersją modelu, a następnie porównywać z realizacją. Nie oceniać historycznych
decyzji przy użyciu później poprawionej prognozy. Oddzielić okres uczenia
od okresu walidacji; porównywać z obecnym POC i prostą prognozą utrzymania
temperatury, uwzględniając komfort obu kondygnacji oraz liczbę zmian CO1.

Prognoza nieaktualna, niepełna lub sprzeczna z obserwacjami zmniejsza wagę
korekty, a po przekroczeniu limitu jakości wyłącza ją. Powrót do regulatora
opartego na bieżących pomiarach jest automatyczny. Brak danych PV nie oznacza
braku słońca; niespodziewane chmury nie mogą pozostawić trwałego ograniczenia CO.

## Dashboard i kryteria wdrożenia

Pokazywać prognozę temperatury zewnętrznej i PV, trend 24/48 h, przewidywane
temperatury każdej kondygnacji za 1/3/6 h, niepewność oraz osobne korekty za
ochłodzenie i słońce. Wyjaśniać decyzje, np. „odroczenie podniesienia CO1:
oczekiwane dogrzanie parteru, komfort piętra zachowany”. Zapewnić przełącznik
korekty predykcyjnej i ograniczenie jej wpływu.

Najpierw walidacja obserwacyjna obejmująca dni słoneczne, pochmurne i zmiany
pogody, dopiero później ograniczony wpływ na sterowanie. Nie ustalać trwałych
współczynników ani dokładności modelu na podstawie jednej doby.

## Źródła techniczne

- https://www.home-assistant.io/actions/weather.get_forecasts/
- https://www.home-assistant.io/integrations/forecast_solar/
