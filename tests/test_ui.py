import os, sys, tempfile, unittest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from desktop import application, QApplication, QTimer, QLineEdit, QPushButton, Qt
from PySide6.QtTest import QTest
from service import Service
from main import Window


class UITests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = application("Sanad test", "#237d9d", "#152d3c")

    def test_create_ticket_through_dialog(self):
        with tempfile.TemporaryDirectory() as folder:
            service = Service(Path(folder) / "test.sqlite3")
            window = Window(service)
            window.show()

            def complete():
                dialog = self.app.activeModalWidget()
                dialog.findChild(QLineEdit, "subject").setText("طلب من الواجهة")
                dialog.findChild(QLineEdit, "requester").setText("حساب تجريبي")
                QTest.mouseClick(dialog.findChild(QPushButton, "save"), Qt.LeftButton)

            QTimer.singleShot(100, complete)
            QTest.mouseClick(window.new_button, Qt.LeftButton)
            self.assertEqual(len(service.tickets()), 1)
            self.assertEqual(window.grid.rowCount(), 1)
            window.close()
            service.close()


if __name__ == "__main__":
    unittest.main()
