"""Cart Dial CRM. Python standard library only; all records stay on this computer."""
import csv
import io
import os
import re
import sqlite3
import webbrowser
import zipfile
import posixpath
from pathlib import Path
from datetime import datetime, timedelta
import xml.etree.ElementTree as ET
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from tkinter.scrolledtext import ScrolledText
from theme import COLORS, apply_theme

BASE = Path(__file__).resolve().parent
DATA = Path(os.environ.get('LOCALAPPDATA', str(Path.home()))) / 'CartDialCRM'
FIELDS = ['business_name', 'phone', 'decision_maker', 'category', 'store', 'address', 'website', 'about', 'notes']
LABELS = ['Business name', 'Phone number', 'Decision maker', 'Business type', 'Store / location', 'Meeting address', 'Website', 'About this business', 'General notes']
OUTCOMES = ['No answer', 'Voicemail', 'Gatekeeper', 'Spoke to decision maker', 'Callback requested', 'Appointment set', 'Not interested', 'Wrong number', 'Do not call']
STATUSES = ['New', 'Working', 'Callback', 'Appointment set', 'Not interested', 'Wrong number', 'Do not call']
# How a business type is said out loud in 'we restrict each store to just ONE ___'.
# Categories with no entry fall back to the lowercased category name.
TRADE_NOUNS = {
    'Realtors': 'real estate agent',
    'Insurance Agents': 'insurance agent',
    'Automotive Repair': 'auto repair shop',
    'Spas and Salons': 'salon',
    'Doctors and Urgent Care Clinics': 'urgent care clinic',
    'Construction & Home Services': 'contractor',
    'Pet Grooming and Boarding': 'pet groomer',
    'Restaurants and Pizza': 'restaurant',
    'Chiropractors and Therapeutic Massage Studios': 'chiropractor',
}
ALIASES = {'business':'business_name','businessname':'business_name','company':'business_name','companyname':'business_name','phone':'phone','phonenumber':'phone','telephone':'phone','decisionmaker':'decision_maker','decisionmakername':'decision_maker','contact':'decision_maker','contactname':'decision_maker','name':'decision_maker','notes':'notes','note':'notes','about':'about','aboutthisbusiness':'about','businessinformation':'about','category':'category','businesscategory':'category','store':'store','storelocation':'store','address':'address','meetingaddress':'address','website':'website'}
ALIASES.update({'businesstype':'category','typeofbusiness':'category'})

def load_categories():
    """Keep dropdown labels and specialty notes tied to the supplied document."""
    source = (BASE/'references'/'target_categories.md').read_text(encoding='utf-8')
    return {name: detail.strip().lstrip('–').strip().replace('*','')
            for name, detail in re.findall(r'^- \*\*(.+?)\*\*(.*)$',source,re.MULTILINE)}

CATEGORIES = load_categories()

def category_name(value):
    value = (value or '').strip()
    return next((name for name in CATEGORIES if name.casefold()==value.casefold()),value)

def now():
    return datetime.now().isoformat(timespec='seconds')

def valid_date(value):
    if not value.strip(): return ''
    try: return datetime.strptime(value.strip(), '%Y-%m-%d %H:%M').isoformat(timespec='seconds')
    except ValueError: raise ValueError('Use YYYY-MM-DD HH:MM, for example 2026-09-15 14:30 (24-hour time).')

def display_date(value):
    return value[:16].replace('T', ' ') if value else ''

def phone_key(value):
    digits = re.sub(r'\D', '', value)
    return digits[1:] if len(digits) == 11 and digits.startswith('1') else digits

def dial_uri(value):
    """Return a 'tel://' URI for the TextNow desktop app, or None to refuse the dial.

    The double slash is required and must not be 'tidied' to 'tel:'. TextNow tests
    the argument with includes('tel://'); when that fails it raises its window and
    loads no number, which looks like the dial worked but silently did nothing.
    Only an unambiguous ten-digit number loads. Extensions, partial numbers, and
    blanks return None so the card warns instead of reaching a wrong line.
    """
    digits = phone_key(value)
    return f'tel://{digits}' if len(digits) == 10 else None

def store_label(store):
    """Split 'Save Mart #781 Schulte - 875 S Tracy Blvd, Tracy CA' into chain and street."""
    head, _, tail = store.partition(' - ')
    chain = head.split('#')[0].strip() or head.strip()
    street = re.sub(r'^\s*\d+\s+', '', tail.split(',')[0]).strip()
    street = re.sub(r'^[NSEW]\s+', '', street)  # 'S Tracy Blvd' reads better spoken as 'Tracy Blvd'
    return chain, street

def city_of(address):
    """Pull the city out of a US street address, skipping suite lines, state, and ZIP."""
    for part in reversed([p.strip() for p in address.split(',') if p.strip()]):
        if re.fullmatch(r'[A-Z]{2}(\s+\d{5}(-\d{4})?)?', part) or re.fullmatch(r'\d{5}(-\d{4})?', part): continue
        if re.match(r'^(ste|suite|unit|apt|#)', part, re.I) or re.match(r'^\d', part): continue
        return part
    return ''

