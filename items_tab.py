# items_tab.py
import os
import pandas as pd
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTableWidget, QPushButton,
    QDialog, QFormLayout, QLineEdit, QTableWidgetItem, QFileDialog,
    QMessageBox, QAbstractItemView, QHeaderView, QComboBox, QGroupBox
)
from PyQt6.QtCore import Qt
from database import Database

class ItemsTab(QWidget):
    def __init__(self, db: Database):
        super().__init__()
        self.db = db
        self._loading = False

        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(12, 12, 12, 12)
        self.layout.setSpacing(10)

        group = QGroupBox("Gestor de Ítems")
        group_layout = QVBoxLayout()

        note = QLabel("<i>Marca los ítems que quieras incluir en Seguimiento</i>")
        note.setStyleSheet("color: #B0B0B0;")
        group_layout.addWidget(note)

        toolbar = QHBoxLayout()
        self.import_btn = QPushButton("📥 Importar")
        self.add_btn = QPushButton("➕ Añadir")
        self.del_btn = QPushButton("🗑 Eliminar")
        self.search = QLineEdit(); self.search.setPlaceholderText("Filtrar…")

        toolbar.addWidget(self.import_btn)
        toolbar.addWidget(self.add_btn)
        toolbar.addWidget(self.del_btn)
        toolbar.addStretch()
        toolbar.addWidget(self.search)
        group_layout.addLayout(toolbar)
        group.setLayout(group_layout)
        self.layout.addWidget(group)

        self.table = QTableWidget()
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setAlternatingRowColors(True)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.setMinimumHeight(350)
        self.layout.addWidget(self.table)

        self.import_btn.clicked.connect(self.import_items)
        self.add_btn.clicked.connect(self.open_add)
        self.del_btn.clicked.connect(self.delete_item)
        self.table.cellChanged.connect(self.on_cell_changed)
        self.search.textChanged.connect(self.filter_rows)

        self.setStyleSheet("""
            QWidget {
                background-color: #1e1e1e;
                color: #e0e0e0;
                font-family: Segoe UI;
                font-size: 12pt;
            }
            QGroupBox {
                font-weight: bold;
                border: 1px solid #444;
                border-radius: 10px;
                padding: 10px;
                margin-top: 6px;
                background-color: #252525;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                top: -4px;
            }
            QPushButton {
                background-color: #0d6efd;
                color: #ffffff;
                padding: 6px 14px;
                border: none;
                border-radius: 6px;
            }
            QPushButton:hover {
                background-color: #1a75ff;
            }
            QLineEdit {
                background-color: #2a2a2a;
                color: #e0e0e0;
                border: 1px solid #555;
                border-radius: 6px;
                padding: 5px;
            }
            QTableWidget {
                background-color: #272727;
                alternate-background-color: #1f1f1f;
                color: #e0e0e0;
                border: 1px solid #444;
            }
            QHeaderView::section {
                background-color: #353535;
                color: #e0e0e0;
                font-weight: bold;
                padding: 4px;
                border: 1px solid #444;
            }
        """)

        self.refresh()

    def refresh(self):
        self._loading = True
        rows = self.db.fetchall("SELECT id, name, unit, total, incidence, active, progress FROM items")
        self.table.setRowCount(len(rows))
        self.table.setColumnCount(8)
        self.table.setHorizontalHeaderLabels(["ID", "Activo", "Nombre", "Unidad", "Cant.", "P.U.", "Total", "Avance (%)"])
        for r, (iid, name, unit, qty, pu, active, progress) in enumerate(rows):
            total = qty * pu
            self.table.setItem(r, 0, QTableWidgetItem(str(iid)))
            chk = QTableWidgetItem(); chk.setFlags(chk.flags() | Qt.ItemFlag.ItemIsUserCheckable)
            chk.setCheckState(Qt.CheckState.Checked if active else Qt.CheckState.Unchecked)
            self.table.setItem(r, 1, chk)
            for c, val in enumerate([name, unit, qty, pu, total], start=2):
                item = QTableWidgetItem(str(val))
                if c in (2,3,4,5): item.setFlags(item.flags() | Qt.ItemFlag.ItemIsEditable)
                else: item.setFlags(item.flags() ^ Qt.ItemFlag.ItemIsEditable)
                self.table.setItem(r, c, item)
            if active:
                avg = self.db.fetchall("SELECT AVG(quantity) FROM avances WHERE item_id=?", (iid,))[0][0] or 0
                avance = QTableWidgetItem(f"{avg:.0f}"); avance.setFlags(avance.flags() ^ Qt.ItemFlag.ItemIsEditable)
                self.table.setItem(r, 7, avance)
            else:
                combo = QComboBox(); combo.addItems(["50", "100"])
                combo.setCurrentText(f"{int(progress)}")
                combo.currentTextChanged.connect(lambda val, iid=iid: self.on_progress_changed(iid, val))
                self.table.setCellWidget(r, 7, combo)
        self._loading = False

    def on_cell_changed(self, row, col):
        if self._loading: return
        iid = int(self.table.item(row, 0).text())
        if col == 1:
            state = self.table.item(row,1).checkState()
            self.db.execute("UPDATE items SET active=? WHERE id=?", (1 if state==Qt.CheckState.Checked else 0, iid))
            return
        mapa = {2: "name", 3: "unit", 4: "total", 5: "incidence"}
        if col in mapa:
            campo = mapa[col]
            valor = self.table.item(row, col).text()
            try:
                nuevo = float(valor) if campo in ("total","incidence") else valor
                self.db.execute(f"UPDATE items SET {campo}=? WHERE id=?", (nuevo, iid))
                qty = float(self.db.fetchall("SELECT total FROM items WHERE id=?", (iid,))[0][0])
                pu = float(self.db.fetchall("SELECT incidence FROM items WHERE id=?", (iid,))[0][0])
                total = qty * pu
                self._loading = True
                self.table.item(row, 6).setText(f"{total}")
                self._loading = False
            except: QMessageBox.warning(self, "Error", "Valor inválido")

    def import_items(self):
        path, _ = QFileDialog.getOpenFileName(self, "Importar Ítems", "", "Excel (*.xlsx);;CSV (*.csv)")
        if not path: return
        try:
            df = pd.read_excel(path) if path.lower().endswith(("xls", "xlsx")) else pd.read_csv(path)
            for _, row in df.iterrows():
                self.db.execute(
                    "INSERT INTO items(name, unit, total, incidence, active) VALUES(?,?,?,?,0)",
                    (str(row.get("DESCRIPCIÓN","")), str(row.get("UNIDAD","")), float(row.get("CANT.",0)), float(row.get("P.U.",0)))
                )
            self.refresh()
            QMessageBox.information(self, "Importado", "Ítems importados correctamente.")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"No se pudo importar:\n{e}")

    def open_add(self):
        dlg = QDialog(self); dlg.setWindowTitle("Añadir Ítem")
        form = QFormLayout(dlg)
        name = QLineEdit(); unit = QLineEdit(); qty = QLineEdit(); pu = QLineEdit(); btn = QPushButton("Guardar")
        form.addRow("Nombre:", name)
        form.addRow("Unidad:", unit)
        form.addRow("Cantidad:", qty)
        form.addRow("P. Unitario:", pu)
        form.addRow(btn)
        def guardar():
            try:
                self.db.execute("INSERT INTO items(name, unit, total, incidence, active) VALUES(?,?,?,?,0)", (name.text(), unit.text(), float(qty.text()), float(pu.text())))
                dlg.accept(); self.refresh()
            except: QMessageBox.warning(dlg, "Error", "Cantidad y P.U. deben ser números.")
        btn.clicked.connect(guardar)
        dlg.exec()

    def delete_item(self):
        sel = self.table.selectionModel().selectedRows()
        if not sel: QMessageBox.information(self, "Eliminar", "Selecciona una fila."); return
        row = sel[0].row(); iid = int(self.table.item(row, 0).text())
        if QMessageBox.question(self, "Confirmar", f"¿Eliminar ítem {iid}?", QMessageBox.Yes | QMessageBox.No) == QMessageBox.Yes:
            self.db.execute("DELETE FROM items WHERE id=?", (iid,)); self.refresh()

    def filter_rows(self, text):
        text = text.lower()
        for r in range(self.table.rowCount()):
            visible = any(text in (self.table.item(r, c).text().lower() if self.table.item(r, c) else '') for c in range(self.table.columnCount()))
            self.table.setRowHidden(r, not visible)

    def on_progress_changed(self, item_id, value):
        try:
            self.db.execute("UPDATE items SET progress=? WHERE id=?", (float(value), item_id))
        except: pass
