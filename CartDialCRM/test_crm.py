import csv
import sqlite3
import tempfile
import unittest
import tkinter as tk
from tkinter import ttk
from tkinter.scrolledtext import ScrolledText
from pathlib import Path
from datetime import datetime
import zipfile
import crm
from crm import App,Database,read_sheet,valid_date,dial_uri,greeting_name,trade_noun,priority_of,plural,CATEGORIES

class CRMTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.base=Path(self.temp.name);self.db=Database(self.base/'crm.sqlite3')
    def tearDown(self):self.db.con.close();self.temp.cleanup()
    def test_calls_persist_counts_are_individual_and_backup_is_complete(self):
        a=self.db.save_lead({'business_name':'Alpha','phone':'555-0100','about':'Family owned'})
        b=self.db.save_lead({'business_name':'Beta','phone':'555-0101'})
        self.db.log_call(a,'2026-09-12T10:00:00','No answer','First try')
        self.db.log_call(a,'2026-09-12T11:00:00','Appointment set','Confirmed address',appointment='2026-09-14T12:00:00')
        self.db.log_call(b,'2026-09-11T09:00:00','Voicemail','Left message')
        self.assertEqual(len(self.db.calls(a)),2);self.assertEqual(len(self.db.calls(b)),1)
        self.assertEqual(self.db.con.execute("SELECT COUNT(*) FROM calls WHERE substr(at,1,10)='2026-09-12'").fetchone()[0],2)
        self.db.save_lead({'business_name':'Alpha','phone':'555-0100','notes':'Extra note'},a)
        self.assertEqual(len(self.db.calls(a)),2)
        self.db.backup(self.base/'backup.sqlite3');copy=Database(self.base/'backup.sqlite3')
        self.assertEqual(copy.lead(a)['about'],'Family owned');self.assertEqual(len(copy.calls(a)),2);copy.con.close()
        self.db.con.close();self.db=Database(self.base/'crm.sqlite3');self.assertEqual(len(self.db.calls(a)),2)
    def test_duplicate_import_preserves_notes(self):
        rows=[{'business_name':'Alpha','phone':'(928) 555-0100','notes':'Keep me'}, {'business_name':'alpha','phone':'+1 928 555 0100','notes':'Overwrite'}, {'business_name':'Missing'}]
        self.assertEqual(self.db.import_rows(rows),(1,1,1))
        self.assertEqual(self.db.lead(1)['notes'],'Keep me')
        self.assertEqual(self.db.import_rows(rows),(0,2,1))
    def test_failed_call_does_not_increment(self):
        a=self.db.save_lead({'business_name':'Alpha','phone':'555-0100'})
        with self.assertRaises(ValueError):self.db.log_call(a,'2026-09-12T10:00:00','Appointment set','')
        self.assertEqual(len(self.db.calls(a)),0)
        self.db.log_call(a,'2026-09-12T10:00:00','Do not call','Requested removal',callback='2026-09-13T10:00:00')
        self.assertEqual(self.db.lead(a)['callback'],'')
        with self.assertRaises(ValueError):self.db.log_call(a,'2026-09-12T11:00:00','No answer','')
        self.assertEqual(len(self.db.calls(a)),1)
    def test_csv_preserves_quoted_notes_and_zeros(self):
        path=self.base/'test.csv';path.write_text('Business name,Phone,Notes\nAlpha,001234,"Line one, detail\nLine two"\n',encoding='utf-8-sig')
        headers,rows=read_sheet(path);self.assertEqual(rows[0][1],'001234');self.assertEqual(rows[0][2],'Line one, detail\nLine two')
    def test_csv_keeps_columns_aligned_when_a_cell_quotes_a_phrase(self):
        # csv.Sniffer infers doublequote from whether it happens to see "" in its sample.
        # Guessing False splits a cell containing a quoted phrase into extra columns and
        # every later field lands in the wrong one, which is silent data corruption.
        path=self.base/'quoted.csv'
        with path.open('w',newline='',encoding='utf-8-sig') as fh:
            w=csv.writer(fh)
            w.writerow(['Business name','Phone number','About','Notes'])
            w.writerow(['Prime Pool','(209) 640-1838','Advertises a "Best of Tracy" win, which means they already pay for local reach.','PRIORITY 2. Ranked.'])
        headers,rows=read_sheet(path)
        self.assertEqual(len(headers),4)
        self.assertEqual(len(rows[0]),4,'a quoted phrase must not add columns')
        self.assertIn('"Best of Tracy"',rows[0][2])
        self.assertEqual(rows[0][3],'PRIORITY 2. Ranked.')
        self.assertEqual(priority_of(rows[0][3]),2,'a mis-split row silently loses the rank')
    def test_xlsx_first_sheet_uses_workbook_relationship(self):
        path=self.base/'test.xlsx'
        with zipfile.ZipFile(path,'w') as z:
            z.writestr('xl/workbook.xml','<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"><sheets><sheet name="Leads" sheetId="2" r:id="rId2"/></sheets></workbook>')
            z.writestr('xl/_rels/workbook.xml.rels','<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId2" Target="worksheets/sheet2.xml"/></Relationships>')
            z.writestr('xl/sharedStrings.xml','<sst xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"><si><t>Phone</t></si><si><t>001234</t></si></sst>')
            z.writestr('xl/worksheets/sheet2.xml','<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"><sheetData><row r="1"><c r="A1" t="inlineStr"><is><t>Business name</t></is></c><c r="B1" t="s"><v>0</v></c></row><row r="2"><c r="A2" t="inlineStr"><is><t>Alpha</t></is></c><c r="B2" t="s"><v>1</v></c><c r="D2" t="inlineStr"><is><t>Sparse notes</t></is></c></row></sheetData></worksheet>')
        headers,rows=read_sheet(path);self.assertEqual(headers,['Business name','Phone']);self.assertEqual(rows[0],['Alpha','001234','','Sparse notes'])
    def test_dates(self):
        self.assertEqual(valid_date('2026-09-15 14:30'),'2026-09-15T14:30:00')
        with self.assertRaises(ValueError):valid_date('tomorrow')
        self.assertEqual(valid_date(''),'')
    def test_category_document_and_live_totals(self):
        self.assertEqual(len(CATEGORIES),54)
        self.assertIn('Save Mart only',CATEGORIES['Tattoo Shops'])
        self.assertIn('Dentists',CATEGORIES['Doctors and Urgent Care Clinics'])
        a=self.db.save_lead({'business_name':'Alpha','phone':'1','category':' realtors '})
        self.db.import_rows([{'business_name':'Beta','phone':'2','category':'Realtors'}, {'business_name':'Gamma','phone':'3'}, {'business_name':'Delta','phone':'4','category':'Custom specialty'}])
        totals=self.db.category_totals()
        self.assertEqual(totals['Realtors'],2)
        self.assertEqual(totals['Uncategorized'],1)
        self.assertEqual(totals['Custom specialty'],1)
        self.assertEqual(totals['Insurance Agents'],0)
        self.assertEqual(sum(totals.values()),4)
        self.db.save_lead({'business_name':'Alpha','phone':'1','category':'Insurance Agents'},a)
        self.assertEqual(self.db.category_totals()['Realtors'],1)
        self.assertEqual(self.db.category_totals()['Insurance Agents'],1)
        self.assertIn('Custom specialty',self.db.category_choices())
    def test_lead_card_does_not_clip_button_labels(self):
        lead_id=self.db.save_lead({'business_name':'Alpha','phone':'555-0100'})
        root=tk.Tk()
        try:
            app=App(root,self.db);app.card(lead_id);root.update()
            card=next(widget for widget in root.winfo_children() if isinstance(widget,tk.Toplevel))
            buttons=self.buttons_in(card)
            self.assertEqual({button.cget('text') for button in buttons},{'Save lead','Call with TextNow','Log a call','Close','Rebuild from lead fields'})
            for notebook in [w for w in self.widgets_in(card) if isinstance(w,ttk.Notebook)]:
                for tab in notebook.tabs():
                    notebook.select(tab);root.update()
                    for button in buttons:
                        if button.winfo_ismapped():
                            self.assertGreaterEqual(button.winfo_height(),button.winfo_reqheight(),button.cget('text'))
        finally:
            root.destroy()
    def test_dial_uri_loads_ten_digits_and_refuses_anything_ambiguous(self):
        for value in ['(209) 640-7111','1 (209) 640-7111','+1 209-640-7111','209.640.7111','2096407111']:
            self.assertEqual(dial_uri(value),'tel://2096407111',value)
        for value in ['(209) 640-7111 x204','209-640-7111 ext 3','640-7111','','n/a','(209) 640-7111 / (925) 667-0055']:
            self.assertIsNone(dial_uri(value),value)
    def test_generated_script_fills_every_slot_from_lead_fields(self):
        lead_id=self.db.save_lead({'business_name':'Realta Homes','phone':'(209) 640-7111','category':'Realtors',
            'decision_maker':'Juliana Lanier','store':'Save Mart #781 Schulte - 875 S Tracy Blvd, Tracy CA 95376',
            'address':'793 S Tracy Blvd, Ste 105, Tracy, CA 95376','about':'Broker/Owner since 2005.'})
        self.db.set_setting('caller_name','Clay')
        text,edited=self.db.script_for(lead_id)
        self.assertFalse(edited)
        for expected in ['Juliana','Clay','Save Mart on Tracy Blvd','real estate agent','real estate agents in Tracy','Broker/Owner since 2005.']:
            self.assertIn(expected,text,expected)
        self.assertNotIn('[OWNER]',text);self.assertNotIn('[CITY]',text);self.assertNotIn('[YOUR NAME]',text)
    def test_greeting_name_handles_titles_and_bare_names(self):
        self.assertEqual(greeting_name('Dr. William Do'),'Dr. Do')
        self.assertEqual(greeting_name('Dr. Katherine D. Sanchez'),'Dr. Sanchez')
        self.assertEqual(greeting_name('Carlos E. Sanchez, DDS'),'Carlos')
        self.assertEqual(greeting_name('Juliana Lanier'),'Juliana')
        self.assertEqual(greeting_name('Ryan'),'Ryan')
        self.assertEqual(greeting_name(''),'[OWNER]')
        self.assertEqual(greeting_name('Dr.'),'[OWNER]')
    def test_trade_noun_prefers_the_business_over_a_mixed_category(self):
        for name,category,expected in [
                ('Tracy Family Dental Center','Doctors and Urgent Care Clinics','dentist'),
                ('Sutter Urgent Care','Doctors and Urgent Care Clinics','urgent care clinic'),
                ('Crown Key Realty property management','Realtors','property manager'),
                ('Yvette Larson, Realtor','Realtors','real estate agent'),
                ('Simpson Plumbing','Construction & Home Services','plumber'),
                ('Valor & Virtue Barbershop','Spas and Salons','barber shop'),
                ('Reflect Hair Studio','Spas and Salons','salon')]:
            self.assertEqual(trade_noun({'business_name':name,'category':category,'about':''}),expected,name)
    def test_plural_handles_the_trade_nouns_actually_in_use(self):
        # 'one car wash' is fine but 'local car washs in town' reads as carelessness in the
        # one sentence meant to sound like an insider.
        for one, many in [('car wash','car washes'),('cleaning company','cleaning companies'),
                          ('storage facility','storage facilities'),('attorney','attorneys'),
                          ('pool service','pool services'),('gym','gyms'),('jeweler','jewelers'),
                          ('business','businesses'),('dentist','dentists'),('auto repair shop','auto repair shops')]:
            self.assertEqual(plural(one),many,one)
    def test_every_target_category_says_something_sayable(self):
        # A category with no curated noun falls back to its own lowercased name, so the script
        # says 'ONE photographers / photography and video'. A noun phrase containing 'and' is
        # fine ('one moving and storage company'); echoing the category label is not.
        for category in CATEGORIES:
            one = trade_noun({'business_name':'Some Business','category':category,'about':''})
            self.assertNotEqual(one,category.lower(),f'{category} has no curated trade noun')
            self.assertNotIn('/',one,f'{category} yields an unsayable noun: {one!r}')
            self.assertNotIn(',',one,f'{category} yields an unsayable noun: {one!r}')
            self.assertEqual(one,one.strip())
            self.assertTrue(plural(one).endswith(('s','es')),f'{category} pluralises badly: {plural(one)!r}')
    def test_script_never_quotes_a_price(self):
        lead_id=self.db.save_lead({'business_name':'Alpha','phone':'(209) 640-7111','category':'Realtors'})
        text=self.db.script_for(lead_id)[0]
        for banned in ['$','cup of coffee','a week,','per week','dollars','a dime']:
            self.assertNotIn(banned,text,f'script must not quote a price: {banned!r}')
        self.assertNotRegex(text,r'\$\s*\d|\d+\s*(dollars|bucks)')
        # It must still answer the question rather than stonewall.
        self.assertIn("I'm not going to dance around it",text)
        self.assertIn('one mailer drop',text)
    def test_missing_fields_become_visible_brackets_not_silent_gaps(self):
        lead_id=self.db.save_lead({'business_name':'Mystery Shop','phone':'(209) 640-7112'})
        text,_=self.db.script_for(lead_id)
        self.assertIn('[OWNER]',text);self.assertIn('[CITY]',text);self.assertIn('[YOUR NAME]',text)
    def test_nameless_lead_gets_a_name_discovery_gatekeeper_not_a_broken_one(self):
        blank=self.db.save_lead({'business_name':'No Name Shop','phone':'(209) 640-7112','category':'Realtors',
            'store':'Save Mart #781 - 875 S Tracy Blvd, Tracy CA','address':'1 Main St, Tracy, CA 95376'})
        text=self.db.script_for(blank)[0]
        self.assertIn('who would I need to talk to',text)
        self.assertNotIn("I'm looking for [OWNER]",text)
        named=self.db.save_lead({'business_name':'Named Shop','phone':'(209) 640-7113','category':'Realtors',
            'decision_maker':'Susan Goulding','store':'Save Mart #781 - 875 S Tracy Blvd, Tracy CA',
            'address':'1 Main St, Tracy, CA 95376'})
        text=self.db.script_for(named)[0]
        self.assertIn("I'm looking for Susan",text)
        self.assertNotIn('who would I need to talk to',text)
    def test_research_never_overwrites_a_hand_edited_script(self):
        lead_id=self.db.save_lead({'business_name':'Alpha','phone':'(209) 640-7111','category':'Realtors'})
        self.assertTrue(self.db.set_script(lead_id,'Researched version one'))
        self.assertEqual(self.db.script_for(lead_id),('Researched version one',False))
        self.db.save_lead({'business_name':'Alpha','phone':'(209) 640-7111','script':'My own wording'},lead_id)
        text,edited=self.db.script_for(lead_id)
        self.assertEqual(text,'My own wording');self.assertTrue(edited)
        self.assertFalse(self.db.set_script(lead_id,'Researched version two'))
        self.assertEqual(self.db.script_for(lead_id)[0],'My own wording')
        self.assertTrue(self.db.set_script(lead_id,'Forced version',force=True))
        self.assertEqual(self.db.script_for(lead_id)[0],'Forced version')
    def test_script_columns_are_added_to_an_existing_database(self):
        path=self.base/'legacy.sqlite3'
        old=sqlite3.connect(path)
        old.executescript("CREATE TABLE leads (id INTEGER PRIMARY KEY, business_name TEXT NOT NULL, phone TEXT NOT NULL,"
            "decision_maker TEXT DEFAULT '', category TEXT DEFAULT '', store TEXT DEFAULT '', address TEXT DEFAULT '',"
            "website TEXT DEFAULT '', about TEXT DEFAULT '', notes TEXT DEFAULT '', status TEXT DEFAULT 'New',"
            "callback TEXT DEFAULT '', appointment TEXT DEFAULT '', created TEXT NOT NULL);")
        old.execute("INSERT INTO leads(business_name,phone,created) VALUES('Legacy','(209) 640-7111','2026-01-01T00:00:00')")
        old.commit();old.close()
        migrated=Database(path)
        columns={r['name'] for r in migrated.con.execute('PRAGMA table_info(leads)')}
        self.assertIn('script',columns);self.assertIn('script_edited',columns)
        self.assertEqual(migrated.lead(1)['business_name'],'Legacy')
        self.assertTrue(migrated.set_script(1,'Kept'))
        self.assertEqual(migrated.script_for(1)[0],'Kept')
        migrated.con.close()
    def test_opening_a_card_shows_the_script_without_looking_unsaved(self):
        lead_id=self.db.save_lead({'business_name':'Realta Homes','phone':'(209) 640-7111','category':'Realtors',
            'decision_maker':'Juliana Lanier','store':'Save Mart #781 - 875 S Tracy Blvd, Tracy CA 95376',
            'address':'793 S Tracy Blvd, Tracy, CA 95376'})
        root=tk.Tk()
        try:
            app=App(root,self.db);app.card(lead_id);root.update()
            card=next(w for w in root.winfo_children() if isinstance(w,tk.Toplevel))
            boxes=[w for w in self.widgets_in(card) if isinstance(w,ScrolledText)]
            filled=[b for b in boxes if 'community sponsorship project' in b.get('1.0','end-1c')]
            self.assertEqual(len(filled),1,'exactly one box should hold the generated script')
            # Closing must not prompt about unsaved changes, which means no dialog blocks it.
            self.press(card,'Close');root.update()
            self.assertEqual([w for w in root.winfo_children() if isinstance(w,tk.Toplevel)],[])
            self.assertEqual(self.db.lead(lead_id)['script'],'','an untouched script is never stored')
            self.assertEqual(self.db.lead(lead_id)['script_edited'],'')
        finally:
            root.destroy()
    def test_priority_reads_the_users_own_ranking_convention(self):
        self.assertEqual(priority_of('TIER 0 - office is IN the Save Mart center.'),0)
        self.assertEqual(priority_of('PRIORITY 1. Same building as D&M.'),1)
        self.assertEqual(priority_of('  priority 8 lowercase and indented'),8)
        self.assertEqual(priority_of('Just some notes with no rank'),99)
        self.assertEqual(priority_of(''),99)
        self.assertEqual(priority_of(None),99)
    def test_priority_follows_notes_through_save_and_import(self):
        lead_id=self.db.save_lead({'business_name':'Alpha','phone':'(209) 640-7111','notes':'PRIORITY 3. Later.'})
        self.assertEqual(self.db.lead(lead_id)['priority'],3)
        self.db.save_lead({'business_name':'Alpha','phone':'(209) 640-7111','notes':'TIER 0 - promoted.'},lead_id)
        self.assertEqual(self.db.lead(lead_id)['priority'],0)
        self.db.import_rows([{'business_name':'Beta','phone':'(209) 640-7112','notes':'PRIORITY 5. Imported.'}])
        self.assertEqual(self.db.con.execute("SELECT priority FROM leads WHERE business_name='Beta'").fetchone()[0],5)
    def test_existing_database_gets_priority_backfilled_from_notes(self):
        path=self.base/'legacy2.sqlite3'
        old=sqlite3.connect(path)
        old.executescript("CREATE TABLE leads (id INTEGER PRIMARY KEY, business_name TEXT NOT NULL, phone TEXT NOT NULL,"
            "decision_maker TEXT DEFAULT '', category TEXT DEFAULT '', store TEXT DEFAULT '', address TEXT DEFAULT '',"
            "website TEXT DEFAULT '', about TEXT DEFAULT '', notes TEXT DEFAULT '', status TEXT DEFAULT 'New',"
            "callback TEXT DEFAULT '', appointment TEXT DEFAULT '', created TEXT NOT NULL);")
        for name,note in [('Top','TIER 0 - best'),('Mid','PRIORITY 4. ok'),('None','no rank here')]:
            old.execute('INSERT INTO leads(business_name,phone,notes,created) VALUES(?,?,?,?)',(name,'(209) 640-7111',note,'2026-01-01T00:00:00'))
        old.commit();old.close()
        migrated=Database(path)
        ranks={r['business_name']:r['priority'] for r in migrated.con.execute('SELECT business_name,priority FROM leads')}
        self.assertEqual(ranks,{'Top':0,'Mid':4,'None':99})
        migrated.con.close()
    def test_best_leads_first_orders_by_rank_and_hides_closed_leads(self):
        for name,note,status in [('Zeta','TIER 0 - best','New'),('Alpha','PRIORITY 6. late','New'),
                                 ('Mid','PRIORITY 2. second','New'),('Unranked','no rank','New'),
                                 ('Dropped','TIER 0 - best but unfit','Poor fit'),
                                 ('Refused','TIER 0 - best but refused','Do not call')]:
            self.db.save_lead({'business_name':name,'phone':f'(209) 640-71{10+len(name)}','notes':note,'status':status})
        root=tk.Tk()
        try:
            app=App(root,self.db);app.filter.set('Best leads first');app.refresh();root.update()
            shown=[app.tree.item(i,'values')[1] for i in app.tree.get_children()]
            self.assertEqual(shown,['Zeta','Mid','Alpha','Unranked'])
            self.assertNotIn('Dropped',shown);self.assertNotIn('Refused',shown)
            self.assertEqual(app.tree.item(app.tree.get_children()[0],'values')[0],'0')
            self.assertEqual(app.tree.item(app.tree.get_children()[3],'values')[0],'—')
        finally:
            root.destroy()
    def widgets_in(self,widget):
        stack=[widget];found=[]
        while stack:
            current=stack.pop();stack.extend(current.winfo_children());found.append(current)
        return found
    def buttons_in(self,widget):
        return [w for w in self.widgets_in(widget) if isinstance(w,ttk.Button)]
    def press(self,widget,label):
        next(b for b in self.buttons_in(widget) if b.cget('text').startswith(label)).invoke()
    def test_dialed_call_hands_off_then_closes_the_card_and_keeps_selection(self):
        lead_id=self.db.save_lead({'business_name':'Alpha','phone':'(209) 640-7111'})
        self.db.save_lead({'business_name':'Beta','phone':'(925) 667-0055'})
        root=tk.Tk();dialed=[];original=crm.webbrowser.open
        crm.webbrowser.open=lambda uri:(dialed.append(uri),True)[1]
        try:
            app=App(root,self.db);app.tree.selection_set(str(lead_id));root.update()
            app.card(lead_id);root.update()
            card=next(w for w in root.winfo_children() if isinstance(w,tk.Toplevel))
            self.press(card,'Call with TextNow');root.update()
            self.assertEqual(dialed,['tel://2096407111'])
            dialog=next(w for w in root.winfo_children() if isinstance(w,tk.Toplevel) and w is not card)
            self.press(dialog,'Save call');root.update()
            self.assertEqual(len(self.db.calls(lead_id)),1)
            self.assertEqual([w for w in root.winfo_children() if isinstance(w,tk.Toplevel)],[])
            self.assertEqual(app.tree.selection(),(str(lead_id),))
        finally:
            crm.webbrowser.open=original;root.destroy()
    def test_ctrl_d_dials_selected_row_without_opening_the_card(self):
        lead_id=self.db.save_lead({'business_name':'Alpha','phone':'(209) 640-7111'})
        root=tk.Tk();dialed=[];original=crm.webbrowser.open
        crm.webbrowser.open=lambda uri:(dialed.append(uri),True)[1]
        try:
            app=App(root,self.db);app.tree.selection_set(str(lead_id));root.update()
            app.dial_selected();root.update()
            self.assertEqual(dialed,['tel://2096407111'])
            toplevels=[w for w in root.winfo_children() if isinstance(w,tk.Toplevel)]
            self.assertEqual(len(toplevels),1)
            self.assertEqual(toplevels[0].title(),'Log this call')
            self.press(toplevels[0],'Save call');root.update()
            self.assertEqual(len(self.db.calls(lead_id)),1)
            self.assertEqual(app.tree.selection(),(str(lead_id),))
        finally:
            crm.webbrowser.open=original;root.destroy()
    def test_dial_selected_refuses_do_not_call_and_leaves_the_log_empty(self):
        lead_id=self.db.save_lead({'business_name':'Alpha','phone':'(209) 640-7111','status':'Do not call'})
        root=tk.Tk()
        try:
            app=App(root,self.db);app.tree.selection_set(str(lead_id));root.update()
            self.assertFalse(app.dial_lead(root,lead_id))
            self.assertEqual(self.db.calls(lead_id),[])
        finally:
            root.destroy()
    def test_dialed_disposition_cannot_be_dismissed_without_a_choice(self):
        lead_id=self.db.save_lead({'business_name':'Alpha','phone':'(209) 640-7111'})
        root=tk.Tk()
        try:
            app=App(root,self.db)
            app.call_dialog(root,lead_id,lambda:None,required=True);root.update()
            dialog=next(w for w in root.winfo_children() if isinstance(w,tk.Toplevel))
            labels={button.cget('text') for button in self.buttons_in(dialog)}
            self.assertIn('Save call · count 1 dial',labels)
            self.assertIn('No call placed',labels)
            self.assertNotIn('Cancel',labels)
            self.assertEqual(self.db.calls(lead_id),[])
        finally:
            root.destroy()


if __name__=='__main__':unittest.main()
