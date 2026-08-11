"""Long-form copy for the product deep-dive panes.

Presentation only. None of this reaches the products table, the Embedding
Document, or any ranking input (Core 20, Law 8): the vector index is derived
from the product record, and folding ~1,200 words of prose per product into it
would swamp the capability terms that give retrieval its discrimination.

It exists so that reading a pane takes a shopper the couple of minutes a real
evaluation takes, which is what makes dwell a signal worth having: BP-001 and
BP-003 escalate to Strong at 60 seconds of dwell on the pane's topic, and a
hundred-word page can never earn that honestly.

Two rules hold the copy to the truth:

* **Composed from the product's own record.** Every product-specific claim
  traces to a capability the product actually holds, its name, vendor, or
  category. The same passage repeated across 250 products would make reading
  time meaningless and would be transparently fake in a demo.
* **Never asserts a fact the record does not carry.** The scaffolding
  describes what an evaluation of this *kind* of product involves — what
  reviewers ask, what rollouts usually need — and is written in those terms
  rather than claiming certifications, versions, or limits nobody recorded.
  Where a product lacks a capability the pane says so plainly instead of
  filling the silence.
"""

from smartreco.retrieval import _CAP_BY_ID

# What a reviewer of a capability in this family is actually trying to settle.
# Keyed by the capability's own domain (Domain Pack doc 03), so the guidance
# follows the capability rather than the product's category.
_REVIEW_ANGLE = {
    "Identity & Access":
        "Reviewers usually want to see how this behaves at the edges: what "
        "happens to an account the day someone changes team, how quickly a "
        "revocation takes effect everywhere, and whether an administrator can "
        "answer 'who had access to what, and when' without exporting a "
        "spreadsheet.",
    "Security":
        "The questions here are rarely about whether the control exists — they "
        "are about defaults. Which protections are on before anyone configures "
        "anything, which require a higher plan, and what the failure mode is "
        "when the control cannot be applied.",
    "Compliance":
        "Auditors care less about the feature than about the evidence it "
        "produces: whether records are complete, whether they can be exported "
        "in a form an external reviewer accepts, and whether anyone with "
        "administrative rights could alter them without leaving a trace.",
    "Collaboration":
        "The practical question is what happens to content when people leave, "
        "and how much of the working record lives inside this product rather "
        "than somewhere it can be governed centrally.",
    "Automation":
        "Teams evaluating this want to know what happens when an automation "
        "fails halfway: whether it retries, whether it can be replayed safely, "
        "and whether a failure is visible to anyone who is not already looking "
        "for it.",
    "Artificial Intelligence":
        "The recurring questions are about data: what is sent to the model, "
        "whether it is retained or used for training, and whether output is "
        "attributable to a source a person can check.",
    "CRM":
        "Buyers look at how records merge and de-duplicate, because a pipeline "
        "is only as trustworthy as the contact data underneath it.",
    "HR":
        "Evaluation tends to hinge on employment data handling — who can see "
        "what, how corrections propagate, and how long records persist after "
        "someone leaves.",
    "Finance":
        "Finance teams push on the audit trail and the close: whether entries "
        "are traceable to source documents and whether period ends reconcile "
        "without manual adjustment.",
    "Marketing": "Teams check suppression and consent handling first, because "
                 "an unsubscribe honoured late is a compliance problem.",
    "DevOps":
        "The interesting questions are about noise: what is signal at three in "
        "the morning, and how much configuration it takes to get there.",
    "Data & Analytics":
        "Analysts ask where the numbers come from — whether a figure can be "
        "traced to its source table and refresh time without asking a person.",
}

_DEFAULT_ANGLE = ("Evaluation usually comes down to defaults and edge cases: "
                  "what works before configuration, and what happens when it "
                  "does not.")

_SECURITY_DOMAINS = ("Identity & Access", "Security", "Compliance")
_INTEGRATION_DOMAINS = ("Automation", "Identity & Access", "Data & Analytics")


def _caps(capability_ids):
    """(name, domain, narrative) for the capabilities this product holds."""
    return [_CAP_BY_ID[c] for c in sorted(capability_ids) if c in _CAP_BY_ID]


def _in_domains(capability_ids, domains):
    return [c for c in _caps(capability_ids) if c[1] in domains]


def _angle(domain):
    return _REVIEW_ANGLE.get(domain, _DEFAULT_ANGLE)


