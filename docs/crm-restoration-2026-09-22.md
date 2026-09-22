# CRM restoration — September 22, 2026

Repository: blendlytech/cart_-advertising.

## Findings and repair

Commit `4d6d2c07dacf8b3797357a578fd3dbc53968c283` replaced the per-lead NEPQ script builder with category templates. Restore `build_script` from its parent, `cc35269778280350286cad1e2f2c3d31af93aac8`, including decision-maker greetings, store/category personalization, the lead's About and notes, objections, and no phone price quote. Existing stored scripts remain untouched and continue to take precedence.

The TextNow button and `tel://` handoff were not removed by that commit. Restore the preceding shared button styling, including explicit enabled text color. This is a restoration of the previous appearance, not confirmation of the reported missing button's cause. TextNow receives only the number; the CRM does not press its call button. Ctrl+D on a selected lead uses the same handoff.

Recover `docs/leads_savemart_tracy_875_s_tracy_blvd.md` alongside the new San Leandro research document. Both Tracy import CSVs remain present. No database records are changed by this repair.

## Update and check on Windows

1. Close the CRM and use its Backup database command first if it is still running. Keep a copy of the current database before attempting any data recovery.
2. After this repair is merged, pull the repository's main branch in your existing checkout. Start `CartDialCRM/Start-CRM.bat` from that checkout, rather than an older extracted copy.
3. Open an existing lead. Check the Call script tab and the Call with TextNow button. Clicking the latter should load the number; place the call only by clicking inside TextNow. Choose No call placed if you were only checking the handoff.
4. If a lead has a stored generic script, automatic generation will not replace it. Copy that text somewhere safe first, then use Rebuild from lead fields on that individual lead and Save lead. This deliberately replaces that lead's stored script only after your edit is saved.

## Recovering deleted leads or authored scripts

The database is not tracked in Git. On Windows the app uses `%LOCALAPPDATA%\CartDialCRM\crm.sqlite3`, with daily startup snapshots in `%LOCALAPPDATA%\CartDialCRM\backups\YYYY-MM-DD.sqlite3`. Manual backups may be elsewhere. A startup snapshot reflects the data at the first launch that day; check its contents rather than assuming it predates the deletion.

Git can restore committed research documents and import sheets, but cannot restore deleted local call history, research, or hand-edited scripts. Preserve the current database and older backups as separate files. Compare them and recover missing records selectively so new territory leads and call history survive. Do not replace the current database blindly with an old snapshot. No database was accessible during this repair, so no local record recovery has been claimed.

## Verification

- 23 existing non-GUI tests passed, covering script personalization, script edit protection, schema migration, duplicate import preservation, backups, call accounting, and TextNow URI formatting.
- Seven existing Tk desktop tests could not run because this environment has no display. Installing a virtual display was unavailable due to environment permissions. Windows button visibility and actual TextNow handoff remain to be checked locally.
- Strict UI static audit: zero findings. This does not establish desktop runtime correctness.
