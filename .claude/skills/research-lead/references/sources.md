# Where to look, and what actually qualifies a lead

## The qualification signal that matters most

The user's own prospecting method, recorded in
`CartDialCRM/references/internet_prospecting_guide.md`, is to find businesses **already
paying to advertise locally**. This is sharper than it first looks, and it is worth
treating as the primary qualifier rather than an afterthought.

A business already running printed coupons, a radio spot, a newspaper ad or a paid
directory listing has settled the hard question by itself: it believes local paid reach
works. The call is then only about which channel, which is a far easier conversation than
convincing someone that advertising is worth money at all.

So when researching, actively look for evidence of existing ad spend and say so in
`about`. A smog shop advertising a fixed price with coupons is a stronger lead than a
larger business with no visible marketing, even though the larger one looks better on
paper.

Where to find that evidence:

- Coupon and deal sites, and the business's own site (a "specials" or "coupons" page)
- Local newspaper sites — their advertisers are usually listed or visible in banners
- Local radio station sites — sponsors and advertiser directories
- Direct-mail packs for the ZIP code, which show current advertisers
- Paid lead platforms like Thumbtack and Angi, where presence means they buy leads
- Sponsorship of local sport, schools or events

## General sources for a local business

Start with a plain web search on the business name plus the town, then the street or phone
from the CRM to disambiguate. In one town, similar names are common and attributing the
wrong owner is the worst available error.

Useful in rough order:

- The business's own site, especially `/about`, `/team`, `/our-staff`, `/meet-the-doctor`
- Review sites for named staff, tenure claims and what customers actually praise
- Chamber of commerce and business directory listings for ownership and founding dates
- State corporate filings for the registered officer and the filing date
- Professional licence registries for regulated trades, which give a licence number and
  the licensed individual — useful for realtors, contractors, medical and dental

## When the trade does not match the category

The CRM's categories come from a fixed list and some of them mix trades that are not
interchangeable on a call. Every lead filed under one category may in practice be a
different trade — this has already happened with dental practices filed under a
doctors-and-urgent-care category.

`crm.py` handles this with `TRADE_HINTS`, which lets a business name its own trade. If you
find a lead whose real trade is not covered, say so in `about` and mention that the
category or the hint list may need updating. The trade noun is not cosmetic: it is the
exclusivity being sold, so "one urgent care clinic" offered to a dentist both sounds wrong
and promises the wrong thing.

## Structural obstacles worth recording

These do not always disqualify a lead, but they change who to ask and what to expect:

- **Franchise** — local ad spend often needs brand approval or runs through a regional
  co-op. The question that settles it: *"do you handle your own local advertising, or does
  that go through corporate?"* Ask early.
- **Multi-location owner** — will want to know which store, and may want all of them.
- **Regional with a head office elsewhere** — single-store exclusivity has little value
  and the decision sits with a media buyer who does not take cold calls. If called at all,
  pitch the local branch manager on local presence, not head office on reach.
- **Partnership or several co-owners** — expect "let me talk to my partners" rather than a
  decision on the call. Ask for the founder.
- **Service-area business with no storefront** — often the best fit in principle, since
  they have no passing trade at all, but usually the smallest budget.

One caution learned the hard way: check the address against the store before writing off a
franchise. A franchise *inside the supermarket centre* is a top lead, and the user had
already ranked one that way from having been there. Their `TIER 0` notes encode local
knowledge that is not on the web.
