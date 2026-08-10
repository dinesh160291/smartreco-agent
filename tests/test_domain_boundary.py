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

# Domain Pack identifier families (Domain Pack docs 01-10). POL- is deliberately
# absent: policy IDs are Core 10's and belong everywhere.
DOMAIN_ID = re.compile(r"\b(?:BP|BC|CAP|REQ|PROD)-\d{3}\b")

# Platform surfaces that must stay domain-free for a second domain to be
# possible without editing them.
PLATFORM_CODE = "src/smartreco"
PLATFORM_DOCS = "docs/core"
REUSABLE_DOCS = "docs/implementation"

KNOWN_DEVIATIONS: dict[str, str] = {
    # --- code: the pack is declarative, these are its imperative duplicate ---
    "src/smartreco/engines/patterns.py":
        "BP-001…012 evaluators and their topic vocabulary are Software Buying "
        "logic living in a platform engine. Must move to the domain layer, "
        "driven by the declarative PATTERNS registry the pack already holds.",
    "src/smartreco/engines/stages.py":
        "Decision/Adoption milestones hardcode BP-010/BP-011. Milestones are "
        "Domain Pack artifact 8; the engine should evaluate a supplied "
        "milestone spec rather than name patterns itself.",
    "src/smartreco/engines/requirements.py":
        "REQ ids appear in docstring examples only. Reword to a neutral "
        "example; the arithmetic itself is already domain-agnostic.",
    "src/smartreco/pipeline.py":
        "REQ-003 in a comment. Reword.",
    "src/smartreco/seeding.py":
        "PROD-001 in a docstring describing the canonical fixture. Reword to "
        "reference the roster by name rather than by identifier.",

    # --- docs: illustrative use is legitimate; hosting a registry is not ---
    "docs/core/10-decision-policies.md":
        "Worked examples name BC-001/REQ-00x. Legitimate illustration under "
        "Law 2, but should be marked as Software Buying examples so a reader "
        "porting the platform knows they are not platform constants.",
    "docs/core/17-platform-enumerations.md":
        "REQ-002 used as an example of a requirement identifier. Same as above.",
    "docs/core/decision-log.md":
        "Historical record of decisions that were about domain content. "
        "PERMANENT: rewriting past entries to satisfy a later boundary rule "
        "would falsify the record.",

    # --- implementation docs: must be reusable across domains ---
    "docs/implementation/data-model.md":
        "Catalog seed strategy cites CAP-001/PROD-001 and a SaaS category "
        "list. The schema is platform; the seed policy is Domain Pack "
        "artifact 9 and should move there.",
    "docs/implementation/stack-decisions.md":
        "Vocabulary rule illustrated with CAP-001. Reword to a neutral "
        "example — the rule itself is platform.",
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
    domain_module = REPO / "src/smartreco/domain/software_buying.py"
    assert domain_module.exists(), "the Domain Pack transcription must exist"

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
