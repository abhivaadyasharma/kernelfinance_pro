import customtkinter as ctk
from tkinter import messagebox
class GoalFrame(ctk.CTkScrollableFrame):
    def __init__(self, master, db, user_id, refresh_callback, **kwargs):
        super().__init__(master, **kwargs)
        self.db = db
        self.user_id = user_id
        self.refresh_main = refresh_callback
        self.render()

    def render(self):
        for w in self.winfo_children(): w.destroy()
        goals = self.db.query("SELECT id, name, target, saved FROM goals WHERE user_id=?", (self.user_id,), fetch=True)
        
        for gid, name, target, saved in goals:
            f = ctk.CTkFrame(self, fg_color="#2b2b2b")
            f.pack(fill="x", pady=5, padx=5)
            
            ctk.CTkLabel(f, text=name.upper(), font=("Arial", 12, "bold"), width=100).pack(side="left", padx=10)
            
            # Transfer input
            amt_ent = ctk.CTkEntry(f, placeholder_text="Amt", width=60)
            amt_ent.pack(side="left", padx=5)
            
            ctk.CTkButton(f, text="+", width=30, fg_color="#2da44e", command=lambda g=gid, e=amt_ent: self.upd(g, e, 1)).pack(side="left", padx=2)
            ctk.CTkButton(f, text="-", width=30, fg_color="#cf222e", command=lambda g=gid, e=amt_ent: self.upd(g, e, -1)).pack(side="left", padx=2)
            ctk.CTkButton(f, text="🗑", width=30, fg_color="#444444", command=lambda g=gid: self.delete_goal(g)).pack(side="right", padx=10)

    def upd(self, gid, entry, mult):
        try:
            val = float(entry.get()) * mult
            self.db.query("UPDATE goals SET saved = saved + ? WHERE id=?", (val, gid), commit=True)
            self.render(); self.refresh_main()
        except: messagebox.showerror("Error", "Invalid Amount")

    def delete_goal(self, gid):
        if messagebox.askyesno("Confirm", "Delete goal?"):
            self.db.query("DELETE FROM goals WHERE id=?", (gid,), commit=True)
            self.render(); self.refresh_main()