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
