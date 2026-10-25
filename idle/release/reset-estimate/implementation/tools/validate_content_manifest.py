#!/usr/bin/env python3
"""Validate Tideglass's launch registry, not the existence of a finished game.

Default mode checks the production contract while permitting explicitly planned
content. --content-gate requires gameplay content while deferring support documents.
--release additionally requires every final file and acceptance evidence.
--self-test exercises known failure modes by mutating an in-memory copy.
"""
from __future__ import annotations

import argparse
import copy
import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_MANIFEST = ROOT / "implementation/content/launch_manifest.json"
STATUSES = {"planned", "in_production", "verified"}
ASSET_STATUSES = {"unproduced", "in_production", "verified"}


def walk(value):
    if isinstance(value, dict):
        yield value
        for child in value.values():
            yield from walk(child)
    elif isinstance(value, list):
        for child in value:
            yield from walk(child)


def validate(data, *, release=False, content_gate=False, root=ROOT):
    """Return actionable contract errors; never interpret plan validity as release."""
    errors = []

    def require(condition, message):
        if not condition:
            errors.append(message)

    def local_file(value):
        if not isinstance(value, str) or not value:
            return False
        candidate = (root / value).resolve()
        return candidate.is_relative_to(root.resolve()) and candidate.is_file()

    if not isinstance(data, dict):
        return ["Manifest must be an object"]
    required = {
        "chapters", "ending", "harbor_presentations", "producer_families",
        "challenges", "calibration_reward_profiles", "calibrations",
        "main_archive", "season_fragments", "cosmetics", "season", "pass",
        "audio", "support_content", "ui_flows", "supporter_bundle", "assets",
    }
    missing = required - data.keys()
    if missing:
        return [f"Missing registry: {key}" for key in sorted(missing)]
    require(data.get("schema_version") == 1, "Unsupported schema version")
    content_groups = ("chapters", "harbor_presentations", "producer_families", "challenges", "calibrations", "main_archive", "season_fragments", "cosmetics", "audio", "support_content", "ui_flows")
    tracked_content = [item for key in content_groups for item in data[key]]
    tracked_content.extend(data[key] for key in ("ending", "season", "pass", "supporter_bundle"))
    tracked_content.extend(item for producer in data["producer_families"] for item in producer["presentations"])
    tracked_content.extend(data["pass"]["free_rewards"] + data["pass"]["premium_rewards"])
    for item in tracked_content:
        require("production_status" in item and "verification_evidence" in item, f"{item.get('id', 'content')}: explicit status and evidence fields required")
    # Authoring fields are schema obligations, not optional flags that can be
    # deleted to bypass a verified record's completion check.
    authoring_groups = [
        (data['chapters'], 'objectives_status', 'objective_spec'),
        (data['challenges'], 'rules_status', 'rule_spec'),
        (data['calibrations'], 'pattern_status', 'pattern_spec'),
        (data['main_archive'] + data['season_fragments'] + [data['ending']], 'copy_status', None),
    ]
    for group, status_field, spec_field in authoring_groups:
        for item in group:
            require(item.get(status_field) in {'not_authored', 'in_production', 'verified'},
                    f"{item['id']}: required {status_field} missing or invalid")
            if spec_field:
                require(spec_field in item, f"{item['id']}: required {spec_field} missing")
                if item.get('production_status') == 'verified':
                    require(isinstance(item.get(spec_field), (dict, list, str)) and bool(item.get(spec_field)),
                            f"{item['id']}: verified content requires a nonempty {spec_field}")
    implementation_states = {'not_implemented', 'in_progress', 'implemented'}
    for item in data['ui_flows']:
        require(item.get('implementation_status') in implementation_states,
                f"{item['id']}: required implementation_status missing or invalid")
        require('acceptance_evidence' in item, f"{item['id']}: required acceptance_evidence missing")
        if item.get('production_status') == 'verified':
            require(item.get('implementation_status') == 'implemented',
                    f"{item['id']}: verified UI requires an implemented flow")
            require(local_file(item.get('acceptance_evidence')),
                    f"{item['id']}: verified UI needs actual acceptance evidence")
    bundle_record = data['supporter_bundle']
    require(bundle_record.get('fulfillment_status') in implementation_states,
            'bundle.supporter: required fulfillment_status missing or invalid')
    if bundle_record.get('production_status') == 'verified':
        require(bundle_record.get('fulfillment_status') == 'implemented',
                'bundle.supporter: verified offer requires implemented fulfillment')
    objects = list(walk(data))
    deferred_content_ids = {item['id'] for item in data['support_content']} | {'ui.help_and_support'}
    content_asset_ids = {ref for obj in objects if obj.get('id') not in deferred_content_ids
                         for ref in obj.get('asset_refs', [])}
    ids = [obj["id"] for obj in objects if "id" in obj]
    require(all(isinstance(id_, str) and id_ for id_ in ids), "IDs must be nonempty strings")
    if not all(isinstance(id_, str) for id_ in ids):
        return errors
    require(len(ids) == len(set(ids)), "All registry and nested IDs must be globally unique")
    assets = {a["id"]: a for a in data["assets"]}
    asset_usage = []
    for obj in objects:
        id_ = obj.get("id", "manifest")
        if "production_status" in obj:
            status = obj["production_status"]
            require(status in STATUSES, f"{id_}: invalid production status")
            if status == "verified":
                require(local_file(obj.get("verification_evidence")), f"{id_}: verified content needs real evidence")
                for child in walk(obj):
                    if child is not obj and "production_status" in child:
                        require(child["production_status"] == "verified", f"{id_}: verified parent contains unfinished content")
                for field in ("objectives_status", "rules_status", "pattern_status", "copy_status"):
                    if field in obj:
                        require(obj[field] == "verified", f"{id_}: {field} is unfinished")
                for field in ("objective_spec", "rule_spec", "pattern_spec"):
                    if field in obj:
                        require(bool(obj[field]), f"{id_}: {field} cannot remain empty")
            if release or (content_gate and id_ not in deferred_content_ids):
                require(status == "verified", f"{id_}: content not verified")
        for ref in obj.get("asset_refs", []):
            asset_usage.append(ref)
            require(ref in assets, f"{id_}: missing asset {ref}")
            if obj.get("production_status") == "verified" and ref in assets:
                require(assets[ref]["delivery_status"] == "verified", f"{id_}: references unfinished asset {ref}")
        if obj.get("implementation_status") == "not_implemented":
            require(obj.get("production_status") != "verified", f"{id_}: unimplemented UI cannot be verified")
        if obj.get("fulfillment_status") == "not_implemented":
            require(obj.get("production_status") != "verified", f"{id_}: unimplemented fulfillment cannot be verified")
    require(set(asset_usage) == set(assets), "All assets must be referenced and all references registered")
    for id_, a in assets.items():
        status = a.get("delivery_status")
        require(status in ASSET_STATUSES, f"{id_}: invalid delivery status")
        if status == "verified":
            for key in ("source_path", "verification_evidence", "license_evidence"):
                require(local_file(a.get(key)), f"{id_}: verified asset needs an existing {key}")
        if status == "unproduced":
            require(a.get("source_path") is None and a.get("verification_evidence") is None,
                    f"{id_}: unproduced asset must not claim a delivered source/evidence")
        if release or (content_gate and id_ in content_asset_ids):
            require(status == "verified", f"{id_}: asset not verified")

    chapters = data["chapters"]
    chapter_ids = {f"chapter.{i:02}" for i in range(1, 7)}
    require({c["id"] for c in chapters} == chapter_ids and len(chapters) == 6, "Exactly six stable chapter IDs required")
    require([c["order"] for c in chapters] == list(range(1, 7)), "Chapters must have sequential order")
    require(len(data["harbor_presentations"]) == 7, "Initial harbor plus six restorations required")
    require({h["restoration_index"] for h in data["harbor_presentations"]} == set(range(7)), "Harbor restoration indices must be 0..6")
    harbors = {h["id"] for h in data["harbor_presentations"]}
    for i, c in enumerate(chapters, 1):
        require(c.get("prerequisite_chapter_id") == (None if i == 1 else f"chapter.{i-1:02}"), f"{c['id']}: wrong chapter prerequisite")
        require(c.get("restored_harbor_id") == f"harbor.restored.{i:02}" and c.get("restored_harbor_id") in harbors, f"{c['id']}: missing matching restoration")
        require(c.get("paid_requirements") == [] and c.get("requires_all_note_sinks") is False, f"{c['id']}: mandatory pay or all-Notes gate prohibited")
    ending = data["ending"]
    require(ending.get("chapter_id") == "chapter.06" and ending.get("invites_continued_play") is True, "Ending must follow chapter six and allow continuing play")
    require(ending.get("paid_requirements") == [] and ending.get("requires_all_note_sinks") is False, "Ending cannot require payment or all Note sinks")

    producers = data["producer_families"]
    require(len(producers) == 5 and {p["tier"] for p in producers} == set(range(1, 6)), "Five producer tiers required")
    require(sum(len(p["presentations"]) for p in producers) == 25, "Exactly 25 producer presentations required")
    for p in producers:
        require([x["ownership_threshold"] for x in p["presentations"]] == [0, 25, 50, 75, 100], f"{p['id']}: base and four milestone presentations required")

    challenges = data["challenges"]
    require(len(challenges) == 12, "Exactly twelve challenges required")
    require(Counter(x["rule_family"] for x in challenges) == {"constrained_fleets": 4, "synergy_priorities": 4, "automation_planning": 4}, "Challenge registry must cover all three rule families with four drafts each")
    for c in challenges:
        require(c.get("dossier_cost") == {"currency": "survey_notes", "amount": 100}, f"{c['id']}: dossier cost must be 100 Notes")
        require(c.get("state_partition") == "challenge" and c.get("main_policy_continues") is True and c.get("export_economic_resources") is False, f"{c['id']}: challenge state must be isolated")
        require(c.get("completion_rewards") == [], f"{c['id']}: new challenge rewards require explicit scope revision")

    profiles = data["calibration_reward_profiles"]
    require(profiles == [{"id": "calibration.standard", "bonus_fraction": 0.2, "duration_seconds": 600, "stacking": "extend_duration", "collectible_award": "completed_pattern"}], "Calibration reward profile must preserve the blueprint")
    require(len(data["calibrations"]) == 12, "Exactly twelve calibration patterns required")
    for c in data["calibrations"]:
        paths = c.get("completion_paths", [])
        require(len(paths) == 2 and {p.get("interaction") for p in paths} == {"untimed_routing", "single_button_completion"}, f"{c['id']}: routing and accessible paths required")
        for p in paths:
            require(p.get("reward_profile_id") == "calibration.standard" and p.get("focus_cost") == 1 and p.get("collectible_pattern_id") == c["id"], f"{c['id']}: accessible and routing rewards/costs/collectibles must be equal")
            require(p.get("time_limit_seconds") is None and p.get("reflex_requirement") is False, f"{c['id']}: completion must be untimed and non-reflex")

    archive = data["main_archive"]
    require(len(archive) == 18, "Exactly eighteen main archive entries required")
    require(Counter(a.get("chapter_id") for a in archive) == {key: 3 for key in chapter_ids}, "Main archive entries need three draft links per chapter")
    fragments = data["season_fragments"]
    fragment_ids = {f["id"] for f in fragments}
    require(len(fragments) == 20 and all(f.get("season_id") == "season.01" for f in fragments), "Twenty Season 1 fragments required")

    cosmetics = data["cosmetics"]
    cosmetic_map = {c["id"]: c for c in cosmetics}
    require(len(cosmetics) == 36, "Exactly 36 unique cosmetics required")
    require(Counter(c["origin"] for c in cosmetics) == {"core": 12, "free_pass": 10, "premium_pass": 10, "shop": 4}, "Cosmetic source split must be 12/10/10/4")
    for c in cosmetics:
        require(c.get("economic_effects") == [], f"{c['id']}: cosmetic power prohibited")
    decorations = [c for c in cosmetics if c.get("kind") == "archive_decoration"]
    require(len(decorations) == 6, "Six Note-priced archive decorations required")
    for c in decorations:
        require(c["origin"] == "core" and c.get("unlock") == {"kind": "note_purchase", "currency": "survey_notes", "amount": 50}, f"{c['id']}: decoration belongs to core and costs 50 Notes")
    chapter_cosmetics = [c for c in cosmetics if c["origin"] == "core" and c.get("kind") != "archive_decoration"]
    require({c.get("unlock", {}).get("chapter_id") for c in chapter_cosmetics} == chapter_ids, "Six remaining core cosmetics must reference six chapters")
    require(all(c.get("unlock", {}).get("kind") == "chapter_completion" for c in chapter_cosmetics), "Core chapter cosmetics must be earned through chapter completion")

    season = data["season"]
    require(season.get("id") == "season.01" and season.get("live_duration_days") == 28, "Season 1 must last 28 days")
    require(season.get("state_partition") == "season.01" and season.get("initial_state_policy") == "identical_for_all_players", "Season state must be isolated and equal at entry")
    require(season.get("main_policy_continues") is True and season.get("prestige_enabled") is False and season.get("synergies_available_immediately") is True, "Season baseline mechanics changed")
    require(season.get("imported_resources") == [] and season.get("imported_boosts") == [] and season.get("economic_exports") == [], "Season cannot import/export economic power")
    require(season.get("exported_reward_kinds") == ["cosmetic", "archive_fragment", "badge"], "Season exports must be non-economic")
    require(season.get("synergy") == {"source_tiers": [1, 2], "target_tiers": [4, 5], "coefficients": [[0.1, 0.2], [0.25, 0.1]]}, "Season synergy matrix must use explicit source/target orientation")
    require(season.get("lifecycle") == ["upcoming", "live", "archived"] and season.get("archive_playable") is True, "Season archive flow required")

    pass_ = data["pass"]
    require(pass_.get("season_id") == season["id"] and pass_.get("levels") == 30 and pass_.get("xp_per_level") == 500, "Pass must reference Season 1 and require 15,000 XP")
    require(pass_.get("daily_contract_count") == 3 and pass_.get("xp_per_contract") == 250, "Pass must preserve the shared 750 XP daily budget")
    require(pass_.get("xp_ledger") == "shared_daily_contract_receipts" and pass_.get("event_alternatives_replace_daily_objective") is True, "Event alternatives must share rather than duplicate XP receipts")
    require(pass_.get("selected_pass_capacity") == 1 and pass_.get("archive_completion") is True and pass_.get("paid_xp_multiplier") == 1, "Pass must preserve archived completion and paid/free speed parity")
    free, premium = pass_["free_rewards"], pass_["premium_rewards"]
    require(len(free) == 30 and [r["level"] for r in free] == list(range(1, 31)), "One free reward slot per pass level required")
    require(len(premium) == 10 and [r["level"] for r in premium] == list(range(3, 31, 3)), "Ten premium reward milestones required")
    require(Counter(r["reward"].get("kind") for r in free) == {"cosmetic": 10, "archive_fragment": 20}, "Free pass must contain ten cosmetics and twenty fragments")
    all_rewards = free + premium
    claimed_ids = [r["reward"].get("content_id") for r in all_rewards]
    require(len(set(claimed_ids)) == len(claimed_ids), "Pass rewards must not duplicate collectible IDs")
    for lane, rewards in (("free_pass", free), ("premium_pass", premium)):
        for slot in rewards:
            reward = slot["reward"]
            require(set(reward) == {"kind", "content_id"}, f"{slot['id']}: unbudgeted reward fields prohibited")
            ref = reward.get("content_id")
            if reward.get("kind") == "cosmetic":
                require(ref in cosmetic_map and cosmetic_map[ref]["origin"] == lane, f"{slot['id']}: cosmetic must exist in the correct pass lane")
            else:
                require(lane == "free_pass" and reward.get("kind") == "archive_fragment" and ref in fragment_ids, f"{slot['id']}: unsupported or missing pass reward")
    require({r["reward"]["content_id"] for r in free if r["reward"].get("kind") == "archive_fragment"} == fragment_ids, "All twenty fragments must be rewarded")

    audio_ids = {a["id"] for a in data["audio"]}
    require(audio_ids == {"audio.ambient_score", "audio.interaction", "audio.milestone", "audio.rechart", "audio.soundtrack"}, "Score, interaction, milestone, Rechart and soundtrack packages required")
    require({s["id"] for s in data["support_content"]} == {"support." + n for n in ("help", "recovery_guide", "release_notes", "credits", "privacy_page", "support_page", "operations_runbooks", "season02_brief")}, "Support and operating content missing")
    ui_names = {"harbor_and_producers", "purchase_modes_and_network_value", "rechart_preview", "automation_plans", "forecasts", "offline_return", "calibration_accessible_choice", "surveys", "contracts_and_backlog", "archive_and_challenges", "season_start_end_archive", "pass_selection_and_claims", "shop_preview_and_purchase", "purchase_restore_and_pending", "save_conflict_and_recovery", "settings_and_notifications", "help_and_support"}
    require({u["id"] for u in data["ui_flows"]} == {"ui." + name for name in ui_names}, "All seventeen critical UI flow assignments required")
    bundle = data["supporter_bundle"]
    require(set(bundle.get("cosmetic_ids", [])) == {c["id"] for c in cosmetics if c["origin"] == "shop"}, "Supporter bundle must reuse four shop cosmetics")
    require(bundle.get("audio_ids") == ["audio.soundtrack"] and bundle.get("new_unique_cosmetics") == 0 and bundle.get("economic_effects") == [], "Supporter offer must contain the soundtrack and no new power/cosmetics")
    production_complete = all(o["production_status"] == "verified" for o in objects if "production_status" in o) and all(a["delivery_status"] == "verified" for a in assets.values())
    require(data.get("release_ready") is False or (production_complete and not errors), "release_ready cannot be true for unfinished or invalid content")
    if release:
        require(data.get("release_ready") is True, "Release readiness has not been asserted after acceptance")
    return errors


