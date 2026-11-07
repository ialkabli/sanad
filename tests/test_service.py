import unittest, tempfile, sys, csv
from pathlib import Path
from datetime import date, timedelta

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from service import Service
from core import RuleError, export_csv


class Tests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.path = Path(self.temp.name) / "records.sqlite3"
        self.s = Service(self.path)

    def tearDown(self):
        self.s.close()
        self.temp.cleanup()

    def ticket(self):
        return self.s.create(
            "عطل في الشبكة",
            "عميل تجريبي",
            "PC-1",
            "شبكات",
            "urgent",
            (date.today() - timedelta(days=1)).isoformat(),
        )

    def test_assignment_resolution_and_stale_update(self):
        tid = self.ticket()
        with self.assertRaises(RuleError):
            self.s.update(tid, 1, "working", None, "")
        tech = self.s.add_technician("فني تجريبي", "شبكات")
        self.s.update(tid, 1, "working", tech, "فحص الجهاز")
        with self.assertRaises(RuleError):
            self.s.update(tid, 1, "closed", tech, "أُصلح العطل بالكامل")
        with self.assertRaises(RuleError):
            self.s.update(tid, 2, "closed", tech, "")
        self.s.update(tid, 2, "closed", tech, "أُصلح العطل بالكامل")
        self.assertEqual(self.s.summary()["overdue"], 0)
        with self.assertRaises(RuleError):
            self.s.update(tid, 3, "working", tech, "إعادة فتح")
        self.assertEqual(len(self.s.events(tid)), 3)

    def test_invalid_input_and_transaction_rollback(self):
        with self.assertRaises(RuleError):
            self.s.create("x", "عميل", "", "أخرى", "urgent", "2026-02-31")
        tid = self.ticket()
        with self.assertRaises(RuleError):
            self.s.update(tid, 1, "working", 999, "معالجة")
        self.assertEqual(self.s.ticket(tid)["version"], 1)
        self.assertEqual(len(self.s.events(tid)), 1)

    def test_persistence_search_and_overdue(self):
        tid = self.ticket()
        self.s.close()
        self.s = Service(self.path)
        self.assertEqual(self.s.tickets("PC-1")[0]["id"], tid)
        self.assertEqual(self.s.summary()["overdue"], 1)
        self.assertEqual(self.s.tickets("' OR 1=1 --"), [])

    def test_csv_formula_safety_and_demo_guard(self):
        self.s.demo()
        with self.assertRaises(RuleError):
            self.s.demo()
        path = Path(self.temp.name) / "report.csv"
        export_csv(path, ["اسم"], [["=1+2"], ["نص عربي"]])
        with path.open(encoding="utf-8-sig", newline="") as f:
            rows = list(csv.reader(f))
        self.assertEqual(rows[1][0], "'=1+2")
        self.assertEqual(rows[2][0], "نص عربي")

    def test_two_windows_do_not_overwrite_each_other(self):
        import threading

        tid = self.ticket()
        tech = self.s.add_technician("فني آخر", "أجهزة")
        barrier = threading.Barrier(2)
        outcomes = []

        def update():
            other = Service(self.path)
            try:
                version = other.ticket(tid)["version"]
                barrier.wait(timeout=5)
                other.update(tid, version, "working", tech, "فحص الطلب")
                outcomes.append("saved")
            except RuleError:
                outcomes.append("stale")
            finally:
                other.close()

        threads = [threading.Thread(target=update) for _ in range(2)]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join(timeout=15)
        self.assertCountEqual(outcomes, ["saved", "stale"])
        self.assertEqual(self.s.ticket(tid)["version"], 2)


if __name__ == "__main__":
    unittest.main()
