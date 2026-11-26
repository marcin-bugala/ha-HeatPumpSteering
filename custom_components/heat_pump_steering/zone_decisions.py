"""Pure zone requests and observation-only temperature condition memory."""

from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import datetime, timedelta
from enum import StrEnum
from math import isfinite
from uuid import UUID


class ZoneRequest(StrEnum):
    OPEN = "open"
    CLOSE = "close"


@dataclass(frozen=True, slots=True)
class ZonePolicy:
    trend_threshold: float = 0.2
    hysteresis: float = 0.2
    sudden_drop: float = 0.7
    confirmation: timedelta = timedelta(minutes=30)
    minimum_closed: timedelta = timedelta(minutes=30)
    loss_grace: timedelta = timedelta(minutes=30)
    overheat_on: float = 0.5
    overheat_off: float = 0.2
    overheat_confirmation: timedelta = timedelta(minutes=60)
    release_confirmation: timedelta = timedelta(minutes=30)
    warning_duration: timedelta = timedelta(minutes=120)
    actuator_duration: timedelta = timedelta(minutes=3)
    priority: int = 3

    def __post_init__(self) -> None:
        for value in (
            self.trend_threshold,
            self.hysteresis,
            self.sudden_drop,
            self.overheat_on,
            self.overheat_off,
        ):
            if isinstance(value, bool) or not isfinite(value) or value <= 0:
                raise ValueError("zone thresholds must be finite and positive")
        if self.overheat_off >= self.overheat_on:
            raise ValueError("release threshold must be lower than activation")
        for duration in (
            self.confirmation,
            self.minimum_closed,
            self.loss_grace,
            self.overheat_confirmation,
            self.release_confirmation,
            self.warning_duration,
            self.actuator_duration,
        ):
            if not isinstance(duration, timedelta) or duration <= timedelta():
                raise ValueError("zone durations must be positive")
        if type(self.priority) is not int or not 1 <= self.priority <= 5:
            raise ValueError("zone priority must be between one and five")


@dataclass(frozen=True, slots=True)
class ConditionProgress:
    elapsed: timedelta = timedelta()
    last_valid_at: datetime | None = None


def _progress(
    previous: ConditionProgress,
    condition: bool | None,
    now: datetime,
    *,
    continuous: bool,
) -> ConditionProgress:
    if condition is False:
        return ConditionProgress()
    if condition is None:
        return replace(previous, last_valid_at=None)
    delta = (
        max(now - previous.last_valid_at, timedelta())
        if continuous and previous.last_valid_at is not None
        else timedelta()
    )
    return ConditionProgress(previous.elapsed + delta, now)


@dataclass(frozen=True, slots=True)
class ZoneMemory:
    request: ZoneRequest | None = None
    target: float | None = None
    source_ids: tuple[UUID, ...] = ()
    lost_since: datetime | None = None
    closed_at: datetime | None = None
    drop_latched: bool = False
    underheat: ConditionProgress = ConditionProgress()
    overheat: ConditionProgress = ConditionProgress()
    release: ConditionProgress = ConditionProgress()
    warning: ConditionProgress = ConditionProgress()
    growth_blocked: bool = False
    warning_active: bool = False
    evaluated_at: datetime | None = None

    def after_restart(self) -> ZoneMemory:
        """Retain accrued progress but never bridge an observation gap."""
        return replace(
            self,
            evaluated_at=None,
            underheat=replace(self.underheat, last_valid_at=None),
            overheat=replace(self.overheat, last_valid_at=None),
            release=replace(self.release, last_valid_at=None),
            warning=replace(self.warning, last_valid_at=None),
        )


@dataclass(frozen=True, slots=True)
class ZoneInput:
    target: float
    current: float | None
    valve: float | None
    comfort: float | None
    trend: float | None
    source_ids: tuple[UUID, ...]
    has_outputs: bool
    # The caller supplies reliable output evidence, never a predicted request.
    observed_open: bool | None = None
    confirmed_closed_at: datetime | None = None
    enabled: bool = True


