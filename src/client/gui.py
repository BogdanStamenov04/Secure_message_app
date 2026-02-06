import customtkinter as ctk
import os
from PIL import Image
from src.client.network import NetworkClient

# --- 🎨 НАСТРОЙКИ ---
COLOR_BG = "#1a1a1a"            # Тъмен фон
COLOR_PANEL = "#2b2b2b"         # Фон на панелите
COLOR_ACCENT = "#D32F2F"        # ЧЕРВЕНО
COLOR_ACCENT_HOVER = "#B71C1C"  
COLOR_TEXT = "#ffffff"
COLOR_GREEN = "#2ecc71"
COLOR_RED = "#e74c3c"

MY_FONT = "Verdana" 

ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("dark-blue")

class MessengerApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Secure Messenger")
        self.geometry("950x700")
        self.configure(fg_color=COLOR_BG)

        self.client = NetworkClient(self.on_message, self.update_contact_list)
        self.current_chat_target = None
        self.chat_history = {}

        # Зареждане на ресурси (Лого)
        self.load_resources()

        # --- КОНТЕЙНЕРИ ЗА ЕКРАНИТЕ ---
        # 1. Екран за Вход (Първоначално видим)
        self.login_screen = ctk.CTkFrame(self, fg_color=COLOR_BG)
        self.login_screen.pack(fill="both", expand=True)

        # 2. Екран на Приложението (Първоначално скрит)
        self.main_app_screen = ctk.CTkFrame(self, fg_color=COLOR_BG)
        # Не го pack-ваме, докато не влезем успешно!

        # --- ИЗГРАЖДАНЕ НА ДВАТА ЕКРАНА ---
        self.build_login_screen()
        self.build_main_app_screen()

    def load_resources(self):
        try:
            base = os.path.dirname(os.path.abspath(__file__))
            root = os.path.dirname(os.path.dirname(base))
            path = os.path.join(root, "assets", "logo.png")
            pil_img = Image.open(path)
            self.logo_img = ctk.CTkImage(light_image=pil_img, dark_image=pil_img, size=(70, 70))
            self.list_icon = ctk.CTkImage(light_image=pil_img, dark_image=pil_img, size=(25, 25))
            # По-голямо лого за логин екрана
            self.login_logo = ctk.CTkImage(light_image=pil_img, dark_image=pil_img, size=(100, 100))
        except:
            self.logo_img = None
            self.list_icon = None
            self.login_logo = None

    # ==========================================
    # ЕКРАН 1: ЛОГИН (ИЗОЛИРАН)
    # ==========================================
    def build_login_screen(self):
        # Рамка в центъра на екрана
        self.login_box = ctk.CTkFrame(self.login_screen, fg_color=COLOR_PANEL, corner_radius=15)
        self.login_box.place(relx=0.5, rely=0.5, anchor="center")

        # Лого в логин екрана (за красота)
        if self.login_logo:
            ctk.CTkLabel(self.login_box, text="", image=self.login_logo).pack(pady=(30, 10))

        ctk.CTkLabel(self.login_box, text="Вход в системата", font=(MY_FONT, 20, "bold")).pack(pady=10, padx=50)
        
        self.user_entry = ctk.CTkEntry(self.login_box, placeholder_text="Потребител", font=(MY_FONT, 14), width=220)
        self.user_entry.pack(pady=10)
        
        self.pass_entry = ctk.CTkEntry(self.login_box, placeholder_text="Парола", show="*", font=(MY_FONT, 14), width=220)
        self.pass_entry.pack(pady=10)
        
        ctk.CTkButton(self.login_box, text="ВЛЕЗ", command=self.login, width=220,
                      fg_color=COLOR_ACCENT, hover_color=COLOR_ACCENT_HOVER, 
                      font=(MY_FONT, 14, "bold")).pack(pady=10)
        
        ctk.CTkButton(self.login_box, text="Регистрация", command=self.register, width=220,
                      fg_color="transparent", border_width=1, font=(MY_FONT, 12)).pack(pady=(0, 30))
        
        self.status_label = ctk.CTkLabel(self.login_box, text="", text_color="red", font=(MY_FONT, 12))
        self.status_label.pack(pady=5)

    # ==========================================
    # ЕКРАН 2: ОСНОВНО ПРИЛОЖЕНИЕ ( СКРИТО )
    # ==========================================
    def build_main_app_screen(self):
        # Разделяме на ЛЯВО и ДЯСНО вътре в главния екран
        self.left_panel = ctk.CTkFrame(self.main_app_screen, width=280, corner_radius=0, fg_color=COLOR_PANEL)
        self.left_panel.pack(side="left", fill="y")

        self.right_panel = ctk.CTkFrame(self.main_app_screen, corner_radius=0, fg_color="transparent")
        self.right_panel.pack(side="right", fill="both", expand=True)

        # --- ЛЯВ ПАНЕЛ ---
        # Лого рамка
        self.logo_frame = ctk.CTkFrame(self.left_panel, height=80, fg_color="transparent")
        self.logo_frame.pack(side="top", fill="x", pady=(10, 20))
        
        if self.logo_img:
            ctk.CTkLabel(self.logo_frame, text="", image=self.logo_img).pack(anchor="center")
        else:
            ctk.CTkLabel(self.logo_frame, text="APP", font=(MY_FONT, 20, "bold")).pack()

        # Списък контакти
        ctk.CTkLabel(self.left_panel, text="КОНТАКТИ", text_color="gray", font=(MY_FONT, 12, "bold")).pack(pady=5)
        self.contacts_list = ctk.CTkScrollableFrame(self.left_panel, fg_color="transparent")
        self.contacts_list.pack(fill="both", expand=True, padx=5, pady=5)

        # Контроли долу
        ctrl_frame = ctk.CTkFrame(self.left_panel, fg_color="#222")
        ctrl_frame.pack(fill="x", padx=10, pady=10)

        self.add_entry = ctk.CTkEntry(ctrl_frame, placeholder_text="Име...", border_width=0, font=(MY_FONT, 12))
        self.add_entry.pack(fill="x", padx=5, pady=5)
        
        ctk.CTkButton(ctrl_frame, text="+ Покани", command=self.send_invite, 
                      fg_color=COLOR_ACCENT, hover_color=COLOR_ACCENT_HOVER, 
                      font=(MY_FONT, 12, "bold"), height=25).pack(fill="x", padx=5, pady=2)
        
        ctk.CTkFrame(ctrl_frame, height=2, fg_color="gray").pack(fill="x", pady=5)
        
        ctk.CTkButton(ctrl_frame, text="+ Група", command=self.create_group, 
                      fg_color="#076969", font=(MY_FONT, 12), height=25).pack(fill="x", padx=5, pady=2)
        ctk.CTkButton(ctrl_frame, text="-> Влез", command=self.join_group, 
                      fg_color="transparent", border_width=1, font=(MY_FONT, 12), height=25).pack(fill="x", padx=5, pady=2)

        # --- ДЕСЕН ПАНЕЛ (ЧАТ) ---
        # Хедър
        self.chat_header = ctk.CTkLabel(self.right_panel, text="Избери чат...", 
                                        font=(MY_FONT, 24, "bold"), text_color="gray")
        self.chat_header.pack(pady=20)
        
        # Чат кутия
        self.chat_box = ctk.CTkTextbox(self.right_panel, state="disabled", font=(MY_FONT, 14), fg_color="#222")
        self.chat_box.pack(fill="both", expand=True, padx=20, pady=10)
        
        # Вход за съобщение
        input_fr = ctk.CTkFrame(self.right_panel, height=50, fg_color="transparent")
        input_fr.pack(fill="x", padx=20, pady=20)
        
        self.msg_entry = ctk.CTkEntry(input_fr, placeholder_text="Съобщение...", font=(MY_FONT, 14))
        self.msg_entry.pack(side="left", fill="x", expand=True)
        self.msg_entry.bind("<Return>", lambda e: self.send_msg())
        
        ctk.CTkButton(input_fr, text="ПРАТИ", width=100, command=self.send_msg, 
                      fg_color=COLOR_ACCENT, hover_color=COLOR_ACCENT_HOVER,
                      font=(MY_FONT, 12, "bold")).pack(side="right", padx=5)

    # ==========================================
    # ЛОГИКА И ПРЕВКЛЮЧВАНЕ
    # ==========================================
    def login(self):
        u, p = self.user_entry.get(), self.pass_entry.get()
        success, msg = self.client.connect(u, p)
        
        if success:
            # ТУК Е МАГИЯТА: Скриваме Логин екрана, Показваме Апп екрана
            self.login_screen.pack_forget()     # Скрий логина
            self.main_app_screen.pack(fill="both", expand=True) # Покажи приложението
            self.title(f"Secure Messenger - {u}")
        else: 
            self.status_label.configure(text=msg)

    def register(self):
        u, p = self.user_entry.get(), self.pass_entry.get()
        success, msg = self.client.connect(u, p, is_register=True)
        self.status_label.configure(text=msg, text_color=COLOR_GREEN if success else COLOR_RED)

    # --- ОСТАНАЛИТЕ ФУНКЦИИ (Без промяна) ---
    def send_invite(self):
        t=self.add_entry.get(); self.client.send_friend_request(t) if t else None; self.add_entry.delete(0,"end")
    def create_group(self):
        t=self.add_entry.get(); self.client.create_group(t) if t else None; self.add_entry.delete(0,"end")
    def join_group(self):
        t=self.add_entry.get(); self.client.join_group(t) if t else None; self.add_entry.delete(0,"end")

    def update_contact_list(self, friends, groups, requests):
        for w in self.contacts_list.winfo_children(): w.destroy()
        
        if requests:
            ctk.CTkLabel(self.contacts_list, text="🔔 ПОКАНИ", text_color="#f1c40f", font=(MY_FONT, 11, "bold")).pack(pady=5)
            for req in requests:
                fr = ctk.CTkFrame(self.contacts_list, fg_color="#333")
                fr.pack(fill="x", pady=2, padx=2)
                ctk.CTkLabel(fr, text=req, width=100, anchor="w", font=(MY_FONT, 12)).pack(side="left", padx=5)
                ctk.CTkButton(fr, text="✘", width=30, fg_color=COLOR_RED, font=(MY_FONT, 10, "bold"), command=lambda s=req: self.client.handle_request(s, "decline")).pack(side="right", padx=2)
                ctk.CTkButton(fr, text="✔", width=30, fg_color=COLOR_GREEN, font=(MY_FONT, 10, "bold"), command=lambda s=req: self.client.handle_request(s, "accept")).pack(side="right", padx=2)

        if groups:
            ctk.CTkLabel(self.contacts_list, text="--- Групи ---", text_color="gray", font=(MY_FONT, 10)).pack(pady=5)
            for g in groups:
                ctk.CTkButton(self.contacts_list, text=f" {g}", image=self.list_icon, compound="left", fg_color="#444", hover_color="#555", anchor="w", font=(MY_FONT, 12), command=lambda x=g: self.select_chat(x)).pack(fill="x", pady=2)
        
        if friends:
            ctk.CTkLabel(self.contacts_list, text="--- Приятели ---", text_color="gray", font=(MY_FONT, 10)).pack(pady=5)
            for f in friends:
                ctk.CTkButton(self.contacts_list, text=f"  {f}", image=self.list_icon, compound="left", fg_color="transparent", border_width=1, border_color="#444", anchor="w", font=(MY_FONT, 12), command=lambda x=f: self.select_chat(x)).pack(fill="x", pady=2)

    def select_chat(self, target):
        self.current_chat_target = target
        self.chat_header.configure(text=target, text_color=COLOR_ACCENT) 
        self.chat_box.configure(state="normal"); self.chat_box.delete("1.0","end"); 
        self.chat_box.insert("end", self.chat_history.get(target,"")); self.chat_box.configure(state="disabled")

    def send_msg(self):
        t=self.msg_entry.get()
        if t and self.current_chat_target:
            self.client.send_message(self.current_chat_target, t)
            self.append_msg(self.current_chat_target, f"Аз: {t}\n")
            self.msg_entry.delete(0,"end")

    def on_message(self, d):
        s, to, t = d.get("sender"), d.get("to"), d.get("text")
        c = to if to.startswith("#") else s
        self.append_msg(c, f"[{s}]: {t}\n" if to.startswith("#") else f"{s}: {t}\n")

    def append_msg(self, c, t):
        if c not in self.chat_history: self.chat_history[c] = ""
        self.chat_history[c] += t
        if self.current_chat_target == c:
            self.chat_box.configure(state="normal"); self.chat_box.insert("end", t); self.chat_box.configure(state="disabled"); self.chat_box.see("end")

if __name__ == "__main__":
    app = MessengerApp()
    app.mainloop()