def self_test(data):
    """Exercise independent scope, parity, power and false-completion failures."""
    cases = [
        ("missing chapter", lambda d: d["chapters"].pop()),
        ("missing production status", lambda d: d["chapters"][0].pop("production_status")),
        ("missing objectives status", lambda d: d["chapters"][0].pop("objectives_status")),
        ("missing objective specification", lambda d: d["chapters"][0].pop("objective_spec")),
        ("missing rules status", lambda d: d["challenges"][0].pop("rules_status")),
        ("missing rule specification", lambda d: d["challenges"][0].pop("rule_spec")),
        ("missing pattern status", lambda d: d["calibrations"][0].pop("pattern_status")),
        ("missing pattern specification", lambda d: d["calibrations"][0].pop("pattern_spec")),
        ("missing copy status", lambda d: d["main_archive"][0].pop("copy_status")),
        ("missing UI implementation status", lambda d: d["ui_flows"][0].pop("implementation_status")),
        ("missing UI acceptance field", lambda d: d["ui_flows"][0].pop("acceptance_evidence")),
        ("missing bundle fulfillment status", lambda d: d["supporter_bundle"].pop("fulfillment_status")),
        ("missing UI flow", lambda d: d["ui_flows"].pop()),
        ("duplicate ID", lambda d: d["cosmetics"][1].update(id=d["cosmetics"][0]["id"])),
        ("missing restoration", lambda d: d["harbor_presentations"].pop()),
        ("wrong milestone", lambda d: d["producer_families"][0]["presentations"][1].update(ownership_threshold=20)),
        ("inaccessible reward parity", lambda d: d["calibrations"][0]["completion_paths"][1].update(focus_cost=2)),
        ("missing collectible parity", lambda d: d["calibrations"][0]["completion_paths"][1].update(collectible_pattern_id="calibration.02")),
        ("economic pass reward", lambda d: d["pass"]["free_rewards"][0]["reward"].update(kind="radiance")),
        ("hidden reward amount", lambda d: d["pass"]["free_rewards"][0]["reward"].update(amount=100)),
        ("paid pass acceleration", lambda d: d["pass"].update(paid_xp_multiplier=2)),
        ("imported event power", lambda d: d["season"]["imported_resources"].append("charts")),
        ("season economic export", lambda d: d["season"]["economic_exports"].append("survey_notes")),
        ("unbudgeted supporter item", lambda d: d["supporter_bundle"]["cosmetic_ids"].append("cosmetic.extra")),
        ("missing asset", lambda d: d["assets"].pop()),
        ("false complete content", lambda d: d["chapters"][0].update(production_status="verified")),
        ("false verified asset", lambda d: d["assets"][0].update(delivery_status="verified")),
        ("false ready flag", lambda d: d.update(release_ready=True)),
        ("required payment", lambda d: d["ending"]["paid_requirements"].append("pass.01")),
        ("missing note decoration", lambda d: d["cosmetics"][6]["unlock"].update(amount=100)),
    ]
    failures = []
    for name, mutate in cases:
        changed = copy.deepcopy(data)
        mutate(changed)
        if not validate(changed):
            failures.append(name)
    if not validate(data, release=True):
        failures.append("unfinished registry must fail release validation")
    stage_errors = validate(data, content_gate=True)
    if not stage_errors or not any('chapter.01: content not verified' in e for e in stage_errors):
        failures.append('content gate must reject unfinished gameplay content')
    if any(e.startswith(('support.', 'asset.support.', 'ui.help_and_support:')) for e in stage_errors):
        failures.append('content gate must defer later support acceptance')
    return len(cases) + 3, failures


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("manifest", nargs="?", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--release", action="store_true", help="Reject every unfinished asset/content entry")
    parser.add_argument("--content-gate", action="store_true", help="Require gameplay content; defer support documents until release")
    parser.add_argument("--self-test", action="store_true", help="Exercise rejection of invalid registry mutations")
    args = parser.parse_args()
    try:
        data = json.loads(args.manifest.read_text())
        errors = validate(data, release=args.release, content_gate=args.content_gate)
    except (OSError, ValueError, KeyError, TypeError, AttributeError) as exc:
        print(f"INVALID MANIFEST: {exc}")
        return 1
    if errors:
        mode = 'RELEASE' if args.release else ('CONTENT GATE' if args.content_gate else 'PLAN')
        print(f"{mode} VALIDATION FAILED: {len(errors)} issues")
        for error in errors[:12]:
            print(f"- {error}")
        if len(errors) > 12:
            print(f"- ... {len(errors)-12} further unfinished/invalid obligations")
        return 1
    unfinished = sum(a["delivery_status"] != "verified" for a in data["assets"])
    print(f"PLAN CONTRACT VALID: {len(data['assets'])} asset packages; {unfinished} unfinished.")
    print("Registry validation does not prove authored content, playability, reachability, accessibility, or a shippable build.")
    if args.self_test:
        count, failures = self_test(data)
        if failures:
            print("REJECTION SELF-TEST FAILED: " + ", ".join(failures))
            return 1
        print(f"REJECTION SELF-TEST PASSED: {count} scope/parity/isolation/false-readiness cases.")
    if args.release:
        print("CONTENT RELEASE CONTRACT VALID: separate native runtime and device acceptance still required.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
