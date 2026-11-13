# Środowisko agentic development

To lekkie instrukcje repozytorium i GitHub Actions, bez serwera agentów i bez kodu
sterującego pompą. Punktem wejścia jest [AGENTS.md](../../AGENTS.md).

| Materiał | Zastosowanie |
| --- | --- |
| [Ocena bazy](baseline.md) | Co istniało i czego jeszcze nie ma |
| [Workflow](workflow.md) | Wymagania → projekt → implementacja → review → PR |
| [Tech Lead / Orchestrator](roles/tech-lead.md) | Projekt, zależności i przekazanie |
| [Developer](roles/developer.md) | Mała implementacja zgodna z projektem |
| [Reviewer](roles/reviewer.md) | Niezależny przegląd zachowania i ryzyk |
| [Tester](roles/tester.md) | Scenariusze, regresje i dowody |
| [Release / Deployment](roles/release-deployment.md) | Gotowość wydania i plan wycofania |
| [Standardy i bezpieczeństwo](standards.md) | Czytelny kod i granice sterowania |
| [CI i uruchomienie lokalne](ci.md) | Kontrole teraz i po dodaniu integracji |
| [Projekt techniczny do przeglądu](../technical/README.md) | Architektura, pytania, macierz A/B i plan PR-ów |
| [Brief projektu technicznego](technical-design-brief.md) | Konkretne następne zadanie |
| [Przekazania dla Developera](handoffs/README.md) | Aktualnie I04: wersjonowany Store, po sprawdzonym i scalonym I03 |
| [Szablon przekazania](templates/handoff.md) | Kontrakt między rolami |

Przykład użycia w dowolnym asystencie pracującym na repo:

> Przeczytaj AGENTS.md i docs/development/roles/tech-lead.md. Wykonaj
> docs/development/technical-design-brief.md na osobnej gałęzi od main.
> Przygotuj dokumentacyjny PR, bez implementacji, merge i deploy.

Dla kolejnej roli podaj zatwierdzony projekt, zakres US/Issue i commit wejściowy
według szablonu przekazania. Nie wymagamy płatnej usługi ani konkretnego modelu.
