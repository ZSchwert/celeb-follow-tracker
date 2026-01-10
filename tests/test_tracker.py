import unittest
import os
import json
import shutil
from src.tracker import Tracker

class TestTracker(unittest.TestCase):
    def setUp(self):
        self.test_data_dir = "test_data"
        self.tracker = Tracker(data_dir=self.test_data_dir)

    def tearDown(self):
        if os.path.exists(self.test_data_dir):
            shutil.rmtree(self.test_data_dir)

    def test_compare_logic(self):
        old_list = ["user1", "user2", "user3"]
        new_list = ["user2", "user3", "user4"]

        new_follows, unfollows = self.tracker.compare(old_list, new_list)

        self.assertEqual(new_follows, {"user4"})
        self.assertEqual(unfollows, {"user1"})

    def test_compare_no_changes(self):
        old_list = ["user1", "user2"]
        new_list = ["user1", "user2"]

        new_follows, unfollows = self.tracker.compare(old_list, new_list)

        self.assertEqual(new_follows, set())
        self.assertEqual(unfollows, set())

    def test_save_and_load_data(self):
        username = "test_celeb"
        following = ["u1", "u2"]

        filepath = self.tracker.save_data(username, following)
        self.assertTrue(os.path.exists(filepath))

        loaded_data = self.tracker.load_data(filepath)
        self.assertEqual(loaded_data["username"], username)
        self.assertEqual(loaded_data["following"], following)

    def test_get_latest_file(self):
        username = "test_celeb"
        # Create two files
        # Since the saver uses today's date, we can't easily create two files with different dates using `save_data` without mocking date.
        # So we manually create files.

        os.makedirs(self.test_data_dir, exist_ok=True)
        file1 = os.path.join(self.test_data_dir, f"{username}_2023-01-01.json")
        file2 = os.path.join(self.test_data_dir, f"{username}_2023-01-02.json")

        with open(file1, 'w') as f: json.dump({}, f)
        with open(file2, 'w') as f: json.dump({}, f)

        latest = self.tracker.get_latest_file(username)
        self.assertEqual(latest, file2)

if __name__ == '__main__':
    unittest.main()
