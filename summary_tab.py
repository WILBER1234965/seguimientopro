# summary_tab.py
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QTableWidget, QTableWidgetItem
from PyQt6.QtCore import Qt
from database import Database

class SummaryTab(QWidget):
    """Display progress summary per atajado."""
    def __init__(self, db: Database):
        super().__init__()
        self.db = db
        layout = QVBoxLayout(self)
        self.table = QTableWidget()
        self.table.setAlternatingRowColors(True)
        self.table.horizontalHeader().setStretchLastSection(True)
        layout.addWidget(self.table)
        self.refresh()

    def refresh(self):
        rows = self.db.fetchall(
            """
            SELECT a.number, a.beneficiario, MAX(v.date),
                   COALESCE(AVG(v.quantity), 0)
            FROM atajados a
            LEFT JOIN avances v ON a.number = v.atajado_id
            GROUP BY a.number, a.beneficiario
            ORDER BY MAX(v.date) DESC
            """
        )
        headers = ["Atajado", "Beneficiario", "Fecha", "Avance (%)"]
        self.table.setColumnCount(len(headers))
        self.table.setHorizontalHeaderLabels(headers)
        self.table.setRowCount(len(rows))
        for r, (num, ben, dt, pct) in enumerate(rows):
            self.table.setItem(r, 0, QTableWidgetItem(str(num)))
            self.table.setItem(r, 1, QTableWidgetItem(ben))
            self.table.setItem(r, 2, QTableWidgetItem(dt if dt else ""))
            self.table.setItem(r, 3, QTableWidgetItem(f"{pct:.0f}"))
        self.table.resizeColumnsToContents()