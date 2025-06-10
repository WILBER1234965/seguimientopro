# items_tab.py
import os
import pandas as pd
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTableWidget, QPushButton,
    QDialog, QFormLayout, QLineEdit, QTableWidgetItem, QFileDialog,
    QMessageBox, QAbstractItemView, QHeaderView
)
from PyQt6.QtCore import Qt
from database import Database

class ItemsTab(QWidget):
    def __init__(self, db: Database):
        super().__init__()
        self.db = db
        self.layout = QVBoxLayout(self)

        # Nota para el usuario
        note = QLabel("<i>Marca los ítems que quieras incluir en Seguimiento</i>")
        note.setStyleSheet("color: #AAA; margin-bottom: 8px;")
        self.layout.addWidget(note)

        # Toolbar con Importar, Añadir y Eliminar
        toolbar = QHBoxLayout()
        self.import_btn = QPushButton("📥 Importar Ítems")
        self.add_btn    = QPushButton("➕ Añadir Ítem")
        self.del_btn    = QPushButton("🗑 Eliminar Ítem")
        self.search     = QLineEdit(); self.search.setPlaceholderText("Filtrar...")
        toolbar.addWidget(self.import_btn)
        toolbar.addWidget(self.add_btn)
        toolbar.addWidget(self.del_btn)
        toolbar.addWidget(self.search)
        toolbar.addStretch()
        self.layout.addLayout(toolbar)

        # Tabla de ítems con checkbox embebido
        self.table = QTableWidget()
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setAlternatingRowColors(True)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setStretchLastSection(True)
        self.layout.addWidget(self.table)

        # Conectar señales
        self.import_btn.clicked.connect(self.import_items)
        self.add_btn.clicked.connect(self.open_add)
        self.del_btn.clicked.connect(self.delete_item)
        self.table.cellChanged.connect(self.on_cell_changed)
        self.search.textChanged.connect(self.filter_rows)

        # Inicializar
        self._loading = False
        self.refresh()

    def refresh(self):
        """
        Recarga todos los ítems y su estado 'active' desde la DB.
        """
        self._loading = True
        rows = self.db.fetchall("SELECT id, name, unit, total, incidence, active FROM items")
        self.table.clearContents()
        self.table.setRowCount(len(rows))
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels([
            "ID", "Activo", "Nombre", "Unidad", "Cant.", "P.U.", "Total"
        ])

        for r, (iid, name, unit, qty, pu, active) in enumerate(rows):
            total_price = qty * pu

            # ID
            id_item = QTableWidgetItem(str(iid))
            id_item.setFlags(id_item.flags() ^ Qt.ItemFlag.ItemIsEditable)
            self.table.setItem(r, 0, id_item)

            # Checkable item en columna Activo
            chk_item = QTableWidgetItem()
            chk_item.setFlags(chk_item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
            chk_item.setCheckState(Qt.CheckState.Checked if active else Qt.CheckState.Unchecked)
            self.table.setItem(r, 1, chk_item)

            # Resto de columnas
            for c, val in enumerate([name, unit, qty, pu, total_price], start=2):
                item = QTableWidgetItem(str(val))
                # editable sólo columnas 2-5
                if c in (2,3,4,5):
                    item.setFlags(item.flags() | Qt.ItemFlag.ItemIsEditable)
                else:
                    item.setFlags(item.flags() ^ Qt.ItemFlag.ItemIsEditable)
                self.table.setItem(r, c, item)

        self._loading = False

    def on_cell_changed(self, row, col):
        """
        Detecta cambios en la tabla:
        - Col 1: togglear active
        - Col 2-5: actualizar campos y recalcular Total
        """
        if self._loading:
            return
        item_id = int(self.table.item(row, 0).text())

        # Si cambió Activo
        if col == 1:
            state = self.table.item(row,1).checkState()
            new_val = 1 if state==Qt.CheckState.Checked else 0
            self.db.execute("UPDATE items SET active=? WHERE id=?", (new_val, item_id))
            return

        # Mapear columnas editables a campos
        field_map = {2:"name", 3:"unit", 4:"total", 5:"incidence"}
        if col in field_map:
            field = field_map[col]
            new_text = self.table.item(row,col).text()
            try:
                val = float(new_text) if field in ("total","incidence") else new_text
                self.db.execute(f"UPDATE items SET {field}=? WHERE id=?", (val,item_id))
                # recalcular Total
                qty = float(self.db.fetchall("SELECT total FROM items WHERE id=?",(item_id,))[0][0])
                pu  = float(self.db.fetchall("SELECT incidence FROM items WHERE id=?",(item_id,))[0][0])
                total_price = qty*pu
                self._loading = True
                self.table.item(row,6).setText(f"{total_price}")
                self._loading = False
            except Exception:
                QMessageBox.warning(self, "Error", "Valor inválido.")

    def import_items(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Importar Ítems", "", "Excel (*.xlsx);;CSV (*.csv)"
        )
        if not path:
            return
        try:
            df = pd.read_excel(path) if path.lower().endswith(("xls","xlsx")) else pd.read_csv(path)
            for _,row in df.iterrows():
                name = str(row.get("DESCRIPCIÓN",""))
                unit = str(row.get("UNIDAD",""))
                qty  = float(row.get("CANT.",0))
                pu   = float(row.get("P.U.",0))
                self.db.execute(
                    "INSERT INTO items(name, unit, total, incidence, active) VALUES(?,?,?,?,?)",
                    (name,unit,qty,pu,0)
                )
            self.refresh()
            QMessageBox.information(self, "Importación", "Ítems importados correctamente.")
        except Exception as e:
            QMessageBox.critical(self, "Error de importación", f"No se pudo importar:\n{e}")

    def open_add(self):
        dlg = QDialog(self)
        dlg.setWindowTitle("Añadir Ítem")
        form = QFormLayout(dlg)
        name=QLineEdit(); unit=QLineEdit(); qty=QLineEdit(); pu=QLineEdit()
        save=QPushButton("Guardar")
        form.addRow("Nombre:",name); form.addRow("Unidad:",unit)
        form.addRow("Cantidad:",qty); form.addRow("P.U.:",pu)
        form.addRow(save)
        def on_save():
            try:
                self.db.execute(
                    "INSERT INTO items(name, unit, total, incidence, active) VALUES(?,?,?,?,?)",
                    (name.text(),unit.text(),float(qty.text()),float(pu.text()),0)
                )
                dlg.accept(); self.refresh()
            except:
                QMessageBox.warning(dlg,"Error","Cantidad y P.U. deben ser números.")
        save.clicked.connect(on_save)
        dlg.exec()

    def delete_item(self):
        sel=self.table.selectionModel().selectedRows()
        if not sel:
            QMessageBox.information(self,"Eliminar","Selecciona una fila.")
            return
        row=sel[0].row(); iid=int(self.table.item(row,0).text())
        if QMessageBox.question(self,"Confirmar",f"Eliminar ítem {iid}?",QMessageBox.Yes|QMessageBox.No)==QMessageBox.Yes:
            self.db.execute("DELETE FROM items WHERE id=?",(iid,)); self.refresh()

    def filter_rows(self, text: str):
        text = text.lower()
        for r in range(self.table.rowCount()):
            visible = any(text in (self.table.item(r, c).text().lower() if self.table.item(r, c) else "")
                           for c in range(self.table.columnCount()))
            self.table.setRowHidden(r, not visible)