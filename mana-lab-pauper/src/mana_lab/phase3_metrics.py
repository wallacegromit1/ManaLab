from __future__ import annotations

from collections import Counter, defaultdict
from typing import Any, Iterable, Mapping

from .metrics import PHASE3_METRIC_REGISTRY


# Every registry metric has a predeclared aggregation family.  This table is
# validated as a set equality so a new metric cannot silently lack a route.
AGGREGATION_METHODS: dict[str, str] = {
    "opening_land_distribution": "opening_hand_histogram",
    "mulligan_count_and_kept_hand_size": "opening_hand_means",
    "usable_untapped_mana_by_turn": "primary_snapshot_mean_by_turn",
    "W_U_B_R_access_by_turn": "primary_snapshot_rate_by_turn_color",
    "joint_UB_access_by_turn": "primary_snapshot_rate_by_turn",
    "spell_level_on_time_castability": "unique_primary_spell_opportunity_rate",
    "opponent_turn_interaction_availability": "opponent_window_present_card_rate",
    "full_effect_metalcraft_interaction_availability": "opponent_window_payable_and_metalcraft_rate",
    "double_spell_success": "main_window_functional_resolution_join",
    "spell_plus_held_interaction_success": "main_to_opponent_window_join",
    "artifact_count_by_window": "primary_snapshot_mean_by_window",
    "metalcraft_rate_by_window": "primary_snapshot_rate_by_window",
    "affinity_reduction_by_spell_and_turn": "spell_cast_mean_by_card_turn",
    "boulder_deploy_activation_rescue_dependency": "boulder_event_boolean_rates",
    "cryogen_enter_leave_draw_events": "draw_reason_counts",
    "glint_hawk_functional_execution_and_return_cost": "cast_resolution_return_join",
    "bargain_functional_execution_and_sacrifice_resource_loss": "cast_resolution_resource_join",
    "critical_sequence_success": "frozen_predicate_by_trial",
    "stranded_spell_reason": "failed_primary_spell_opportunity_histogram",
    "realized_etb_tapped_block": "land_entry_block_rate",
    "unused_mana": "post_spend_snapshot_mean",
    "unavailable_tapped_mana": "snapshot_mean_by_window",
    "blood_token_activation_option": "validation_fixture_only",
    "nihil_optional_black_draw_option": "trigger_outcome_join",
    "munitions_activation_option": "validation_fixture_only",
    "cryogen_stun_activation_option": "validation_fixture_only",
    "scry_decision_outcome": "reveal_resolution_join",
    "land_return_events": "hawk_return_replay_join",
    "land_sacrifice_events": "bargain_resource_loss_fields",
}