@dataclass(frozen=True, slots=True)
class ZoneDecision:
    request: ZoneRequest | None
    reasons: tuple[str, ...]
    demand_eligible: bool
    room_correction_eligible: bool
    growth_blocked: bool
    warning_active: bool
    warning_suspended: bool
    priority: int
    next_deadline: datetime | None
    memory: ZoneMemory


_DEFAULT_POLICY = ZonePolicy()


def evaluate_zone(
    data: ZoneInput,
    previous: ZoneMemory,
    *,
    now: datetime,
    policy: ZonePolicy = _DEFAULT_POLICY,
) -> ZoneDecision:
    """Return a request and next memory without reading time or calling HA."""
    if now.tzinfo is None or not isfinite(data.target):
        raise ValueError("zone evaluation requires aware time and finite target")
    if any(
        value is not None and not isfinite(value)
        for value in (
            data.current,
            data.valve,
            data.comfort,
            data.trend,
        )
    ):
        raise ValueError("zone inputs must be finite or unavailable")
    if not data.enabled:
        return ZoneDecision(
            None,
            ("zone_disabled",),
            False,
            False,
            False,
            previous.warning_active,
            True,
            policy.priority,
            None,
            previous.after_restart(),
        )
    changed = previous.target is not None and (
        previous.target != data.target or previous.source_ids != data.source_ids
    )
    memory = previous
    if changed:
        memory = replace(
            memory,
            underheat=ConditionProgress(),
            overheat=ConditionProgress(),
            release=ConditionProgress(),
            warning=ConditionProgress(),
            drop_latched=False,
        )
    continuous = previous.evaluated_at is not None and now >= previous.evaluated_at
    deadlines: list[datetime] = []
    reasons: list[str] = []
    closed_at = data.confirmed_closed_at
    if data.observed_open is True:
        closed_at = None
    elif data.observed_open is False and closed_at is None:
        closed_at = previous.closed_at or now
    # Unknown evidence cannot let an old close deadline authorize opening.
    minimum_due = (
        closed_at + policy.minimum_closed
        if data.observed_open is False and closed_at is not None
        else None
    )
    available = data.current is not None and bool(data.source_ids)
    lost_since = None if available else previous.lost_since or now
    request = memory.request
    if not available:
        loss_due = lost_since + policy.loss_grace
        if now >= loss_due:
            request = ZoneRequest.OPEN
        …10661 tokens truncated…et nie tworzą fałszywego spadku; Tester |