def build_script(lead, caller='', trade=''):
    """Assemble a NEPQ call script from one lead's fields. Pure text; no network.

    Every blank comes from stored data, so the script re-derives itself as the lead
    is corrected. Unknown values become visible [BRACKETS] rather than silent gaps.
    """
    chain, street = store_label(lead['store'] or '')
    city = city_of(lead['address'] or '') or '[CITY]'
    first = (lead['decision_maker'] or '').split()[0] if (lead['decision_maker'] or '').strip() else '[OWNER]'
    one = trade or TRADE_NOUNS.get(lead['category'] or '', (lead['category'] or 'business').lower())
    many = one + ('' if one.endswith('s') else 's')
    at_store = f'{chain} on {street}' if street else (chain or '[STORE]')
    me = caller or '[YOUR NAME]'
    research = '\n'.join(f'  {line}' for line in [lead['about'] or '', lead['notes'] or ''] if line.strip())
    return f'''{lead['business_name']}  ·  {one}  ·  {city}
{'='*64}

GATEKEEPER  (low, relaxed, peer-to-peer)
  "Hey, good morning... I'm looking for {first} — are they around today?"

  If asked what it's regarding:
  "Yeah, it's regarding the local business sponsorship for the {at_store}
   cart project... I just needed to see if {first} is the one handling local
   community branding, or if someone else does that?"

OPENER  (familiar and calm; the ... are real pauses)
  "Hey {first}? ... it's {me}... with the community sponsorship project
   over at the {at_store}.
   Look, I know you weren't expecting my call today, and to be completely
   upfront... I'm not even sure if what we're rolling out is a fit for what
   you're doing right now...
   Do you have about 30 seconds for me to tell you why I called, and then you
   can tell me whether it makes sense to keep chatting or hang up?"

THE HOOK  (low, conversational, detached)
  "So we're finalizing the new cart directory and child seat panels for the
   {at_store}.
   Typically local {many} in {city} tell us they're tired of burning money on
   digital clicks or mailers that get tossed before anyone reads them...
   ...whereas with this you get exclusive category visibility in front of
   20,000+ local families who shop that store 2 to 3 times every week.
   The reason I reached out to you specifically is that we restrict each store
   to just ONE {one}, and we haven't locked in our partner for this store yet.
   I was curious... are you guys even taking on more local business in {city}
   right now, or are your hands pretty full?"

WHAT I KNOW ABOUT THEM
{research or '  (No research yet — fill in About and General notes on this lead.)'}

THE ASK  (detached, matter-of-fact)
  "Rather than trying to explain visual layouts over the phone while you're
   busy running your day... would you be completely opposed to taking 5 or 10
   minutes this week just to look at the store mock-ups and the foot-traffic
   breakdown? If it's not a fit, no hard feelings — we'll just open the
   category to another business in town.
   Would Thursday morning around 10:00 hurt, or would Friday afternoon be better?"

OBJECTIONS
  "Not interested."
    "Totally understand. Just so I'm not bothering you in the future — when you
     say not interested, is that because you're already booked out with enough
     local customers, or you just haven't seen how supermarket cart branding
     actually works for {a_or_an(one)}?"

  "Just send me an email."
    "I can definitely send something over. The challenge is, without seeing the
     actual store layout and which panels are still unreserved, an email just
     looks like generic numbers. Would you be opposed to a quick 5 minutes, or
     letting me drop off a sample printout? If it's a no, just tell me."

  "We already do advertising."
    "That makes sense, most established businesses do. Out of curiosity, are you
     mostly digital, or do you have a way right now to reach every family within
     three miles of the {at_store} every week?"

  "How much does it cost?"
    "It averages around $25 to $50 a week, less than a cup of coffee a day. But
     honestly, even at five dollars, if it doesn't bring you at least a client or
     two a month it isn't worth a dime. Would it hurt to look at the store's
     traffic numbers first and see if they even make sense for you?"
'''

def a_or_an(word):
    return ('an ' if word[:1].lower() in 'aeiou' else 'a ') + word if word else 'a business'

