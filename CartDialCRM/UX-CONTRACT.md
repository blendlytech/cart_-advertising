# Desktop behavior contract
Source: current user brief and references/*.md. One local user; appointment
setting only. Python/Tk UI and SQLite persistence. Native desktop interactions
are intentional; browser-only CSS/ARIA/URL contracts do not apply.

| Capability | Canonical owner | Source of truth | Allowed variants | Verification |
|---|---|---|---|---|
| Table Selection | ttk.Treeview | App | single selection | desktop check pending |
| Select/Listbox | ttk.Combobox | App | native readonly | desktop check pending |
| Date | valid_date | crm.py | typed local time | test_crm.py |
| Form | App.card snapshot/save | crm.py | create/edit | desktop check pending |
| Scrollbar | ttk.Scrollbar / ScrolledText | App | native platform | desktop check pending |
| Toast | native messagebox + persistent labels | App | status/error | desktop check pending |
| CRUD | Database | crm.py | create/edit, no deletion | test_crm.py |
| Dial handoff | dial_uri + App.dial_lead | crm.py | card button, Ctrl+D on list | test_crm.py |
| Call script | build_script + Database.script_for | crm.py | derived, or stored per lead | test_crm.py |
| Call order | priority_of + Best leads first | crm.py | derived from notes | test_crm.py |

Call insert and status update are atomic. Imported duplicates never overwrite
existing records. Each explicit saved call counts one dial. Imported notes and
profile edits do not count. Modals guard unsaved edits. Dispositions update status
and clear callbacks for terminal outcomes. Manual status changes are allowed.
Records stay local. The one external side effect is handing a tel: URI to the
installed TextNow desktop app, which opens its dialer with the number filled in
and never places the call itself. Only an unambiguous ten-digit number is handed
off. No credentials, tokens, or lead data leave this computer, and a Do not call
lead is never dialed. A dial always opens the call form, which then refuses to
close without an explicit outcome or an acknowledged no-call. Saving a dialed
call closes the lead card and returns focus to the list; the list preserves its
selection across refresh so the next lead stays reachable by keyboard.
Each lead has a call script. With nothing stored it is derived from the lead's
own fields by build_script, so correcting a lead corrects its script; missing
values appear as visible [BRACKETS] rather than silent gaps. A stored script
replaces the derived one, and once the user edits a script it is marked and
set_script refuses to overwrite it without force. Script generation is offline
text assembly; any research that enriches it happens outside this app and lands
in the ordinary About, notes, decision maker, and website fields. The dialed
call form carries the script, because the lead card is unreachable behind it.
Script columns are added to existing databases by ALTER TABLE at startup.

Call order is derived, not entered. priority_of reads the rank the user already
writes at the front of their notes, where TIER and PRIORITY share one scale and a
smaller number calls first; an unranked lead sorts last so a new lead never
silently jumps the queue. notes stays the source and priority follows it through
save and import, and is backfilled by ALTER TABLE on existing databases. The Best
leads first view hides closed leads. Poor fit is our own judgement that a lead is
not worth calling and is kept distinct from Do not call, which is a promise to a
person who asked; only the latter blocks logging a call.
Native dialogs, keyboard traversal,
text selection, scrolling, Escape, and window Close are the desktop primitives.
There are no app-controlled web dialogs. No delete operation is provided.
Search is local and explicitly committed. List state stays in memory per session.
Database backups include all records. Failures retain forms for correction.

Business type uses the native readonly Combobox with all 54 source categories
and existing imported custom values. Document specialty/restriction notes are
shown beneath the form. Blank values count as Uncategorized. Database.category_totals
is the single count owner; counts include every lead regardless of filters,
status, or activity date. Each lead contributes once. No migration is needed.
