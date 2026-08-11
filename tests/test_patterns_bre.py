"""Signature tests: Behavioral Reasoning Engine pattern evaluation (BP-001, BP-002).

Pins the Domain 02 activation conditions, strength ladders, session windows,
BP-002's multi-session Strong rule, and evidence dedup (identical activation
over the same supporting events never duplicates — core 19)."""

import pytest

from smartreco.engines.patterns import EventView, evaluate_patterns
from smartreco.policies import load_policies


@pytest.fixture(scope="module")
def policies():
    return load_policies()


def E(i, etype, session="s1", **metadata):
    return EventView(event_id=f"e{i}", event_type=etype, session_id=session, metadata=metadata)


def by_pattern(drafts, pattern):
    return [d for d in drafts if d.pattern_id == pattern]


def test_bp001_no_activation_below_threshold(policies):
    events = [E(1, "SECURITY_VIEWED", page="overview")]
    assert by_pattern(evaluate_patterns(events, policies), "BP-001") == []


def test_bp001_activates_on_two_distinct_security_pages(policies):
    events = [E(1, "SECURITY_VIEWED", page="overview"), E(2, "SECURITY_VIEWED", page="certs")]
    drafts = by_pattern(evaluate_patterns(events, policies), "BP-001")
    assert len(drafts) == 1
    assert drafts[0].strength == "MEDIUM"
    assert drafts[0].concept_ids == ["BC-001"]
    assert set(drafts[0].supporting_event_ids) == {"e1", "e2"}


def test_bp001_same_page_twice_does_not_activate(policies):
    events = [E(1, "SECURITY_VIEWED", page="overview"), E(2, "SECURITY_VIEWED", page="overview")]
    assert by_pattern(evaluate_patterns(events, policies), "BP-001") == []


def test_bp001_activates_on_security_plus_sso_doc(policies):
    events = [E(1, "SECURITY_VIEWED", page="overview"),
              E(2, "DOCUMENTATION_VIEWED", topic="sso")]
    drafts = by_pattern(evaluate_patterns(events, policies), "BP-001")
    assert len(drafts) == 1 and drafts[0].strength == "MEDIUM"


def test_bp001_dwell_upgrades_to_strong(policies):
    events = [E(1, "SECURITY_VIEWED", page="overview"),
              E(2, "DOCUMENTATION_VIEWED", topic="sso")]
    events += [E(10 + n, "DWELL", topic="security", seconds=10) for n in range(6)]  # 60s
    drafts = by_pattern(evaluate_patterns(events, policies), "BP-001")
    assert len(drafts) == 1 and drafts[0].strength == "STRONG"


def test_bp001_window_is_session_scoped(policies):
    events = [E(1, "SECURITY_VIEWED", session="s1", page="overview"),
              E(2, "DOCUMENTATION_VIEWED", session="s2", topic="sso")]
    assert by_pattern(evaluate_patterns(events, policies), "BP-001") == []


def test_bp002_activates_on_enterprise_pricing_plus_admin_docs(policies):
    events = [E(1, "PRICING_VIEWED", tier="enterprise"),
              E(2, "DOCUMENTATION_VIEWED", topic="admin")]
    drafts = by_pattern(evaluate_patterns(events, policies), "BP-002")
    assert len(drafts) == 1 and drafts[0].strength == "MEDIUM"
    assert drafts[0].concept_ids == ["BC-002"]


def test_bp002_individual_tier_pricing_does_not_qualify(policies):
    # Individual/free tiers never SUPPORT Enterprise Evaluation — they produce
    # contradicting evidence instead (Phase 4; pinned in test_patterns_bre_phase4)
    events = [E(1, "PRICING_VIEWED", tier="individual"),
              E(2, "PRICING_VIEWED", tier="free")]
    supporting = [d for d in evaluate_patterns(events, policies)
                  if d.pattern_id == "BP-002" and not d.contradicts]
    assert supporting == []


