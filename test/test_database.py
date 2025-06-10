import unittest
from database import Database

class DatabaseTestCase(unittest.TestCase):
    def setUp(self):
        self.db = Database(':memory:')

    def tearDown(self):
        self.db.close()

    def test_insert_item(self):
        self.db.execute(
            "INSERT INTO items(name, unit, total, incidence, active) VALUES(?,?,?,?,?)",
            ("Item1", "u", 1.0, 2.0, 0),
        )
        rows = self.db.fetchall("SELECT name, unit FROM items")
        self.assertEqual(rows[0], ("Item1", "u"))

if __name__ == '__main__':
    unittest.main()