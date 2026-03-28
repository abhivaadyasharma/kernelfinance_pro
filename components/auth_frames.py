import customtkinter as ctk
from tkinter import messagebox
import bcrypt
from tkinter import messagebox

class AuthFrame(ctk.CTkFrame):
    def __init__(self, master, db, login_success_callback, **kwargs):
        super().__init__(master, **kwargs)
        self.db = db
        self.on_login_success = login_success_callback
        self.show_login()

    def clear(self):
        for widget in self.winfo_children():
            widget.destroy()

    def show_login(self):
        self.clear()
        ctk.CTkLabel(self, text="KernelFinance Pro", font=("Helvetica", 24, "bold")).pack(pady=30)
        
        u_ent = ctk.CTkEntry(self, placeholder_text="Username", width=260)
        u_ent.pack(pady=10)
        
        p_ent = ctk.CTkEntry(self, placeholder_text="Password", show="*", width=260)
        p_ent.pack(pady=10)

        def do_login():
            u, p = u_ent.get().strip().lower(), p_ent.get()
            res = self.db.query("SELECT id, password FROM users WHERE username=?", (u,), fetch=True)
            if res and bcrypt.checkpw(p.encode(), res[0][1]):
                self.on_login_success(res[0][0])
            else:
                messagebox.showerror("Error", "Invalid Credentials")

        ctk.CTkButton(self, text="Login", command=do_login, width=260).pack(pady=15)
        ctk.CTkButton(self, text="Forgot Password?", fg_color="transparent", text_color="gray", command=self.show_recovery).pack()
        ctk.CTkButton(self, text="Create Account", fg_color="transparent", command=self.show_register).pack()

    def show_register(self):
        self.clear()
        ctk.CTkLabel(self, text="Create Account", font=("Helvetica", 20, "bold")).pack(pady=20)
        
        u = ctk.CTkEntry(self, placeholder_text="Username", width=260); u.pack(pady=5)
        p = ctk.CTkEntry(self, placeholder_text="Password", show="*", width=260); p.pack(pady=5)
        q = ctk.CTkEntry(self, placeholder_text="Security Question (e.g., Pet Name?)", width=260); q.pack(pady=5)
        a = ctk.CTkEntry(self, placeholder_text="Answer", width=260); a.pack(pady=5)

        def reg():
            if not u.get() or not p.get(): return
            hp = bcrypt.hashpw(p.get().encode(), bcrypt.gensalt())
            try:
                self.db.query("INSERT INTO users (username, password, s_ques, s_ans) VALUES (?,?,?,?)", 
                              (u.get().lower(), hp, q.get(), a.get()), commit=True)
                messagebox.showinfo("Success", "Account Created!")
                self.show_login()
            except:
                messagebox.showerror("Error", "Username already exists")

        ctk.CTkButton(self, text="Register", command=reg, width=260).pack(pady=20)
        ctk.CTkButton(self, text="Back to Login", fg_color="transparent", command=self.show_login).pack()

    def show_recovery(self):
        self.clear()
        ctk.CTkLabel(self, text="Password Recovery", font=("Helvetica", 20, "bold")).pack(pady=20)
        
        u_ent = ctk.CTkEntry(self, placeholder_text="Enter Username", width=260)
        u_ent.pack(pady=10)

        def find():
            user = u_ent.get().lower()
            res = self.db.query("SELECT s_ques, s_ans FROM users WHERE username=?", (user,), fetch=True)
            if res:
                ctk.CTkLabel(self, text=f"Question: {res[0][0]}", wraplength=250).pack(pady=10)
                ans_ent = ctk.CTkEntry(self, placeholder_text="Your Answer", width=260); ans_ent.pack(pady=5)
                
                def verify():
                    if ans_ent.get() == res[0][1]:
                        new_p = ctk.CTkEntry(self, placeholder_text="New Password", show="*", width=260); new_p.pack(pady=10)
                        def save():
                            nhp = bcrypt.hashpw(new_p.get().encode(), bcrypt.gensalt())
                            self.db.query("UPDATE users SET password=? WHERE username=?", (nhp, user), commit=True)
                            messagebox.showinfo("Success", "Password Reset!")
                            self.show_login()
                        ctk.CTkButton(self, text="Update Password", command=save, fg_color="#2da44e").pack()
                    else:
                        messagebox.showerror("Error", "Incorrect Answer")
                ctk.CTkButton(self, text="Verify Answer", command=verify).pack(pady=10)
            else:
                messagebox.showerror("Error", "User not found")

        ctk.CTkButton(self, text="Next", command=find, width=260).pack(pady=10)
        ctk.CTkButton(self, text="Back", fg_color="transparent", command=self.show_login).pack()