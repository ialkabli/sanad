from datetime import date, timedelta, datetime
import sqlite3
from core import Database, RuleError, required, valid_date

STATUSES = {
    "new": "جديد",
    "working": "قيد المعالجة",
    "waiting": "بانتظار رد",
    "closed": "مغلق",
}
PRIORITIES = {"low": "منخفضة", "normal": "عادية", "urgent": "عاجلة"}


class Service(Database):
    def __init__(self, path):
        super().__init__(path)
        self.conn.executescript("""
        CREATE TABLE IF NOT EXISTS technicians(id INTEGER PRIMARY KEY,name TEXT NOT NULL UNIQUE,specialty TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS tickets(id INTEGER PRIMARY KEY,subject TEXT NOT NULL,requester TEXT NOT NULL,asset TEXT NOT NULL DEFAULT '',category TEXT NOT NULL,priority TEXT NOT NULL CHECK(priority IN ('low','normal','urgent')),status TEXT NOT NULL DEFAULT 'new' CHECK(status IN ('new','working','waiting','closed')),due TEXT NOT NULL,technician_id INTEGER REFERENCES technicians(id),resolution TEXT NOT NULL DEFAULT '',version INTEGER NOT NULL DEFAULT 1,created TEXT NOT NULL,updated TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS events(id INTEGER PRIMARY KEY,ticket_id INTEGER REFERENCES tickets(id),message TEXT NOT NULL,created TEXT NOT NULL);
        CREATE INDEX IF NOT EXISTS tickets_status_due ON tickets(status,due);
        PRAGMA user_version=1;
        """)

    def add_technician(self, name, specialty):
        name = required(name, "الاسم", 2, 80)
        specialty = required(specialty, "التخصص", 2, 80)
        try:
            with self.transaction() as c:
                return c.execute(
                    "INSERT INTO technicians(name,specialty) VALUES(?,?)",
                    (name, specialty),
                ).lastrowid
        except sqlite3.IntegrityError:
            raise RuleError("اسم الفني موجود مسبقًا.")

    def technicians(self):
        return self.rows("SELECT * FROM technicians ORDER BY name")

    def create(self, subject, requester, asset, category, priority, due):
        subject = required(subject, "عنوان الطلب", 3, 160)
        requester = required(requester, "مقدم الطلب", 2, 100)
        asset = required(asset, "رمز الأصل", 0, 60)
        category = required(category, "التصنيف", 2, 60)
        valid_date(due)
        if priority not in PRIORITIES:
            raise RuleError("الأولوية غير صحيحة.")
        stamp = datetime.now().isoformat(timespec="seconds")
        with self.transaction() as c:
            tid = c.execute(
                "INSERT INTO tickets(subject,requester,asset,category,priority,due,created,updated) VALUES(?,?,?,?,?,?,?,?)",
                (subject, requester, asset, category, priority, due, stamp, stamp),
            ).lastrowid
            c.execute(
                "INSERT INTO events(ticket_id,message,created) VALUES(?,?,?)",
                (tid, "إنشاء الطلب", stamp),
            )
            return tid

    def tickets(self, search="", status=""):
        if status and status not in STATUSES:
            raise RuleError("الحالة غير صحيحة.")
        return self.rows(
            'SELECT t.*,u.name AS technician FROM tickets t LEFT JOIN technicians u ON u.id=t.technician_id WHERE (?="" OR status=?) AND (subject LIKE ? OR requester LIKE ? OR asset LIKE ?) ORDER BY CASE status WHEN "closed" THEN 1 ELSE 0 END,due,id DESC',
            (status, status, *(["%" + str(search).strip() + "%"] * 3)),
        )

    def ticket(self, tid):
        rows = self.rows("SELECT * FROM tickets WHERE id=?", (tid,))
        if not rows:
            raise RuleError("الطلب غير موجود.")
        return rows[0]

    def update(self, tid, version, status, technician_id, resolution):
        if status not in STATUSES:
            raise RuleError("الحالة غير صحيحة.")
        resolution = required(resolution, "وصف المعالجة", 0, 3000)
        with self.transaction() as c:
            row = c.execute("SELECT * FROM tickets WHERE id=?", (tid,)).fetchone()
            if not row:
                raise RuleError("الطلب غير موجود.")
            if row["version"] != version:
                raise RuleError("عُدّل الطلب في نافذة أخرى. أغلقه وحدّث القائمة.")
            if (
                technician_id is not None
                and not c.execute(
                    "SELECT id FROM technicians WHERE id=?", (technician_id,)
                ).fetchone()
            ):
                raise RuleError("الفني غير موجود.")
            if status in ["working", "waiting", "closed"] and technician_id is None:
                raise RuleError("اختر الفني المسؤول أولًا.")
            if status == "closed" and len(resolution) < 5:
                raise RuleError("اكتب وصف المعالجة قبل إغلاق الطلب (5 أحرف على الأقل).")
            if row["status"] == "closed" and status != "closed":
                raise RuleError(
                    "الطلب المغلق لا يعاد فتحه في هذه النسخة؛ أنشئ طلب متابعة جديدًا."
                )
            stamp = datetime.now().isoformat(timespec="seconds")
            c.execute(
                "UPDATE tickets SET status=?,technician_id=?,resolution=?,version=version+1,updated=? WHERE id=?",
                (status, technician_id, resolution, stamp, tid),
            )
            c.execute(
                "INSERT INTO events(ticket_id,message,created) VALUES(?,?,?)",
                (tid, "تحديث الحالة إلى " + STATUSES[status], stamp),
            )

    def events(self, tid):
        self.ticket(tid)
        return self.rows(
            "SELECT * FROM events WHERE ticket_id=? ORDER BY id DESC", (tid,)
        )

    def summary(self):
        return self.rows(
            'SELECT COUNT(*) AS total,SUM(status!="closed") AS active,SUM(status!="closed" AND due<?) AS overdue,SUM(status="closed") AS closed FROM tickets',
            (date.today().isoformat(),),
        )[0]

    def demo(self):
        if self.rows("SELECT id FROM tickets LIMIT 1"):
            raise RuleError("تتوفر البيانات التجريبية عندما تكون الطلبات فارغة فقط.")
        technicians = self.technicians()
        if not technicians:
            self.add_technician("محمد سالم", "أجهزة وشبكات")
            self.add_technician("سارة حسن", "أنظمة وتطبيقات")
        tech = self.technicians()[0]["id"]
        subjects = [
            (
                "انقطاع الاتصال في قسم المبيعات",
                "خالد أحمد",
                "PC-014",
                "شبكات",
                "urgent",
                -1,
            ),
            ("تحديث برنامج المحاسبة", "نورة سالم", "PC-008", "برمجيات", "normal", 2),
            ("صيانة طابعة الاستقبال", "ريم حسن", "PR-003", "طابعات", "normal", 0),
            ("تهيئة جهاز موظف جديد", "أحمد علي", "PC-021", "أجهزة", "low", 4),
            (
                "استعادة الوصول إلى المجلد المشترك",
                "ماجد عمر",
                "NET-004",
                "شبكات",
                "urgent",
                -2,
            ),
        ]
        for i, values in enumerate(subjects):
            subject, requester, asset, category, priority, days = values
            tid = self.create(
                subject,
                requester,
                asset,
                category,
                priority,
                (date.today() + timedelta(days=days)).isoformat(),
            )
            if i in [0, 2]:
                self.update(tid, 1, "working", tech, "جارٍ فحص الاتصال والمعدات.")
            if i == 4:
                self.update(
                    tid,
                    1,
                    "closed",
                    tech,
                    "استعيد الاتصال بعد مراجعة إعدادات المشاركة.",
                )
