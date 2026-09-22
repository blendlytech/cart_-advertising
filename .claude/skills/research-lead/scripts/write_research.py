"""Apply researched findings to the Cart Dial CRM, without damaging what the user owns.

Writes only decision_maker, website and about. Backs up first, prints a before/after for
every change, and aborts if notes or a stored script would be touched -- notes carries the
user's ranking (the CRM derives call priority from it) and an edited script is theirs.

    python write_research.py findings.json
    python write_research.py findings.json --dry-run   # show changes, write nothing

findings.json maps lead id to the fields established. An omitted field is left alone, so
leaving out decision_maker is how you record "no name published" -- never invent one.

    {"34": {"decision_maker": "Dr. William Do", "about": "... ANGLE: ..."},
     "8":  {"about": "... GATEKEEPER: ask for Kunar ... ANGLE: ..."}}
"""
import argparse
import json
import os
import shutil
import sqlite3
import sys
from datetime import datetime
from pathlib import Path

DB = Path(os.environ.get('LOCALAPPDATA', str(Path.home()))) / 'CartDialCRM' / 'crm.sqlite3'
WRITABLE = ('decision_maker', 'website', 'about')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('findings', help='JSON file mapping lead id to fields')
    ap.add_argument('--dry-run', action='store_true', help='report changes without writing')
    args = ap.parse_args()

    if not DB.exists(): sys.exit(f'No database at {DB}')
    findings = json.loads(Path(args.findings).read_text(encoding='utf-8'))
    if not isinstance(findings, dict): sys.exit('findings must be a JSON object keyed by lead id')

    for lead_id, fields in findings.items():
        stray = set(fields) - set(WRITABLE)
        if stray:
            sys.exit(f'lead {lead_id}: refusing to write {sorted(stray)}. '
                     f'Only {list(WRITABLE)} may be written; notes belongs to the user.')

    if not args.dry_run:
        stamp = datetime.now().strftime('%Y%m%d-%H%M%S')
        backup = DB.with_name(f'crm-before-research-{stamp}.sqlite3')
        shutil.copy2(DB, backup)
        print(f'backup: {backup}\n')

    con = sqlite3.connect(DB)
    con.row_factory = sqlite3.Row
    named = tactic = skipped = 0

    for lead_id, fields in findings.items():
        before = con.execute('SELECT * FROM leads WHERE id=?', (lead_id,)).fetchone()
        if before is None:
            print(f'[{lead_id}] no such lead, skipped'); skipped += 1; continue

        changes = {k: v for k, v in fields.items() if (before[k] or '') != v}
        print(f"[{lead_id}] {before['business_name']}")
        if not changes:
            print('    already current, nothing written\n'); continue
        for key, new in changes.items():
            print(f"    {key}\n      was: {(before[key] or '(empty)')[:160]}\n      now: {new[:160]}")

        if 'ANGLE:' not in (changes.get('about') or before['about'] or ''):
            print('    WARNING: no ANGLE line. The caller has facts but no reason to call.')

        if fields.get('decision_maker', '').strip(): named += 1
        else: tactic += 1

        if not args.dry_run:
            con.execute(f'UPDATE leads SET {",".join(k + "=?" for k in changes)} WHERE id=?',
                        [*changes.values(), lead_id])
            after = con.execute('SELECT notes,script,script_edited,priority FROM leads WHERE id=?',
                                (lead_id,)).fetchone()
            # These belong to the user. If any moved, something wrote outside its lane.
            for guarded in ('notes', 'script', 'script_edited', 'priority'):
                if after[guarded] != before[guarded]:
                    con.rollback()
                    sys.exit(f'ABORTED on lead {lead_id}: {guarded} changed. Nothing committed.')
        print()

    if args.dry_run:
        con.rollback(); print('dry run, nothing written')
    else:
        con.commit(); print(f'written. names: {named}   gatekeeper tactic only: {tactic}   skipped: {skipped}')
        print('notes, priority and edited scripts verified unchanged.')
    con.close()


main()
