# Catalog Seed Strategy — Software Buying

**Domain Pack artifact 9** (`knowledge/architecture/domain-pack-contract.md`).

Moved here from `docs/implementation/data-model.md`: the schema is platform and reusable, but catalog scale, the real/fictional split, the category spread and the distractor rule are all domain judgements. `data-model.md` keeps the tables and the dual-write contract and points here.

---

**Scale (locked):** ~250 products total — **125 real** (well-known SaaS across CRM, HR, finance, DevOps, analytics, support, marketing, security, collaboration…) and **125 fictional but plausible**, anchored by the 10 canonical products (PROD-001…010) from the Domain Pack roster. Authored by an LLM-assisted **seed script** at build time into `seed/products.json`, reviewed once, never generated at runtime.

Rules:

1. **Taxonomy grows first:** the Capability Catalog extends to ~55 capabilities (Domain Pack v1.1, append-only IDs, new domains: CRM, HR, Finance, Marketing, DevOps, Data & Analytics) so wide-catalog products express themselves honestly. The five REQ→CAP mappings are unchanged — out-of-domain products are the realistic noise retrieval and matching must cut through.
2. **Fixture separation:** acceptance tests (Domain 09 numbers, Stories 1–2) seed **only the canonical 10**. The demo database seeds all ~250.
3. **Distractor constraint:** products (real or fictional) in the four scenario domains get deliberately partial capability sets so canonical winners remain deterministic in the live demo.
4. **Editorial disclaimer:** seed data ships with the note that capability profiles are illustrative editorial interpretations for demonstration, not vendor claims.

---