| I08 feat/24-co-calculation | Baza, kwalifikacja i ważony komfort, trend, aktywność modułów; bez usług | US17/18/20; #24 #25 #29; D10,D37,D40–D41,D45,D49; A18–A23,A33,A34,A57 | I06,I07; P09/P10 | Wyniki liczbowe A18–A23; zamknięte vs utracone vs mieszane osobno; Reviewer |
| I09 feat/24-co-constraints | Zakres, siatka, tempo i ochrona wzrostu; nadal obserwacyjnie | US16/17; #23 #24; D38,D42,D50,D61; A21,A24–A26,A35 | I08; P01/P10 | Połówki w górę; D99: clipping do granicy z konfliktem przy nastawie poza zakresem, bez zwykłego limitu kroku/odstępu; inne braki legalnego kroku blokują; ręczna nastawa; Tester |
| I10 feat/11-command-evidence | Dwuetapowy odczyt tej samej encji, provisional/confirmed po 2 min, bez automatycznych usług runtime | US04/16/19; #11 #23 #26; D51,D60,D68; A36,A37,A39 | I03,I05; przyjęte P01/D90 | Wstępny zgodny stan nie kończy kontroli 2 min; zgodny ponowny odczyt, także cache HA, kończy retry bez dodatkowej telemetrii; granice fizycznego dowodu jawne; Reviewer |
| I11 feat/11-command-retries | Jedyny wykonawca, liczniki na wyjście, retry i generation, aktywacja tylko po gotowości | US03/04/17/19; #10 #11 #24 #26; D52,D60,D73–D74,D84; A08,A37–A40; B04,B10 | I04,I09,I10; P01/P03 | Dokładne czasy prób, późny/stary ACK, observation/unload w await; retry nie krokiem CO; Reviewer → Tester |
| I12 feat/17-valve-execution | NC/NO i polaryzacja, raport elektryczny i predicted movement, niezależny eksport stanów | US05/10; #12 #17; D08,D21,D51,D66; A04,A17,A20,A36 | I07,I11; P04 | Brak udawanego physical feedback; błąd close nie usuwa ochrony; Tester |
| I13 feat/16-demand-sequencing | OR, jedna gotowa strefa, brak minimum ON, 15min od OFF, anulowanie ON i ręczny demand | US07/09; #14 #16; D06,D43,D48–D51,D55; A27–A29,A31,A33,A34,A43,A56 | I12; P03 | Cztery kombinacje zawory/demand; bez demandu brak ON/OFF CO; Reviewer → Tester |
| I14 feat/21-dhw-planner | Czysty plan 7×48 i next effective change, DST i override terminy, inicjalizacja | US13/14; #20 #21; D13,D26–D28,D56,D63–D65; A47–A51,A54–A56 | I04; P02/P05/P06 | Bez efektów urządzeń; jednakowe pola nie kończą nadpisania; Tester |
| I15 feat/20-dhw-execution | Temperatura→ponowny odczyt po 2 min→ON, OFF niezależne, każda niealgorytmiczna zmiana external; bez obsługi higieny | US07/13/14; #14 #20 #21; D27,D56,D63–D64,D88; A46–A53; B11 | I10,I11,I14; P01/P02/P05 | Częściowe wykonanie, external bez blokady pochodzenia, restart i brak wymogu encji higieny; brak wpływu awarii na CO; Reviewer → Tester |
| I16 feat/18-product-entities | number celu, switch trybów, sensor/binary/event decyzji, bounded diagnostics i anonimizacja | US02/04/11/12; #9 #11 #18 #19; D79,D81–D83; A07,A59; B12 | I04–I15; P07/P11/P12 | Własne dashboardy bez helperów; testy anonimizacji zagnieżdżeń i PL/EN; Reviewer |
| I17 feat/20-dhw-settings-api | Uwierzytelnione WS odczytu/zapisu, revision conflict, jeden trwały zapis | US13/14; #20 #21; D29–D30,D62–D63; A44,A45,A48,A49 | I14–I16; P06 | Brak częściowego zapisu i last-write-wins; identyczny save kończy override; Tester |
| I18 feat/18-bundled-frontend | Karta, panel CWU, draft/cancel/save i osobny ekran zaawansowany, lint/build/browser CI | US11–14; #18 #19 #20 #21; D29–D30,D62,D79–D81; A44–A56,A59; B02,B13 | I16,I17; P11/P12 | Bundle lokalny, klawiatura/mobile, PL/EN, frontend w zbiorczej bramce CI; Reviewer → Tester |
| I19 fix/15-lifecycle-regressions | Przegląd pełnych restart/reload/unload, reconfigure i aktualizacji na złożonych stanach | US08/19; #15 #26; D54–D55,D71–D74,D84–D89; A41,A43,A51,A56; B03–B12 | I01–I18 | Testy migracji i race bez aktywnego sprzętu; brak nieplanowanych usług; Reviewer → Tester |
| I20 docs/first-developer-release | Materiały wydania beta, instrukcje PL/EN, HACS/manual, macierz, wyniki i rollback | US08/11–14/19; #15 #18–#21 #26; D75–D81,D89; A58; B13 | Całość + osobno autoryzowany odbiór sprzętu | Release/Deployment przygotowuje materiały dla właściciela; żadnego publish/deploy |

Jeśli zakres pakietu przestaje być czytelnym diffem, Tech Lead dzieli go według
kontraktu (np. karta, panel CWU i ekran zaawansowany jako osobne PR-y z własnymi
testami). I18 zalecane podzielić na I18a karta+CI, I18b panel CWU, I18c zaawansowane.
Tak samo I16 można podzielić encje i diagnostykę. Nie przenosić brakujących testów
z implementacji do I19; I19 jest dodatkową regresją, nie odroczoną jakością.

