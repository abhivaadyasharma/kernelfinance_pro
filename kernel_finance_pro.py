import math
from collections import defaultdict
from datetime import datetime, timedelta
from pathlib import Path
import sys
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

from api_client import ApiClient

APP_TITLE = "KernelFinance Pro"

CATEGORIES = [
    "Food",
    "Transport",
    "Monthly Bills",
    "Stationary",
    "Party",
    "Shopping",
    "Others",
]

CATEGORY_COLORS = {
    "Food": "#ff5e5b",
    "Transport": "#4aa3ff",
    "Monthly Bills": "#ffd166",
    "Stationary": "#56f39a",
    "Party": "#c084fc",
    "Shopping": "#ff9f1c",
    "Others": "#94a3b8",
}

THEMES = {
    "dark": {
        "bg": "#1e1f22",
        "panel": "#24262b",
        "panel_alt": "#2c2f36",
        "text": "#39ff14",
        "muted": "#8ce88a",
        "danger": "#ff7373",
        "btn_bg": "#2d3a2d",
        "btn_active": "#3d4f3d",
        "entry_bg": "#121315",
        "entry_fg": "#d7ffd1",
    },
    "light": {
        "bg": "#f2f5f3",
        "panel": "#e1e8e3",
        "panel_alt": "#d4dfd8",
        "text": "#0f6b2b",
        "muted": "#2f7f45",
        "danger": "#b73333",
        "btn_bg": "#b8cdbd",
        "btn_active": "#a8c0ae",
        "entry_bg": "#fbfdfb",
        "entry_fg": "#194e2a",
    },
}
THEME = dict(THEMES["dark"])

DEFAULT_CURRENCY = "INR"
CURRENCY_OPTIONS = [
    ("INR", "\u20b9"),
    ("USD", "$"),
    ("EUR", "\u20ac"),
    ("GBP", "\u00a3"),
    ("JPY", "\u00a5"),
    ("AED", "\u062f.\u0625"),
]
CURRENCY_SYMBOLS = {code: symbol for code, symbol in CURRENCY_OPTIONS}




