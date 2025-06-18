# items_tab.py
import pandas as pd
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTableWidget, QPushButton,
    QDialog, QFormLayout, QLineEdit, QTableWidgetItem, QFileDialog,
    QMessageBox, QAbstractItemView, QHeaderView, QComboBox, QGroupBox
)
from PyQt6.QtCore import Qt
from database import Database

# ---------- QSS local ----------
LIGHT_QSS_ITEM = """
QWidget      { background:#ffffff; color:#202020; font-family:Segoe UI; font-size:12pt; }
QGroupBox    { border:1px solid #ccc; border-radius:10px; padding:10px; margin-top:6px; }
QPushButton  { background:#1976D2; color:#fff; border-radius:6px; padding:6px 14px; }
QPushButton:hover { background:#1259a4; }
QLineEdit    { background:#fafafa; border:1px solid #aaa; border-radius:6px; padding:5px; }
QTableWidget { background:#f9f9f9; alternate-background-color:#e8f0fe; color:#202020; border:1px solid #ccc; }
QHeaderView::section { background:#d0e8ff; color:#202020; font-weight:bold; padding:4px; border:1px solid #ccc; }
"""

DARK_QSS_ITEM = """
QWidget      { background:#1e1e1e; color:#e0e0e0; font-family:Segoe UI; font-size:12pt; }
QGroupBox    { background:#252525; border:1px solid #444; border-radius:10px; padding:10px; margin-top:6px; }
QPushButton  { background:#0d6efd; color:#fff; border-radius:6px; padding:6px 14px; }
QPushButton:hover { background:#1a75ff; }
QLineEdit    { background:#2a2a2a; border:1px solid #555; border-radius:6px; padding:5px; color:#e0e0e0; }
QTableWidget { background:#272727; alternate-background-color:#1f1f1f; color:#e0e0e0; border:1px solid #444; }
QHeaderView::section { background:#353535; color:#e0e0e0; font-weight:bold; padding:4px; border:1px solid #444; }
"""