class Database:
    def __init__(self, path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.con = sqlite3.connect(self.path)
        self.con.row_factory = sqlite3.Row
        self.con.execute('PRAGMA foreign_keys=ON')
        self.con.executescript('''
        CREATE TABLE IF NOT EXISTS leads (
          id INTEGER PRIMARY KEY, business_name TEXT NOT NULL, phone TEXT NOT NULL,
          decision_maker TEXT DEFAULT '', category TEXT DEFAULT '', store TEXT DEFAULT '',
          address TEXT DEFAULT '', website TEXT DEFAULT '', about TEXT DEFAULT '', notes TEXT DEFAULT '',
          status TEXT DEFAULT 'New', callback TEXT DEFAULT '', appointment TEXT DEFAULT '', created TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS calls (
          id INTEGER PRIMARY KEY, lead_id INTEGER NOT NULL REFERENCES leads(id), at TEXT NOT NULL,
          outcome TEXT NOT NULL, notes TEXT DEFAULT '');
        CREATE INDEX IF NOT EXISTS calls_lead ON calls(lead_id);
        CREATE INDEX IF NOT EXISTS calls_at ON calls(at);
        CREATE TABLE IF NOT EXISTS settings (key TEXT PRIMARY KEY, value TEXT DEFAULT '');
        ''')
        # CREATE TABLE IF NOT EXISTS never adds columns, so existing databases need this.
        existing = {row['name'] for row in self.con.execute('PRAGMA table_info(leads)')}
        for column in ['script','script_edited']:
            if column not in existing: self.con.execute(f"ALTER TABLE leads ADD COLUMN {column} TEXT DEFAULT ''")
        self.con.commit()
    def setting(self, key, default=''):
        row = self.con.execute('SELECT value FROM settings WHERE key=?',(key,)).fetchone()
        return row['value'] if row and row['value'] else default
    def set_setting(self, key, value):
        with self.con:
            self.con.execute('INSERT INTO settings(key,value) VALUES(?,?) ON CONFLICT(key) DO UPDATE SET value=excluded.value',(key,str(value).strip()))
    def script_for(self, lead_id):
        """Stored script if there is one, otherwise a script derived from the lead's fields."""
        lead = self.lead(lead_id)
        if (lead['script'] or '').strip(): return lead['script'], bool(lead['script_edited'])
        return build_script(lead,self.setting('caller_name')), False
    def set_script(self, lead_id, text, force=False):
        """Store a researched script. Refuses to clobber a script the user has edited."""
        if self.lead(lead_id)['script_edited'] and not force: return False
        with self.con: self.con.execute('UPDATE leads SET script=? WHERE id=?',(text.strip(),lead_id))
        return True
    def save_lead(self, values, lead_id=None):
        if not values.get('business_name','').strip() or not values.get('phone','').strip():
            raise ValueError('Business name and phone number are required.')
        allowed = FIELDS + ['status','callback','appointment','script']
        clean = {k:str(v).strip() for k,v in values.items() if k in allowed}
        if 'category' in clean: clean['category'] = category_name(clean['category'])
        with self.con:
            if lead_id:
                if 'script' in clean and clean['script'] != (self.lead(lead_id)['script'] or ''):
                    clean['script_edited'] = now()
                self.con.execute('UPDATE leads SET '+','.join(k+'=?' for k in clean)+' WHERE id=?', [*clean.values(), lead_id])
            else:
                clean['created'] = now()
                cur = self.con.execute('INSERT INTO leads ('+','.join(clean)+') VALUES ('+','.join('?' for _ in clean)+')', list(clean.values()))
                lead_id = cur.lastrowid
        return lead_id
    def lead(self, lead_id):
        return self.con.execute('SELECT * FROM leads WHERE id=?',(lead_id,)).fetchone()
    def calls(self, lead_id):
        return self.con.execute('SELECT * FROM calls WHERE lead_id=? ORDER BY at DESC,id DESC',(lead_id,)).fetchall()
    def log_call(self, lead_id, at, outcome, notes, callback='', appointment=''):
        lead = self.lead(lead_id)
        if lead['status'] == 'Do not call': raise ValueError('This lead is marked Do not call. Change its status before logging another call.')
        if outcome not in OUTCOMES: raise ValueError('Choose a call outcome.')
        datetime.fromisoformat(at)
        if outcome == 'Appointment set' and not appointment: raise ValueError('Enter the appointment date and time.')
        if outcome == 'Callback requested' and not callback: raise ValueError('Enter the callback date and time.')
        status = {'Callback requested':'Callback','Appointment set':'Appointment set','Not interested':'Not interested','Wrong number':'Wrong number','Do not call':'Do not call'}.get(outcome,'Working')
        if status in ('Do not call','Not interested','Wrong number','Appointment set'): callback = ''
        with self.con:
            self.con.execute('INSERT INTO calls(lead_id,at,outcome,notes) VALUES (?,?,?,?)',(lead_id,at,outcome,notes))
            self.con.execute('UPDATE leads SET status=?,callback=?,appointment=? WHERE id=?',(status,callback,appointment or lead['appointment'],lead_id))
    def import_rows(self, rows):
        known = {(r['business_name'].casefold().strip(),phone_key(r['phone'])) for r in self.con.execute('SELECT business_name,phone FROM leads')}
        added = duplicates = invalid = 0
        with self.con:
            for row in rows:
                if not row.get('business_name','').strip() or not row.get('phone','').strip(): invalid += 1; continue
                key = (row['business_name'].casefold().strip(),phone_key(row['phone']))
                if key in known: duplicates += 1; continue
                vals = [category_name(row.get(k,'')) if k=='category' else str(row.get(k,'')).strip() for k in FIELDS]
                self.con.execute('INSERT INTO leads('+','.join(FIELDS)+',created) VALUES ('+','.join('?' for _ in range(len(FIELDS)+1))+')',vals+[now()])
                known.add(key); added += 1
        return added,duplicates,invalid
    def category_totals(self):
        totals = {name:0 for name in CATEGORIES}
        totals['Uncategorized'] = 0
        for row in self.con.execute('SELECT category,COUNT(*) AS total FROM leads GROUP BY category'):
            name = category_name(row['category']) or 'Uncategorized'
            totals[name] = totals.get(name,0) + row['total']
        return totals
    def category_choices(self):
        extras = sorted({category_name(r[0]) for r in self.con.execute("SELECT DISTINCT category FROM leads WHERE category!=''")} - set(CATEGORIES))
        return [''] + list(CATEGORIES) + extras
    def backup(self, path):
        if Path(path).resolve() == self.path.resolve(): raise ValueError('Choose a different file from the active database.')
        with sqlite3.connect(path) as dest: self.con.backup(dest)

def read_sheet(path):
    path = Path(path)
    if path.suffix.lower() == '.csv':
        raw = path.read_bytes()
        try: content = raw.decode('utf-8-sig')
        except UnicodeDecodeError: content = raw.decode('cp1252')
        try: dialect = csv.Sniffer().sniff(content[:8192], delimiters=',;\t')
        except csv.Error: dialect = csv.excel
        rows = list(csv.reader(io.StringIO(content),dialect))
    elif path.suffix.lower() == '.xlsx':
        ns = {'m':'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}
        with zipfile.ZipFile(path) as z:
            if sum(i.file_size for i in z.infolist()) > 100_000_000: raise ValueError('Workbook is too large. Split it into smaller files.')
            shared = []
            if 'xl/sharedStrings.xml' in z.namelist():
                root = ET.fromstring(z.read('xl/sharedStrings.xml'))
                shared = [''.join(t.text or '' for t in si.findall('.//m:t',ns)) for si in root]
            workbook = ET.fromstring(z.read('xl/workbook.xml'))
            first = workbook.find('m:sheets/m:sheet',ns)
            if first is None: raise ValueError('Workbook has no worksheets.')
            rid = first.get('{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id')
            rels = ET.fromstring(z.read('xl/_rels/workbook.xml.rels'))
            target = next(x.get('Target') for x in rels if x.get('Id') == rid)
            target = target.lstrip('/') if target.startswith('/') else posixpath.normpath('xl/'+target)
            root = ET.fromstring(z.read(target)); rows = []
            for row in root.findall('m:sheetData/m:row',ns):
                values = []
                for cell in row.findall('m:c',ns):
                    col = re.sub('[^A-Z]','',cell.get('r','A')); index = 0
                    for letter in col: index = index*26+ord(letter)-64
                    while len(values)<index: values.append('')
                    v = cell.find('m:v',ns); value = v.text or '' if v is not None else ''
                    if cell.get('t') == 's': value = shared[int(value)]
                    elif cell.get('t') == 'inlineStr': value = ''.join(t.text or '' for t in cell.findall('.//m:t',ns))
                    values[index-1] = value
                rows.append(values)
    else: raise ValueError('Choose a CSV or XLSX file. Save older XLS files as XLSX first.')
    rows = [r for r in rows if any(str(v).strip() for v in r)]
    if not rows: raise ValueError('The spreadsheet is empty.')
    return rows[0], rows[1:]

class App:
    def __init__(self, root, db):
        self.root,self.db = root,db
        self.page = 0
        self.last_view = None
        root.title('Cart Dial CRM | Appointment desk'); root.geometry('1180x800'); root.minsize(920,650)
        apply_theme(root)
        header=tk.Frame(root,background=COLORS['navy'],padx=24,pady=16); header.pack(fill='x')
        badge=tk.Label(header,text='CART DIAL  /  CRM',font=('Segoe UI',10,'bold'),background=COLORS['navy'],foreground=COLORS['gold']);badge.pack(anchor='w')
        tk.Label(header,text='Appointment desk',font=('Segoe UI',27,'bold'),background=COLORS['navy'],foreground=COLORS['white']).pack(anchor='w',pady=(2,0))
        tk.Label(header,text='Your leads. Your conversations. Your next appointment.',font=('Segoe UI',10),background=COLORS['navy'],foreground=COLORS['header_text']).pack(anchor='w',pady=(2,0))
        tk.Frame(root,background=COLORS['teal'],height=4).pack(fill='x')
        frame = ttk.Frame(root,padding=(20,14)); frame.pack(fill='both',expand=True)
        toolbar = ttk.Frame(frame); toolbar.pack(fill='x')
        for name, action in [('Add lead',lambda:self.card()),('Import spreadsheet',self.import_file),('Scripts & references',self.references),('Backup database',self.backup),('Export call log',self.export_calls)]:
            ttk.Button(toolbar,text=name,command=action,style='Primary.TButton' if name=='Add lead' else 'TButton').pack(side='left',padx=(0,6))
        self.caller = tk.StringVar(value=self.db.setting('caller_name'))
        ttk.Entry(toolbar,textvariable=self.caller,width=16).pack(side='right')
        ttk.Label(toolbar,text='Name you give on calls:').pack(side='right',padx=(0,6))
        self.caller.trace_add('write',lambda *a:self.db.set_setting('caller_name',self.caller.get()))
        types = ttk.Frame(frame); types.pack(fill='x',pady=(8,0))
        ttk.Button(types,text='Leads by business type',command=self.business_totals).pack(side='left')
        self.type_summary = ttk.Label(types,style='Muted.TLabel'); self.type_summary.pack(side='left',padx=12)
        stats = ttk.Frame(frame); stats.pack(fill='x',pady=(10,6))
        ttk.Label(stats,text='Activity date:').pack(side='left')
        self.day = tk.StringVar(value=datetime.now().strftime('%Y-%m-%d'))
        ttk.Entry(stats,textvariable=self.day,width=12).pack(side='left',padx=6)
        ttk.Button(stats,text='Show',command=self.refresh).pack(side='left')
        ttk.Label(stats,text='Daily activity',style='Muted.TLabel').pack(side='right')
        metrics=ttk.Frame(frame);metrics.pack(fill='x',pady=(0,12))
        self.metric_values=[]
        for i,(label,tint,accent) in enumerate([('DIALS MADE','teal_tint','teal'),('LEADS REACHED OUT TO','blue_tint','blue'),('APPOINTMENTS BOOKED','gold_tint','gold_ink')]):
            metrics.columnconfigure(i,weight=1,uniform='metric')
            tile=tk.Frame(metrics,background=COLORS[tint]);tile.grid(row=0,column=i,sticky='nsew',padx=(0,8) if i<2 else 0)
            tk.Frame(tile,background=COLORS[accent],width=4).pack(side='left',fill='y')
            body=tk.Frame(tile,background=COLORS[tint],padx=14,pady=8);body.pack(side='left',fill='both',expand=True)
            number=tk.Label(body,text='0',font=('Segoe UI',25,'bold'),background=COLORS[tint],foreground=COLORS[accent]);number.pack(anchor='w')
            tk.Label(body,text=label,font=('Segoe UI',9,'bold'),background=COLORS[tint],foreground=COLORS[accent]).pack(anchor='w')
            self.metric_values.append(number)
        search = ttk.Frame(frame); search.pack(fill='x',pady=(0,10))
        ttk.Label(search,text='Find a lead:').pack(side='left')
        self.query = tk.StringVar(); entry = ttk.Entry(search,textvariable=self.query,width=33); entry.pack(side='left',padx=6)
        entry.bind('<Return>',lambda e:self.refresh())
        ttk.Button(search,text='Search',command=self.refresh).pack(side='left')
        ttk.Button(search,text='Clear',command=lambda:(self.query.set(''),self.refresh(),entry.focus_set())).pack(side='left',padx=4)
        self.filter = tk.StringVar(value='All leads')
        box = ttk.Combobox(search,textvariable=self.filter,values=['All leads','Callbacks due','Upcoming appointments']+STATUSES,state='readonly',width=24)
        box.pack(side='right'); box.bind('<<ComboboxSelected>>',lambda e:self.refresh())
        area = ttk.Frame(frame); area.pack(fill='both',expand=True)
        columns = ['Business','Phone','Decision maker','Calls','Status','Next callback']
        self.tree = ttk.Treeview(area,columns=columns,show='headings',selectmode='browse')
        self.tree.tag_configure('stripe',background=COLORS['stripe'])
        self.tree.tag_configure('booked',foreground=COLORS['green'])
        self.tree.tag_configure('callback',foreground=COLORS['blue'])
        self.tree.tag_configure('stopped',foreground=COLORS['red'])
        for col,width in zip(columns,[240,145,155,60,145,155]):
            self.tree.heading(col,text=col); self.tree.column(col,width=width,minwidth=55)
        self.tree.pack(side='left',fill='both',expand=True)
        scrollbar = ttk.Scrollbar(area,orient='vertical',command=self.tree.yview); scrollbar.pack(side='right',fill='y'); self.tree.configure(yscrollcommand=scrollbar.set)
        horizontal = ttk.Scrollbar(frame,orient='horizontal',command=self.tree.xview); horizontal.pack(fill='x'); self.tree.configure(xscrollcommand=horizontal.set)
        paging = ttk.Frame(frame); paging.pack(fill='x',pady=(6,0))
        self.previous = ttk.Button(paging,text='Previous 200',command=lambda:self.change_page(-1)); self.previous.pack(side='left')
        self.next_page = ttk.Button(paging,text='Next 200',command=lambda:self.change_page(1)); self.next_page.pack(side='left',padx=6)
        self.tree.bind('<ButtonRelease-1>',self.click_lead); self.tree.bind('<Return>',lambda e:self.open_selected())
        self.tree.bind('<Control-d>',lambda e:self.dial_selected())
        self.feedback = ttk.Label(frame,text='Import a spreadsheet or add your first lead. Click any lead to open its card.'); self.feedback.pack(anchor='w',pady=10)
        root.report_callback_exception = lambda t,v,tb:messagebox.showerror('Could not complete action',str(v),parent=root)
        root.protocol('WM_DELETE_WINDOW',self.shutdown)
        self.refresh()
    def shutdown(self):
        self.db.con.close(); self.root.destroy()
    def change_page(self,delta):
        self.page = max(0,self.page+delta)
        self.refresh()
    def refresh(self):
        try: datetime.strptime(self.day.get(),'%Y-%m-%d')
        except ValueError: messagebox.showerror('Check activity date','Use YYYY-MM-DD.',parent=self.root); return
        day = self.day.get()
        totals = self.db.category_totals()
        self.type_summary.configure(text=f"{sum(totals.values())} total leads   |   {totals['Uncategorized']} uncategorized")
        total,unique,appts = self.db.con.execute("SELECT COUNT(*),COUNT(DISTINCT lead_id),COALESCE(SUM(outcome='Appointment set'),0) FROM calls WHERE substr(at,1,10)=?",(day,)).fetchone()
        for widget,value in zip(self.metric_values,(total,unique,appts)): widget.configure(text=f'{value:,}')
        q = '%'+self.query.get().strip()+'%'
        view = (self.query.get(),self.filter.get())
        if view != self.last_view: self.page = 0; self.last_view = view
        sql = '''SELECT l.*, (SELECT COUNT(*) FROM calls c WHERE c.lead_id=l.id) AS call_count FROM leads l
                 WHERE (business_name LIKE ? OR phone LIKE ? OR decision_maker LIKE ? OR category LIKE ?)'''
        args = [q]*4; f = self.filter.get()
        if f == 'Callbacks due': sql += " AND callback!='' AND callback<=? AND status NOT IN ('Do not call','Not interested','Wrong number','Appointment set')"; args.append(now())
        elif f == 'Upcoming appointments': sql += " AND appointment>=?"; args.append(now())
        elif f != 'All leads': sql += ' AND status=?'; args.append(f)
        sql += ' ORDER BY business_name COLLATE NOCASE LIMIT 201 OFFSET ?'
        args.append(self.page*200)
        rows = self.db.con.execute(sql,args).fetchall()
        has_next = len(rows)>200
        rows = rows[:200]
        self.previous.configure(state='normal' if self.page else 'disabled')
        self.next_page.configure(state='normal' if has_next else 'disabled')
        selected = self.tree.selection()
        self.tree.delete(*self.tree.get_children())
        for index,r in enumerate(rows):
            tags=['stripe'] if index%2 else []
            if r['status']=='Appointment set':tags.append('booked')
            elif r['status']=='Callback':tags.append('callback')
            elif r['status']=='Do not call':tags.append('stopped')
            self.tree.insert('', 'end',iid=str(r['id']),values=(r['business_name'],r['phone'],r['decision_maker'],r['call_count'],r['status'],display_date(r['callback'])),tags=tags)
        kept = [iid for iid in selected if self.tree.exists(iid)]
        if kept: self.tree.selection_set(kept); self.tree.see(kept[0])
        self.feedback.configure(text=f'Leads {self.page*200+1}–{self.page*200+len(rows)}. Enter opens a lead card; Ctrl+D dials the selected lead with TextNow.' if rows else 'No leads found. Add a lead, import a spreadsheet, or clear your filters.')
    def click_lead(self,event):
        row = self.tree.identify_row(event.y)
        if row and self.tree.identify_region(event.x,event.y) in ('cell','tree'): self.card(int(row))
    def open_selected(self):
        if self.tree.selection(): self.card(int(self.tree.selection()[0]))
    def dial_lead(self,parent,lead_id,phone=None):
        lead=self.db.lead(lead_id)
        if lead['status']=='Do not call':
            messagebox.showinfo('Do not call','This lead is marked Do not call. Nothing was dialed.',parent=parent); return False
        number=lead['phone'] if phone is None else phone
        uri=dial_uri(number)
        if not uri:
            messagebox.showwarning('Cannot dial',f"{number or 'This lead'} is not a number TextNow can dial. Correct the phone number, or use Log a call to record the attempt by hand.",parent=parent); return False
        webbrowser.open(uri); return True
    def dial_selected(self):
        if not self.tree.selection():
            self.feedback.configure(text='Select a lead first, then press Ctrl+D to dial it with TextNow.'); return
        lead_id=int(self.tree.selection()[0])
        if not self.dial_lead(self.root,lead_id): return
        name=self.db.lead(lead_id)['business_name']
        self.call_dialog(self.root,lead_id,lambda:(self.refresh(),self.feedback.configure(text=f'Call logged for {name}. Select the next lead and press Ctrl+D.')),required=True)
    def window(self,title,width=840,height=700):
        win = tk.Toplevel(self.root); win.title(title); win.geometry(f'{width}x{height}'); win.minsize(720,620); win.transient(self.root); win.grab_set()
        return win
    def card(self,lead_id=None):
        win = self.window('Lead card'); row = dict(self.db.lead(lead_id)) if lead_id else {k:'' for k in FIELDS}
        frame = ttk.Frame(win,padding=16); frame.pack(fill='both',expand=True)
        title = ttk.Label(frame,text=row.get('business_name') or 'New lead',style='Title.TLabel'); title.pack(anchor='w')
        count = ttk.Label(frame,text=f"{row.get('phone','')}   |   {len(self.db.calls(lead_id)) if lead_id else 0} calls logged"); count.pack(anchor='w',pady=(0,10))
        tabs = ttk.Notebook(frame); tabs.pack(fill='both',expand=True)
        details = ttk.Frame(tabs,padding=12); about = ttk.Frame(tabs,padding=12); log = ttk.Frame(tabs,padding=12)
        script = ttk.Frame(tabs,padding=12)
        tabs.add(details,text='Contact & schedule'); tabs.add(script,text='Call script'); tabs.add(about,text='About & notes'); tabs.add(log,text='Call history')
        values = {}; texts = {}
        for i,(key,label) in enumerate(zip(FIELDS[:7],LABELS[:7])):
            ttk.Label(details,text=label).grid(row=i,column=0,sticky='w',pady=5)
            values[key] = tk.StringVar(value=category_name(row.get(key,'')) if key=='category' else row.get(key,''))
            widget = ttk.Combobox(details,textvariable=values[key],values=self.db.category_choices(),state='readonly',height=16) if key=='category' else ttk.Entry(details,textvariable=values[key])
            widget.grid(row=i,column=1,sticky='ew',padx=12,pady=5)
        for i,key in enumerate(['status','callback','appointment'],7):
            ttk.Label(details,text={'status':'Status','callback':'Next callback','appointment':'Appointment'}[key]).grid(row=i,column=0,sticky='w',pady=5)
            values[key]=tk.StringVar(value=display_date(row.get(key,'')) if key!='status' else row.get(key,'New'))
            widget = ttk.Combobox(details,textvariable=values[key],values=STATUSES,state='readonly') if key=='status' else ttk.Entry(details,textvariable=values[key])
            widget.grid(row=i,column=1,sticky='ew',padx=12,pady=5)
        details.columnconfigure(1,weight=1)
        ttk.Label(details,text='Dates: YYYY-MM-DD HH:MM (24-hour time on your laptop)').grid(row=10,column=0,columnspan=2,sticky='w',pady=8)
        category_help = ttk.Label(details,wraplength=600)
        category_help.grid(row=11,column=0,columnspan=2,sticky='w')
        def explain_category(*args):
            chosen=values['category'].get()
            category_help.configure(text=CATEGORIES.get(chosen,'') or (f'Business type: {chosen}' if chosen else 'Choose a business type above. Blank means uncategorized.'))
        values['category'].trace_add('write',explain_category); explain_category()
        for key,label in [('about','About this business — services, differentiators, useful call context'),('notes','General notes — separate from individual call notes')]:
            ttk.Label(about,text=label).pack(anchor='w'); text = ScrolledText(about,height=6,wrap='word',font=('Segoe UI',11)); text.pack(fill='both',expand=True,pady=(4,10)); text.insert('1.0',row.get(key,'')); texts[key]=text
        script_note = ttk.Label(script,wraplength=740,style='Muted.TLabel'); script_note.pack(anchor='w')
        script_box = ScrolledText(script,height=14,wrap='word',font=('Segoe UI',11)); script_box.pack(fill='both',expand=True,pady=(4,6))
        texts['script'] = script_box; script_loaded = ['']
        def load_script(regenerate=False):
            if not lead_id:
                script_note.configure(text='Save this lead first. The script builds itself from business type, store, city, and decision maker.'); return
            text,edited = (build_script(self.db.lead(lead_id),self.caller.get()),False) if regenerate else self.db.script_for(lead_id)
            script_box.delete('1.0','end'); script_box.insert('1.0',text); script_loaded[0] = text
            script_note.configure(text='Your edited version. Research will not overwrite it.' if edited else 'Built from this lead. Edit it and it becomes yours.')
        ttk.Button(script,text='Rebuild from lead fields',command=lambda:load_script(True)).pack(anchor='w')
        history = ScrolledText(log,height=10,wrap='word',font=('Segoe UI',11)); history.pack(fill='both',expand=True)
        def render_history():
            calls = self.db.calls(lead_id) if lead_id else []
            history.configure(state='normal'); history.delete('1.0','end')
            history.insert('end','\n\n'.join(f"{display_date(c['at'])}  ·  {c['outcome']}\n{c['notes'] or '(No call notes)'}" for c in calls) or 'No calls logged yet. Saving lead details does not count as a dial.')
            history.configure(state='disabled'); count.configure(text=f"{values['phone'].get()}   |   {len(calls)} calls logged")
        def snapshot(): return {**{k:v.get() for k,v in values.items()},**{k:t.get('1.0','end-1c') for k,t in texts.items()}}
        load_script()  # must precede the baseline, or the card opens looking unsaved
        saved = snapshot()
        def close():
            if snapshot()!=saved and not messagebox.askyesno('Unsaved changes','Discard your unsaved lead changes?',parent=win): return
            win.destroy(); self.tree.focus_set()
        def save():
            nonlocal lead_id,saved
            try:
                data=snapshot(); data['callback']=valid_date(data['callback']); data['appointment']=valid_date(data['appointment'])
                # An untouched generated script must not be stored as a hand edit.
                if data.get('script','').strip()==script_loaded[0].strip(): data.pop('script',None)
                lead_id=self.db.save_lead(data,lead_id); load_script(); saved=snapshot(); title.configure(text=data['business_name']); self.refresh(); status.configure(text='Lead saved.'); call_button.configure(state='normal'); dial_button.configure(state='normal'); render_history()
                return True
            except (ValueError,sqlite3.Error) as e: messagebox.showerror('Could not save lead',str(e),parent=win); return False
        def open_call(dial=False):
            if snapshot()!=saved:
                if not messagebox.askyesno('Save lead changes','Save your lead changes before logging this call?',parent=win): return
                if not save(): return
            if dial and not self.dial_lead(win,lead_id,values['phone'].get()): return
            self.call_dialog(win,lead_id,lambda:after_call(dial),required=dial)
        def after_call(dialed=False):
            nonlocal saved
            fresh=self.db.lead(lead_id)
            for k in ['status','callback','appointment']: values[k].set(display_date(fresh[k]) if k!='status' else fresh[k])
            saved=snapshot(); render_history(); self.refresh()
            if dialed:
                win.destroy(); self.tree.focus_set()
                self.feedback.configure(text=f"Call logged for {fresh['business_name']}. Select the next lead and press Ctrl+D."); return
            tabs.select(log); status.configure(text='Call logged. Dial totals updated.')
        buttons=ttk.Frame(frame); buttons.pack(fill='x',pady=(12,0))
        ttk.Button(buttons,text='Save lead',style='Primary.TButton',command=save).pack(side='left')
        dial_button=ttk.Button(buttons,text='Call with TextNow',style='Navy.TButton',command=lambda:open_call(True),state='normal' if lead_id else 'disabled'); dial_button.pack(side='left',padx=8)
        call_button=ttk.Button(buttons,text='Log a call',style='Navy.TButton',command=open_call,state='normal' if lead_id else 'disabled'); call_button.pack(side='left')
        ttk.Button(buttons,text='Close',command=close).pack(side='right')
        status=ttk.Label(frame,text='Save the lead before calling.' if not lead_id else 'Call with TextNow opens the dialer and this call form together. Only a saved call counts as a dial.'); status.pack(anchor='w',pady=(8,0))
        win.protocol('WM_DELETE_WINDOW',close); win.bind('<Escape>',lambda e:close()); render_history()
    def call_dialog(self,parent,lead_id,done,required=False):
        lead=self.db.lead(lead_id)
        if lead['status']=='Do not call': messagebox.showinfo('Do not call','This lead is marked Do not call.',parent=parent); return
        win=self.window('Log this call' if required else 'Log a call',*((900,790) if required else (740,570))); win.transient(parent)
        frame=ttk.Frame(win,padding=20); frame.pack(fill='both',expand=True)
        ttk.Label(frame,text=lead['business_name'],style='Title.TLabel').pack(anchor='w')
        if required:
            ttk.Label(frame,text=f"{lead['phone']} is loaded in TextNow. Press the dial icon there, then record the outcome here before moving to the next lead.",wraplength=840).pack(anchor='w',pady=(2,0))
            # The card is unreachable behind this modal, and Ctrl+D opens no card at all,
            # so the script has to live here or it is not readable during the call.
            script=ScrolledText(frame,height=13,wrap='word',font=('Segoe UI',11)); script.pack(fill='both',expand=True,pady=(8,4))
            script.insert('1.0',self.db.script_for(lead_id)[0]); script.configure(state='disabled')
        vars={}
        fields=[('at','Call date & time',display_date(now())),('outcome','Outcome','No answer'),('callback','Next callback (optional)',display_date(lead['callback']) or (datetime.now()+timedelta(days=1)).strftime('%Y-%m-%d %H:%M')),('appointment','Appointment date & time (if booked)',display_date(lead['appointment']))]
        for key,label,value in fields:
            ttk.Label(frame,text=label).pack(anchor='w',pady=(8,2)); vars[key]=tk.StringVar(value=value)
            widget=ttk.Combobox(frame,textvariable=vars[key],values=OUTCOMES,state='readonly') if key=='outcome' else ttk.Entry(frame,textvariable=vars[key]); widget.pack(fill='x')
        ttk.Label(frame,text='Dates: YYYY-MM-DD HH:MM. Clear callback if no follow-up is needed.').pack(anchor='w',pady=6)
        ttk.Label(frame,text='Notes from this call').pack(anchor='w'); notes=ScrolledText(frame,height=5,wrap='word',font=('Segoe UI',11)); notes.pack(fill='both',expand=True)
        initial={k:v.get() for k,v in vars.items()}
        def restore():
            win.destroy()
            if parent is self.root: self.tree.focus_set()
            else: parent.grab_set()
        def close():
            if required:
                if not messagebox.askyesno('No call placed',f"Close without recording an outcome for {lead['business_name']}?\n\nChoose No to go back and log it. Nothing is saved and this dial is not counted.",icon='warning',default='no',parent=win): return
            elif (any(v.get()!=initial[k] for k,v in vars.items()) or notes.get('1.0','end-1c')) and not messagebox.askyesno('Unsaved call','Discard this unsaved call?',parent=win): return
            restore()
        def commit():
            try:
                at=valid_date(vars['at'].get())
                if not at: raise ValueError('Call date and time are required.')
                self.db.log_call(lead_id,at,vars['outcome'].get(),notes.get('1.0','end-1c'),valid_date(vars['callback'].get()),valid_date(vars['appointment'].get()))
            except (ValueError,sqlite3.Error) as e: messagebox.showerror('Could not log call',str(e),parent=win); return
            restore(); done()
        buttons=ttk.Frame(frame); buttons.pack(fill='x',pady=12)
        ttk.Button(buttons,text='Save call · count 1 dial',style='Primary.TButton',command=commit).pack(side='left'); ttk.Button(buttons,text='No call placed' if required else 'Cancel',command=close).pack(side='right')
        win.protocol('WM_DELETE_WINDOW',close); win.bind('<Escape>',lambda e:close())
    def import_file(self):
        path=filedialog.askopenfilename(title='Import leads',filetypes=[('Spreadsheets','*.csv *.xlsx')],parent=self.root)
        if not path:return
        try: headers,rows=read_sheet(path)
        except Exception as e: messagebox.showerror('Could not read spreadsheet',str(e),parent=self.root); return
        win=self.window('Match spreadsheet columns',800,640); frame=ttk.Frame(win,padding=18); frame.pack(fill='both',expand=True)
        ttk.Label(frame,text='Match your columns',style='Title.TLabel').pack(anchor='w')
        ttk.Label(frame,text=f'{len(rows)} rows found. XLSX uses the first worksheet. Existing leads will not be overwritten.').pack(anchor='w',pady=10)
        choices=['(Not imported)']+[f'{i+1}: {h}' for i,h in enumerate(headers)]; mappings={}; grid=ttk.Frame(frame); grid.pack(fill='x')
        normalized={ALIASES.get(re.sub('[^a-z0-9]','',str(h).lower())):i+1 for i,h in enumerate(headers)}
        for i,(key,label) in enumerate(zip(FIELDS,LABELS)):
            ttk.Label(grid,text=label+(' *' if i<2 else '')).grid(row=i,column=0,sticky='w',pady=4)
            value=tk.StringVar(value=choices[normalized.get(key,0)]); mappings[key]=value
            ttk.Combobox(grid,textvariable=value,values=choices,state='readonly',width=52).grid(row=i,column=1,sticky='ew',padx=12,pady=4)
        ttk.Label(frame,text='First data row (source order):').pack(anchor='w',pady=(12,4))
        preview=ScrolledText(frame,height=4,wrap='word'); preview.pack(fill='both',expand=True); preview.insert('1.0',' | '.join(rows[0]) if rows else '(No data rows)'); preview.configure(state='disabled')
        def commit():
            selected={k:choices.index(v.get())-1 for k,v in mappings.items()}
            if selected['business_name']<0 or selected['phone']<0: messagebox.showerror('Match required columns','Business name and phone number must be matched.',parent=win); return
            used=[v for v in selected.values() if v>=0]
            if len(used)!=len(set(used)): messagebox.showerror('Duplicate mapping','Use each spreadsheet column only once.',parent=win); return
            mapped=[{k:r[i] if 0<=i<len(r) else '' for k,i in selected.items()} for r in rows]
            if not messagebox.askyesno('Import leads',f'Import {len(mapped)} rows? Duplicate business-name / phone pairs and rows missing required values will be skipped.',parent=win): return
            try: added,dupes,bad=self.db.import_rows(mapped)
            except sqlite3.Error as e: messagebox.showerror('Import failed',str(e),parent=win); return
            win.destroy(); self.refresh(); messagebox.showinfo('Import complete',f'{added} added\n{dupes} duplicates skipped\n{bad} rows missing business name or phone skipped',parent=self.root)
        buttons=ttk.Frame(frame); buttons.pack(fill='x',pady=12); ttk.Button(buttons,text='Import leads',style='Primary.TButton',command=commit).pack(side='left'); ttk.Button(buttons,text='Cancel',command=win.destroy).pack(side='right')
    def business_totals(self):
        win=self.window('Leads by business type',940,680)
        frame=ttk.Frame(win,padding=16); frame.pack(fill='both',expand=True)
        totals=self.db.category_totals()
        ttk.Label(frame,text='Leads by business type',style='Title.TLabel').pack(anchor='w')
        ttk.Label(frame,text=f'{sum(totals.values())} total leads · All records, regardless of status or activity date.').pack(anchor='w',pady=8)
        ttk.Label(frame,text='Categories with no leads are included. Each lead counts once under its saved business type.').pack(anchor='w',pady=(0,10))
        area=ttk.Frame(frame);area.pack(fill='both',expand=True)
        table=ttk.Treeview(area,columns=('type','count','details'),show='headings',selectmode='browse')
        for name,label,width in [('type','Business type',340),('count','Leads',65),('details','Specialties / restrictions',440)]:
            table.heading(name,text=label);table.column(name,width=width,minwidth=60,anchor='center' if name=='count' else 'w')
        table.pack(side='left',fill='both',expand=True)
        scroll=ttk.Scrollbar(area,orient='vertical',command=table.yview);scroll.pack(side='right',fill='y');table.configure(yscrollcommand=scroll.set)
        horizontal=ttk.Scrollbar(frame,orient='horizontal',command=table.xview);horizontal.pack(fill='x');table.configure(xscrollcommand=horizontal.set)
        for name,total in totals.items():table.insert('','end',values=(name,total,CATEGORIES.get(name,'Imported custom type' if name!='Uncategorized' else 'No business type selected')))
        ttk.Button(frame,text='Close',command=win.destroy).pack(anchor='e',pady=(12,0));win.bind('<Escape>',lambda e:win.destroy())
    def references(self):
        win=self.window('Scripts & prospecting references',940,680); frame=ttk.Frame(win,padding=16); frame.pack(fill='both',expand=True)
        ttk.Label(frame,text='Your calling playbook',style='Title.TLabel').pack(anchor='w')
        ttk.Label(frame,text='Original supplied text. Replace placeholders and use claims that apply to your current campaign.').pack(anchor='w',pady=10)
        tabs=ttk.Notebook(frame); tabs.pack(fill='both',expand=True)
        names={'safeway_referral_script.md':'Safeway','shopping_cart_directory_script.md':'Cart directory','realtor_script.md':'Realtor','target_categories.md':'Categories','internet_prospecting_guide.md':'Prospecting'}
        for file,label in names.items():
            page=ttk.Frame(tabs); tabs.add(page,text=label); text=ScrolledText(page,wrap='word',font=('Segoe UI',12),padx=12,pady=12); text.pack(fill='both',expand=True)
            path=BASE/'references'/file; text.insert('1.0',path.read_text(encoding='utf-8') if path.exists() else 'Reference file missing. Extract the complete app folder again.'); text.configure(state='disabled')
        ttk.Button(frame,text='Close',command=win.destroy).pack(anchor='e',pady=10); win.bind('<Escape>',lambda e:win.destroy())
    def backup(self):
        path=filedialog.asksaveasfilename(title='Save full database backup',defaultextension='.sqlite3',initialfile='cart-dial-backup-'+datetime.now().strftime('%Y%m%d-%H%M')+'.sqlite3',parent=self.root)
        if path:
            try:self.db.backup(path)
            except Exception as e:messagebox.showerror('Backup failed',str(e),parent=self.root);return
            messagebox.showinfo('Backup saved','All leads, call history, and schedules are in this backup.',parent=self.root)
    def export_calls(self):
        path=filedialog.asksaveasfilename(title='Export complete call history',defaultextension='.csv',initialfile='call-history.csv',parent=self.root)
        if not path:return
        rows=self.db.con.execute('SELECT c.at,l.business_name,l.phone,l.decision_maker,c.outcome,c.notes FROM calls c JOIN leads l ON l.id=c.lead_id ORDER BY c.at DESC').fetchall()
        def safe(value):
            s=str(value or ''); return "'"+s if s.lstrip().startswith(('=','+','-','@')) else s
        with open(path,'w',newline='',encoding='utf-8-sig') as out:
            writer=csv.writer(out);writer.writerow(['Call date','Business name','Phone','Decision maker','Outcome','Call notes']);writer.writerows([[safe(v) for v in r] for r in rows])
        messagebox.showinfo('Export saved',f'{len(rows)} calls exported.',parent=self.root)

def main():
    root=tk.Tk()
    try:
        db=Database(DATA/'crm.sqlite3')
        backupdir=DATA/'backups';backupdir.mkdir(exist_ok=True)
        backup=backupdir/(datetime.now().strftime('%Y-%m-%d')+'.sqlite3')
        if not backup.exists(): db.backup(backup)
        App(root,db);root.mainloop()
    except Exception as e:
        messagebox.showerror('CRM could not start',str(e),parent=root);root.destroy()

if __name__=='__main__':main()
