# cronograma_tab.py
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QTableWidget, QPushButton, QDialog, QFormLayout, QLineEdit, QTextEdit, QDateEdit, QTableWidgetItem
from PyQt6.QtCore import QDate
from database import Database

class CronogramaTab(QWidget):
    def __init__(self, db: Database):
        super().__init__()
        self.db   = db
        self.layout = QVBoxLayout(self)
        self.table  = QTableWidget()
        self.btn    = QPushButton("Añadir Hito")
        self.layout.addWidget(self.table)
        self.layout.addWidget(self.btn)
        self.btn.clicked.connect(self.open_add)
        self.refresh()

    def refresh(self):
        rows = self.db.fetchall("SELECT id,name,date,notes FROM hitos")
        hdrs = ["ID","Hito","Fecha","Obs."]
        self.table.setColumnCount(len(hdrs))
        self.table.setHorizontalHeaderLabels(hdrs)
        self.table.setRowCount(len(rows))
        for r,row in enumerate(rows):
            for c,val in enumerate(row):
                self.table.setItem(r,c, QTableWidgetItem(str(val)))

    def open_add(self):
        dlg = QDialog(self)
        dlg.setWindowTitle("Añadir Hito")
        form = QFormLayout(dlg)
        nm = QLineEdit()
        dt = QDateEdit(); dt.setCalendarPopup(True); dt.setDate(QDate.currentDate())
        nt = QTextEdit()
        save = QPushButton("Guardar")
        for lbl,w in [("Nombre Hito:",nm),("Fecha:",dt),("Obs.:",nt),("",save)]:
            form.addRow(lbl,w)
        def on_save():
            self.db.execute(
                "INSERT INTO hitos(name,date,notes) VALUES(?,?,?)",
                (nm.text(),dt.date().toString("yyyy-MM-dd"),nt.toPlainText())
            )
            dlg.accept(); self.refresh()
        save.clicked.connect(on_save)
        dlg.exec()