# Route callables are deliberately small and composable; they operate on
# validated schema-shaped event rows and are used by production table builders.
def opening_hand_histogram(rows): return Counter(int(r["opening_land_count"]) for r in rows if r.get("event") == "opening_hand")
def opening_hand_means(rows): return [r for r in rows if r.get("event") == "opening_hand"]
def primary_snapshot_mean_by_turn(rows): return [r for r in rows if r.get("event") == "state_snapshot" and r.get("event_role") == "primary_pre_spend_opportunity"]
def primary_snapshot_rate_by_turn_color(rows): return primary_snapshot_mean_by_turn(rows)
def primary_snapshot_rate_by_turn(rows): return primary_snapshot_mean_by_turn(rows)
def unique_primary_spell_opportunity_rate(rows): return [r for r in rows if r.get("event") == "spell_window" and r.get("event_role") == "primary_pre_spend_opportunity"]
def opponent_window_present_card_rate(rows): return [r for r in rows if r.get("event") == "opponent_window" and r.get("interaction_in_hand")]
def opponent_window_payable_and_metalcraft_rate(rows): return [r for r in opponent_window_present_card_rate(rows) if r.get("payable") and r.get("metalcraft")]
def main_window_functional_resolution_join(rows): return evaluate_critical_sequences(rows)
def main_to_opponent_window_join(rows): return evaluate_critical_sequences(rows)
def primary_snapshot_mean_by_window(rows): return primary_snapshot_mean_by_turn(rows)
def primary_snapshot_rate_by_window(rows): return primary_snapshot_mean_by_turn(rows)
def spell_cast_mean_by_card_turn(rows): return [r for r in rows if r.get("event") == "spell_cast"]
def boulder_event_boolean_rates(rows): return [r for r in rows if str(r.get("event", "")).startswith("boulder_")]
def draw_reason_counts(rows): return Counter(str(r.get("reason")) for r in rows if r.get("event") == "draw")
def cast_resolution_return_join(rows): return [r for r in rows if r.get("event") in {"spell_cast", "spell_resolution", "glint_hawk_return"}]
def cast_resolution_resource_join(rows): return [r for r in rows if r.get("event") in {"spell_cast", "spell_resolution", "bargain_cast"}]
def frozen_predicate_by_trial(rows): return evaluate_critical_sequences(rows)
def failed_primary_spell_opportunity_histogram(rows): return Counter(str(r.get("failure_reason")) for r in unique_primary_spell_opportunity_rate(rows) if not r.get("castable"))
def land_entry_block_rate(rows): return [r for r in rows if r.get("event") == "etb_tempo"]
def post_spend_snapshot_mean(rows): return [r for r in rows if r.get("event") == "state_snapshot" and r.get("timing") != "start_own_main"]
def snapshot_mean_by_window(rows): return [r for r in rows if r.get("event") == "state_snapshot"]
def validation_fixture_only(rows): return [r for r in rows if str(r.get("event", "")).endswith("_activation")]
def trigger_outcome_join(rows): return [r for r in rows if str(r.get("event", "")).startswith("nihil_")]
def reveal_resolution_join(rows): return [r for r in rows if r.get("event") in {"scry_reveal", "scry_resolve"}]
def hawk_return_replay_join(rows): return [r for r in rows if r.get("event") in {"glint_hawk_return", "hawk_land_replay"}]
def bargain_resource_loss_fields(rows): return [r for r in rows if r.get("event") == "bargain_cast"]

def validate_aggregation_coverage() -> None:
    registry = set(PHASE3_METRIC_REGISTRY)
    routes = set(AGGREGATION_METHODS)
    if registry != routes:
        raise ValueError(f"metric aggregation coverage mismatch missing={sorted(registry-routes)} extra={sorted(routes-registry)}")
    missing_callables = sorted(
        route for route in AGGREGATION_METHODS.values()
        if not callable(globals().get(route))
    )
    if missing_callables:
        raise ValueError(f"metric aggregation routes are not callable: {missing_callables}")


def _trial_key(event: Mapping[str, Any]) -> tuple[str, int | str, int, bool]:
    required = {"scenario", "replicate", "on_play"}
    missing = required - set(event)
    if "trial_id" not in event and "trial" not in event:
        missing.add("trial_id")
    if missing:
        raise ValueError(f"event row missing trial identity fields: {sorted(missing)}")
    if event["scenario"] in {None, ""} or event["replicate"] in {None, ""}:
        raise ValueError("event row has blank trial identity")
    return (
        str(event["scenario"]), event["replicate"],
        int(event["trial_id"] if "trial_id" in event else event["trial"]),
        bool(event["on_play"]),
    )


def validate_event_stream(events: Iterable[Mapping[str, Any]]) -> list[dict[str, Any]]:
    rows = [dict(event) for event in events]
    seen_event_ids: set[tuple[tuple[str, int | str, int, bool], int]] = set()
    seen_primary_opportunities: set[tuple[Any, ...]] = set()
    identities: set[tuple[str, int | str, int, bool]] = set()
    for event in rows:
        if "event" not in event or "event_id" not in event:
            raise ValueError("event row missing event/event_id")
        trial_identity = _trial_key(event)
        identities.add(trial_identity)
        identity = (trial_identity, int(event["event_id"]))
        if identity in seen_event_ids:
            raise ValueError("duplicate event_id within trial")
        seen_event_ids.add(identity)
        if event.get("event_role") == "primary_pre_spend_opportunity":
            if event["event"] == "spell_window":
                opportunity = event.get("opportunity_id")
                if not opportunity:
                    raise ValueError("primary spell opportunity lacks opportunity_id")
                key = (_trial_key(event), event["event"], opportunity, event["event_role"])
            else:
                key = (_trial_key(event), event["event"], event.get("turn"), event["event_role"])
            if key in seen_primary_opportunities:
                raise ValueError("duplicate primary opportunity")
            seen_primary_opportunities.add(key)
    if len(identities) > 1:
        raise ValueError("event stream mixes trial/scenario identities")
    return rows


