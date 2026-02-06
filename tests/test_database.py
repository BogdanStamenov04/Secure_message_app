import unittest
import os
import time
from typing import List
from src.server.database import Database

class TestDatabase(unittest.TestCase):
    def setUp(self) -> None:
        self.test_db_path: str = "test_users_full.db"
        
        # Clean up old file
        if os.path.exists(self.test_db_path):
            try:
                os.remove(self.test_db_path)
            except PermissionError:
                time.sleep(0.1)
                try:
                    os.remove(self.test_db_path)
                except Exception:
                    pass

        # Monkeypatch the DB path
        from src.server import database
        database.DB_PATH = self.test_db_path
        
        self.db: Database = Database()

    def tearDown(self) -> None:
        if os.path.exists(self.test_db_path):
            try:
                os.remove(self.test_db_path)
            except Exception:
                pass

    def test_register_flow(self) -> None:
        """Test registration success and duplicate prevention."""
        self.assertEqual(self.db.register_user("alex", "123"), "success")
        self.assertEqual(self.db.register_user("alex", "123"), "taken")
        self.assertEqual(self.db.register_user("bob", "123"), "success")

    def test_login_flow(self) -> None:
        """Test login success and failure."""
        self.db.register_user("user1", "pass1")
        self.assertTrue(self.db.check_login("user1", "pass1"))
        self.assertFalse(self.db.check_login("user1", "wrong"))
        self.assertFalse(self.db.check_login("ghost", "pass1"))

    def test_friend_request_lifecycle(self) -> None:
        """Full friend request cycle: Send -> Pending -> Accept -> Friends."""
        self.db.register_user("u1", "p")
        self.db.register_user("u2", "p")

        # 1. Send request
        self.assertEqual(self.db.send_friend_request("u1", "u2"), "success")
        
        # 2. Check pending
        pending: List[str] = self.db.get_pending_requests("u2")
        self.assertEqual(pending, ["u1"])
        
        # 3. Accept
        self.db.handle_request("u1", "u2", "accept")
        
        # 4. Verify friends
        friends_u1: List[str] = self.db.get_friends_list("u1")
        friends_u2: List[str] = self.db.get_friends_list("u2")
        
        self.assertIn("u2", friends_u1)
        self.assertIn("u1", friends_u2)
        
        # 5. Pending should be empty
        self.assertEqual(self.db.get_pending_requests("u2"), [])

    def test_friend_request_errors(self) -> None:
        """Test error conditions for friend requests."""
        self.db.register_user("me", "p")
        
        # Self request
        self.assertEqual(self.db.send_friend_request("me", "me"), "error")
        
        # Non-existent user
        self.assertEqual(self.db.send_friend_request("me", "ghost"), "not_found")

    def test_decline_friend_request(self) -> None:
        """Test declining a request."""
        self.db.register_user("A", "p")
        self.db.register_user("B", "p")
        self.db.send_friend_request("A", "B")
        
        self.db.handle_request("A", "B", "decline")
        
        self.assertNotIn("A", self.db.get_friends_list("B"))
        self.assertEqual(self.db.get_pending_requests("B"), [])

    def test_groups(self) -> None:
        """Test creating and joining groups."""
        self.db.register_user("creator", "p")
        self.db.register_user("joiner", "p")
        
        # Create
        self.assertTrue(self.db.create_group("TeamA", "creator"))
        self.assertFalse(self.db.create_group("TeamA", "joiner")) # Duplicate name
        
        # Join
        self.assertTrue(self.db.join_group("TeamA", "joiner"))
        self.assertFalse(self.db.join_group("MissingGroup", "joiner"))
        
        # Members check
        members: List[str] = self.db.get_group_members("TeamA")
        self.assertIn("creator", members)
        self.assertIn("joiner", members)
        
        # User groups check
        self.assertIn("TeamA", self.db.get_user_groups("creator"))

if __name__ == '__main__':
    unittest.main()