Kolejność umożliwia równoległość logiczną I07–I09 i I14 dopiero po wspólnych
kontraktach, ale delegowanie nie jest uruchomione tym planem.
Developer → Reviewer → Tester → Tech Lead / właściciel to kontrakt pracy.
Autor swojej samokontroli nie zgłasza jako niezależnego review.

## Definition of Done pojedynczego PR

Zmiana realizuje tylko przekazany zakres, ma testy właściwych US/D/A/B i brak
nieuzgodnionych reguł. Uruchomione wymagane komendy z CI, dla kodu także pytest HA
na minimum/current i hassfest; frontend od pierwszego PR ma lint/build/test.
Brak testów/symulacja/skipped jawnie opisane. Uzupełnione PL/EN i procedura
powrotu przy zmianie schematów. Reviewer otrzymuje SHA, diff, źródła i dowody.
Tester raportuje wersję i wyniki dla wskazanego SHA; nowe commity ponawiają
dotknięte kontrole. Merge tylko decyzją właściciela.

Wycofanie PR: zanim wydano produkt, revert małego zakresu przez kolejny PR;
po zmianie danych według macierzy schematów i zgodnej kopii HA.
Nigdy revert schematu z cichym czyszczeniem Store.
Scalenie dokumentacji lub części kodu nie zamyka US pełnego zakresu.

## Konkretne przekazania po scaleniu projektu

- [Weryfikacja I00/I01](../development/handoffs/i00-i01-verification.md):
  oba pakiety scalono w PR #38, commit main 552ea427086786e3b3411d95ed0305dc35ba80c0.
- [I02](../development/handoffs/i02-installation-model.md) wykonano w PR #40;
  [odbiór](../development/handoffs/i02-verification.md) dotyczy SHA 060c0f0 / main 3068903.
- [I03](../development/handoffs/i03-output-ownership.md): kontrakt wykonany
  w PR #42/#43; [odbiór](../development/handoffs/i03-verification.md)
  dotyczy SHA 1b452bd / main 74f326b.
- [I04](../development/handoffs/i04-versioned-store.md) wykonano w PR #45;
  [odbiór](../development/handoffs/i04-verification.md) dotyczy c00c029 / main 5f49b2e.
- [I05](../development/handoffs/i05-source-quality.md): aktualne przekazanie
  Developera; jakość źródeł i raporty HA, nadal bez historii i usług.
- [Pierwotny I00](../development/handoffs/i00-ha-test-tooling.md) i
  [I01](../development/handoffs/i01-ha-foundation.md) pozostają historią kontraktu;
  nie uruchamiać ich ponownie. Zmianę drogi current i wspólny PR opisuje raport.
- I02 ma minimalny D87 po entity_id. I03 rozszerza go na registry identity,
  wszystkie konfigurowane wyjścia i pełną granicę finalizacji/setup.
  Konfiguracja NC/NO/polaryzacji/zaworów/demandu jest częścią I03;
  wykonanie ruchu i sekwencjonowanie nadal I12/I13. I04/I05 muszą korzystać
  z kanonicznych bindingów schema 3, bez cofania do stringów I02.

I02 doprecyzowuje realną migrację z uproszczonego modelu I01 do rozszerzonego
modelu stref. Bieżący cel w ConfigEntry jest wartością bootstrap odziedziczoną
po I01; Store pozostaje I04, bez równoległej kopii celu w options.
Nie zmienia to docelowego działania ani zakresu pierwszego kompletnego wydania.

C01–C13 w verification.md uzupełniają testy pakietów I01–I18: C01/C02 I10–I11,
C03/C06 I14–I15, C04 I13, C05 I03/I12, C07 I14/I17/I18, C08 I04/I07/I16,
C09 I06, C10 I08, C11 I09/I11, C12 I07/I16, C13 I01/I03/I18.
Te testy powstają wraz z odpowiednimi zmianami, nie dopiero w I19.