def evaluate_critical_sequences(events: Iterable[Mapping[str, Any]]) -> dict[str, bool]:
    rows = [dict(event) for event in events]
    if rows:
        identities = {_trial_key(event) for event in rows}
        if len(identities) != 1:
            # A sequence can never be assembled across scenarios/trials.
            return {name: False for name in (
                "T2_STRIX_UB", "T2_CRYOGEN", "T2_THOUGHTCAST", "T2_FAMILIAR",
                "T2_MONITOR", "T3_CRYOGEN_HAWK_LOOP", "T3_DRAW_PLUS_INTERACTION",
                "T3_AFFINITY_PLUS_INTERACTION", "T4_DOUBLE_SPELL",
                "OPP_FULL_DISPATCH", "OPP_FULL_BLAST",
            )}
    functional = [
        event for event in rows
        if event.get("event") == "spell_resolution" and event.get("functional")
    ]
    windows = [event for event in rows if event.get("event") == "opponent_window"]

    def resolved_by(card: str, deadline: int) -> bool:
        return any(
            str(event.get("card", "")) == card
            and 0 < int(event.get("turn", 0)) <= deadline
            for event in functional
        )

    def resolved_on(card: str, turn: int) -> bool:
        return any(
            str(event.get("card", "")) == card and int(event.get("turn", 0)) == turn
            for event in functional
        )

    def interaction_by(deadline: int, card: str | None = None, *, metalcraft: bool = False) -> bool:
        for event in windows:
            turn = int(event.get("turn", 0))
            if turn <= 0 or turn > deadline or not event.get("payable"):
                continue
            if card is not None and event.get("card") != card:
                continue
            if metalcraft and not event.get("metalcraft", event.get("full_effect", False)):
                continue
            return True
        return False

    cryogen_draws_by = lambda deadline: [
        event for event in rows
        if event.get("event") == "draw"
        and "Cryogen" in str(event.get("reason", event.get("source", "")))
        and 0 < int(event.get("turn", 0)) <= deadline
    ]
    hawk_returns_by_t3 = [
        event for event in rows
        if event.get("event") == "glint_hawk_return"
        and event.get("card", event.get("returned")) == "Cryogen Relic"
        and 0 < int(event.get("turn", 0)) <= 3
    ]
    t3_cards = {
        str(event.get("card", ""))
        for event in functional if int(event.get("turn", 0)) == 3
    }
    affinity_cards = {"Thoughtcast", "Myr Enforcer", "Refurbished Familiar", "Utrom Monitor"}
    draw_development = {"Baleful Strix", "Cryogen Relic", "Thoughtcast"}
    t4_uids = {
        str(event.get("uid"))
        for event in functional
        if int(event.get("turn", 0)) == 4 and event.get("uid") is not None
    }
    return {
        "T2_STRIX_UB": resolved_by("Baleful Strix", 2),
        "T2_CRYOGEN": resolved_by("Cryogen Relic", 2) and len(cryogen_draws_by(2)) >= 1,
        "T2_THOUGHTCAST": resolved_by("Thoughtcast", 2),
        "T2_FAMILIAR": resolved_by("Refurbished Familiar", 2),
        "T2_MONITOR": resolved_by("Utrom Monitor", 2),
        "T3_CRYOGEN_HAWK_LOOP": (
            resolved_by("Cryogen Relic", 3) and resolved_on("Glint Hawk", 3)
            and bool(hawk_returns_by_t3) and len(cryogen_draws_by(3)) >= 2
        ),
        "T3_DRAW_PLUS_INTERACTION": bool(t3_cards & draw_development) and interaction_by(3),
        "T3_AFFINITY_PLUS_INTERACTION": bool(t3_cards & affinity_cards) and interaction_by(3),
        "T4_DOUBLE_SPELL": len(t4_uids) >= 2,
        "OPP_FULL_DISPATCH": interaction_by(4, "Dispatch", metalcraft=True),
        "OPP_FULL_BLAST": interaction_by(4, "Galvanic Blast", metalcraft=True),
    }