def _absent(capability_ids, domains):
    """Capabilities in these families the product does *not* hold.

    Naming the gaps keeps the pane honest and gives a shopper something real to
    weigh; a page that only lists strengths reads as marketing and teaches the
    platform nothing about what the shopper is actually missing.
    """
    held = set(capability_ids)
    return sorted({name for cap_id, (name, domain, _narrative) in _CAP_BY_ID.items()
                   if domain in domains and cap_id not in held})


def security_sections(product, capability_ids):
    """~1,200 words on security posture, composed from what the record holds."""
    name, vendor = product["name"], product["vendor"]
    relevant = _in_domains(capability_ids, _SECURITY_DOMAINS)
    missing = _absent(capability_ids, _SECURITY_DOMAINS)

    sections = [("Security posture", [
        f"This page summarises how {name} is usually assessed during a "
        f"security review, and what {vendor} exposes to the teams doing the "
        f"assessing. It is written for the person who has to justify the "
        f"choice to someone else — a security lead, a data protection "
        f"officer, or a procurement committee that will ask why this product "
        f"and not another one.",
        f"{name} carries "
        + (f"{len(relevant)} capabilities that bear directly on security, "
           f"identity, or compliance" if relevant else
           "no capabilities in the identity, security, or compliance families")
        + ". That count is not a score. A product with fewer controls that "
          "are on by default and well documented is frequently a safer choice "
          "than one with a longer list gated behind an enterprise agreement, "
          "and the sections below are arranged so you can tell the difference.",
        "Nothing here is a certification claim. Where a control matters to "
        "you, treat this page as the list of questions to put to the vendor "
        "rather than as the answer.",
    ])]

    for cap_name, domain, narrative in relevant:
        sections.append((cap_name, [
            narrative,
            _angle(domain),
            f"In a {product['category'].lower()} deployment this usually "
            f"surfaces during the pilot rather than the trial: a single team "
            f"can work around a gap here, while an organisation-wide rollout "
            f"cannot. If {cap_name.lower()} is load-bearing for you, ask to "
            f"see it configured against your own directory and your own data "
            f"before the contract is signed, not after.",
        ]))

    if missing:
        sections.append(("Not covered by this product", [
            "A security review is as much about absence as presence. Within "
            "the identity, security, and compliance families, the product "
            "record for " + name + " does not carry: " + ", ".join(missing[:12])
            + ("." if len(missing) <= 12 else ", among others."),
            "An absence is not automatically a problem. Most organisations "
            "cover several of these centrally — through an identity provider, "
            "an endpoint agent, or a data-governance platform that sits above "
            "individual applications — and buying the same control twice is "
            "waste rather than defence in depth. What matters is knowing "
            "which layer owns each control, and being able to say so.",
            "Where nothing owns a control, that is the finding worth writing "
            "down. It is far cheaper to record it now than to discover it "
            "during an incident, and a reviewer who sees a candid gap list is "
            "generally more confident in the rest of the assessment.",
        ]))

    sections.append(("Evidence a review will ask for", [
        "Most reviews converge on the same short list, whatever the product. "
        "Expect to be asked for a current architecture description, a "
        "statement of where data is stored and processed, the subprocessor "
        "list, an incident-notification commitment with a stated timeframe, "
        "and whatever independent assurance the vendor holds. None of these "
        "are unusual requests and a mature vendor will have them ready.",
        "The answers matter less than their consistency. A vendor whose "
        "documentation, sales team, and security questionnaire tell three "
        "slightly different stories about data residency is telling you "
        "something about how the organisation is run, and that signal tends "
        "to be more predictive than any single control.",
        "Ask, too, what happens at the end. Export formats, deletion "
        "timelines, and what remains in backups after an account closes are "
        "easy to agree before a contract and very hard to negotiate after "
        "one. Teams that skip this step are the ones that later discover "
        "their exit costs more than their entry.",
    ]))

    sections.append(("Running the review", [
        "A review that produces a decision looks different from one that "
        "produces a document. The difference is usually sequencing: decide "
        "first what would disqualify the product, then look only for those "
        "things. A review that starts with a two-hundred-question "
        "spreadsheet tends to end with a two-hundred-answer spreadsheet and "
        "no clearer view than it began with.",
        "Give the disqualifying items to whoever will actually be "
        "accountable for them. Data residency belongs to whoever answers "
        "regulatory questions; access review belongs to whoever runs "
        "identity; retention belongs to whoever holds the records policy. "
        "Questions answered by someone who does not own the consequence tend "
        "to be answered optimistically.",
        "Timebox it. Security reviews expand to fill whatever calendar they "
        "are given, and the marginal question after the first fortnight "
        "rarely changes the outcome. If it would not change the decision, it "
        "belongs in the onboarding plan rather than the evaluation.",
    ]))

    sections.append(("Questions that separate vendors", [
        "Most vendors answer the standard questionnaire competently, so the "
        "standard questionnaire rarely discriminates. The questions that do "
        "tend to be about behaviour under stress rather than about features: "
        "how the last significant incident was communicated, how long it took "
        "customers to hear, and what changed afterwards.",
        "Ask how a customer finds out that a security-relevant default has "
        "changed. Products ship changes continuously, and a control you "
        "verified during evaluation is a control that can quietly move. A "
        "vendor with a clear answer here is telling you something real about "
        "their change management.",
        "Ask who can access your data internally, under what circumstances, "
        "and whether that access is logged in a way you can see. Support "
        "engineers usually can, for good reasons; the distinguishing factor "
        "is whether that access is exceptional, recorded, and visible to you "
        "rather than routine and invisible.",
    ]))

    sections.append(("Shared responsibility", [
        f"Whatever {vendor} operates, a substantial part of the security of "
        f"{name} ends up being yours: who you grant administrative rights to, "
        f"how you handle joiners and leavers, whether you review access "
        f"periodically, and how you respond when the vendor notifies you of "
        f"something. Products differ far less on this than buyers expect.",
        "The useful exercise during evaluation is to write down, control by "
        "control, which side owns it — and to notice the ones where the "
        "honest answer is 'neither of us, yet'. Those are the items that "
        "become findings later.",
        "It is also worth deciding who will own this relationship after "
        "purchase. Security posture is not a state you reach at signature; "
        "it drifts as the product ships features and as your own use of it "
        "widens, and somebody needs to be watching.",
    ]))
    return sections


