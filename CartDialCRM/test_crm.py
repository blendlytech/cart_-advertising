import tempfile
import unittest
import tkinter as tk
from tkinter import ttk
from pathlib import Path
from datetime import datetime
import zipfile
import crm
from crm import App,Database,read_sheet,valid_date,dial_uri,CATEGORIES

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
            self.assertEqual({button.cget('text') for button in buttons},{'Save lead','Call with TextNow','Log a call','Close'})
            for button in buttons:self.assertGreaterEqual(button.winfo_height(),button.winfo_reqheight(),button.cget('text'))
        finally:
            root.destroy()
    def test_dial_uri_loads_ten_digits_and_refuses_anything_ambiguous(self):
        for value in ['(209) 640-7111','1 (209) 640-7111','+1 209-640-7111','209.640.7111','2096407111']:
            self.assertEqual(dial_uri(value),'tel:+12096407111',value)
        for value in ['(209) 640-7111 x204','209-640-7111 ext 3','640-7111','','n/a','(209) 640-7111 / (925) 667-0055']:
            self.assertIsNone(dial_uri(value),value)
    def buttons_in(self,widget):
        stack=[widget];found=[]
        while stack:
            current=stack.pop();stack.extend(current.winfo_children())
            if isinstance(current,ttk.Button):found.append(current)
        return found
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
            self.assertEqual(dialed,['tel:+12096407111'])
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
            self.assertEqual(dialed,['tel:+12096407111'])
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
