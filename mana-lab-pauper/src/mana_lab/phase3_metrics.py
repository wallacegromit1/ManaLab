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


def validate_aggregation_coverage() -> None:
    registry = set(PHASE3_METRIC_REGISTRY)
    routes = set(AGGREGATION_METHODS)
    if registry != routes:
        raise ValueError(f"metric aggregation coverage mismatch missing={sorted(registry-routes)} extra={sorted(routes-registry)}")


def _trial_key(event: Mapping[str, Any]) -> tuple[str, int | str, int, bool]:
    return (
        str(event.get("scenario", "")), event.get("replicate", ""),
        int(event.get("trial_id", event.get("trial", 0))), bool(event.get("on_play", False)),
    )


def validate_event_stream(events: Iterable[Mapping[str, Any]]) -> list[dict[str, Any]]:
    rows = [dict(event) for event in events]
    seen_event_ids: set[tuple[tuple[str, int | str, int, bool], int]] = set()
    seen_primary_opportunities: set[tuple[Any, ...]] = set()
    for event in rows:
        if "event" not in event or "event_id" not in event:
            raise ValueError("event row missing event/event_id")
        identity = (_trial_key(event), int(event["event_id"]))
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
    return rows


def evaluate_critical_sequences(events: Iterable[Mapping[str, Any]]) -> dict[str, bool]:
    rows = list(events)
    functional = [event for event in rows if event.get("event") == "spell_resolution" and event.get("functional")]
    casts = [event for event in rows if event.get("event") == "spell_cast"]
    windows = [event for event in rows if event.get("event") == "opponent_window"]
    cards_by_turn = defaultdict(list)
    for event in functional:
        cards_by_turn[int(event.get("turn", 0))].append(str(event.get("card", "")))

    def resolved(card: str, turn: int) -> bool:
        return card in cards_by_turn[turn]

    def interaction(turn: int, card: str | None = None, *, metalcraft: bool = False) -> bool:
        for event in windows:
            if int(event.get("turn", 0)) != turn or not event.get("payable"):
                continue
            if card is not None and event.get("card") != card:
                continue
            if metalcraft and not event.get("metalcraft", event.get("full_effect", False)):
                continue
            return True
        return False

    cryogen_draws = sum(
        event.get("event") == "draw" and "Cryogen" in str(event.get("reason", event.get("source", "")))
        for event in rows
    )
    hawk_returned_cryogen = any(
        event.get("event") == "glint_hawk_return" and event.get("returned") == "Cryogen Relic"
        for event in rows
    )
    t3_cards = cards_by_turn[3]
    affinity_cards = {"Thoughtcast", "Myr Enforcer", "Refurbished Familiar", "Utrom Monitor"}
    draw_development = {"Baleful Strix", "Cryogen Relic", "Thoughtcast"}
    return {
        "T2_STRIX_UB": resolved("Baleful Strix", 2),
        "T2_CRYOGEN": resolved("Cryogen Relic", 2) and cryogen_draws >= 1,
        "T2_THOUGHTCAST": resolved("Thoughtcast", 2),
        "T2_FAMILIAR": resolved("Refurbished Familiar", 2),
        "T2_MONITOR": resolved("Utrom Monitor", 2),
        "T3_CRYOGEN_HAWK_LOOP": resolved("Cryogen Relic", 3) and resolved("Glint Hawk", 3) and hawk_returned_cryogen and cryogen_draws >= 2,
        "T3_DRAW_PLUS_INTERACTION": any(card in draw_development for card in t3_cards) and interaction(3),
        "T3_AFFINITY_PLUS_INTERACTION": any(card in affinity_cards for card in t3_cards) and interaction(3),
        "T4_DOUBLE_SPELL": len(cards_by_turn[4]) >= 2,
        "OPP_FULL_DISPATCH": interaction(3, "Dispatch", metalcraft=True) or interaction(4, "Dispatch", metalcraft=True),
        "OPP_FULL_BLAST": interaction(3, "Galvanic Blast", metalcraft=True) or interaction(4, "Galvanic Blast", metalcraft=True),
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
    primary_spells = [
        event for event in rows
        if event["event"] == "spell_window" and event.get("event_role") == "primary_pre_spend_opportunity"
    ]
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

