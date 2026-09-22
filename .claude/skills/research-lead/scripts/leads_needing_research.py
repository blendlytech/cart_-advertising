"""List Cart Dial CRM leads that still need research, in the user's own call order.

Prints in priority order (TIER 0 first) so research effort lands on the leads that will
actually be called first. Read-only -- safe to run while the CRM is open.

    python leads_needing_research.py            # leads missing a name or thin on research
    python leads_needing_research.py --all      # every open lead
    python leads_needing_research.py --limit 5  # just the next few
"""
import argparse
import os
import sqlite3
import sys
from pathlib import Path

DB = Path(os.environ.get('LOCALAPPDATA', str(Path.home()))) / 'CartDialCRM' / 'crm.sqlite3'
# Mirrors CLOSED in crm.py: leads that are out of the calling rotation are not worth research.
CLOSED = ('Do not call', 'Not interested', 'Wrong number', 'Poor fit', 'Appointment set')
THIN_ABOUT = 120  # chars; below this a lead has little more than a one-line description


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--all', action='store_true', help='include leads that already look researched')
    ap.add_argument('--limit', type=int, default=0, help='only the first N')
    args = ap.parse_args()

    if not DB.exists():
        sys.exit(f'No database at {DB}. Open the CRM once to create it.')

    con = sqlite3.connect(f'file:{DB.as_posix()}?mode=ro', uri=True)
    con.row_factory = sqlite3.Row
    placeholders = ','.join('?' for _ in CLOSED)
    rows = con.execute(
        f'SELECT * FROM leads WHERE status NOT IN ({placeholders}) '
        'ORDER BY priority, business_name COLLATE NOCASE', CLOSED).fetchall()

    picked = []
    for r in rows:
        missing = []
        if not (r['decision_maker'] or '').strip(): missing.append('no name')
        if len(r['about'] or '') < THIN_ABOUT: missing.append('thin about')
        if not (r['website'] or '').strip(): missing.append('no site')
        if 'ANGLE:' not in (r['about'] or ''): missing.append('no ANGLE')
        if missing or args.all:
            picked.append((r, missing))
    if args.limit: picked = picked[:args.limit]

    if not picked:
        print('Every open lead has a name, a site, substantial research and an ANGLE.')
        return

    print(f'{len(picked)} lead(s) needing research, in call order:\n')
    for r, missing in picked:
        rank = '--' if r['priority'] >= 99 else str(r['priority'])
        print(f"[{r['id']:>3}] rank {rank:>2}  {r['business_name']}")
        print(f"        {r['category']}  |  {r['phone']}  |  {r['address'] or 'no address'}")
        print(f"        site: {r['website'] or '(none)'}   contact: {r['decision_maker'] or '(none)'}")
        print(f"        needs: {', '.join(missing) or 'nothing, --all shown'}")
        if (r['notes'] or '').strip():
            print(f"        their note: {r['notes'][:150]}")
        print()
    print('Research these, then write a findings JSON keyed by the ids above and apply it')
    print('with write_research.py. Leave decision_maker out when no name is published.')


main()