class ItemsTab(QWidget):
    def __init__(self, db: Database):
        super().__init__()
        self.db = db
        self._loading = False

        # ---------- Layout raíz ----------
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(12, 12, 12, 12)
        self.layout.setSpacing(10)

        # ---------- Grupo superior ----------
        group = QGroupBox("Gestor de Ítems")
        group_layout = QVBoxLayout()

        self.note = QLabel("<i>Marca los ítems que quieras incluir en Seguimiento</i>")
        group_layout.addWidget(self.note)

        toolbar = QHBoxLayout()
        self.import_btn = QPushButton("📥 Importar")
        self.add_btn    = QPushButton("➕ Añadir")
        self.del_btn    = QPushButton("🗑 Eliminar")
        self.search     = QLineEdit(); self.search.setPlaceholderText("Filtrar…")

        for w in (self.import_btn, self.add_btn, self.del_btn, self.search):
            toolbar.addWidget(w)
        toolbar.addStretch()
        group_layout.addLayout(toolbar)
        group.setLayout(group_layout)
        self.layout.addWidget(group)

        # ---------- Tabla ----------
        self.table = QTableWidget()
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setAlternatingRowColors(True)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.setMinimumHeight(350)
        self.layout.addWidget(self.table)

        # ---------- Conexiones ----------
        self.import_btn.clicked.connect(self.import_items)
        self.add_btn.clicked.connect(self.open_add)
        self.del_btn.clicked.connect(self.delete_item)
        self.table.cellChanged.connect(self.on_cell_changed)
        self.search.textChanged.connect(self.filter_rows)

        # ---------- Tema inicial ----------
        self.set_theme(False)   # claro por defecto
        self.refresh()

    # =====================================================
    #              CAMBIO DE TEMA
    # =====================================================
    def set_theme(self, dark: bool):
        """Aplica estilo claro u oscuro a la pestaña."""
        self.setStyleSheet(DARK_QSS_ITEM if dark else LIGHT_QSS_ITEM)
        self.note.setStyleSheet("color:#B0B0B0;" if dark else "color:#777777;")

    # ---------- Resto de métodos (lógica sin cambios) ----------
    def refresh(self):
        self._loading = True
        rows = self.db.fetchall("SELECT id, name, unit, total, incidence, active, progress FROM items")
        self.table.setRowCount(len(rows))
        self.table.setColumnCount(8)
        self.table.setHorizontalHeaderLabels(["ID","Activo","Nombre","Unidad","Cant.","P.U.","Total","Avance (%)"])
        for r,(iid,name,unit,qty,pu,active,progress) in enumerate(rows):
            total = qty*pu
            self.table.setItem(r,0,QTableWidgetItem(str(iid)))
            chk = QTableWidgetItem(); chk.setFlags(chk.flags()|Qt.ItemFlag.ItemIsUserCheckable)
            chk.setCheckState(Qt.CheckState.Checked if active else Qt.CheckState.Unchecked)
            self.table.setItem(r,1,chk)
            for c,val in enumerate([name,unit,qty,pu,total],start=2):
                item = QTableWidgetItem(str(val))
                item.setFlags(item.flags()|Qt.ItemFlag.ItemIsEditable if c in (2,3,4,5) else item.flags()^Qt.ItemFlag.ItemIsEditable)
                self.table.setItem(r,c,item)
            if active:
                avg=self.db.fetchall("SELECT AVG(quantity) FROM avances WHERE item_id=?", (iid,))[0][0] or 0
                it=QTableWidgetItem(f"{avg:.0f}"); it.setFlags(it.flags()^Qt.ItemFlag.ItemIsEditable)
                self.table.setItem(r,7,it)
            else:
                combo=QComboBox(); combo.addItems(["50","100"])
                combo.setCurrentText(str(int(progress)))
                combo.currentTextChanged.connect(lambda v,iid=iid:self.on_progress_changed(iid,v))
                self.table.setCellWidget(r,7,combo)
        self._loading=False

    def on_cell_changed(self,row,col):
        if self._loading: return
        iid=int(self.table.item(row,0).text())
        if col==1:
            st=self.table.item(row,1).checkState()
            self.db.execute("UPDATE items SET active=? WHERE id=?", (1 if st==Qt.CheckState.Checked else 0,iid))
            return
        mapa={2:"name",3:"unit",4:"total",5:"incidence"}
        if col in mapa:
            campo=mapa[col]; valtxt=self.table.item(row,col).text()
            try:
                val=float(valtxt) if campo in ("total","incidence") else valtxt
                self.db.execute(f"UPDATE items SET {campo}=? WHERE id=?", (val,iid))
                qty=float(self.db.fetchall("SELECT total FROM items WHERE id=?", (iid,))[0][0])
                pu=float(self.db.fetchall("SELECT incidence FROM items WHERE id=?", (iid,))[0][0])
                self._loading=True
                self.table.item(row,6).setText(str(qty*pu))
                self._loading=False
            except: QMessageBox.warning(self,"Error","Valor inválido")

    def import_items(self):
        p,_ = QFileDialog.getOpenFileName(self,"Importar Ítems","","Excel (*.xlsx);;CSV (*.csv)")
        if not p: return
        try:
            df = pd.read_excel(p) if p.lower().endswith(("xls","xlsx")) else pd.read_csv(p)
            for _,row in df.iterrows():
                self.db.execute(
                    "INSERT INTO items(name, unit, total, incidence, active) VALUES(?,?,?,?,0)",
                    (row.get("DESCRIPCIÓN",""), row.get("UNIDAD",""), float(row.get("CANT.",0)), float(row.get("P.U.",0)))
                )
            self.refresh(); QMessageBox.information(self,"Importado","Ítems importados correctamente.")
        except Exception as e:
            QMessageBox.critical(self,"Error",f"No se pudo importar:\n{e}")

    def open_add(self):
        dlg=QDialog(self); dlg.setWindowTitle("Añadir Ítem")
        form=QFormLayout(dlg)
        name=QLineEdit(); unit=QLineEdit(); qty=QLineEdit(); pu=QLineEdit(); btn=QPushButton("Guardar")
        form.addRow("Nombre:",name); form.addRow("Unidad:",unit); form.addRow("Cantidad:",qty); form.addRow("P. Unitario:",pu); form.addRow(btn)
        def save():
            try:
                self.db.execute("INSERT INTO items(name,unit,total,incidence,active) VALUES(?,?,?,?,0)",
                                (name.text(),unit.text(),float(qty.text()),float(pu.text())))
                dlg.accept(); self.refresh()
            except: QMessageBox.warning(dlg,"Error","Cantidad y P.U. deben ser números.")
        btn.clicked.connect(save); dlg.exec()

    def delete_item(self):
        sel=self.table.selectionModel().selectedRows()
        if not sel: QMessageBox.information(self,"Eliminar","Selecciona una fila."); return
        row=sel[0].row(); iid=int(self.table.item(row,0).text())
        if QMessageBox.question(self,"Confirmar",f"¿Eliminar ítem {iid}?",QMessageBox.Yes|QMessageBox.No)==QMessageBox.Yes:
            self.db.execute("DELETE FROM items WHERE id=?", (iid,)); self.refresh()

    def filter_rows(self,text):
        t=text.lower()
        for r in range(self.table.rowCount()):
            vis=any(t in (self.table.item(r,c).text().lower() if self.table.item(r,c) else '') for c in range(self.table.columnCount()))
            self.table.setRowHidden(r, not vis)

    def on_progress_changed(self,item_id,val):
        try: self.db.execute("UPDATE items SET progress=? WHERE id=?", (float(val),item_id))
        except: pass
