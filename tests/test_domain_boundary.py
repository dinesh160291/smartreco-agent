"""Signature test: the platform/domain boundary (domain-pack-contract.md).

The platform's central reuse claim is that the engines are identical across
domains and only the Domain Pack changes. That claim is only worth anything if
something checks it — otherwise domain knowledge drifts into platform modules
one convenient constant at a time, and the drift is invisible until someone
tries to add a second domain and finds they must edit an engine.

The check: **no module outside `domain/` may hardcode a domain identifier.**
Importing from the Domain Pack module is the sanctioned seam and is fine; a
literal `BP-001` in an engine is not, because it means the engine knows
something only the Software Buying pack should know.

KNOWN_DEVIATIONS records the leakage that exists today. It is a ratchet, not
an excuse: nothing may be added to it (new leakage fails), and an entry that
stops leaking must be deleted (test_no_stale_deviations enforces that, so the
list can only shrink). Each entry names what has to move and where.
"""

import pathlib
import re

import pytest

REPO = pathlib.Path(__file__).resolve().parents[1]

# Domain Pack identifier families (Domain Pack docs 01-10).
#
# The `POL-` lookbehind is load-bearing, not tidiness: policy identifiers are
# Core 10's and belong in platform code everywhere, but `POL-REQ-003` ends in
# `REQ-003`, so a naive pattern flags every engine that reads a requirement
# policy. That false positive is not academic — acting on it once rewrote live
# `policies.param("POL-REQ-003", …)` lookups and broke 25 tests.
DOMAIN_ID = re.compile(r"(?<!POL-)\b(?:BP|BC|CAP|REQ|PROD)-\d{3}\b")

# Platform surfaces that must stay domain-free for a second domain to be
# possible without editing them.
PLATFORM_CODE = "src/smartreco"
PLATFORM_DOCS = "docs/core"
REUSABLE_DOCS = "docs/implementation"

KNOWN_DEVIATIONS: dict[str, str] = {
    # --- docs: illustrative use is legitimate; hosting a registry is not ---
    "docs/core/decision-log.md":
        "Historical record of decisions that were about domain content. "
        "PERMANENT: rewriting past entries to satisfy a later boundary rule "
        "would falsify the record.",
}


def _scan(root: str, skip: tuple[str, ...] = ()) -> dict[str, set[str]]:
    found: dict[str, set[str]] = {}
    for path in sorted((REPO / root).rglob("*")):
        if path.suffix not in {".py", ".md"} or not path.is_file():
            continue
        rel = path.relative_to(REPO).as_posix()
        if any(fragment in rel for fragment in skip):
            continue
        ids = set(DOMAIN_ID.findall(path.read_text(encoding="utf-8", errors="ignore")))
        if ids:
            found[rel] = ids
    return found


def _offenders() -> dict[str, set[str]]:
    offenders = {}
    offenders.update(_scan(PLATFORM_CODE, skip=("/domain/", "__pycache__")))
    offenders.update(_scan(PLATFORM_DOCS))
    offenders.update(_scan(REUSABLE_DOCS))
    return offenders


def test_no_new_domain_leakage_into_platform_surfaces():
    """A domain identifier in an engine means the engine knows something only
    one Domain Pack should know — the exact coupling that blocks reuse."""
    unexpected = {
        path: sorted(ids) for path, ids in _offenders().items()
        if path not in KNOWN_DEVIATIONS
    }
    assert not unexpected, (
        "domain identifiers leaked into a platform surface:\n"
        + "\n".join(f"  {p}: {ids}" for p, ids in unexpected.items())
        + "\n\nImport from the Domain Pack module instead of hardcoding the id. "
          "If the value genuinely belongs to the platform, it is not a domain "
          "identifier and should not carry a BP/BC/CAP/REQ/PROD prefix."
    )


def test_no_stale_deviations():
    """The ratchet. When a file stops leaking, its entry must be deleted —
    otherwise the list quietly becomes a permanent licence rather than a debt
    register, and the boundary stops tightening."""
    offenders = _offenders()
    fixed = sorted(path for path in KNOWN_DEVIATIONS if path not in offenders)
    assert not fixed, (
        "these no longer leak — remove them from KNOWN_DEVIATIONS:\n"
        + "\n".join(f"  {p}" for p in fixed)
    )


def test_domain_pack_module_is_the_only_home_for_domain_knowledge():
    """The seam itself: platform modules reach domain knowledge by importing
    it, never by restating it. This passes today and must keep passing."""
    pack = REPO / "src/smartreco/domain/software_buying"
    assert pack.is_dir(), "the Domain Pack transcription must exist"
    for artifact_file in ("__init__.py", "knowledge.py", "enums.py", "patterns.py"):
        assert (pack / artifact_file).exists(), f"pack is missing {artifact_file}"

    importers = []
    for path in sorted((REPO / PLATFORM_CODE).rglob("*.py")):
        rel = path.relative_to(REPO).as_posix()
        if "/domain/" in rel or "__pycache__" in rel:
            continue
        if "from smartreco.domain" in path.read_text(encoding="utf-8", errors="ignore"):
            importers.append(rel)
    assert importers, (
        "no platform module imports the Domain Pack — either the seam is "
        "gone or domain knowledge is being restated instead of referenced"
    )


@pytest.mark.parametrize("artifact", [
    "BEHAVIORAL_CONCEPTS", "PATTERNS", "REQUIREMENTS", "CAPABILITIES",
    "BC_TO_REQ", "REQ_TO_CAP", "STAGE_MILESTONES", "CANONICAL_PRODUCTS",
    "SEARCH_ALIASES",
])
def test_domain_pack_supplies_every_contracted_artifact(artifact):
    """domain-pack-contract.md lists what a pack must provide. A second domain
    is only possible if the first one actually demonstrates the full set."""
    from smartreco.domain import software_buying

    assert hasattr(software_buying, artifact), (
        f"Domain Pack is missing {artifact} — see "
        f"knowledge/architecture/domain-pack-contract.md"
    )
    assert getattr(software_buying, artifact), f"{artifact} is empty"
