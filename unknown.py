import sqlite3
from tkinter import *
from tkinter import ttk, messagebox
from datetime import datetime
import sys

# --- Database Setup ---
DB_NAME = 'hms_EXISTS.db'

def setup_database(db_path):
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS patients (
                patient_id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                age INTEGER NOT NULL,
                gender TEXT NOT NULL,
                condition TEXT NOT NULL,
                admission_date TEXT NOT NULL,
                status TEXT NOT NULL
            )
        ''')
        conn.commit()
        return conn
    except sqlite3.Error as e:
        messagebox.showerror("FATAL ERROR", f"Database connection failed:\n{e}")
        return None

# --- Main Application ---
class HospitalManagementApp:
    def __init__(self, master, conn, cursor):
        self.master = master
        self.conn = conn
        self.cursor = cursor

        self.colors = {
            'bg': '#F8F9FA',          
            'panel': '#FFFFFF',       
            'primary': '#003366',     
            'success': '#18A0FB',     
            'danger': '#DC3545',      
            'warning': '#FFC107',     
            'text': '#212529',        
            'header_bg': '#E9ECEF',   
            'select_bg': '#C4E1FF'    
        }

        master.title("HMS")
        master.geometry("1100x700")
        master.configure(bg=self.colors['bg']) 
        master.protocol("WM_DELETE_WINDOW", self.on_closing)

        self.setup_styles()

        # Header
        header_frame = Frame(master, bg=self.colors['primary'], height=50)
        header_frame.pack(fill=X)
        Label(header_frame, text="Hospital Administration Dashboard", font=('Inter', 16, 'bold'), 
              bg=self.colors['primary'], fg='white').pack(pady=10)

        # Main Container
        self.main_container = Frame(master, bg=self.colors['bg'], padx=25, pady=25)
        self.main_container.pack(fill=BOTH, expand=True)

        # Controls & Search
        self.control_frame = Frame(self.main_container, bg=self.colors['panel'], padx=15, pady=10, relief=RIDGE, bd=1)
        self.control_frame.pack(fill=X, pady=(0, 20))
        self.setup_controls()

        # List Area
        self.list_frame = Frame(self.main_container, bg=self.colors['panel'], relief=RIDGE, bd=1)
        self.list_frame.pack(fill=BOTH, expand=True)
        self.setup_patient_list()

        self.load_patients()

    def setup_styles(self):
        self.style = ttk.Style()
        self.style.theme_use('clam')
        
        self.style.configure('TFrame', background=self.colors['panel'])
        self.style.configure('TLabel', background=self.colors['panel'], foreground=self.colors['text'], font=('Segoe UI', 10))
        self.style.configure('TEntry', fieldbackground='white', padding=5, font=('Segoe UI', 10))

        common_btn = {'font': ('Segoe UI', 9, 'bold'), 'borderwidth': 0, 'relief': 'flat', 'padding': [10, 5]}
        
        self.style.configure('Primary.TButton', background=self.colors['success'], foreground='white', **common_btn)
        self.style.map('Primary.TButton', background=[('active', '#0B7DCC')])
        
        self.style.configure('Action.TButton', background=self.colors['warning'], foreground=self.colors['text'], **common_btn)
        self.style.map('Action.TButton', background=[('active', '#E0A800')])
        
        self.style.configure('Danger.TButton', background=self.colors['danger'], foreground='white', **common_btn)
        self.style.map('Danger.TButton', background=[('active', '#BD2130')])
        
        self.style.configure('Neutral.TButton', background='#6C757D', foreground='white', **common_btn)
        self.style.map('Neutral.TButton', background=[('active', '#5A6268')])

        self.style.configure("Treeview", background="white", fieldbackground="white", foreground=self.colors['text'], rowheight=30, font=('Segoe UI', 10))
        self.style.configure("Treeview.Heading", background=self.colors['header_bg'], foreground=self.colors['text'], font=('Segoe UI', 10, 'bold'), relief="flat")
        self.style.map('Treeview', background=[('selected', self.colors['select_bg'])], foreground=[('selected', 'black')])

    def on_closing(self):
        if messagebox.askokcancel("Quit", "Close Application?"):
            if self.conn: self.conn.close()
            self.master.destroy()

    def setup_controls(self):
        btn_frame = Frame(self.control_frame, bg=self.colors['panel'])
        btn_frame.pack(side=LEFT)
        
        ttk.Button(btn_frame, text="+ Admit Patient", command=self.open_add_patient_window, style='Primary.TButton').pack(side=LEFT, padx=8)
        ttk.Button(btn_frame, text="Update / Discharge", command=self.update_patient_status, style='Action.TButton').pack(side=LEFT, padx=8)
        ttk.Button(btn_frame, text="Delete Record", command=self.delete_patient, style='Danger.TButton').pack(side=LEFT, padx=8)

        search_frame = Frame(self.control_frame, bg=self.colors['panel'])
        search_frame.pack(side=RIGHT)
        
        Label(search_frame, text="Search (ID/Name):", bg=self.colors['panel'], font=('Segoe UI', 10, 'bold')).pack(side=LEFT, padx=5)
        
        self.search_var = StringVar()
        entry = ttk.Entry(search_frame, textvariable=self.search_var, width=25)
        entry.pack(side=LEFT, padx=5)
        entry.bind('<Return>', lambda e: self.search_patients())
        
        ttk.Button(search_frame, text="Refresh", command=self.load_patients, style='Neutral.TButton').pack(side=LEFT, padx=2)

    def search_patients(self):
        query = self.search_var.get().strip()
        for i in self.patient_tree.get_children(): self.patient_tree.delete(i)
        sql = "SELECT * FROM patients WHERE name LIKE ? OR CAST(patient_id AS TEXT) LIKE ? ORDER BY patient_id DESC"
        self.cursor.execute(sql, ('%' + query + '%', '%' + query + '%'))
        for index, row in enumerate(self.cursor.fetchall()): self._insert_patient(row, index)

    def setup_patient_list(self):
        cols = ("ID", "Name", "Age", "Gender", "Condition", "Admission Date", "Status")
        self.patient_tree = ttk.Treeview(self.list_frame, columns=cols, show='headings')
        wid = [60, 200, 60, 80, 250, 150, 120]
        aligns = ['center', 'w', 'center', 'center', 'w', 'w', 'center']
        
        for i, c in enumerate(cols):
            self.patient_tree.heading(c, text=c)
            self.patient_tree.column(c, width=wid[i], anchor=aligns[i])
        
        self.patient_tree.tag_configure('oddrow', background='white')
        self.patient_tree.tag_configure('evenrow', background='#F8F8F8') 

        sb = ttk.Scrollbar(self.list_frame, orient=VERTICAL, command=self.patient_tree.yview)
        self.patient_tree.configure(yscrollcommand=sb.set)
        sb.pack(side=RIGHT, fill=Y)
        self.patient_tree.pack(fill=BOTH, expand=True)

    def load_patients(self):
        for i in self.patient_tree.get_children(): self.patient_tree.delete(i)
        self.cursor.execute("SELECT * FROM patients ORDER BY patient_id DESC")
        for index, row in enumerate(self.cursor.fetchall()): self._insert_patient(row, index)

    def _insert_patient(self, p, index=0):
        date_short = p[5].split(' ')[0]
        tag = 'evenrow' if index % 2 == 0 else 'oddrow'
        self.patient_tree.insert('', END, values=(p[0], p[1], p[2], p[3], p[4], date_short, p[6]), tags=(tag,))

    def open_add_patient_window(self):
        self.add_win = Toplevel(self.master)
        self.add_win.title("Admit Patient")
        self.add_win.geometry("450x450")
        self.add_win.configure(bg=self.colors['bg'])
        self.add_win.grab_set()

        Label(self.add_win, text="Admit New Patient", font=("Inter", 14, "bold"), bg=self.colors['bg'], fg=self.colors['primary']).pack(pady=20)

        f = Frame(self.add_win, bg=self.colors['panel'], padx=30, pady=30, relief=FLAT, bd=1)
        f.pack(fill=BOTH, expand=True, padx=20, pady=(0, 20))

        self.vars = {'name': StringVar(), 'age': StringVar(), 'gender': StringVar(value='M'), 'cond': StringVar()}
        fields = [("Patient Name:", 'name'), ("Age:", 'age'), ("Gender:", 'gender'), ("Condition:", 'cond')]
        
        for i, (label_text, var_key) in enumerate(fields):
            Label(f, text=label_text, bg=self.colors['panel'], font=('Segoe UI', 10, 'bold')).grid(row=i, column=0, sticky=W, pady=10)
            if var_key == 'gender':
                ttk.OptionMenu(f, self.vars['gender'], 'M', 'M', 'F', 'O').grid(row=i, column=1, sticky=EW, padx=10)
            else:
                ttk.Entry(f, textvariable=self.vars[var_key], width=30).grid(row=i, column=1, sticky=EW, padx=10)

        ttk.Button(f, text="Admit Patient", command=self.save_patient, style='Primary.TButton').grid(row=4, columnspan=2, pady=30, sticky=EW, ipady=5)

    def save_patient(self):
        v = self.vars
        if not (v['name'].get() and v['age'].get() and v['cond'].get()):
            messagebox.showwarning("Error", "All fields required")
            return
        try:
            age = int(v['age'].get())
            dt = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            self.cursor.execute("INSERT INTO patients (name, age, gender, condition, admission_date, status) VALUES (?,?,?,?,?,?)",
                                (v['name'].get(), age, v['gender'].get(), v['cond'].get(), dt, "Admitted"))
            self.conn.commit()
            self.add_win.destroy()
            self.load_patients()
            messagebox.showinfo("Success", "Patient Admitted")
        except: messagebox.showerror("Error", "Invalid Age or Data")

    def update_patient_status(self):
        sel = self.patient_tree.focus()
        if not sel: 
            messagebox.showwarning("Select Patient", "Please select a patient record to update.")
            return
        
        vals = self.patient_tree.item(sel, 'values')
        self.curr_id, self.curr_name, self.curr_status = vals[0], vals[1], vals[6]
        self.cursor.execute("SELECT admission_date FROM patients WHERE patient_id=?", (self.curr_id,))
        self.admission_date_str = self.cursor.fetchone()[0]

        self.upd_win = Toplevel(self.master)
        self.upd_win.title(f"Update: {self.curr_name}")
        self.upd_win.geometry("400x300")
        self.upd_win.configure(bg=self.colors['bg'])
        self.upd_win.grab_set()

        Label(self.upd_win, text=f"Update Status for: {self.curr_name}", font=("Inter", 12, "bold"), bg=self.colors['bg']).pack(pady=15)
        f = Frame(self.upd_win, bg=self.colors['panel'], padx=30, pady=20, relief=RIDGE, bd=1)
        f.pack(fill=BOTH, expand=True, padx=20, pady=(0, 20))

        Label(f, text=f"Current Status: {self.curr_status}", bg=self.colors['panel'], font=('bold')).pack(anchor=W, pady=(0, 10))
        self.new_status_var = StringVar(value=self.curr_status)
        ttk.OptionMenu(f, self.new_status_var, self.curr_status, "Admitted", "Stable", "Critical", "Discharged").pack(fill=X, pady=5)
        ttk.Button(f, text="Proceed (Discharge opens Bill)", command=self._check_status_and_proceed, style='Action.TButton').pack(pady=20, fill=X)

    def _check_status_and_proceed(self):
        new_stat = self.new_status_var.get()
        if new_stat == "Discharged":
            self.upd_win.destroy()
            self.open_billing_dashboard()
        else:
            self._commit_status_change(new_stat)
            self.upd_win.destroy()

    def _commit_status_change(self, status):
        self.cursor.execute("UPDATE patients SET status=? WHERE patient_id=?", (status, self.curr_id))
        self.conn.commit()
        self.load_patients()

    def open_billing_dashboard(self):
        fmt = "%Y-%m-%d %H:%M:%S"
        try: ad_dt = datetime.strptime(self.admission_date_str, fmt)
        except: ad_dt = datetime.strptime(self.admission_date_str, "%Y-%m-%d")
        
        days = (datetime.now() - ad_dt).days
        if days < 1: days = 1

        self.bill_win = Toplevel(self.master)
        self.bill_win.title(f"Billing - {self.curr_name}")
        self.bill_win.geometry("450x550")
        self.bill_win.configure(bg=self.colors['bg'])
        self.bill_win.grab_set()

        Label(self.bill_win, text="Invoice Generation", font=("Inter", 16, "bold"), bg=self.colors['bg']).pack(pady=20)
        f = Frame(self.bill_win, bg=self.colors['panel'], padx=30, pady=30, relief=RIDGE, bd=1)
        f.pack(fill=BOTH, expand=True, padx=20, pady=(0, 20))

        self.bill_vars = {'days': StringVar(value=str(days)), 'room_rate': StringVar(value="2500"), 'doc_fee': StringVar(value="2000"), 'med_cost': StringVar(value="500")}

        Label(f, text="Days Stayed:", bg=self.colors['panel'], font=('Segoe UI', 10, 'bold')).grid(row=1, column=0, sticky=W, pady=10)
        ttk.Entry(f, textvariable=self.bill_vars['days'], width=15, justify='right').grid(row=1, column=1, sticky=E, pady=10)
        
        Label(f, text="Room Rate (Per Day) ₹:", bg=self.colors['panel'], font=('Segoe UI', 10, 'bold')).grid(row=2, column=0, sticky=W, pady=10)
        ttk.Entry(f, textvariable=self.bill_vars['room_rate'], width=15, justify='right').grid(row=2, column=1, sticky=E, pady=10)
        
        Label(f, text="Doctor Fees (Fixed) ₹:", bg=self.colors['panel'], font=('Segoe UI', 10, 'bold')).grid(row=3, column=0, sticky=W, pady=10)
        ttk.Entry(f, textvariable=self.bill_vars['doc_fee'], width=15, justify='right').grid(row=3, column=1, sticky=E, pady=10)
        
        Label(f, text="Medicine/Lab Cost ₹:", bg=self.colors['panel'], font=('Segoe UI', 10, 'bold')).grid(row=4, column=0, sticky=W, pady=10)
        ttk.Entry(f, textvariable=self.bill_vars['med_cost'], width=15, justify='right').grid(row=4, column=1, sticky=E, pady=10)

        ttk.Separator(f, orient=HORIZONTAL).grid(row=5, columnspan=2, sticky=EW, pady=20)
        ttk.Button(f, text="Finalize & Generate Invoice", command=self.generate_final_invoice, style='Primary.TButton').grid(row=6, columnspan=2, sticky=EW, ipady=5)

    def generate_final_invoice(self):
        try:
            days = int(self.bill_vars['days'].get())
            rate = float(self.bill_vars['room_rate'].get())
            doc = float(self.bill_vars['doc_fee'].get())
            med = float(self.bill_vars['med_cost'].get())
            grand_total = (days * rate) + doc + med
        except ValueError:
            messagebox.showerror("Input Error", "Valid numbers required.")
            return

        self._commit_status_change("Discharged")
        self.bill_win.destroy()

        inv_win = Toplevel(self.master)
        inv_win.title("Invoice Preview")
        inv_win.geometry("500x550")
        inv_win.configure(bg=self.colors['bg'])
        inv_win.grab_set()

        paper = Frame(inv_win, bg="white", padx=30, pady=30, relief=FLAT, bd=1)
        paper.pack(pady=20, padx=20, fill=BOTH, expand=True)

        Label(paper, text="INVOICE", font=("Inter", 18, "bold"), fg=self.colors['primary'], bg="white").pack(anchor=W)
        Label(paper, text="------------------------------------------------", fg="#CCC", bg="white").pack(fill=X)

        Label(paper, text=f"Patient: {self.curr_name} (ID: {self.curr_id})", bg="white", font=("Segoe UI", 10, "bold")).pack(anchor=W, pady=10)
        
        tbl_frame = Frame(paper, bg="white", pady=10)
        tbl_frame.pack(fill=X)
        
        Label(tbl_frame, text="ITEM DESCRIPTION", font=("Segoe UI", 10, "bold"), fg=self.colors['primary'], bg="white").grid(row=0, column=0, sticky=W)
        Label(tbl_frame, text="AMOUNT (₹)", font=("Segoe UI", 10, "bold"), fg=self.colors['primary'], bg="white").grid(row=0, column=1, sticky=E)

        items = [(f"Room Charges ({days} days)", days * rate), ("Doctor Fees", doc), ("Medical/Lab", med)]
        for i, (desc, amt) in enumerate(items, 1):
            Label(tbl_frame, text=desc, font=("Segoe UI", 10), bg="white").grid(row=i, column=0, sticky=W, pady=5)
            Label(tbl_frame, text=f"₹ {amt:,.2f}", font=("Segoe UI", 10), bg="white").grid(row=i, column=1, sticky=E, pady=5)
        
        tbl_frame.grid_columnconfigure(0, weight=1)
        Label(paper, text="------------------------------------------------", fg="#CCC", bg="white").pack(fill=X, pady=10)

        tot_frame = Frame(paper, bg="white")
        tot_frame.pack(fill=X)
        Label(tot_frame, text="TOTAL DUE:", font=("Segoe UI", 14, "bold"), bg="white").pack(side=LEFT)
        Label(tot_frame, text=f"₹ {grand_total:,.2f}", font=("Segoe UI", 16, "bold"), fg=self.colors['primary'], bg="white").pack(side=RIGHT)

        ttk.Button(inv_win, text="Close Invoice", command=inv_win.destroy, style='Neutral.TButton').pack(side=BOTTOM, pady=10)

    def delete_patient(self):
        sel = self.patient_tree.focus()
        if not sel: 
            messagebox.showwarning("Select Patient", "Please select a record.")
            return
        pid = self.patient_tree.item(sel, 'values')[0]
        if messagebox.askyesno("Confirm", "Delete this record permanently?"):
            self.cursor.execute("DELETE FROM patients WHERE patient_id=?", (pid,))
            self.conn.commit()
            self.load_patients()

if __name__ == "__main__":
    db_conn = setup_database(DB_NAME)
    if db_conn:
        root = Tk()
        app = HospitalManagementApp(root, db_conn, db_conn.cursor())
        root.mainloop()
