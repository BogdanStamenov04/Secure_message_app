"""
Main GUI module for the Secure Messenger client using CustomTkinter.
"""

import os
from typing import List, Dict, Any, Optional, Tuple
from PIL import Image
import customtkinter as ctk
from src.client.network import NetworkClient

# --- COLORS ---
COLOR_BG: str = "#1a1a1a"
COLOR_PANEL: str = "#2b2b2b"
COLOR_ACCENT: str = "#D32F2F"
COLOR_ACCENT_HOVER: str = "#B71C1C"
COLOR_TEXT: str = "#ffffff"
COLOR_GREEN: str = "#2ecc71"
COLOR_RED: str = "#e74c3c"
MY_FONT: str = "Verdana"

ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("dark-blue")

# pylint: disable=too-many-instance-attributes


class MessengerApp(ctk.CTk):
    """
    Main GUI class using CustomTkinter.
    Handles UI construction, event binding, and updates.
    """

    def __init__(self) -> None:
        super().__init__()
        self.title("Secure Messenger - vFinal")
        self.geometry("1100x700")
        self.configure(fg_color=COLOR_BG)

        self.client: NetworkClient = NetworkClient(
            self.on_message, self.update_data, self.on_history_loaded
        )
        self.current_chat_target: Optional[str] = None
        self.chat_history: Dict[str, str] = {}
        self.all_public_rooms: List[Tuple[str, str]] = []

        self.load_resources()

        # Screens
        self.login_screen: ctk.CTkFrame = ctk.CTkFrame(self, fg_color=COLOR_BG)
        self.login_screen.pack(fill="both", expand=True)

        self.main_app_screen: ctk.CTkFrame = ctk.CTkFrame(self, fg_color=COLOR_BG)

        self.build_login_screen()
        self.build_main_app_screen()

    def load_resources(self) -> None:
        """Loads images and assets from the assets directory."""
        try:
            base = os.path.dirname(os.path.abspath(__file__))
            root = os.path.dirname(os.path.dirname(base))
            path = os.path.join(root, "assets", "logo.png")
            pil_img = Image.open(path)
            self.logo_img = ctk.CTkImage(light_image=pil_img, dark_image=pil_img, size=(70, 70))
            self.list_icon = ctk.CTkImage(light_image=pil_img, dark_image=pil_img, size=(20, 20))
            self.login_logo = ctk.CTkImage(light_image=pil_img, dark_image=pil_img, size=(100, 100))
        except Exception:  # pylint: disable=broad-exception-caught
            self.logo_img = None
            self.list_icon = None
            self.login_logo = None

    def build_login_screen(self) -> None:
        """Constructs the Login/Register interface."""
        self.login_box = ctk.CTkFrame(self.login_screen, fg_color=COLOR_PANEL, corner_radius=20)
        self.login_box.place(relx=0.5, rely=0.5, anchor="center")

        inner_frame = ctk.CTkFrame(self.login_box, fg_color="transparent")
        inner_frame.pack(padx=50, pady=50)

        if self.login_logo:
            ctk.CTkLabel(inner_frame, text="", image=self.login_logo).pack(pady=(10, 20))

        ctk.CTkLabel(inner_frame, text="System Login", font=(MY_FONT, 24, "bold")).pack(pady=15)

        self.user_entry = ctk.CTkEntry(
            inner_frame, placeholder_text="Username", font=(MY_FONT, 14), width=300, height=40
        )
        self.user_entry.pack(pady=10)

        self.pass_entry = ctk.CTkEntry(
            inner_frame, placeholder_text="Password", show="*",
            font=(MY_FONT, 14), width=300, height=40
        )
        self.pass_entry.pack(pady=10)

        ctk.CTkButton(
            inner_frame, text="LOGIN", command=self.login,
            fg_color=COLOR_ACCENT, hover_color=COLOR_ACCENT_HOVER,
            width=300, height=40, font=(MY_FONT, 14, "bold")
        ).pack(pady=(20, 10))

        ctk.CTkButton(
            inner_frame, text="No account? Register", command=self.register,
            fg_color="transparent", hover_color="#333", border_width=0, width=300
        ).pack(pady=(0, 10))

        self.status_label = ctk.CTkLabel(inner_frame, text="", text_color="red", font=(MY_FONT, 12))
        self.status_label.pack(pady=5)

    def build_main_app_screen(self) -> None:
        """Constructs the main dashboard interface."""
        self.left_panel = ctk.CTkFrame(
            self.main_app_screen, width=320, corner_radius=0, fg_color=COLOR_PANEL
        )
        self.left_panel.pack(side="left", fill="y")
        self.right_panel = ctk.CTkFrame(
            self.main_app_screen, corner_radius=0, fg_color="transparent"
        )
        self.right_panel.pack(side="right", fill="both", expand=True)

        self.logo_frame = ctk.CTkFrame(self.left_panel, height=80, fg_color="transparent")
        self.logo_frame.pack(side="top", fill="x", pady=10)
        if self.logo_img:
            ctk.CTkLabel(self.logo_frame, text="", image=self.logo_img).pack(anchor="center")

        self.tabs = ctk.CTkTabview(self.left_panel, width=300, fg_color="transparent")
        self.tabs.pack(fill="both", expand=True, padx=5, pady=5)
        self.tab_chats = self.tabs.add("Chats")
        self.tab_public = self.tabs.add("Public")
        self.tab_online = self.tabs.add("Online")

        # 1. MY CHATS
        self.my_chats_scroll = ctk.CTkScrollableFrame(self.tab_chats, fg_color="transparent")
        self.my_chats_scroll.pack(fill="both", expand=True)
        c = ctk.CTkFrame(self.tab_chats, fg_color="#222")
        c.pack(fill="x", pady=5)
        self.add_entry = ctk.CTkEntry(c, placeholder_text="Name...")
        self.add_entry.pack(fill="x", padx=2, pady=2)
        ctk.CTkButton(
            c, text="+ User", command=self.send_invite, fg_color=COLOR_ACCENT, height=25
        ).pack(side="left", fill="x", expand=True)
        ctk.CTkButton(
            c, text="+ Group", command=self.create_group, fg_color="#8e44ad", height=25
        ).pack(side="right", fill="x", expand=True)
        ctk.CTkButton(
            c, text="-> Join", command=self.join_group,
            fg_color="transparent", border_width=1, height=25
        ).pack(fill="x", pady=2)

        # 2. PUBLIC ROOMS
        ctk.CTkButton(
            self.tab_public, text="🔄 Refresh Rooms",
            command=lambda: self.client.refresh_data(),
            height=25, fg_color="#e67e22"
        ).pack(fill="x", pady=5)

        self.tag_search = ctk.CTkEntry(self.tab_public, placeholder_text="🔍 Filter by tag...")
        self.tag_search.pack(fill="x", padx=2, pady=5)
        # Using lambda _e to denote unused event argument
        self.tag_search.bind("<KeyRelease>", lambda _e: self.filter_public_rooms())

        self.public_list_scroll = ctk.CTkScrollableFrame(self.tab_public, fg_color="transparent")
        self.public_list_scroll.pack(fill="both", expand=True)

        cp = ctk.CTkFrame(self.tab_public, fg_color="#222")
        cp.pack(fill="x", pady=5)
        self.pub_name_ent = ctk.CTkEntry(cp, placeholder_text="Room Name")
        self.pub_name_ent.pack(fill="x", pady=1)
        self.pub_tags_ent = ctk.CTkEntry(cp, placeholder_text="Tags")
        self.pub_tags_ent.pack(fill="x", pady=1)
        ctk.CTkButton(
            cp, text="Create", command=self.create_public_room, fg_color="#e67e22"
        ).pack(fill="x", pady=2)

        # 3. ONLINE
        ctk.CTkButton(
            self.tab_online, text="🔄 Refresh",
            command=lambda: self.client.refresh_data(), height=25
        ).pack(fill="x", pady=5)
        self.online_scroll = ctk.CTkScrollableFrame(self.tab_online, fg_color="transparent")
        self.online_scroll.pack(fill="both", expand=True)

        # CHAT AREA
        self.chat_header = ctk.CTkLabel(
            self.right_panel, text="...", font=(MY_FONT, 24, "bold"), text_color="gray"
        )
        self.chat_header.pack(pady=20)
        self.chat_box = ctk.CTkTextbox(
            self.right_panel, state="disabled", font=(MY_FONT, 14), fg_color="#222"
        )
        self.chat_box.pack(fill="both", expand=True, padx=20, pady=10)
        inp = ctk.CTkFrame(self.right_panel, height=50, fg_color="transparent")
        inp.pack(fill="x", padx=20, pady=20)
        self.msg_entry = ctk.CTkEntry(inp, placeholder_text="Type a message...")
        self.msg_entry.pack(side="left", fill="x", expand=True)
        self.msg_entry.bind("<Return>", lambda _e: self.send_msg())
        ctk.CTkButton(
            inp, text="SEND", width=100, command=self.send_msg, fg_color=COLOR_ACCENT
        ).pack(side="right", padx=5)

    def login(self) -> None:
        """Handles login action."""
        u = self.user_entry.get().strip()
        p = self.pass_entry.get()
        s, m = self.client.connect(u, p)
        self.handle_auth(s, m, u)

    def register(self) -> None:
        """Handles registration action."""
        u = self.user_entry.get().strip()
        p = self.pass_entry.get().strip()  # Чистим и паролата за проверка

        # ВАЛИДАЦИЯ НА КЛИЕНТА
        if not u or not p:
            self.status_label.configure(text="Fields cannot be empty!", text_color=COLOR_RED)
            return

        s, m = self.client.connect(u, p, True)
        self.status_label.configure(text=m, text_color=COLOR_GREEN if s else COLOR_RED)

    def handle_auth(self, s: bool, m: str, u: str) -> None:
        """Processes authentication result."""
        if s:
            self.login_screen.pack_forget()
            self.main_app_screen.pack(fill="both", expand=True)
            self.title(f"User: {u}")
        else:
            self.status_label.configure(text=m)

    def send_invite(self) -> None:
        """Sends a friend request."""
        t = self.add_entry.get().strip()
        if t:
            self.client.send_friend_request(t)
            self.add_entry.delete(0, "end")

    def create_group(self) -> None:
        """Creates a private group."""
        t = self.add_entry.get().strip()
        if t:
            self.client.create_group(t)
            self.add_entry.delete(0, "end")

    def join_group(self) -> None:
        """Joins a private group."""
        t = self.add_entry.get().strip()
        if t:
            self.client.join_group(t)
            self.add_entry.delete(0, "end")

    def create_public_room(self) -> None:
        """Creates a public room."""
        n = self.pub_name_ent.get().strip()
        t = self.pub_tags_ent.get().strip()
        if n:
            self.client.create_public_room(n, t)
            self.pub_name_ent.delete(0, "end")
            self.pub_tags_ent.delete(0, "end")

    def select_chat(self, target: str) -> None:
        """Selects a chat, displays cached history, and requests full history."""
        self.current_chat_target = target
        self.chat_header.configure(text=target, text_color=COLOR_ACCENT)
        self.chat_box.configure(state="normal")
        self.chat_box.delete("1.0", "end")
        self.chat_box.insert("end", self.chat_history.get(target, "Loading history...\n"))
        self.chat_box.configure(state="disabled")
        self.client.get_chat_history(target)

    def on_history_loaded(self, target: str, messages: List[Dict[str, Any]]) -> None:
        """Callback when history is received from server."""
        history_text = ""
        for m in messages:
            s, t = m.get("sender"), m.get("text")
            history_text += f"[{s}]: {t}\n"

        self.chat_history[target] = history_text
        if self.current_chat_target == target:
            self.chat_box.configure(state="normal")
            self.chat_box.delete("1.0", "end")
            self.chat_box.insert("end", history_text)
            self.chat_box.see("end")
            self.chat_box.configure(state="disabled")

    def send_msg(self) -> None:
        """Sends a message to the current target."""
        t = self.msg_entry.get()
        if t and self.current_chat_target:
            self.client.send_message(self.current_chat_target, t)
            # Optimistic UI update
            self.append_msg(self.current_chat_target, f"Me: {t}\n")
            self.msg_entry.delete(0, "end")

    def on_message(self, d: Dict[str, Any]) -> None:
        """Callback when a real-time message is received."""
        s = str(d.get("sender", "Unknown"))
        to = str(d.get("to", ""))
        t = str(d.get("text", ""))
        context = to if to and (to.startswith("#") or to.startswith("&")) else s
        if s == self.client.username:
            context = to
        self.append_msg(context, f"[{s}]: {t}\n")

    def append_msg(self, c: str, t: str) -> None:
        """Appends a message to the chat view and history cache."""
        if c not in self.chat_history:
            self.chat_history[c] = ""
        self.chat_history[c] += t
        if self.current_chat_target == c:
            self.chat_box.configure(state="normal")
            self.chat_box.insert("end", t)
            self.chat_box.configure(state="disabled")
            self.chat_box.see("end")

    # pylint: disable=too-many-arguments, too-many-positional-arguments
    def update_data(self, fr: List[str], gr: List[str], req: List[str],
                    act: List[str], pub: List[Tuple[str, str]]) -> None:
        """Updates the UI lists based on server data."""
        for w in self.my_chats_scroll.winfo_children():
            w.destroy()
        if req:
            ctk.CTkLabel(self.my_chats_scroll, text="🔔 INVITES", text_color="#f1c40f").pack()
            for r in req:
                f = ctk.CTkFrame(self.my_chats_scroll, fg_color="#333")
                f.pack(fill="x", pady=2)
                ctk.CTkLabel(f, text=r).pack(side="left", padx=5)
                ctk.CTkButton(
                    f, text="✘", width=30, fg_color=COLOR_RED,
                    command=lambda s=r: self.client.handle_request(s, "decline")
                ).pack(side="right")
                ctk.CTkButton(
                    f, text="✔", width=30, fg_color=COLOR_GREEN,
                    command=lambda s=r: self.client.handle_request(s, "accept")
                ).pack(side="right")
        if gr:
            ctk.CTkLabel(self.my_chats_scroll, text="--- Groups ---").pack(pady=5)
            for g in gr:
                ctk.CTkButton(
                    self.my_chats_scroll, text=f" {g}", fg_color="#444",
                    anchor="w", command=lambda x=g: self.select_chat(x)
                ).pack(fill="x", pady=2)
        if fr:
            ctk.CTkLabel(self.my_chats_scroll, text="--- Friends ---").pack(pady=5)
            for f in fr:
                ctk.CTkButton(
                    self.my_chats_scroll, text=f"  {f}", fg_color="transparent",
                    border_width=1, anchor="w", command=lambda x=f: self.select_chat(x)
                ).pack(fill="x", pady=2)

        for w in self.online_scroll.winfo_children():
            w.destroy()
        for u in act:
            c = COLOR_GREEN if u != self.client.username else "gray"
            ctk.CTkLabel(
                self.online_scroll, text=f"● {u}", text_color=c, anchor="w"
            ).pack(fill="x", padx=10)

        self.all_public_rooms = pub
        self.filter_public_rooms()

    def filter_public_rooms(self) -> None:
        """Filters the public rooms list based on the search tag."""
        q = self.tag_search.get().lower()
        for w in self.public_list_scroll.winfo_children():
            w.destroy()
        for n, t in self.all_public_rooms:
            if not q or (q in t.lower()):
                ctk.CTkButton(
                    self.public_list_scroll, text=f"{n}\n{t}", fg_color="#e67e22",
                    anchor="w", command=lambda x=n: self.select_chat(x)
                ).pack(fill="x", pady=2)


if __name__ == "__main__":
    app = MessengerApp()
    app.mainloop()