def test_bp002_strong_needs_three_qualifying_across_two_sessions(policies):
    events = [E(1, "DOCUMENTATION_VIEWED", session="s1", topic="provisioning"),
              E(2, "PRICING_VIEWED", session="s2", tier="enterprise"),
              E(3, "DOCUMENTATION_VIEWED", session="s2", topic="admin")]
    drafts = by_pattern(evaluate_patterns(events, policies), "BP-002")
    # Session s2 activates; journey-wide 3 qualifying across 2 sessions → STRONG
    assert len(drafts) == 1 and drafts[0].strength == "STRONG"
    assert set(drafts[0].supporting_event_ids) == {"e1", "e2", "e3"}


def test_evidence_is_deterministic_and_dedupable(policies):
    events = [E(1, "SECURITY_VIEWED", page="a"), E(2, "SECURITY_VIEWED", page="b")]
    first = evaluate_patterns(events, policies)
    second = evaluate_patterns(events, policies)
    keys1 = {(d.pattern_id, tuple(sorted(d.supporting_event_ids))) for d in first}
    keys2 = {(d.pattern_id, tuple(sorted(d.supporting_event_ids))) for d in second}
    assert keys1 == keys2  # identical inputs → identical evidence (dedup key stable)


def test_ai_evaluation_does_not_upgrade_to_strong_on_reading_time(policies):
    """Only Security Evaluation lets reading time stand in for activity
    (Decision #045).

    The code carried a dwell clause here that doc 02 never granted, and no
    test covered it — which is how it survived. The distinction the pack draws
    is deliberate: security interest can only be shown on a product's single
    security page, so four qualifying events means four products, and reading
    one closely deserves an alternative. AI interest qualifies on docs, product
    views *and* searches, so four accumulate inside one product without help.
    Promoting on dwell made Strong cheaper here than anywhere else, unasked.
    """
    events = [E(1, "DOCUMENTATION_VIEWED", topic="ai"),
              E(2, "SEARCH", query="ai assistant")]
    events += [E(10 + n, "DWELL", topic="ai", seconds=10) for n in range(12)]  # 120s

    drafts = by_pattern(evaluate_patterns(events, policies), "BP-003")
    assert len(drafts) == 1
    assert drafts[0].strength == "MEDIUM", (
        "two minutes of reading promoted AI Evaluation to Strong; doc 02 "
        "grants it no dwell path")


def test_ai_evaluation_still_reaches_strong_on_activity(policies):
    """The counterpart, so the fix cannot be 'AI can never be Strong'."""
    events = [E(1, "DOCUMENTATION_VIEWED", topic="ai"),
              E(2, "SEARCH", query="ai assistant"),
              E(3, "DOCUMENTATION_VIEWED", topic="ai"),
              E(4, "SEARCH", query="copilot pricing")]
    drafts = by_pattern(evaluate_patterns(events, policies), "BP-003")
    assert len(drafts) == 1 and drafts[0].strength == "STRONG"


def test_the_set_of_contradiction_rules_matches_what_doc_02_says_is_built():
    """Doc 02 § 'Clauses not implemented in v1' claims exactly two of the four
    Contradicting clauses exist. That claim is the only thing standing between
    a reader and the assumption that the pack describes the platform — so it
    has to fail here rather than be discovered by someone debugging why a
    contradiction never fires.

    Either direction is a failure: building a third rule without recording it
    makes the doc understate the platform, and deleting one makes it overstate.
    """
    import ast
    import pathlib

    from smartreco.domain.software_buying import patterns as module

    # Parsed rather than regexed: an EvidenceDraft call spans several lines and
    # sits next to others, and a non-greedy pattern quietly matched across call
    # boundaries — reporting a pattern that has no contradiction rule at all.
    tree = ast.parse(pathlib.Path(module.__file__).read_text(encoding="utf-8"))
    emitting = set()
    for node in ast.walk(tree):
        if not (isinstance(node, ast.Call)
                and getattr(node.func, "id", None) == "EvidenceDraft"):
            continue
        keywords = {kw.arg: kw.value for kw in node.keywords}
        if "contradicts" not in keywords:
            continue
        pattern_id = keywords.get("pattern_id")
        if isinstance(pattern_id, ast.Constant):
            emitting.add(pattern_id.value)
    assert emitting == {"BP-002", "BP-010"}, (
        f"patterns emitting contradicting evidence: {sorted(emitting)} — doc 02 "
        f"records exactly BP-002 and BP-010 as built; update the doc and this "
        f"test together")