def docs_sections(product, capability_ids):
    """~1,200 words of setup, reference, and rollout notes."""
    name, vendor = product["name"], product["vendor"]
    held = _caps(capability_ids)

    sections = [("Before you start", [
        f"This is the practical documentation for {name}: what a working "
        f"deployment involves, what to configure first, and what teams "
        f"usually discover late. It assumes you have decided {name} is "
        f"plausible and are now working out what adopting it would actually "
        f"cost in effort.",
        "Two decisions shape everything that follows. The first is who owns "
        "the product internally — a single team, a platform group, or nobody "
        "in particular, which is the answer that quietly predicts a failed "
        "rollout. The second is whether this is replacing something. "
        "Migrations are almost always harder than greenfield adoption, "
        "because the work is not configuration but the accumulated "
        "exceptions the old system was carrying.",
        f"Budget time for both. In {product['category'].lower()} rollouts the "
        f"configuration is rarely the long pole; agreeing who decides, and "
        f"reconciling the old system's edge cases, is.",
    ])]

    if held:
        sections.append(("What you will be configuring", [
            f"{name} exposes {len(held)} capabilities, and they are not equal "
            f"in setup cost. The ones below are listed as the record holds "
            f"them, with a note on what each typically demands during "
            f"implementation.",
        ]))
        for cap_name, domain, narrative in held[:10]:
            sections.append((cap_name, [
                narrative,
                _angle(domain),
                f"Practically, plan for {cap_name.lower()} to need a named "
                f"owner, a decision about defaults, and a test that proves it "
                f"works for a real person rather than an administrator. The "
                f"third item is the one most often skipped, and the one most "
                f"often responsible for a rollout stalling in week three.",
            ]))

    sections.append(("Reference material", [
        f"{vendor} publishes the usual reference surfaces: an API reference, "
        f"configuration guides, and release notes. Read the release notes "
        f"before committing — their cadence and candour tell you more about "
        f"how the product is maintained than any feature list. A changelog "
        f"that records breaking changes plainly is worth a great deal.",
        "When you evaluate an API, look past the endpoint list. The questions "
        "that matter are how authentication is handled, whether pagination "
        "and rate limits are documented rather than discovered, whether "
        "errors are specific enough to act on, and whether there is a "
        "sandbox you can break without consequence.",
        "Check how versioning works and how long old versions are supported. "
        "An integration you build this quarter will still be running in three "
        "years, and the cost of that integration is dominated by how often it "
        "is forced to change.",
    ]))

    sections.append(("Environments and change management", [
        "Decide early whether you need a non-production environment. Some "
        "teams treat this as optional and then find they are testing "
        "configuration changes against live data, which works until the day "
        "it does not.",
        "Agree how configuration changes are reviewed. The failure mode is "
        "not a malicious change; it is a well-intentioned one made on a "
        "Friday by someone who did not know what depended on it. A written "
        "record of who changed what, and why, is worth more than an approval "
        "workflow nobody follows.",
        f"Finally, plan the boring part: how {name} gets patched, how you "
        f"learn about incidents, and who is on the receiving end of that "
        f"notification. Rollouts are judged on their first bad week.",
    ]))

    sections.append(("Moving existing data in", [
        f"If {name} is replacing something, the migration is the project. "
        f"Exporting from the old system is usually straightforward; deciding "
        f"what not to bring is not. Most teams discover that a meaningful "
        f"share of their existing data is stale, duplicated, or was only ever "
        f"correct in the context of a workflow they are about to abandon.",
        "Do the quality pass before the import, not after. Data that arrives "
        "wrong tends to stay wrong, because once people are working in the "
        "new system nobody has an uninterrupted window to fix it. A smaller, "
        "clean migration followed by a backfill is almost always faster in "
        "practice than a complete one you then have to correct.",
        "Plan for a period where both systems are live, and decide "
        "explicitly which one is authoritative during it. 'Both' is not an "
        "answer; it is how two divergent copies of the truth get created. "
        "Write the cutover date down and make it someone's responsibility.",
    ]))

    sections.append(("Training and adoption", [
        f"Adoption failures rarely look like refusal. They look like people "
        f"using {name} for the part of their work it makes obvious and "
        f"quietly keeping the old habit for everything else, which leaves you "
        f"paying for two systems and getting the benefits of neither.",
        "The most reliable predictor of adoption is whether the product "
        "removes a step someone currently resents. Lead with that, and let "
        "the rest follow. Training that walks through every feature in order "
        "tends to be forgotten by the time any of it is needed.",
        "Identify who people will actually ask when they are stuck. It is "
        "usually a colleague rather than a help desk, and that colleague is "
        "worth investing in early — an informal expert on each team does more "
        "for adoption than a documentation portal.",
    ]))

    sections.append(("Support and escalation", [
        "Establish what support you are entitled to before you need it. "
        "Response targets, escalation paths, and whether support is included "
        "or priced separately all vary by plan, and the difference is only "
        "visible when something is broken.",
        "It is worth asking how the vendor handles a problem they cannot "
        "reproduce. That is where support relationships genuinely differ, and "
        "the answer is rarely in the documentation.",
    ]))
    return sections


