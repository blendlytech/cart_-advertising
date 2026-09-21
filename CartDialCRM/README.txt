CART DIAL CRM — LOCAL APPOINTMENT DESK

GET STARTED (WINDOWS)
1. Extract this entire ZIP to a folder on your laptop. Do not run inside the ZIP.
2. This version requires Python 3 with Tkinter (Tcl/Tk), included in the normal
   Python Windows installer. If Python is already installed, try step 3 first.
3. Double-click Start-CRM.bat. Keep the accompanying console window open.
   Closing the CRM closes the launcher. No pip packages or account are needed.

This is a Python desktop app, not a standalone Windows EXE. It uses no server,
network calls, browser storage, paid services, or login. You place calls on your
phone; the CRM records them when you choose Save call.

DAILY WORKFLOW
- Choose Import spreadsheet, select CSV or XLSX, and match your columns.
- Business name and phone are required. Other columns are optional.
- Click a lead row (or select with the keyboard and press Enter).
- Contact & schedule: decision maker, category, store, address, website, status,
  callback time, and appointment time. Save lead commits changes without a dial.
- About & notes: permanent business background plus general notes.
- Log a call: timestamp defaults to now; select outcome and enter call notes.
  The suggested callback is tomorrow at the same time unless one exists.
  Edit or clear it as needed. Save call adds exactly one dial.
- Appointment set requires an appointment date and time. Callback requested
  requires a callback date and time. Do not call stops additional call logging
  until you deliberately change the status. Terminal outcomes clear callbacks.
- Call history shows every saved call, its date/time, disposition, and notes.
- Activity date defaults to today. Change it and press Show for past daily totals.
  Appointments booked counts call entries marked Appointment set on that date.
- Filter for due callbacks, upcoming appointments, or a status. Search matches
  business name, phone, decision maker, or category. Call counts are lifetime.
- Scripts & references contains all five supplied files, verbatim. The business
  About section is yours to fill; the app does not research or invent facts.

SPREADSHEET IMPORT
Use lead-import-template.csv as a header template, or map your existing headers.
Supported: CSV and XLSX (first worksheet only). Save legacy XLS as XLSX or CSV.
The first nonempty row must contain headers. Format phone cells as Text in Excel
so leading zeros and extensions survive. XLSX uses underlying stored values,
not visual number formats. Replace formulas with values before importing.
Rows missing business name or phone are skipped and counted. Matching business
name (ignoring case) plus normalized phone is treated as a duplicate and skipped.
An import never overwrites existing notes or call history. Different business
names with the same phone remain separate. Review the import summary.

DATA AND BACKUPS
The live database is stored outside the application folder at:
  %LOCALAPPDATA%\CartDialCRM\crm.sqlite3
Paste %LOCALAPPDATA%\CartDialCRM into Windows File Explorer to find it.
All app copies on this Windows account use this same database. Use one app
window at a time. Updating the program folder does not replace your database.
An automatic backup is taken on the first launch each day, before that day's
work. Those copies are in the backups subfolder. Use Backup database after a
calling session to save a current copy somewhere safe (for example a USB drive).
Automatic backups remain on the same laptop and do not protect against loss of
that laptop. Backups are ordinary unencrypted SQLite files.

RESTORE A BACKUP
Close the CRM. In the data folder above, rename the existing crm.sqlite3 to
crm-before-restore.sqlite3 so you keep a recovery copy. Copy your chosen backup
into this folder and rename the copy crm.sqlite3. Reopen the CRM.

Export call log creates CSV containing every call and its associated business.
This CSV is a report; use the SQLite backup for a complete restorable copy.

SCOPE AND VERIFICATION
Designed for one laptop user setting appointments for cart advertising.
No email/SMS/calendar integrations, automatic dialing, sales pipeline, or cloud
sync. Schedules appear inside the CRM; there are no background notifications.
Python syntax and automated data/import/backup tests were run in the development
environment. The Windows launcher and desktop UI still need a first-run check
on your laptop; a compiled installer is not included.

BUSINESS TYPES UPDATE
The Business type dropdown on every lead card includes the 54 categories from
target_categories.md. Specialty notes and store restrictions appear beneath the
contact form. Existing imported custom types remain available. Blank means
uncategorized. Save lead to apply a change.

Choose Leads by business type on the main screen to see totals for every type,
including types with zero leads, imported custom types, and Uncategorized. These
are lead counts across the entire database, not call counts or daily totals.
The main screen also shows total leads and the number still uncategorized.
Spreadsheet headers Business type, Type of business, and Category are recognized.

TO UPDATE: Close the CRM, extract the new ZIP, and launch Start-CRM.bat from the
updated folder. Your existing database remains in the same local data folder.

VISUAL UPDATE
Navy header, teal primary buttons, colored daily activity panels, alternating
table rows, colored status text, and coordinated tabs, forms, and scrollbars.
Keep theme.py alongside crm.py when updating. Data storage has not changed.
