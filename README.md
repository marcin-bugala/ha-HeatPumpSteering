# HA HeatPumpSteering

Publiczna, planowana integracja niestandardowa Home Assistant do regulacji ogrzewania pompą ciepła z uwzględnieniem komfortu w strefach.

**Stan: definiowanie wymagań. Docelowa integracja nie została jeszcze zaimplementowana.** Dokumentacja opisuje uzgodnienia i propozycje, nie listę dostępnych funkcji.

## Wymagania i praca nad produktem

- [Indeks wymagań i Issues](docs/requirements/README.md)
- [Specyfikacja produktu](docs/requirements/product.md)
- [User stories US01–US19](docs/requirements/user-stories.md)
- [Decyzje i pytania otwarte](docs/requirements/decisions.md)
- [Etapy wydań, testy i migracja](docs/requirements/roadmap.md)

Planowany produkt korzysta z encji HA, bez wymogu jednej marki sterowników. Hisense/HiMitII będzie pierwszą sprawdzaną konfiguracją. Podstawą jest regulacja nastawy temperatury PC; sterowanie strefami i demandem wybiera się niezależnie. Prognozy i dodatkowa telemetria są opcjonalne.

Pierwsza publiczna wersja testowa ma objąć CO1 i strefy. CWU, prognozy, demand oraz ogrzewanie odpływu mają własne wymagania i bramki wdrożenia; ich obecność w specyfikacji nie oznacza dostępności w pierwszym wydaniu.

## Gałęzie

- `main` — specyfikacja i docelowa integracja produktu.
- [`poc/co1-automation`](https://github.com/marcin-bugala/ha-HeatPumpSteering/tree/poc/co1-automation) — rozwój prototypu, jego automatyzacji, historii, dashboardu i testów.
- Osobne gałęzie zmian produktu — przegląd i integracja przez PR do `main`.

POC nie jest automatycznie publikowaną wersją produktu. Wymaga własnej instrukcji instalacji i może aktywnie sterować urządzeniem. Ten dokumentacyjny etap nie zmienia działającego HA.

## Public release — planned

HA HeatPumpSteering is a planned custom Home Assistant integration for slow comfort-aware heat-pump control. This branch currently contains requirements, not an installable integration. The POC is maintained separately on `poc/co1-automation`. Future releases are intended to support Polish and English.

Licencja: [MIT](LICENSE).