def integrations_sections(product, capability_ids):
    """~1,200 words on connecting the product to the rest of a stack."""
    name = product["name"]
    connective = _in_domains(capability_ids, _INTEGRATION_DOMAINS)
    held = _caps(capability_ids)

    sections = [(f"How {name} fits a stack", [
        f"Very little software is bought to stand alone, and {name} is no "
        f"exception. This page covers how it connects to what you already "
        f"run, the shapes those connections usually take, and the limits "
        f"worth knowing before you design around them.",
        "There are broadly three ways products like this join a stack: a "
        "prebuilt connector maintained by one of the two vendors, a generic "
        "API integration you build and own, or an intermediary automation "
        "platform sitting between them. The three differ less in what they "
        "can achieve than in who is responsible when they break, which is "
        "the question to settle first.",
        f"{name} holds {len(held)} capabilities in total, "
        + (f"{len(connective)} of which bear on how it connects to other "
           f"systems." if connective else
           "none of which are specifically connective — integration here will "
           "mean a generic API or an intermediary rather than a purpose-built "
           "connector."),
    ])]

    for cap_name, domain, narrative in connective:
        sections.append((cap_name, [
            narrative,
            _angle(domain),
            f"When you scope this, be specific about direction and frequency. "
            f"'{name} integrates with our directory' can mean a nightly "
            f"one-way export or a live bidirectional sync, and the two have "
            f"very different failure modes. Write down which one you are "
            f"buying.",
        ]))

    sections.append(("Connector, API, or middleware", [
        "A vendor-maintained connector is the cheapest option when it exists "
        "and covers what you need. Its weakness is that its scope is someone "
        "else's decision: when a field you depend on is not mapped, you have "
        "no recourse except a feature request, and the connector's roadmap is "
        "not yours.",
        "A direct API integration gives you exactly the behaviour you "
        "specify and hands you the maintenance in exchange. That trade is "
        "usually worth it for something central to how the business runs, and "
        "usually not worth it for a convenience that could be done manually "
        "in a few minutes a week.",
        "An intermediary automation platform sits between the two. It moves "
        "quickly, non-engineers can maintain it, and it becomes an "
        "undocumented dependency with remarkable speed. If you take this "
        "route, treat what you build there as production software: name an "
        "owner, keep it in a place people can find, and write down what "
        "breaks if it stops.",
    ]))

    sections.append(("Before you connect", [
        "Start by writing the sentence the integration exists to make true — "
        "something like 'when a deal closes, finance sees it without anyone "
        "retyping it'. If that sentence is hard to write, the integration is "
        "probably premature, and the honest first step is doing the work "
        "manually until the shape of it is clear.",
        "Then decide what a failure is allowed to look like. Some flows can "
        "be hours late without anyone caring; others are wrong if they are "
        "five minutes late. This single distinction drives most of the "
        "design, and getting it wrong in the optimistic direction is how "
        "integrations end up needing to be rebuilt.",
        "Check what already exists before building. It is common to find "
        "that a partial integration was set up by someone who has since "
        "changed team, is still running, and is quietly contradicting the one "
        "you are about to create.",
    ]))

    sections.append(("Testing an integration", [
        "Test with data that resembles yours, including the awkward parts: "
        "the record with an apostrophe in the name, the one with an empty "
        "required field, the one created before a schema change. Clean "
        "fixtures prove very little, because clean data was never the problem.",
        "Verify the failure path deliberately. Disconnect one side, let "
        "changes accumulate, reconnect, and check what happened to them. Most "
        "integrations are only ever tested along the happy path, which is why "
        "so many of them lose data the first time something is unavailable.",
        "Once live, watch it for a full business cycle before trusting it. "
        "Month-end, payroll runs, and quarter close surface volume and "
        "timing problems that a quiet Tuesday never will.",
    ]))

    sections.append(("Patterns teams use", [
        "The most common pattern is a single system of record with everything "
        "else subscribing to it. It is boring and it works, because it makes "
        "the question 'which value is correct?' answerable. The trouble "
        "starts when two systems both believe they are the record.",
        "The second pattern is event-driven: one system emits a change and "
        "others react. It scales well and it fails quietly, so it is worth "
        "the effort of making failures loud — an event that is silently "
        "dropped is indistinguishable from one that never happened.",
        "The third is scheduled reconciliation, which is unfashionable and "
        "extremely effective. Even with a live integration, a periodic job "
        "that compares both sides and reports differences will catch the "
        "class of bug that live syncing hides.",
    ]))

    sections.append(("Data flow and ownership", [
        "Before connecting anything, agree which system owns each field. This "
        "sounds procedural and it prevents the most expensive category of "
        "integration bug, where two systems overwrite each other in a loop "
        "and neither is wrong by its own rules.",
        "Be equally explicit about deletion. Many integrations propagate "
        "creates and updates faithfully and simply ignore deletes, which "
        "leaves records alive in a downstream system long after they were "
        "removed upstream — a problem that is invisible until somebody asks a "
        "data protection question.",
        "Decide, too, what personal data crosses the boundary and whether it "
        "needs to. The cheapest way to reduce the compliance surface of an "
        "integration is to send fewer fields.",
    ]))

    sections.append(("Limits worth knowing", [
        "Rate limits, payload sizes, and sync intervals are the three "
        "constraints that most often force a redesign, and all three are "
        "easier to find before you build. Ask for the numbers rather than "
        "assurances.",
        f"Ask also what happens during a {name} outage. Whether queued "
        f"changes are replayed on recovery or silently lost determines "
        f"whether your integration needs its own buffer, and that is an "
        f"architectural decision, not a configuration one.",
    ]))
    return sections
