import sys
import os
from unittest.mock import MagicMock, Mock
from typing import Any


current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
if project_root not in sys.path:
    sys.path.insert(0, project_root)


class FakeWidget:
    def __init__(self, master: Any = None, *args: Any, **kwargs: Any) -> None:
        self.master = master
        self.configure = Mock()
        self.pack = Mock()
        self.place = Mock()
        self.grid = Mock()
        self.pack_forget = Mock()
        self.grid_forget = Mock()
        self.destroy = Mock()
        self.bind = Mock()
        self.get = Mock(return_value="")
        self.delete = Mock()
        self.insert = Mock()
        self.see = Mock()
        self.winfo_children = Mock(return_value=[])


class FakeCTk(FakeWidget):
    def title(self, t: Any) -> None: pass
    def geometry(self, g: Any) -> None: pass
    def mainloop(self) -> None: pass
    def __getattr__(self, name: str) -> Any: return Mock()


class FakeCTkTabview(FakeWidget):
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self._tabs: dict[Any, Any] = {}

    def add(self, name: Any) -> Any:
        frame = FakeWidget()
        self._tabs[name] = frame
        return frame



mock_ctk = MagicMock()
mock_ctk.CTk = FakeCTk
mock_ctk.CTkFrame = FakeWidget
mock_ctk.CTkButton = FakeWidget
mock_ctk.CTkLabel = FakeWidget
mock_ctk.CTkEntry = FakeWidget
mock_ctk.CTkTextbox = FakeWidget
mock_ctk.CTkScrollableFrame = FakeWidget
mock_ctk.CTkImage = FakeWidget
mock_ctk.CTkTabview = FakeCTkTabview
mock_ctk.set_appearance_mode = Mock()
mock_ctk.set_default_color_theme = Mock()




class MockDBConnection(MagicMock):
    def __enter__(self) -> Any:
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        pass


mock_sqlite = MagicMock()

mock_sqlite.connect.return_value = MockDBConnection()


sys.modules["customtkinter"] = mock_ctk
sys.modules["PIL"] = MagicMock()
sys.modules["PIL.Image"] = MagicMock()
