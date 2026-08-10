"""Signature tests: deterministic catalog search (ui-design-spec §Catalog Search).

The Explore search was a single case-folded substring over name+vendor+
description. Capabilities — the field that actually says what a product does —
were not searched, so Okta was invisible for "single sign-on" despite holding
that capability, and any punctuation difference ("single sign on") returned
nothing at all.

These pin the replacement: token AND-matching with prefix support over an
expanded field set, punctuation-insensitive, with a domain alias map for
acronyms. Ranking is by where the match lands, so a name hit beats a
description hit.
"""

import pytest

from smartreco.catalog_search import normalize, search_catalog

OKTA = {
    "product_id": "PROD-003", "name": "Okta", "vendor": "Okta",
    "category": "Identity & Access Management",
    "description": ("Independent identity and access management platform providing "
                    "centralized authentication, identity lifecycle management."),
    "business_purpose": "Standardize identity across every application.",
    "capabilities": ["Single Sign-On", "Multi-Factor Authentication",
                     "SCIM Provisioning", "Conditional Access", "Audit Logging"],
}
SLACK = {
    "product_id": "PROD-002", "name": "Slack", "vendor": "Salesforce",
    "category": "Collaboration",
    "description": "Enterprise collaboration platform focused on team communication.",
    "business_purpose": "Help teams communicate.",
    "capabilities": ["Messaging", "File Sharing", "Video Meetings"],
}
BOX = {
    "product_id": "PROD-010", "name": "Box", "vendor": "Box",
    "category": "Content Management",
    "description": "Governed content management for compliance teams.",
    "business_purpose": "Keep content governed.",
    "capabilities": ["Information Governance", "Data Retention", "File Sharing"],
}
CATALOG = [OKTA, SLACK, BOX]


def names(results):
    return [r["name"] for r in results]


# --- the two bugs that started this -------------------------------------------

@pytest.mark.parametrize("query", [
    "single sign-on", "single sign on", "Single Sign On", "single  sign--on",
])
def test_okta_is_found_by_its_capability_however_it_is_punctuated(query):
    """The reported bug: Okta holds Single Sign-On but its description never
    says the phrase, and hyphenation must not decide whether it is findable."""
    assert "Okta" in names(search_catalog(CATALOG, query))


@pytest.mark.parametrize("query", ["multi-factor authentication", "multi factor auth"])
def test_okta_is_found_by_multi_factor_authentication(query):
    assert "Okta" in names(search_catalog(CATALOG, query))


# --- matching semantics --------------------------------------------------------

def test_all_query_tokens_must_match(query=None):
    """AND, not OR: a product matching only some tokens is not a result."""
    assert names(search_catalog(CATALOG, "single sign-on")) == ["Okta"]
    assert search_catalog(CATALOG, "single sign-on unicorn") == []


def test_tokens_match_as_prefixes():
    """'provision' finds 'SCIM Provisioning'; partial words are usable."""
    assert "Okta" in names(search_catalog(CATALOG, "provision"))
    assert "Box" in names(search_catalog(CATALOG, "govern"))


def test_token_order_does_not_matter():
    assert (names(search_catalog(CATALOG, "sign-on single"))
            == names(search_catalog(CATALOG, "single sign-on")))


def test_acronyms_resolve_through_the_domain_alias_map():
    assert "Okta" in names(search_catalog(CATALOG, "sso"))
    assert "Okta" in names(search_catalog(CATALOG, "mfa"))


def test_ranking_prefers_a_name_hit_over_a_description_hit():
    """'box' is Box's name and appears nowhere else; 'file sharing' is a
    capability both Slack and Box hold, so both come back."""
    assert names(search_catalog(CATALOG, "box"))[0] == "Box"
    assert set(names(search_catalog(CATALOG, "file sharing"))) == {"Slack", "Box"}


def test_category_is_searchable():
    assert names(search_catalog(CATALOG, "collaboration")) == ["Slack"]


def test_empty_query_returns_everything_unfiltered():
    assert len(search_catalog(CATALOG, "")) == len(CATALOG)
    assert len(search_catalog(CATALOG, "   ")) == len(CATALOG)


def test_results_are_deterministic():
    """Same inputs, same order — the platform's replayability claim extends to
    the catalog surface, not just the decision spine."""
    first = names(search_catalog(CATALOG, "identity"))
    for _ in range(5):
        assert names(search_catalog(CATALOG, "identity")) == first


def test_short_tokens_do_not_prefix_match_a_name():
    """The 'on' in 'single sign-on' must not match OneLogin's name.

    Found while measuring ranking: a two-letter fragment prefix-matching at
    full name weight put OneLogin first in every single-sign-on search, ahead
    of products whose capabilities were the actual match.
    """
    onelogin = {
        "product_id": "PROD-184", "name": "OneLogin", "vendor": "One Identity",
        "category": "Identity & Access Management",
        "description": "Access management.", "business_purpose": "Access.",
        # Holds the capability too, so both products match on 'single' and
        # 'sign' — the only thing that can separate them is how 'on' is
        # treated. Scored as a name prefix it outweighs every capability hit.
        "capabilities": ["Single Sign-On", "Identity Federation"],
    }
    results = names(search_catalog([OKTA, onelogin], "single sign-on"))
    assert results.index("Okta") < results.index("OneLogin"), (
        f"a two-letter token matched a name it only prefixes: {results}")


def test_normalize_strips_punctuation_and_folds_case():
    assert normalize("Single Sign-On!") == "single sign on"
    assert normalize("multi--factor   auth") == "multi factor auth"