class KernelFinanceApp:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.db = ApiClient()
        self.current_user = None
        self.bar_metadata = []
        self.bar_mode = "monthly"
        self.bar_year_context = None
        self.logo_img = None
        self.logo_scaled_cache = []
        self.logo_path = None
        self.logo_warning_shown = False
        self.currency_var = None
        self.history = None
        self.pie_canvas = None
        self.legend_frame = None
        self.bar_canvas = None
        self.bar_title = None
        self.pie_history_tree = None
        self.pie_history_hint = None
        self.pie_selected_category = None
        self.history_window = None
        self.pie_window = None
        self.compare_window = None
        self.current_screen = "dashboard"
        self.history_category_filter = None
        self.history_month_only = False
        self.history_filters = {}
        self.history_selected_tx_id = None
        self.history_title_label = None
        self.pie_history_tree = None
        self.pie_history_hint = None
        self.pie_selected_category = None

        self.root.title(APP_TITLE)
        self.root.geometry("1400x860")
        self.root.minsize(1200, 760)
        self.root.configure(bg=THEME["bg"])

        self.style = ttk.Style(self.root)
        self.style.theme_use("clam")
        self.configure_ttk_styles()

        self.container = tk.Frame(self.root, bg=THEME["bg"])
        self.container.pack(fill="both", expand=True)
        self.load_logo_image()

        self.login_frame = None
        self.create_account_frame = None
        self.forgot_frame = None
        self.dashboard_frame = None

        self.show_login()

    def configure_ttk_styles(self):
        self.style.configure(
            "Treeview",
            background=THEME["entry_bg"],
            foreground=THEME["entry_fg"],
            fieldbackground=THEME["entry_bg"],
            bordercolor=THEME["panel_alt"],
            rowheight=28,
        )
        self.style.configure(
            "Treeview.Heading",
            background=THEME["panel_alt"],
            foreground=THEME["text"],
            relief="flat",
        )
        self.style.configure(
            "TCombobox",
            fieldbackground=THEME["entry_bg"],
            background=THEME["entry_bg"],
            foreground=THEME["entry_fg"],
            arrowcolor=THEME["text"],
        )

    def load_logo_image(self):
        base_dir = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent))
        candidates = [
            base_dir / "logo.png",
            base_dir / "assets" / "logo.png",
            Path(__file__).resolve().with_name("logo.png"),
            Path(__file__).resolve().with_name("assets").joinpath("logo.png"),
        ]

        for logo_path in candidates:
            if not logo_path.exists():
                continue
            try:
                self.logo_img = tk.PhotoImage(file=str(logo_path))
                self.logo_path = logo_path
                self.root.iconphoto(True, self.logo_img)
                return
            except tk.TclError:
                continue

        self.logo_img = None
        self.logo_path = None

    def clear_container(self):
        for child in self.container.winfo_children():
            child.destroy()

    def make_watermark(self, parent):
        watermark = tk.Label(
            parent,
            text="K",
            font=("Arial Black", 220, "bold"),
            fg="#2c3a2c",
            bg=THEME["bg"],
        )
        watermark.place(relx=0.5, rely=0.53, anchor="center")

    def make_logo_block(self, parent, size=68):
        if self.logo_img is not None:
            canvas = tk.Canvas(parent, width=size, height=size, bg=THEME["bg"], highlightthickness=0)
            w = max(1, self.logo_img.width())
            h = max(1, self.logo_img.height())
            scale = max(1, math.ceil(max(w / size, h / size)))
            img = self.logo_img.subsample(scale, scale)
            self.logo_scaled_cache.append(img)
            canvas.create_image(size / 2, size / 2, image=img)
            return canvas
        canvas = tk.Canvas(parent, width=size, height=size, bg=THEME["bg"], highlightthickness=0)
        canvas.create_rectangle(4, 4, size - 4, size - 4, outline="#1f5cd6", width=2)
        canvas.create_text(size / 2, size / 2, text="K", fill="#76ffe4", font=("Arial Black", int(size * 0.48), "bold"))
        canvas.create_oval(size * 0.44, size * 0.42, size * 0.60, size * 0.58, fill="#ffd23f", outline="#f2a900", width=2)
        return canvas

    def build_auth_shell(self, title_text):
        self.clear_container()
        outer = tk.Frame(self.container, bg=THEME["bg"])
        outer.pack(fill="both", expand=True)

        self.make_watermark(outer)

        card = tk.Frame(outer, bg=THEME["panel"], bd=1, relief="solid")
        card.place(relx=0.5, rely=0.5, anchor="center", width=520, height=620)

        logo = self.make_logo_block(card, size=80)
        logo.place(relx=0.5, y=85, anchor="center")

        title = tk.Label(
            card,
            text=title_text,
            font=("Helvetica", 26, "bold"),
            fg=THEME["text"],
            bg=THEME["panel"],
        )
        title.place(relx=0.5, y=165, anchor="center")

        return card

    def styled_entry(self, parent, show=None):
        entry = tk.Entry(
            parent,
            bg=THEME["entry_bg"],
            fg=THEME["entry_fg"],
            insertbackground=THEME["text"],
            highlightthickness=1,
            highlightbackground=THEME["panel_alt"],
            highlightcolor=THEME["text"],
            relief="flat",
            font=("Helvetica", 12),
            show=show,
        )
        return entry

    def styled_button(self, parent, text, command, width=20):
        btn = tk.Label(
            parent,
            text=text,
            bg=THEME["btn_bg"],
            fg=THEME["text"],
            font=("Helvetica", 11, "bold"),
            padx=10,
            pady=8,
            width=width,
            cursor="hand2",
            bd=1,
            relief="solid",
        )

        def on_enter(_event):
            btn.configure(bg=THEME["btn_active"])

        def on_leave(_event):
            btn.configure(bg=THEME["btn_bg"])

        def on_click(_event):
            command()

        btn.bind("<Enter>", on_enter)
        btn.bind("<Leave>", on_leave)
        btn.bind("<Button-1>", on_click)
        return btn

    def show_login(self):
        card = self.build_auth_shell(APP_TITLE)
        if self.logo_img is None and not self.logo_warning_shown:
            self.logo_warning_shown = True
            messagebox.showwarning(
                "Logo Missing",
                "Logo not found. Put a PNG file at assets/logo.png (or logo.png) and restart the app.",
            )

        username_lbl = tk.Label(card, text="Username", bg=THEME["panel"], fg=THEME["muted"], font=("Helvetica", 11, "bold"))
        username_lbl.place(x=95, y=220)
        username_entry = self.styled_entry(card)
        username_entry.place(x=95, y=246, width=330, height=38)

        password_lbl = tk.Label(card, text="Password", bg=THEME["panel"], fg=THEME["muted"], font=("Helvetica", 11, "bold"))
        password_lbl.place(x=95, y=296)
        password_entry = self.styled_entry(card, show="*")
        password_entry.place(x=95, y=322, width=330, height=38)

        def do_login():
            user = self.db.verify_login(username_entry.get(), password_entry.get())
            if user:
                self.current_user = user
                self.apply_theme(self.get_current_theme(), rerender=False)
                self.show_dashboard()
            else:
                messagebox.showerror("Login Failed", "Invalid username or password.")

        login_btn = self.styled_button(card, "Login", do_login)
        login_btn.place(x=160, y=382)

        create_btn = self.styled_button(card, "New? Create Account", self.show_create_account)
        create_btn.place(x=160, y=442)

        forgot_btn = self.styled_button(card, "Forgot Password?", self.show_forgot_password)
        forgot_btn.place(x=160, y=502)

        username_entry.focus_set()

    def show_create_account(self):
        card = self.build_auth_shell("Create Account")

        labels = [
            ("Username", 200),
            ("Password", 258),
            ("Confirm Password", 316),
            ("Security Answer", 374),
        ]

        entries = {}
        for label, y in labels:
            tk.Label(card, text=label, bg=THEME["panel"], fg=THEME["muted"], font=("Helvetica", 11, "bold")).place(x=95, y=y)
            show_val = "*" if "Password" in label else None
            entry = self.styled_entry(card, show=show_val)
            entry.place(x=95, y=y + 24, width=330, height=34)
            entries[label] = entry

        note = tk.Label(
            card,
            text="Security Question: What is your private answer?",
            bg=THEME["panel"],
            fg=THEME["muted"],
            font=("Helvetica", 10),
        )
        note.place(x=95, y=470)

        def create_account():
            username = entries["Username"].get().strip()
            password = entries["Password"].get()
            confirm = entries["Confirm Password"].get()
            answer = entries["Security Answer"].get().strip()

            if password != confirm:
                messagebox.showerror("Error", "Password and confirm password do not match.")
                return

            try:
                self.db.create_user(username, password, answer)
            except ValueError as exc:
                msg = str(exc)
                if msg == "Username taken":
                    messagebox.showerror("Username taken", "Username taken")
                else:
                    messagebox.showerror("Error", msg)
                return

            messagebox.showinfo("Success", "Account created. Please login.")
            self.show_login()

        create_btn = self.styled_button(card, "Create Account", create_account)
        create_btn.place(x=160, y=516)
        back_btn = self.styled_button(card, "Back to Login", self.show_login)
        back_btn.place(x=160, y=566)

    def show_forgot_password(self):
        card = self.build_auth_shell("Reset Password")

        tk.Label(card, text="Username", bg=THEME["panel"], fg=THEME["muted"], font=("Helvetica", 11, "bold")).place(x=95, y=215)
        username_entry = self.styled_entry(card)
        username_entry.place(x=95, y=240, width=330, height=36)

        tk.Label(card, text="Security Answer", bg=THEME["panel"], fg=THEME["muted"], font=("Helvetica", 11, "bold")).place(x=95, y=290)
        answer_entry = self.styled_entry(card)
        answer_entry.place(x=95, y=315, width=330, height=36)

        tk.Label(card, text="New Password", bg=THEME["panel"], fg=THEME["muted"], font=("Helvetica", 11, "bold")).place(x=95, y=365)
        new_password_entry = self.styled_entry(card, show="*")
        new_password_entry.place(x=95, y=390, width=330, height=36)

        tk.Label(card, text="Confirm New Password", bg=THEME["panel"], fg=THEME["muted"], font=("Helvetica", 11, "bold")).place(x=95, y=440)
        confirm_entry = self.styled_entry(card, show="*")
        confirm_entry.place(x=95, y=465, width=330, height=36)

        def reset_password():
            username = username_entry.get().strip()
            answer = answer_entry.get().strip()
            new_password = new_password_entry.get()
            confirm = confirm_entry.get()

            if new_password != confirm:
                messagebox.showerror("Error", "New password and confirm password do not match.")
                return

            try:
                self.db.reset_password_with_answer(username, answer, new_password)
            except (ValueError, ConnectionError) as exc:
                messagebox.showerror("Error", str(exc))
                return

            messagebox.showinfo("Success", "Password reset successful. Please login.")
            self.show_login()

        reset_btn = self.styled_button(card, "Reset Password", reset_password)
        reset_btn.place(x=160, y=522)
        back_btn = self.styled_button(card, "Back to Login", self.show_login)
        back_btn.place(x=160, y=570)

    def show_dashboard(self):
        self.current_screen = "dashboard"
        self.history_category_filter = None
        self.history_month_only = False
        self.clear_container()
        self.bar_mode = "monthly"
        self.bar_year_context = None
        self.history = None
        self.pie_canvas = None
        self.legend_frame = None
        self.bar_canvas = None
        self.bar_title = None

        page = tk.Frame(self.container, bg=THEME["bg"])
        page.pack(fill="both", expand=True)
        self.build_dashboard_header(page)

        menu_frame = tk.Frame(page, bg=THEME["panel_alt"], bd=1, relief="solid")
        menu_frame.pack(fill="both", expand=True, padx=14, pady=(0, 14))

        tk.Label(
            menu_frame,
            text="Dashboard Menu",
            bg=THEME["panel_alt"],
            fg=THEME["text"],
            font=("Helvetica", 18, "bold"),
        ).pack(pady=(24, 14))

        self.add_menu_button_with_description(
            menu_frame,
            "Add Transaction",
            "Add a new expense with value, category, and remark.",
            self.show_add_transaction_screen,
        )
        self.add_menu_button_with_description(
            menu_frame,
            "View Transaction History",
            "See all transactions from oldest to latest with date and details.",
            self.show_history_screen,
        )
        self.add_menu_button_with_description(
            menu_frame,
            "Monthly Expenditure Pie Chart",
            "View this month category-wise spending distribution.",
            self.show_pie_screen,
        )
        self.add_menu_button_with_description(
            menu_frame,
            "Compare Your Expenditure In Bargraphs",
            "Compare expenses weekly, monthly, and yearly.",
            self.show_compare_screen,
        )
        self.add_menu_button_with_description(
            menu_frame,
            "Edit Profile",
            "Update display name, real name, and account preferences.",
            self.show_profile_screen,
        )
        self.add_menu_button_with_description(
            menu_frame,
            "Backup / Restore Database",
            "Create a backup file or restore from a previous backup.",
            self.show_data_tools_screen,
        )

        footer = tk.Frame(page, bg=THEME["bg"])
        footer.place(relx=0.0, rely=1.0, anchor="sw", x=20, y=-20)
        logout_btn = self.styled_button(footer, "Logout", self.logout, width=10)
        logout_btn.pack()

        self.refresh_dashboard_data()

    def build_dashboard_header(self, parent, show_back=False):
        top = tk.Frame(parent, bg=THEME["panel"], height=120)
        top.pack(fill="x", padx=14, pady=(14, 12))
        top.pack_propagate(False)

        top.grid_columnconfigure(0, weight=1)
        top.grid_columnconfigure(1, weight=1)
        top.grid_columnconfigure(2, weight=1)

        left_block = tk.Frame(top, bg=THEME["panel"])
        left_block.grid(row=0, column=0, sticky="w", padx=8, pady=10)

        logo = self.make_logo_block(left_block, size=64)
        logo.pack(side="left", padx=8)

        greeting = tk.Label(
            left_block,
            text=f"Hello {self.get_greeting_name()}",
            bg=THEME["panel"],
            fg=THEME["text"],
            font=("Helvetica", 24, "bold"),
        )
        greeting.pack(side="left", padx=10)

        if show_back:
            self.styled_button(left_block, "Back", self.show_dashboard, width=8).pack(side="left", padx=14)

        center_info = tk.Frame(top, bg=THEME["panel"])
        center_info.grid(row=0, column=1, sticky="n")

        month_total = self.month_total_for_current_user()
        self.month_total_label = tk.Label(
            center_info,
            text=f"Total Expenditure (This Month): {self.format_amount(month_total)}",
            bg=THEME["panel"],
            fg=THEME["muted"],
            font=("Helvetica", 14, "bold"),
        )
        self.month_total_label.pack(pady=(42, 0))

        right_info = tk.Frame(top, bg=THEME["panel"])
        right_info.grid(row=0, column=2, sticky="e", padx=14, pady=8)

        currency_row = tk.Frame(right_info, bg=THEME["panel"])
        currency_row.pack(anchor="e")
        tk.Label(
            currency_row,
            text="Currency:",
            bg=THEME["panel"],
            fg=THEME["muted"],
            font=("Helvetica", 11, "bold"),
        ).pack(side="left", padx=(0, 8))

        current_currency = self.get_current_currency()
        currency_display_by_code = {code: f"{code} ({symbol})" for code, symbol in CURRENCY_OPTIONS}
        code_by_currency_display = {v: k for k, v in currency_display_by_code.items()}

        self.currency_var = tk.StringVar(value=currency_display_by_code.get(current_currency, currency_display_by_code[DEFAULT_CURRENCY]))
        def on_currency_change(_event=None):
            selected_display = self.currency_var.get()
            selected_code = code_by_currency_display.get(selected_display)
            if not selected_code or not self.current_user:
                return
            self.db.update_currency(self.current_user["id"], selected_code)
            self.current_user = self.db.get_user_by_id(self.current_user["id"])
            self.refresh_dashboard_data()
        self.make_dark_selector(
            currency_row,
            self.currency_var,
            [currency_display_by_code[c] for c, _ in CURRENCY_OPTIONS],
            on_currency_change,
            width=120,
        ).pack(side="left")

        theme_row = tk.Frame(right_info, bg=THEME["panel"])
        theme_row.pack(anchor="e", pady=(8, 0))
        tk.Label(
            theme_row,
            text="Theme:",
            bg=THEME["panel"],
            fg=THEME["muted"],
            font=("Helvetica", 11, "bold"),
        ).pack(side="left", padx=(0, 8))

        theme_display = {"dark": "Dark", "light": "Light"}
        reverse_theme_display = {v: k for k, v in theme_display.items()}
        selected_theme = self.get_current_theme()
        theme_var = tk.StringVar(value=theme_display.get(selected_theme, "Dark"))

        def on_theme_change(_event=None):
            choice = reverse_theme_display.get(theme_var.get(), "dark")
            if self.current_user:
                self.db.update_theme(self.current_user["id"], choice)
                self.current_user = self.db.get_user_by_id(self.current_user["id"])
            self.apply_theme(choice)
        self.make_dark_selector(theme_row, theme_var, ["Dark", "Light"], on_theme_change, width=96).pack(side="left")

    def make_dark_selector(self, parent, variable, options, on_change, width=120):
        outer = tk.Frame(parent, bg=THEME["entry_bg"], highlightthickness=1, highlightbackground=THEME["muted"], width=width, height=30)
        outer.pack_propagate(False)
        row = tk.Frame(outer, bg=THEME["entry_bg"])
        row.pack(fill="both", expand=True, padx=2, pady=2)
        val = tk.Label(row, textvariable=variable, bg=THEME["entry_bg"], fg=THEME["entry_fg"], font=("Helvetica", 10), anchor="w", padx=8, pady=4, cursor="hand2")
        val.pack(side="left", fill="both", expand=True)
        arrow = tk.Label(row, text="\u25be", bg=THEME["entry_bg"], fg=THEME["text"], font=("Helvetica", 10, "bold"), padx=8, pady=4, cursor="hand2")
        arrow.pack(side="right")
        menu = tk.Menu(self.root, tearoff=0)
        menu.config(bg=THEME["entry_bg"], fg=THEME["entry_fg"], activebackground=THEME["panel_alt"], activeforeground=THEME["text"], font=("Helvetica", 10))
        for opt in options:
            menu.add_command(label=opt, command=lambda o=opt: self._set_selector_value(variable, o, on_change))

        def open_menu(_event=None):
            x = row.winfo_rootx()
            y = row.winfo_rooty() + row.winfo_height()
            menu.tk_popup(x, y)
            menu.grab_release()

        val.bind("<Button-1>", open_menu)
        arrow.bind("<Button-1>", open_menu)
        row.bind("<Button-1>", open_menu)
        return outer

    def _set_selector_value(self, var_obj, value, callback):
        var_obj.set(value)
        callback()

    def add_menu_button_with_description(self, parent, title, description, command):
        wrap = tk.Frame(parent, bg=THEME["panel_alt"])
        wrap.pack(fill="x", padx=20, pady=6)
        self.styled_button(wrap, title, command, width=38).pack(pady=(4, 4))
        tk.Label(
            wrap,
            text=description,
            bg=THEME["panel_alt"],
            fg=THEME["muted"],
            font=("Helvetica", 10),
        ).pack()

    def show_add_transaction_screen(self, edit_tx=None, return_screen="dashboard"):
        self.current_screen = "add"
        self.clear_container()
        page = tk.Frame(self.container, bg=THEME["bg"])
        page.pack(fill="both", expand=True)
        self.build_dashboard_header(page, show_back=True)

        card = tk.Frame(page, bg=THEME["panel_alt"], bd=1, relief="solid")
        card.pack(fill="both", expand=True, padx=14, pady=(0, 14))

        heading = "Edit Transaction" if edit_tx else "Add Transaction"
        tk.Label(card, text=heading, bg=THEME["panel_alt"], fg=THEME["text"], font=("Helvetica", 16, "bold")).pack(pady=(20, 10))

        form = tk.Frame(card, bg=THEME["panel_alt"])
        form.pack(pady=8)
        form.grid_columnconfigure(0, minsize=320)

        tk.Label(form, text="Value", bg=THEME["panel_alt"], fg=THEME["muted"], font=("Helvetica", 11, "bold")).grid(row=0, column=0, sticky="w", pady=(4, 2))
        amount_box = tk.Frame(form, bg=THEME["entry_bg"], highlightthickness=1, highlightbackground=THEME["muted"])
        amount_box.grid(row=1, column=0, sticky="ew", pady=(0, 8))
        amount_entry = self.styled_entry(amount_box)
        amount_entry.pack(fill="x", padx=2, pady=2, ipady=6)

        tk.Label(form, text="Category", bg=THEME["panel_alt"], fg=THEME["muted"], font=("Helvetica", 11, "bold")).grid(row=2, column=0, sticky="w", pady=(4, 2))
        category_var = tk.StringVar(value=CATEGORIES[0])
        category_box = tk.Frame(form, bg=THEME["entry_bg"], highlightthickness=1, highlightbackground=THEME["muted"])
        category_box.grid(row=3, column=0, sticky="ew", pady=(0, 8))
        category_row = tk.Frame(category_box, bg=THEME["entry_bg"])
        category_row.pack(fill="x", padx=2, pady=2)
        category_value = tk.Label(
            category_row,
            textvariable=category_var,
            bg=THEME["entry_bg"],
            fg=THEME["entry_fg"],
            font=("Helvetica", 11),
            anchor="w",
            padx=8,
            pady=6,
            cursor="hand2",
        )
        category_value.pack(side="left", fill="x", expand=True)
        category_arrow = tk.Label(
            category_row,
            text="\u25be",
            bg=THEME["entry_bg"],
            fg=THEME["entry_fg"],
            font=("Helvetica", 11, "bold"),
            padx=8,
            pady=6,
            cursor="hand2",
        )
        category_arrow.pack(side="right")

        category_menu = tk.Menu(self.root, tearoff=0)
        category_menu.config(
            bg=THEME["entry_bg"],
            fg=THEME["entry_fg"],
            activebackground=THEME["panel_alt"],
            activeforeground=THEME["text"],
            font=("Helvetica", 11),
        )
        for category in CATEGORIES:
            category_menu.add_command(label=category, command=lambda c=category: category_var.set(c))

        def open_category_menu(_event=None):
            x = category_row.winfo_rootx()
            y = category_row.winfo_rooty() + category_row.winfo_height()
            category_menu.tk_popup(x, y)
            category_menu.grab_release()

        category_value.bind("<Button-1>", open_category_menu)
        category_arrow.bind("<Button-1>", open_category_menu)
        category_row.bind("<Button-1>", open_category_menu)

        tk.Label(form, text="Remark", bg=THEME["panel_alt"], fg=THEME["muted"], font=("Helvetica", 11, "bold")).grid(row=4, column=0, sticky="w", pady=(4, 2))
        remark_box = tk.Frame(form, bg=THEME["entry_bg"], highlightthickness=1, highlightbackground=THEME["muted"])
        remark_box.grid(row=5, column=0, sticky="ew", pady=(0, 12))
        remark_entry = self.styled_entry(remark_box)
        remark_entry.pack(fill="x", padx=2, pady=2, ipady=6)

        if edit_tx:
            amount_entry.insert(0, f"{float(edit_tx['amount']):.2f}")
            category_var.set(edit_tx["category"])
            remark_entry.insert(0, edit_tx["remark"] or "")

        def register_transaction():
            raw_amount = amount_entry.get().strip()
            try:
                amount = float(raw_amount)
                if amount <= 0:
                    raise ValueError
            except ValueError:
                messagebox.showerror("Error", "Please enter a valid positive transaction value.")
                return

            if edit_tx:
                self.db.update_transaction(
                    self.current_user["id"],
                    edit_tx["id"],
                    amount,
                    category_var.get(),
                    remark_entry.get(),
                )
                messagebox.showinfo("Success", "Transaction updated.")
            else:
                self.db.add_transaction(
                    self.current_user["id"],
                    amount,
                    category_var.get(),
                    remark_entry.get(),
                )
                messagebox.showinfo("Success", "Transaction registered.")
            if return_screen == "history":
                self.show_history_screen(self.history_category_filter, self.history_month_only)
            else:
                self.show_dashboard()

        action_text = "Save Changes" if edit_tx else "Register Transaction"
        self.styled_button(card, action_text, register_transaction, width=24).pack(pady=8)
        self.root.after(50, amount_entry.focus_set)

    def show_history_screen(self, category_filter=None, month_only=False):
        self.current_screen = "history"
        self.history_category_filter = category_filter
        self.history_month_only = month_only
        self.history_selected_tx_id = None
        self.clear_container()
        page = tk.Frame(self.container, bg=THEME["bg"])
        page.pack(fill="both", expand=True)
        self.build_dashboard_header(page, show_back=True)

        wrap = tk.Frame(page, bg=THEME["panel_alt"], bd=1, relief="solid")
        wrap.pack(fill="both", expand=True, padx=14, pady=(0, 14))

        self.history_title_label = tk.Label(
            wrap,
            text=self.history_title_text(category_filter, month_only),
            bg=THEME["panel_alt"],
            fg=THEME["text"],
            font=("Helvetica", 14, "bold"),
        )
        self.history_title_label.pack(anchor="nw", padx=14, pady=(12, 4))

        filters_wrap = tk.Frame(wrap, bg=THEME["panel_alt"])
        filters_wrap.pack(fill="x", padx=14, pady=(2, 8))
        self.history_filters = {}

        self.history_filters["from_date"] = self.make_filter_entry(filters_wrap, "From Date (YYYY-MM-DD)", 0, 0)
        self.history_filters["to_date"] = self.make_filter_entry(filters_wrap, "To Date (YYYY-MM-DD)", 0, 1)
        self.history_filters["min_amount"] = self.make_filter_entry(filters_wrap, "Min Amount", 1, 0)
        self.history_filters["max_amount"] = self.make_filter_entry(filters_wrap, "Max Amount", 1, 1)
        self.history_filters["remark"] = self.make_filter_entry(filters_wrap, "Remark Contains", 2, 0)

        filter_btns = tk.Frame(filters_wrap, bg=THEME["panel_alt"])
        filter_btns.grid(row=2, column=1, sticky="e", padx=6, pady=(6, 0))
        self.styled_button(filter_btns, "Apply Filters", self.refresh_history, width=12).pack(side="left", padx=4)
        self.styled_button(filter_btns, "Reset", self.reset_history_filters, width=8).pack(side="left", padx=4)
        self.styled_button(filter_btns, "Export PDF", self.export_history_pdf, width=10).pack(side="left", padx=4)

        table_wrap = tk.Frame(wrap, bg=THEME["panel_alt"])
        table_wrap.pack(fill="both", expand=True, padx=14, pady=(8, 14))

        columns = ("id", "date", "category", "remark", "value")
        self.history = ttk.Treeview(table_wrap, columns=columns, show="headings")
        self.history.heading("id", text="ID")
        self.history.heading("date", text="Date")
        self.history.heading("category", text="Category")
        self.history.heading("remark", text="Remark")
        self.history.heading("value", text="Value")
        self.history.column("id", width=70, anchor="center")
        self.history.column("date", width=140)
        self.history.column("category", width=140)
        self.history.column("remark", width=360)
        self.history.column("value", width=140, anchor="e")
        self.history.bind("<<TreeviewSelect>>", self.on_history_select)

        hist_scroll = ttk.Scrollbar(table_wrap, orient="vertical", command=self.history.yview)
        self.history.configure(yscroll=hist_scroll.set)
        self.history.pack(fill="both", expand=True, side="left")
        hist_scroll.pack(fill="y", side="right")

        action_row = tk.Frame(wrap, bg=THEME["panel_alt"])
        action_row.pack(fill="x", padx=14, pady=(0, 10))
        self.styled_button(action_row, "Edit Selected", self.edit_selected_transaction, width=12).pack(side="left", padx=4)
        self.styled_button(action_row, "Delete Selected", self.delete_selected_transaction, width=13).pack(side="left", padx=4)
        self.refresh_history()

    def make_filter_entry(self, parent, label, row, col):
        wrap = tk.Frame(parent, bg=THEME["panel_alt"])
        wrap.grid(row=row, column=col, sticky="w", padx=6, pady=4)
        tk.Label(wrap, text=label, bg=THEME["panel_alt"], fg=THEME["muted"], font=("Helvetica", 10, "bold")).pack(anchor="w")
        entry = self.styled_entry(wrap)
        entry.pack(ipadx=80, ipady=3)
        return entry

    def show_pie_screen(self):
        self.current_screen = "pie"
        self.pie_selected_category = None
        self.clear_container()
        page = tk.Frame(self.container, bg=THEME["bg"])
        page.pack(fill="both", expand=True)
        self.build_dashboard_header(page, show_back=True)

        wrap = tk.Frame(page, bg=THEME["panel_alt"], bd=1, relief="solid")
        wrap.pack(fill="both", expand=True, padx=14, pady=(0, 14))

        tk.Label(
            wrap,
            text="This Month Category Split",
            bg=THEME["panel_alt"],
            fg=THEME["text"],
            font=("Helvetica", 13, "bold"),
        ).pack(pady=(12, 8))
        tk.Label(
            wrap,
            text="Tip: Click a pie slice to view history for that category only.",
            bg=THEME["panel_alt"],
            fg=THEME["muted"],
            font=("Helvetica", 10),
        ).pack()

        self.pie_canvas = tk.Canvas(wrap, width=420, height=320, bg=THEME["entry_bg"], highlightthickness=0)
        self.pie_canvas.pack(padx=10, pady=8)
        self.legend_frame = tk.Frame(wrap, bg=THEME["panel_alt"])
        self.legend_frame.pack(fill="x", padx=12, pady=(2, 12))

        self.pie_history_hint = tk.Label(
            wrap,
            text="Category History (Current Month): Click a slice to load.",
            bg=THEME["panel_alt"],
            fg=THEME["muted"],
            font=("Helvetica", 11, "bold"),
        )
        self.pie_history_hint.pack(anchor="w", padx=12, pady=(8, 4))

        pie_hist_wrap = tk.Frame(wrap, bg=THEME["panel_alt"])
        pie_hist_wrap.pack(fill="both", expand=True, padx=12, pady=(0, 10))
        cols = ("date", "remark", "value")
        self.pie_history_tree = ttk.Treeview(pie_hist_wrap, columns=cols, show="headings", height=8)
        self.pie_history_tree.heading("date", text="Date")
        self.pie_history_tree.heading("remark", text="Remark")
        self.pie_history_tree.heading("value", text="Value")
        self.pie_history_tree.column("date", width=150)
        self.pie_history_tree.column("remark", width=420)
        self.pie_history_tree.column("value", width=130, anchor="e")
        pie_hist_scroll = ttk.Scrollbar(pie_hist_wrap, orient="vertical", command=self.pie_history_tree.yview)
        self.pie_history_tree.configure(yscroll=pie_hist_scroll.set)
        self.pie_history_tree.pack(fill="both", expand=True, side="left")
        pie_hist_scroll.pack(fill="y", side="right")
        self.draw_pie_chart()

    def show_compare_screen(self):
        self.current_screen = "compare"
        self.bar_mode = "monthly"
        self.bar_year_context = None
        self.clear_container()
        page = tk.Frame(self.container, bg=THEME["bg"])
        page.pack(fill="both", expand=True)
        self.build_dashboard_header(page, show_back=True)

        wrap = tk.Frame(page, bg=THEME["panel_alt"], bd=1, relief="solid")
        wrap.pack(fill="both", expand=True, padx=14, pady=(0, 14))

        mode_row = tk.Frame(wrap, bg=THEME["panel_alt"])
        mode_row.pack(pady=(14, 8))
        self.styled_button(mode_row, "Weekly", lambda: self.draw_comparison_chart("weekly"), width=10).pack(side="left", padx=4)
        self.styled_button(mode_row, "Monthly", lambda: self.draw_comparison_chart("monthly"), width=10).pack(side="left", padx=4)
        self.styled_button(mode_row, "Yearly", lambda: self.draw_comparison_chart("yearly"), width=10).pack(side="left", padx=4)

        self.bar_title = tk.Label(wrap, text="Monthly Comparison", bg=THEME["panel_alt"], fg=THEME["text"], font=("Helvetica", 12, "bold"))
        self.bar_title.pack(pady=(2, 8))

        self.bar_canvas = tk.Canvas(wrap, width=560, height=500, bg=THEME["entry_bg"], highlightthickness=0)
        self.bar_canvas.pack(padx=14, pady=(0, 14), fill="both", expand=True)
        self.bar_canvas.bind("<Button-1>", self.on_bar_click)
        self.draw_comparison_chart("monthly")

    def show_profile_screen(self):
        self.current_screen = "profile"
        self.clear_container()
        page = tk.Frame(self.container, bg=THEME["bg"])
        page.pack(fill="both", expand=True)
        self.build_dashboard_header(page, show_back=True)
        wrap = tk.Frame(page, bg=THEME["panel_alt"], bd=1, relief="solid")
        wrap.pack(fill="both", expand=True, padx=14, pady=(0, 14))

        tk.Label(wrap, text="Edit Profile", bg=THEME["panel_alt"], fg=THEME["text"], font=("Helvetica", 16, "bold")).pack(pady=(20, 10))
        form = tk.Frame(wrap, bg=THEME["panel_alt"])
        form.pack(pady=8)

        tk.Label(form, text="Username", bg=THEME["panel_alt"], fg=THEME["muted"], font=("Helvetica", 11, "bold")).grid(row=0, column=0, sticky="w", pady=(4, 2))
        username_entry = self.styled_entry(form)
        username_entry.grid(row=1, column=0, pady=(0, 8), ipadx=120, ipady=6)
        username_entry.insert(0, self.current_user["username_display"])

        tk.Label(form, text="New Password (optional)", bg=THEME["panel_alt"], fg=THEME["muted"], font=("Helvetica", 11, "bold")).grid(row=2, column=0, sticky="w", pady=(4, 2))
        new_password_entry = self.styled_entry(form, show="*")
        new_password_entry.grid(row=3, column=0, pady=(0, 8), ipadx=120, ipady=6)

        tk.Label(form, text="Confirm New Password", bg=THEME["panel_alt"], fg=THEME["muted"], font=("Helvetica", 11, "bold")).grid(row=4, column=0, sticky="w", pady=(4, 2))
        confirm_password_entry = self.styled_entry(form, show="*")
        confirm_password_entry.grid(row=5, column=0, pady=(0, 8), ipadx=120, ipady=6)

        tk.Label(form, text="New Security Answer (optional)", bg=THEME["panel_alt"], fg=THEME["muted"], font=("Helvetica", 11, "bold")).grid(row=6, column=0, sticky="w", pady=(4, 2))
        security_entry = self.styled_entry(form)
        security_entry.grid(row=7, column=0, pady=(0, 8), ipadx=120, ipady=6)

        def save_profile():
            new_password = new_password_entry.get()
            confirm_password = confirm_password_entry.get()
            if new_password != confirm_password:
                messagebox.showerror("Error", "New password and confirm password do not match.")
                return
            try:
                self.db.update_profile_credentials(
                    self.current_user["id"],
                    username_entry.get(),
                    new_password,
                    security_entry.get(),
                )
            except ValueError as exc:
                msg = str(exc)
                if msg == "Username taken":
                    messagebox.showerror("Username taken", "Username taken")
                else:
                    messagebox.showerror("Error", msg)
                return
            self.current_user = self.db.get_user_by_id(self.current_user["id"])
            messagebox.showinfo("Saved", "Profile updated.")
            self.show_dashboard()

        self.styled_button(wrap, "Save Profile", save_profile, width=20).pack(pady=12)

    def show_data_tools_screen(self):
        self.current_screen = "data_tools"
        self.clear_container()
        page = tk.Frame(self.container, bg=THEME["bg"])
        page.pack(fill="both", expand=True)
        self.build_dashboard_header(page, show_back=True)
        wrap = tk.Frame(page, bg=THEME["panel_alt"], bd=1, relief="solid")
        wrap.pack(fill="both", expand=True, padx=14, pady=(0, 14))
        tk.Label(wrap, text="Backup & Restore", bg=THEME["panel_alt"], fg=THEME["text"], font=("Helvetica", 16, "bold")).pack(pady=(20, 10))
        tk.Label(wrap, text="Backup saves the whole database. Restore replaces current data.", bg=THEME["panel_alt"], fg=THEME["muted"], font=("Helvetica", 11)).pack()
        self.styled_button(wrap, "Backup Database", self.backup_database, width=22).pack(pady=(20, 8))
        self.styled_button(wrap, "Restore Database", self.restore_database, width=22).pack(pady=8)

    def refresh_dashboard_data(self):
        self.refresh_month_total()
        if self.history is not None:
            self.refresh_history()
        if self.pie_canvas is not None and self.legend_frame is not None:
            self.draw_pie_chart()
            if self.pie_selected_category:
                self.update_pie_history(self.pie_selected_category)
        if self.bar_canvas is not None and self.bar_title is not None:
            self.draw_comparison_chart(self.bar_mode)

    def refresh_history(self):
        if not self.current_user or self.history is None:
            return
        for row in self.history.get_children():
            self.history.delete(row)

        parsed = self.parse_history_filters()
        if not parsed["ok"]:
            messagebox.showerror("Invalid Filter", parsed["error"])
            return

        for tx in self.db.get_transactions(self.current_user["id"]):
            tx_dt = datetime.fromisoformat(tx["created_at"])
            if self.history_category_filter and tx["category"] != self.history_category_filter:
                continue
            if self.history_month_only:
                now = datetime.now()
                if tx_dt.year != now.year or tx_dt.month != now.month:
                    continue
            if parsed["from_date"] and tx_dt.date() < parsed["from_date"]:
                continue
            if parsed["to_date"] and tx_dt.date() > parsed["to_date"]:
                continue
            amount = float(tx["amount"])
            if parsed["min_amount"] is not None and amount < parsed["min_amount"]:
                continue
            if parsed["max_amount"] is not None and amount > parsed["max_amount"]:
                continue
            if parsed["remark"] and parsed["remark"] not in (tx["remark"] or "").lower():
                continue
            dt = datetime.fromisoformat(tx["created_at"]).strftime("%Y-%m-%d")
            self.history.insert(
                "",
                "end",
                values=(tx["id"], dt, tx["category"], tx["remark"] or "-", self.format_amount(amount)),
            )

    def parse_history_filters(self):
        if not self.history_filters:
            return {"ok": True, "from_date": None, "to_date": None, "min_amount": None, "max_amount": None, "remark": ""}
        from_txt = self.history_filters["from_date"].get().strip()
        to_txt = self.history_filters["to_date"].get().strip()
        min_txt = self.history_filters["min_amount"].get().strip()
        max_txt = self.history_filters["max_amount"].get().strip()
        remark_txt = self.history_filters["remark"].get().strip().lower()
        try:
            from_date = datetime.strptime(from_txt, "%Y-%m-%d").date() if from_txt else None
            to_date = datetime.strptime(to_txt, "%Y-%m-%d").date() if to_txt else None
        except ValueError:
            return {"ok": False, "error": "Dates must be in YYYY-MM-DD format."}
        try:
            min_amount = float(min_txt) if min_txt else None
            max_amount = float(max_txt) if max_txt else None
        except ValueError:
            return {"ok": False, "error": "Amount filters must be numeric."}
        if from_date and to_date and from_date > to_date:
            return {"ok": False, "error": "From Date cannot be after To Date."}
        if min_amount is not None and max_amount is not None and min_amount > max_amount:
            return {"ok": False, "error": "Min Amount cannot be greater than Max Amount."}
        return {
            "ok": True,
            "from_date": from_date,
            "to_date": to_date,
            "min_amount": min_amount,
            "max_amount": max_amount,
            "remark": remark_txt,
        }

    def reset_history_filters(self):
        for entry in self.history_filters.values():
            entry.delete(0, "end")
        self.refresh_history()

    def on_history_select(self, _event=None):
        selected = self.history.selection()
        if not selected:
            self.history_selected_tx_id = None
            return
        values = self.history.item(selected[0], "values")
        self.history_selected_tx_id = int(values[0])

    def edit_selected_transaction(self):
        if not self.history_selected_tx_id:
            messagebox.showwarning("No Selection", "Select a transaction first.")
            return
        tx = self.db.get_transaction_by_id(self.current_user["id"], self.history_selected_tx_id)
        if not tx:
            messagebox.showerror("Error", "Transaction not found.")
            return
        self.show_add_transaction_screen(edit_tx=tx, return_screen="history")

    def delete_selected_transaction(self):
        if not self.history_selected_tx_id:
            messagebox.showwarning("No Selection", "Select a transaction first.")
            return
        if not messagebox.askyesno("Confirm Delete", "Delete this transaction? This action is permanent."):
            return
        try:
            self.db.delete_transaction(self.current_user["id"], self.history_selected_tx_id)
        except ValueError as exc:
            messagebox.showerror("Error", str(exc))
            return
        self.history_selected_tx_id = None
        self.refresh_dashboard_data()
        messagebox.showinfo("Deleted", "Transaction deleted.")

    def export_history_pdf(self):
        if self.history is None:
            return
        rows = [self.history.item(item_id, "values") for item_id in self.history.get_children()]
        if not rows:
            messagebox.showwarning("No Data", "No rows available to export.")
            return
        default_name = f"kernelfinance_history_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        out_path = filedialog.asksaveasfilename(
            title="Export PDF",
            defaultextension=".pdf",
            initialfile=default_name,
            filetypes=[("PDF Files", "*.pdf")],
        )
        if not out_path:
            return
        lines = []
        for row in rows:
            lines.append(f"ID {row[0]} | {row[1]} | {row[2]} | {row[3]} | {row[4]}")
        self.write_simple_pdf(out_path, self.history_title_label.cget("text"), lines)
        messagebox.showinfo("Exported", f"PDF saved at:\n{out_path}")

    def month_total_for_current_user(self):
        if not self.current_user:
            return 0.0
        now = datetime.now()
        total = 0.0
        for tx in self.db.get_transactions(self.current_user["id"]):
            dt = datetime.fromisoformat(tx["created_at"])
            if dt.year == now.year and dt.month == now.month:
                total += float(tx["amount"])
        return total

    def refresh_month_total(self):
        self.month_total_label.config(text=f"Total Expenditure (This Month): {self.format_amount(self.month_total_for_current_user())}")

    def open_add_transaction_modal(self):
        modal = tk.Toplevel(self.root)
        modal.title("Add Transaction")
        modal.geometry("420x360")
        modal.configure(bg=THEME["panel"])
        modal.resizable(False, False)
        modal.grab_set()

        tk.Label(modal, text="Value", bg=THEME["panel"], fg=THEME["muted"], font=("Helvetica", 11, "bold")).place(x=30, y=24)
        amount_entry = self.styled_entry(modal)
        amount_entry.place(x=30, y=50, width=360, height=34)

        tk.Label(modal, text="Category", bg=THEME["panel"], fg=THEME["muted"], font=("Helvetica", 11, "bold")).place(x=30, y=102)
        category_var = tk.StringVar(value=CATEGORIES[0])
        category_menu = ttk.Combobox(modal, values=CATEGORIES, textvariable=category_var, state="readonly", font=("Helvetica", 11))
        category_menu.place(x=30, y=128, width=360, height=34)

        tk.Label(modal, text="Remark", bg=THEME["panel"], fg=THEME["muted"], font=("Helvetica", 11, "bold")).place(x=30, y=180)
        remark_entry = self.styled_entry(modal)
        remark_entry.place(x=30, y=206, width=360, height=34)

        def register_transaction():
            raw_amount = amount_entry.get().strip()
            try:
                amount = float(raw_amount)
                if amount <= 0:
                    raise ValueError
            except ValueError:
                messagebox.showerror("Error", "Please enter a valid positive transaction value.")
                return

            self.db.add_transaction(
                self.current_user["id"],
                amount,
                category_var.get(),
                remark_entry.get(),
            )
            modal.destroy()
            self.refresh_dashboard_data()

        register_btn = self.styled_button(modal, "Register Transaction", register_transaction)
        register_btn.place(x=98, y=278)

    def monthly_category_totals(self):
        now = datetime.now()
        sums = defaultdict(float)
        for tx in self.db.get_transactions(self.current_user["id"]):
            dt = datetime.fromisoformat(tx["created_at"])
            if dt.year == now.year and dt.month == now.month:
                sums[tx["category"]] += float(tx["amount"])
        return sums

    def draw_pie_chart(self):
        if self.pie_canvas is None or self.legend_frame is None:
            return
        self.pie_canvas.delete("all")
        for child in self.legend_frame.winfo_children():
            child.destroy()

        totals = self.monthly_category_totals()
        grand_total = sum(totals.values())

        if grand_total <= 0:
            self.pie_canvas.create_text(
                210,
                160,
                text="No transactions for this month",
                fill=THEME["muted"],
                font=("Helvetica", 13, "bold"),
            )
            return

        start_angle = 0.0
        cx, cy, r = 210, 160, 115
        non_zero_items = [(cat, val) for cat, val in totals.items() if val > 0]

        # Tk can fail to paint a 360-degree arc on some systems; draw a full oval for single-slice pies.
        if len(non_zero_items) == 1:
            category, value = non_zero_items[0]
            color = CATEGORY_COLORS.get(category, CATEGORY_COLORS["Others"])
            slice_id = self.pie_canvas.create_oval(
                cx - r,
                cy - r,
                cx + r,
                cy + r,
                fill=color,
                outline=THEME["entry_bg"],
                width=1,
                tags=("slice", f"cat::{category}"),
            )
            self.pie_canvas.tag_bind(
                slice_id,
                "<Button-1>",
                lambda _event, cat=category: self.update_pie_history(cat),
            )
            self.pie_canvas.create_text(
                cx - (r + 24),
                cy,
                text="100%",
                fill=THEME["entry_fg"],
                font=("Helvetica", 10, "bold"),
            )

        else:
            for category in CATEGORIES:
                value = totals.get(category, 0.0)
                if value <= 0:
                    continue
                extent = (value / grand_total) * 360.0
                # Keep full-ring floating-point edge cases from becoming an invisible slice.
                extent = min(extent, 359.999)
                color = CATEGORY_COLORS.get(category, CATEGORY_COLORS["Others"])
                slice_id = self.pie_canvas.create_arc(
                    cx - r,
                    cy - r,
                    cx + r,
                    cy + r,
                    start=start_angle,
                    extent=extent,
                    fill=color,
                    outline=THEME["entry_bg"],
                    width=1,
                    tags=("slice", f"cat::{category}"),
                )
                self.pie_canvas.tag_bind(
                    slice_id,
                    "<Button-1>",
                    lambda _event, cat=category: self.update_pie_history(cat),
                )

                mid_angle = math.radians(start_angle + extent / 2)
                lx = cx + math.cos(mid_angle) * (r + 24)
                ly = cy - math.sin(mid_angle) * (r + 24)
                pct = (value / grand_total) * 100
                self.pie_canvas.create_text(
                    lx,
                    ly,
                    text=f"{pct:.0f}%",
                    fill=THEME["entry_fg"],
                    font=("Helvetica", 10, "bold"),
                )
                start_angle += extent

        row = 0
        col = 0
        legend_categories = list(CATEGORIES)
        for category in sorted(totals.keys()):
            if category not in legend_categories:
                legend_categories.append(category)

        for category in legend_categories:
            color = CATEGORY_COLORS.get(category, CATEGORY_COLORS["Others"])
            item = tk.Frame(self.legend_frame, bg=THEME["panel_alt"])
            item.grid(row=row, column=col, padx=8, pady=4, sticky="w")
            swatch = tk.Canvas(item, width=14, height=14, bg=THEME["panel_alt"], highlightthickness=0)
            swatch.create_rectangle(1, 1, 13, 13, fill=color, outline=color)
            swatch.pack(side="left", padx=(0, 5))
            tk.Label(item, text=category, bg=THEME["panel_alt"], fg=THEME["entry_fg"], font=("Helvetica", 10)).pack(side="left")
            col += 1
            if col == 3:
                col = 0
                row += 1

    def update_pie_history(self, category: str):
        if self.pie_history_tree is None:
            return
        self.pie_selected_category = category
        if self.pie_history_hint is not None:
            now = datetime.now().strftime("%B %Y")
            self.pie_history_hint.config(text=f"Category History ({now}): {category}")
        for row_id in self.pie_history_tree.get_children():
            self.pie_history_tree.delete(row_id)

        now = datetime.now()
        found = 0
        for tx in self.db.get_transactions(self.current_user["id"]):
            dt = datetime.fromisoformat(tx["created_at"])
            if dt.year != now.year or dt.month != now.month:
                continue
            if tx["category"] != category:
                continue
            found += 1
            self.pie_history_tree.insert(
                "",
                "end",
                values=(
                    dt.strftime("%Y-%m-%d"),
                    tx["remark"] or "-",
                    self.format_amount(float(tx["amount"])),
                ),
            )
        if found == 0:
            self.pie_history_tree.insert("", "end", values=("-", "No transactions in this category for this month", "-"))

    def aggregate_for_mode(self, mode):
        txs = self.db.get_transactions(self.current_user["id"])
        now = datetime.now()

        if mode == "weekly":
            start_of_week = now - timedelta(days=now.weekday())
            labels = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
            values = [0.0] * 7
            for tx in txs:
                dt = datetime.fromisoformat(tx["created_at"])
                day_delta = (dt.date() - start_of_week.date()).days
                if 0 <= day_delta <= 6:
                    values[day_delta] += float(tx["amount"])
            return labels, values

        if mode == "monthly":
            labels = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
            values = [0.0] * 12
            for tx in txs:
                dt = datetime.fromisoformat(tx["created_at"])
                if dt.year == now.year:
                    values[dt.month - 1] += float(tx["amount"])
            return labels, values

        if mode == "yearly":
            year_map = defaultdict(float)
            for tx in txs:
                dt = datetime.fromisoformat(tx["created_at"])
                year_map[dt.year] += float(tx["amount"])

            if not year_map:
                return [], []

            years = sorted(year_map.keys())
            return [str(y) for y in years], [year_map[y] for y in years]

        if mode.startswith("year-month:"):
            year = int(mode.split(":", 1)[1])
            labels = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
            values = [0.0] * 12
            for tx in txs:
                dt = datetime.fromisoformat(tx["created_at"])
                if dt.year == year:
                    values[dt.month - 1] += float(tx["amount"])
            return labels, values

        return [], []

    def draw_comparison_chart(self, mode=None):
        if self.bar_canvas is None or self.bar_title is None:
            return
        if mode:
            self.bar_mode = mode
            self.bar_year_context = None

        effective_mode = self.bar_mode
        if self.bar_year_context is not None:
            effective_mode = f"year-month:{self.bar_year_context}"

        labels, values = self.aggregate_for_mode(effective_mode)

        if effective_mode == "weekly":
            title = "Weekly Comparison"
        elif effective_mode == "monthly":
            title = "Monthly Comparison"
        elif effective_mode == "yearly":
            title = "Yearly Comparison"
        else:
            title = f"Monthly Comparison ({self.bar_year_context})"
        self.bar_title.config(text=title)

        self.bar_canvas.delete("all")
        self.bar_metadata = []

        if not labels:
            self.bar_canvas.create_text(210, 210, text="No data to compare", fill=THEME["muted"], font=("Helvetica", 13, "bold"))
            return

        w = int(self.bar_canvas.winfo_width())
        h = int(self.bar_canvas.winfo_height())
        if w < 100:
            w = 420
        if h < 100:
            h = 430

        pad_left, pad_right, pad_top, pad_bottom = 50, 20, 20, 50
        plot_w = w - pad_left - pad_right
        plot_h = h - pad_top - pad_bottom

        max_val = max(values) if values else 0.0
        if max_val == 0:
            max_val = 1.0

        n = len(labels)
        gap = 8 if n > 8 else 14
        bar_w = max(12, (plot_w - gap * (n + 1)) / n)

        self.bar_canvas.create_line(pad_left, h - pad_bottom, w - pad_right, h - pad_bottom, fill="#5a6b5a", width=2)
        self.bar_canvas.create_line(pad_left, pad_top, pad_left, h - pad_bottom, fill="#5a6b5a", width=2)

        x = pad_left + gap
        for i, (label, value) in enumerate(zip(labels, values)):
            bar_h = (value / max_val) * (plot_h - 10)
            y0 = h - pad_bottom - bar_h
            y1 = h - pad_bottom
            x0 = x
            x1 = x + bar_w

            color = "#39ff14"
            if effective_mode == "yearly":
                color = "#4aa3ff"
            elif effective_mode.startswith("year-month"):
                color = "#ffd166"

            self.bar_canvas.create_rectangle(x0, y0, x1, y1, fill=color, outline="#0e120e")
            self.bar_canvas.create_text(
                (x0 + x1) / 2,
                y0 - 10,
                text=f"{self.get_currency_symbol()}{value:.0f}",
                fill=THEME["entry_fg"],
                font=("Helvetica", 9),
            )
            self.bar_canvas.create_text((x0 + x1) / 2, y1 + 13, text=label, fill=THEME["entry_fg"], font=("Helvetica", 9))

            self.bar_metadata.append(
                {
                    "index": i,
                    "label": label,
                    "x0": x0,
                    "x1": x1,
                    "y0": y0,
                    "y1": y1,
                    "mode": effective_mode,
                }
            )
            x += bar_w + gap

        if effective_mode == "yearly":
            self.bar_canvas.create_text(
                w / 2,
                h - 20,
                text="Click a year bar to view that year month-wise",
                fill=THEME["muted"],
                font=("Helvetica", 10),
            )

    def on_bar_click(self, event):
        for meta in self.bar_metadata:
            if meta["x0"] <= event.x <= meta["x1"] and meta["y0"] <= event.y <= meta["y1"]:
                if meta["mode"] == "yearly":
                    self.bar_year_context = int(meta["label"])
                    self.draw_comparison_chart()
                return

    def open_history_window(self):
        if self.history_window is not None and self.history_window.winfo_exists():
            self.history_window.focus_force()
            return

        self.history_window = tk.Toplevel(self.root)
        self.history_window.title("Transaction History")
        self.history_window.geometry("900x540")
        self.history_window.configure(bg=THEME["panel_alt"])

        tk.Label(
            self.history_window,
            text="Transaction History",
            bg=THEME["panel_alt"],
            fg=THEME["text"],
            font=("Helvetica", 14, "bold"),
        ).pack(anchor="nw", padx=14, pady=(12, 4))

        table_wrap = tk.Frame(self.history_window, bg=THEME["panel_alt"])
        table_wrap.pack(fill="both", expand=True, padx=14, pady=(8, 14))

        columns = ("date", "category", "remark", "value")
        self.history = ttk.Treeview(table_wrap, columns=columns, show="headings")
        self.history.heading("date", text="Date")
        self.history.heading("category", text="Category")
        self.history.heading("remark", text="Remark")
        self.history.heading("value", text="Value")
        self.history.column("date", width=140)
        self.history.column("category", width=140)
        self.history.column("remark", width=420)
        self.history.column("value", width=140, anchor="e")

        hist_scroll = ttk.Scrollbar(table_wrap, orient="vertical", command=self.history.yview)
        self.history.configure(yscroll=hist_scroll.set)
        self.history.pack(fill="both", expand=True, side="left")
        hist_scroll.pack(fill="y", side="right")

        def on_close():
            self.history = None
            self.history_window.destroy()
            self.history_window = None

        self.history_window.protocol("WM_DELETE_WINDOW", on_close)
        self.refresh_history()

    def open_pie_window(self):
        if self.pie_window is not None and self.pie_window.winfo_exists():
            self.pie_window.focus_force()
            return

        self.pie_window = tk.Toplevel(self.root)
        self.pie_window.title("Monthly Expenditure Pie Chart")
        self.pie_window.geometry("560x560")
        self.pie_window.configure(bg=THEME["panel_alt"])

        tk.Label(
            self.pie_window,
            text="This Month Category Split",
            bg=THEME["panel_alt"],
            fg=THEME["text"],
            font=("Helvetica", 13, "bold"),
        ).pack(pady=(12, 8))

        self.pie_canvas = tk.Canvas(self.pie_window, width=420, height=320, bg=THEME["entry_bg"], highlightthickness=0)
        self.pie_canvas.pack(padx=10, pady=8)
        self.legend_frame = tk.Frame(self.pie_window, bg=THEME["panel_alt"])
        self.legend_frame.pack(fill="x", padx=12, pady=(2, 12))

        def on_close():
            self.pie_canvas = None
            self.legend_frame = None
            self.pie_window.destroy()
            self.pie_window = None

        self.pie_window.protocol("WM_DELETE_WINDOW", on_close)
        self.draw_pie_chart()

    def open_compare_window(self):
        if self.compare_window is not None and self.compare_window.winfo_exists():
            self.compare_window.focus_force()
            return

        self.compare_window = tk.Toplevel(self.root)
        self.compare_window.title("Compare Expenditure")
        self.compare_window.geometry("640x640")
        self.compare_window.configure(bg=THEME["panel_alt"])
        self.bar_mode = "monthly"
        self.bar_year_context = None

        mode_row = tk.Frame(self.compare_window, bg=THEME["panel_alt"])
        mode_row.pack(pady=(14, 8))
        self.styled_button(mode_row, "Weekly", lambda: self.draw_comparison_chart("weekly"), width=10).pack(side="left", padx=4)
        self.styled_button(mode_row, "Monthly", lambda: self.draw_comparison_chart("monthly"), width=10).pack(side="left", padx=4)
        self.styled_button(mode_row, "Yearly", lambda: self.draw_comparison_chart("yearly"), width=10).pack(side="left", padx=4)

        self.bar_title = tk.Label(self.compare_window, text="Monthly Comparison", bg=THEME["panel_alt"], fg=THEME["text"], font=("Helvetica", 12, "bold"))
        self.bar_title.pack(pady=(2, 8))

        self.bar_canvas = tk.Canvas(self.compare_window, width=560, height=500, bg=THEME["entry_bg"], highlightthickness=0)
        self.bar_canvas.pack(padx=14, pady=(0, 14), fill="both", expand=True)
        self.bar_canvas.bind("<Button-1>", self.on_bar_click)

        def on_close():
            self.bar_canvas = None
            self.bar_title = None
            self.compare_window.destroy()
            self.compare_window = None

        self.compare_window.protocol("WM_DELETE_WINDOW", on_close)
        self.draw_comparison_chart("monthly")

    def backup_database(self):
        backup_path = filedialog.asksaveasfilename(
            title="Backup Database",
            defaultextension=".db",
            initialfile=f"kernelfinance_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db",
            filetypes=[("Database Files", "*.db")],
        )
        if not backup_path:
            return
        try:
            data = self.db.download_backup()
            with open(backup_path, "wb") as f:
                f.write(data)
            messagebox.showinfo("Backup Complete", f"Backup saved at:\n{backup_path}")
        except Exception as exc:
            messagebox.showerror("Backup Failed", str(exc))

    def restore_database(self):
        in_path = filedialog.askopenfilename(
            title="Restore Database",
            filetypes=[("Database Files", "*.db"), ("All Files", "*.*")],
        )
        if not in_path:
            return
        if not messagebox.askyesno("Confirm Restore", "This will replace current database. Continue?"):
            return
        user_id = self.current_user["id"] if self.current_user else None
        try:
            self.db.upload_restore(in_path)
        except Exception as exc:
            messagebox.showerror("Restore Failed", str(exc))
            return
        if user_id:
            self.current_user = self.db.get_user_by_id(user_id)
        if self.current_user:
            self.apply_theme(self.get_current_theme(), rerender=False)
            self.show_dashboard()
            messagebox.showinfo("Restore Complete", "Database restored successfully.")
        else:
            self.show_login()
            messagebox.showwarning("Restore Complete", "Database restored. Please login again.")

    def apply_theme(self, theme_name: str, rerender=True):
        target = theme_name if theme_name in THEMES else "dark"
        THEME.clear()
        THEME.update(THEMES[target])
        self.root.configure(bg=THEME["bg"])
        self.configure_ttk_styles()
        if rerender and self.current_user:
            current = self.current_screen
            if current == "dashboard":
                self.show_dashboard()
            elif current == "add":
                self.show_add_transaction_screen()
            elif current == "history":
                self.show_history_screen(self.history_category_filter, self.history_month_only)
            elif current == "pie":
                self.show_pie_screen()
            elif current == "compare":
                self.show_compare_screen()
            elif current == "profile":
                self.show_profile_screen()
            elif current == "data_tools":
                self.show_data_tools_screen()
            else:
                self.show_dashboard()
        elif rerender and not self.current_user:
            self.show_login()

    def logout(self):
        self.current_user = None
        self.apply_theme("dark", rerender=False)
        self.show_login()

    def get_current_theme(self):
        if not self.current_user or "theme" not in self.current_user.keys():
            return "dark"
        theme = self.current_user["theme"]
        return theme if theme in THEMES else "dark"

    def get_greeting_name(self):
        if not self.current_user:
            return ""
        return self.current_user["username_display"]

    def get_current_currency(self):
        if not self.current_user:
            return DEFAULT_CURRENCY
        code = self.current_user["currency"] if "currency" in self.current_user.keys() else DEFAULT_CURRENCY
        if code not in CURRENCY_SYMBOLS:
            return DEFAULT_CURRENCY
        return code

    def get_currency_symbol(self):
        return CURRENCY_SYMBOLS.get(self.get_current_currency(), CURRENCY_SYMBOLS[DEFAULT_CURRENCY])

    def format_amount(self, value: float):
        return f"{self.get_currency_symbol()} {value:.2f}"

    def history_title_text(self, category_filter, month_only):
        now = datetime.now()
        month_label = now.strftime("%B %Y")
        if category_filter and month_only:
            return f"Transaction History - {category_filter} ({month_label})"
        if category_filter:
            return f"Transaction History - {category_filter}"
        return "Transaction History"

    def write_simple_pdf(self, file_path: str, title: str, lines):
        def esc(text):
            return text.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")

        max_lines = 42
        pages = [lines[i:i + max_lines] for i in range(0, len(lines), max_lines)] or [[]]
        objects = []
        page_ids = []
        content_ids = []
        next_id = 1
        catalog_id = next_id
        next_id += 1
        pages_id = next_id
        next_id += 1
        font_id = next_id
        next_id += 1

        for _ in pages:
            page_ids.append(next_id)
            next_id += 1
            content_ids.append(next_id)
            next_id += 1

        objects.append((catalog_id, f"<< /Type /Catalog /Pages {pages_id} 0 R >>"))
        kids = " ".join([f"{pid} 0 R" for pid in page_ids])
        objects.append((pages_id, f"<< /Type /Pages /Kids [{kids}] /Count {len(page_ids)} >>"))
        objects.append((font_id, "<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>"))

        for idx, page_lines in enumerate(pages):
            page_id = page_ids[idx]
            content_id = content_ids[idx]
            page_obj = (
                f"<< /Type /Page /Parent {pages_id} 0 R /MediaBox [0 0 595 842] "
                f"/Resources << /Font << /F1 {font_id} 0 R >> >> "
                f"/Contents {content_id} 0 R >>"
            )
            objects.append((page_id, page_obj))

            content_cmds = []
            y = 800
            page_title = title if idx == 0 else f"{title} (Page {idx + 1})"
            content_cmds.append(f"BT /F1 14 Tf 50 {y} Td ({esc(page_title)}) Tj ET")
            y -= 26
            for line in page_lines:
                content_cmds.append(f"BT /F1 11 Tf 50 {y} Td ({esc(line)}) Tj ET")
                y -= 18
            stream = "\n".join(content_cmds).encode("latin-1", errors="replace")
            content_obj = f"<< /Length {len(stream)} >>\nstream\n{stream.decode('latin-1')}\nendstream"
            objects.append((content_id, content_obj))

        objects.sort(key=lambda item: item[0])
        pdf = bytearray()
        pdf.extend(b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n")
        offsets = [0]

        for obj_id, obj_body in objects:
            offsets.append(len(pdf))
            pdf.extend(f"{obj_id} 0 obj\n{obj_body}\nendobj\n".encode("latin-1"))

        xref_pos = len(pdf)
        pdf.extend(f"xref\n0 {len(objects) + 1}\n".encode("latin-1"))
        pdf.extend(b"0000000000 65535 f \n")
        for off in offsets[1:]:
            pdf.extend(f"{off:010d} 00000 n \n".encode("latin-1"))
        pdf.extend(
            (
                f"trailer\n<< /Size {len(objects) + 1} /Root {catalog_id} 0 R >>\n"
                f"startxref\n{xref_pos}\n%%EOF\n"
            ).encode("latin-1")
        )
        with open(file_path, "wb") as f:
            f.write(pdf)


def main():
    import time
    client = ApiClient()
    for attempt in range(10):
        try:
            if client.health_check():
                break
        except Exception:
            pass
        time.sleep(0.5)
    else:
        root = tk.Tk()
        root.withdraw()
        messagebox.showerror("Connection Error", "Cannot connect to the KernelFinance server.\nPlease start the server first (run start.sh).")
        sys.exit(1)

    root = tk.Tk()
    app = KernelFinanceApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
