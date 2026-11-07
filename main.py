import argparse
from pathlib import Path
from desktop import *
from core import RuleError, export_csv
from service import Service, STATUSES, PRIORITIES


class Window(Shell):
    def __init__(self, service):
        super().__init__(
            "سند",
            "SANAD",
            "كل طلب، له متابعة.",
            ["نظرة عامة والطلبات", "الفنيون", "عن البرنامج"],
        )
        self.service = service
        overview = QWidget()
        layout = QVBoxLayout(overview)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(22)
        metric_row, self.values = metrics(
            [
                ("الطلبات النشطة", "طلبات لم تغلق بعد"),
                ("تجاوزت الموعد", "بحسب تاريخ الاستحقاق"),
                ("الطلبات المغلقة", "مع وصف المعالجة"),
            ]
        )
        layout.addLayout(metric_row)
        frame, body = panel()
        layout.addWidget(frame, 1)
        toolbar = QHBoxLayout()
        toolbar.addWidget(label("سجل طلبات الدعم", "dialogTitle"))
        toolbar.addStretch()
        self.new_button = button("+ طلب جديد", self.new_ticket)
        self.new_button.setObjectName("new_ticket")
        toolbar.addWidget(self.new_button)
        body.addLayout(toolbar)
        filters = QHBoxLayout()
        self.search = line("ابحث بالعنوان أو مقدم الطلب أو رمز الأصل…")
        self.search.setObjectName("search")
        self.status = combo([("", "كل الحالات"), *STATUSES.items()])
        filters.addWidget(self.search, 1)
        filters.addWidget(self.status)
        filters.addWidget(button("تصدير CSV", self.export, "secondary"))
        body.addLayout(filters)
        self.grid = table(
            ["الطلب", "مقدم الطلب", "الأولوية", "الحالة", "الاستحقاق", "الفني"]
        )
        self.grid.setObjectName("tickets")
        body.addWidget(self.grid, 1)
        body.addWidget(
            label("انقر مرتين على الطلب لعرض التفاصيل وتحديث المعالجة.", "small")
        )
        self.search.textChanged.connect(self.refresh)
        self.status.currentIndexChanged.connect(self.refresh)
        self.grid.cellDoubleClicked.connect(
            lambda row, column: self.detail(self.grid.item(row, 0).data(Qt.UserRole))
        )
        self.stack.addWidget(overview)
        technicians = QWidget()
        layout = QVBoxLayout(technicians)
        layout.setContentsMargins(0, 0, 0, 0)
        frame, body = panel()
        layout.addWidget(frame)
        toolbar = QHBoxLayout()
        toolbar.addWidget(label("فريق الدعم", "dialogTitle"))
        toolbar.addStretch()
        toolbar.addWidget(button("+ إضافة فني", self.new_technician))
        body.addLayout(toolbar)
        self.tech_grid = table(["الفني", "التخصص"])
        body.addWidget(self.tech_grid)
        layout.addStretch()
        self.stack.addWidget(technicians)
        about = QWidget()
        layout = QVBoxLayout(about)
        frame, body = panel()
        layout.addWidget(frame)
        body.addWidget(label("سند · إدارة الدعم والصيانة", "dialogTitle"))
        text = label(
            "تطبيق ويندوز محلي لتنظيم الطلبات وتعيين الفنيين وتوثيق المعالجة.\nقاعدة SQLite محفوظة على جهازك، ولا توجد مزامنة سحابية.\nالمشغل المحلي يستطيع الوصول إلى كل السجلات؛ لا توجد حسابات وصلاحيات مستخدمين متعددة.\nهذه نسخة تجريبية لعرض البرمجيات، وليست سجلًا لأعمال عملاء فعلية."
        )
        text.setWordWrap(True)
        body.addWidget(text)
        body.addWidget(button("إضافة بيانات تجريبية", self.seed, "secondary"))
        layout.addStretch()
        self.stack.addWidget(about)
        self.refresh()

    def refresh(self, *args):
        rows = self.service.tickets(self.search.text(), self.status.currentData())
        fill_table(
            self.grid,
            rows,
            [
                "subject",
                "requester",
                lambda r: PRIORITIES[r["priority"]],
                lambda r: STATUSES[r["status"]],
                "due",
                lambda r: r["technician"] or "لم يعيّن",
            ],
        )
        stats = self.service.summary()
        for label_widget, key in zip(self.values, ["active", "overdue", "closed"]):
            label_widget.setText(str(stats[key] or 0))
        fill_table(self.tech_grid, self.service.technicians(), ["name", "specialty"])
        self.notify(f"آخر تحديث محلي · {len(rows)} طلب في العرض الحالي")

    def seed(self):
        try:
            self.service.demo()
            self.refresh()
            self.notify("أُضيفت بيانات تجريبية محلية.")
        except RuleError as e:
            show_error(self, e)

    def new_ticket(self):
        dialog, layout, form, error = form_dialog(self, "طلب دعم جديد")
        dialog.setObjectName("ticket_dialog")
        subject = line()
        subject.setObjectName("subject")
        requester = line()
        requester.setObjectName("requester")
        asset = line()
        category = combo(
            [(s, s) for s in ["أجهزة", "برمجيات", "شبكات", "طابعات", "أخرى"]]
        )
        priority = combo(list(PRIORITIES.items()))
        priority.setCurrentIndex(1)
        due = date_edit()
        for title, widget in [
            ("عنوان الطلب", subject),
            ("مقدم الطلب", requester),
            ("رمز الأصل (اختياري)", asset),
            ("التصنيف", category),
            ("الأولوية", priority),
            ("موعد الاستحقاق", due),
        ]:
            form.addRow(title, widget)

        def save():
            try:
                self.service.create(
                    subject.text(),
                    requester.text(),
                    asset.text(),
                    category.currentData(),
                    priority.currentData(),
                    due.date().toString("yyyy-MM-dd"),
                )
                dialog.accept()
                self.refresh()
            except RuleError as e:
                error.setText(str(e))

        save_button = button("حفظ الطلب", save)
        save_button.setObjectName("save")
        layout.addWidget(save_button)
        dialog.exec()

    def new_technician(self):
        dialog, layout, form, error = form_dialog(self, "إضافة فني")
        name = line()
        specialty = line()
        form.addRow("الاسم", name)
        form.addRow("التخصص", specialty)

        def save():
            try:
                self.service.add_technician(name.text(), specialty.text())
                dialog.accept()
                self.refresh()
            except RuleError as e:
                error.setText(str(e))

        layout.addWidget(button("حفظ الفني", save))
        dialog.exec()

    def detail(self, tid):
        record = self.service.ticket(tid)
        dialog, layout, form, error = form_dialog(self, "تفاصيل الطلب #" + str(tid))
        dialog.resize(600, 680)
        title = label(record["subject"], "dialogTitle")
        title.setWordWrap(True)
        form.addRow(title)
        form.addRow("مقدم الطلب", label(record["requester"]))
        form.addRow("رمز الأصل", label(record["asset"] or "—"))
        status = combo(list(STATUSES.items()))
        status.setCurrentIndex(status.findData(record["status"]))
        technician = combo(
            [
                (None, "لم يعيّن"),
                *[(t["id"], t["name"]) for t in self.service.technicians()],
            ]
        )
        technician.setCurrentIndex(max(0, technician.findData(record["technician_id"])))
        resolution = QTextEdit()
        resolution.setPlainText(record["resolution"])
        resolution.setMaximumHeight(140)
        form.addRow("الحالة", status)
        form.addRow("الفني المسؤول", technician)
        form.addRow("وصف المعالجة", resolution)
        timeline = QTextEdit()
        timeline.setReadOnly(True)
        timeline.setPlainText(
            "\n".join(
                e["created"].replace("T", "  ") + " · " + e["message"]
                for e in self.service.events(tid)
            )
        )
        timeline.setMaximumHeight(140)
        form.addRow("سجل المتابعة", timeline)

        def save():
            try:
                self.service.update(
                    tid,
                    record["version"],
                    status.currentData(),
                    technician.currentData(),
                    resolution.toPlainText(),
                )
                dialog.accept()
                self.refresh()
            except RuleError as e:
                error.setText(str(e))

        layout.addWidget(button("حفظ التحديث", save))
        dialog.exec()

    def export(self):
        path, _ = QFileDialog.getSaveFileName(
            self, "حفظ الطلبات", "sanad-tickets.csv", "CSV (*.csv)"
        )
        if not path:
            return
        try:
            export_csv(
                path,
                ["الرقم", "العنوان", "مقدم الطلب", "الحالة", "الأولوية", "الاستحقاق"],
                [
                    [
                        r["id"],
                        r["subject"],
                        r["requester"],
                        STATUSES[r["status"]],
                        PRIORITIES[r["priority"]],
                        r["due"],
                    ]
                    for r in self.service.tickets(
                        self.search.text(), self.status.currentData()
                    )
                ],
            )
            self.notify("حُفظ التقرير في " + path)
        except OSError as e:
            show_error(self, e)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-dir", type=Path)
    parser.add_argument("--demo", action="store_true")
    parser.add_argument("--screenshot", type=Path)
    args = parser.parse_args()
    app = application("Sanad", "#237d9d", "#152d3c")
    path = args.data_dir / "records.sqlite3" if args.data_dir else default_data("Sanad")
    service = Service(path)
    if args.demo and not service.tickets():
        service.demo()
    window = Window(service)
    window.show()
    if args.screenshot:

        def capture():
            args.screenshot.parent.mkdir(parents=True, exist_ok=True)
            window.grab().save(str(args.screenshot))
            app.quit()

        QTimer.singleShot(700, capture)
    code = app.exec()
    service.close()
    return code


if __name__ == "__main__":
    raise SystemExit(main())
