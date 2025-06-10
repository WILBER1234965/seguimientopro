import unittest
from database import Database

class ProgressTestCase(unittest.TestCase):
    def setUp(self):
        self.db = Database(':memory:')

    def tearDown(self):
        self.db.close()

    def test_project_progress(self):
        # one global item completed
        self.db.execute(
            "INSERT INTO items(name, unit, total, incidence, active, progress) VALUES(?,?,?,?,?,?)",
            ("Global", "u", 1, 10, 0, 100),
        )
        # one item by atajado with 50% progress
        self.db.execute(
            "INSERT INTO items(name, unit, total, incidence, active, progress) VALUES(?,?,?,?,?,?)",
            ("PorAtajado", "u", 1, 10, 1, 0),
        )
        self.db.execute("INSERT INTO atajados(number) VALUES(1)")
        self.db.execute(
            "INSERT INTO avances(atajado_id,item_id,date,quantity) VALUES(?,?,?,?)",
            (1, 2, '2024-01-01', 50),
        )
        pct = self.db.get_project_progress()
        self.assertAlmostEqual(pct, 75.0)

if __name__ == '__main__':
    unittest.main()