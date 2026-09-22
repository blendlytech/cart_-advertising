---
name: research-lead
description: Research local small-business leads for the Cart Dial CRM and write call-ready findings into its database. Use this whenever the user wants leads researched, a decision maker or owner name found, a lead list enriched or qualified, a new store's prospect list worked up, blank decision makers filled in, or asks what they should know before calling a business. Also use when importing a new lead sheet, since imported leads arrive with no research. Prefer this over ad-hoc web searching for anything involving the CRM's leads, because it enforces rules that keep the lead data trustworthy.
---

# Researching leads for a cold call

This skill turns a bare lead (business name, phone, category) into something a caller
can actually open a conversation with. It exists because the useful output of research
is not a pile of facts — it is one sentence that tells the caller why *this* business
should care, plus a way past whoever answers the phone.

The CRM lives at `CartDialCRM/crm.py`. Its database is
`%LOCALAPPDATA%\CartDialCRM\crm.sqlite3`. Scripts here assume that location.

## The shape of the job

1. Find which leads need work: `python scripts/leads_needing_research.py`
2. Research them, in the order that script prints (it is the user's own ranking).
3. Write findings to a JSON file.
4. Apply: `python scripts/write_research.py findings.json`

Read `references/sources.md` when you need places to look beyond a plain web search —
it carries the user's own prospecting sources and the qualification signal below.

## Three rules that protect the data

**Never invent a decision maker.** An imagined name is worse than a blank, because the
caller will use it out loud and burn the call in the first five seconds. If no name is
published, leave `decision_maker` out of the findings entirely and put the route past
the gatekeeper in `about` instead. The CRM already handles a blank name gracefully — it
generates an opener that asks who owns the decision — so a blank is a supported state,
not a failure.

**Never write `notes`.** That field is the user's own judgement, and the CRM derives each
lead's call priority from the `TIER`/`PRIORITY` marker at the front of it. Overwriting it
destroys ranking work and silently reshuffles the call list. Research goes in `about`.
`scripts/write_research.py` asserts `notes` is unchanged and aborts if it is not.

**Never overwrite a script the user has edited.** Leads carry a `script` column with a
`script_edited` marker. `Database.set_script` already refuses without `force=True`. Do not
reach around it.

## What to actually look for

Facts are cheap. These are the things that change how the call goes, roughly in order of
value:

- **The decision maker's name**, and for a titled contact the surname, since the script
  will say "Dr. Do" rather than a first name.
- **A named employee**, when the owner is not published. Reviews often name staff, and
  asking for a person by name gets you a person; asking for "the owner" gets you screened.
- **Whether they already buy local advertising.** This is the strongest qualifier in the
  whole exercise — see `references/sources.md`. Someone running printed coupons or a
  radio spot is pre-sold on paid local reach, so the call is only about the channel.
- **Tenure and family ownership.** "Second generation, since 1988" is a real opener and it
  maps onto the cart pitch, which is about being the familiar local name.
- **What they actually sell**, when the CRM's category is wrong or too broad. Say so in
  `about` — categories here genuinely mix trades, and the pitch offers exclusivity on the
  trade you name.
- **Structural obstacles.** A franchise may need corporate sign-off; a regional with a
  head office in another city cannot be sold single-store exclusivity by a cold call.
  Write the obstacle and the question that reveals it, so the caller finds out in the
  first thirty seconds rather than after pitching.

## Every lead gets an ANGLE

End each `about` with a line starting `ANGLE:` that says why this business in particular
should care. This is the part the caller cannot improvise mid-call, and it is the reason
to do research at all. Derive it from what you found, not from the category.

Good angles connect something specific about them to what the cart panel does:

- *30 years in town with almost no web presence* → invisible to anyone searching, carried
  by referral, so this is the one channel that does not require fixing their website first.
- *Sells property management, not houses* → do not pitch buyers or sellers; pitch the
  accidental landlord, which is exactly who pushes a cart.
- *The only independent agent among captive competitors* → "one agent per store" is worth
  far more to someone who can quote several carriers.
- *Emergency trade* (plumbing, urgent care, vet) → the work is bought in a panic and the
  winner is whoever was already familiar. Recognition before the emergency is the product.

Where something argues against the lead, use `CAUTION:` on its own line. Where a fact is
missing and the caller should ask, use `GAP:`. A caller trusts research more when it
admits what it does not know.

## Confidence, and when to stop

Small local businesses often have a genuinely thin footprint. Two or three searches plus
their own site is usually the ceiling; past that you are guessing. Stop and record the gap.

Be careful about same-name confusion, which is common in one town: verify against the
street address or phone number the CRM already holds before attributing an owner. Getting
this wrong puts a stranger's name in the caller's mouth.

Mark uncertainty in the text — "ownership not confirmed; Dr. Kaur is the named lead vet,
confirm on the call" is useful, while stating her flatly as owner is a trap.

## One thing worth knowing before you disqualify

The user's own ranking sometimes beats structural reasoning, because they have been to
these places. A franchise looks weak on paper, but a franchise *inside the supermarket
centre* is a top lead and they had already ranked it that way. Check the address against
the store before writing a lead off, and treat a `TIER 0` note as knowledge you lack.

## Findings file format

Keys are lead ids. Omit any field you did not establish — an omitted field is left alone,
an empty string clears it.

```json
{
  "34": {
    "decision_maker": "Dr. William Do",
    "about": "Dr. William Do, DDS. 945 N Central Ave. Practice operating since 1996. General and family dentistry, paediatric, implants. Thin web presence: no practice site, directory listings only. ANGLE: 30 years in Tracy with almost no online footprint means he is invisible to search and carried entirely by referral, so cart advertising is the one channel that does not need his website fixed first. Lead with paediatric/family, since the cart audience is parents with kids in the seat."
  },
  "8": {
    "about": "Asian-owned and veteran-owned. 4.9 across ~159 reviews; reviewers praise honesty and no unnecessary work. GATEKEEPER: no owner name published, but reviews name technicians KUNAR and TERRY — asking for one of them by name gets a person instead of a brush-off. ANGLE: their whole reputation is the honest mechanic, so word of mouth is already their channel and the cart directory is that same play in front of families who shop the store. GAP: owner name — get it on the call."
  }
}
```

Note the second entry sets no `decision_maker`. That is the correct output when no name
was found, not an incomplete one.

## After applying

`write_research.py` prints a before/after for every field it changed and confirms `notes`
survived. Read that output rather than assuming success. Then tell the user which leads
got names, which got a gatekeeper tactic instead, and which you would disqualify and why.