def aggregate_trial_events(events: Iterable[Mapping[str, Any]]) -> dict[str, Any]:
    rows = validate_event_stream(events)
    validate_aggregation_coverage()
    opening = [event for event in rows if event["event"] == "opening_hand"]
    if len(opening) != 1:
        raise ValueError("each trial must contain exactly one opening_hand event")
    primary_snapshots = [
        event for event in rows
        if event["event"] == "state_snapshot" and event.get("event_role") == "primary_pre_spend_opportunity"
    ]
    if not primary_snapshots:
        raise ValueError("incomplete trial trace: no primary pre-spend state snapshot")
    raw_primary_spells = [
        event for event in rows
        if event["event"] == "spell_window" and event.get("event_role") == "primary_pre_spend_opportunity"
    ]
    # A card/turn/timing opportunity can have multiple desired-window profile
    # labels. The generic trial denominator counts the physical opportunity once;
    # profile-specific aggregation keeps profile populations separate upstream.
    primary_by_physical: dict[tuple[Any, ...], dict[str, Any]] = {}
    for event in raw_primary_spells:
        key = (
            event.get("turn"), event.get("timing"),
            event.get("card_instance", event.get("uid")), event.get("card"),
        )
        primary_by_physical.setdefault(key, event)
    primary_spells = list(primary_by_physical.values())
    opponent = [event for event in rows if event["event"] == "opponent_window" and event.get("interaction_in_hand")]
    etb = [event for event in rows if event["event"] == "etb_tempo"]
    stranded = Counter(str(event.get("failure_reason")) for event in primary_spells if not event.get("castable"))
    turn_rows: dict[str, Any] = {}
    for event in primary_snapshots:
        turn = int(event["turn"])
        turn_rows[str(turn)] = {
            "usable_untapped_mana": int(event["usable_untapped_mana"]),
            "joint_UB": bool(event["joint_UB"]),
            "direct_or_filtered_colors": sorted(set(event.get("direct_colors", [])) | set(event.get("available_filtered_colors", []))),
            "artifact_count": int(event["artifact_count"]),
            "metalcraft": bool(event["metalcraft"]),
        }
    return {
        "trial_identity": _trial_key(opening[0]),
        "opening_land_count": int(opening[0]["opening_land_count"]),
        "mulligans": int(opening[0]["mulligans"]),
        "kept_hand_size": int(opening[0]["keep_size"]),
        "turn_metrics": turn_rows,
        "spell_opportunities": len(primary_spells),
        "spell_castable": sum(bool(event.get("castable")) for event in primary_spells),
        "stranded_spell_reason": dict(sorted(stranded.items())),
        "opponent_interaction_opportunities": len(opponent),
        "opponent_interaction_payable": sum(bool(event.get("payable")) for event in opponent),
        "realized_etb_tapped_blocks": sum(bool(event.get("blocked_action")) for event in etb),
        "critical_sequences": evaluate_critical_sequences(rows),
        "raw_event_count": len(rows),
    }


def provenance_row(
    *, candidate: str, config_hash: str, policy_hash: str,
    seed_partition: str, scenario: str, metric: str, value: float,
) -> dict[str, Any]:
    return {
        "candidate_id": candidate,
        "config_hash": config_hash,
        "policy_hash": policy_hash,
        "seed_partition": seed_partition,
        "scenario_id": scenario,
        "metric": metric,
        "value": float(value),
    }

