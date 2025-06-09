import os
import shutil
from datetime import datetime
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QComboBox, QCompleter,
    QTableWidget, QTableWidgetItem, QPushButton,
    QFileDialog, QMessageBox, QListWidget, QListWidgetItem, QDialog,
    QScrollArea, QDateEdit, QLineEdit, QHeaderView
)
from PyQt6.QtCore import Qt, QSize, QDate
from PyQt6.QtGui import QPixmap, QIcon
from database import Database

class ImagePreviewDialog(QDialog):
    def __init__(self, image_paths, index=0):
        super().__init__()
        self.image_paths = image_paths
        self.index = index
        self.setWindowTitle("Vista Previa")
        self.setWindowFlags(
            Qt.WindowType.Window |
            Qt.WindowType.WindowMinimizeButtonHint |
            Qt.WindowType.WindowMaximizeButtonHint |
            Qt.WindowType.WindowCloseButtonHint
        )
        self.setWindowState(Qt.WindowState.WindowMaximized)

        main_layout = QVBoxLayout(self)
        nav = QHBoxLayout()
        self.prev_btn = QPushButton("◀")
        self.prev_btn.clicked.connect(self.show_prev)
        nav.addWidget(self.prev_btn)
        nav.addStretch()
        self.next_btn = QPushButton("▶")
        self.next_btn.clicked.connect(self.show_next)
        nav.addWidget(self.next_btn)
        main_layout.addLayout(nav)

        self.scroll = QScrollArea(self)
        self.scroll.setWidgetResizable(True)
        self.label = QLabel()
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.scroll.setWidget(self.label)
        main_layout.addWidget(self.scroll)

        self._load_pixmap()

    def _load_pixmap(self):
        pix = QPixmap(self.image_paths[self.index])
        self._original = pix
        self._update_pixmap()

    def show_prev(self):
        self.index = (self.index - 1) % len(self.image_paths)
        self._load_pixmap()

    def show_next(self):
        self.index = (self.index + 1) % len(self.image_paths)
        self._load_pixmap()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._update_pixmap()

    def _update_pixmap(self):
        if hasattr(self, '_original') and not self._original.isNull():
            area = self.scroll.viewport().size()
            scaled = self._original.scaled(
                area,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )
            self.label.setPixmap(scaled)

class AvanceTab(QWidget):
    def __init__(self, db: Database):
        super().__init__()
        self.db = db
        self.current_atajado = None

        layout = QVBoxLayout(self)
        # Selector
        sel = QHBoxLayout()
        sel.addWidget(QLabel("Atajado / Beneficiario:"))
        self.at_combo = QComboBox()
        ats = self.db.fetchall("SELECT number, beneficiario FROM atajados")
        opts = [f"{num} – {ben}" for num, ben in ats]
        self.at_combo.addItems(opts)
        self.at_combo.setEditable(True)
        comp = QCompleter(opts)
        comp.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        self.at_combo.setCompleter(comp)
        self.at_combo.currentIndexChanged.connect(self.load_items)
        sel.addWidget(self.at_combo)
        btn = QPushButton("Cargar Ítems")
        btn.clicked.connect(self.load_items)
        sel.addWidget(btn)
        layout.addLayout(sel)

        # Tabla
        self.table = QTableWidget()
        hdr = self.table.horizontalHeader()
        hdr.setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        hdr.setStretchLastSection(True)
        layout.addWidget(self.table)

        # Botones de acción
        actions = QHBoxLayout()
        self.img_btn = QPushButton("📎 Adjuntar Imágenes")
        self.img_btn.clicked.connect(self.attach_images)
        actions.addWidget(self.img_btn)
        self.save_btn = QPushButton("💾 Guardar Avance")
        self.save_btn.clicked.connect(self.save_progress)
        actions.addWidget(self.save_btn)
        actions.addStretch()
        layout.addLayout(actions)

        # Miniaturas
        self.img_list = QListWidget()
        self.img_list.setViewMode(QListWidget.ViewMode.IconMode)
        self.img_list.setIconSize(QSize(100, 100))
        self.img_list.setResizeMode(QListWidget.ResizeMode.Adjust)
        self.img_list.itemDoubleClicked.connect(self.preview_image)
        layout.addWidget(self.img_list)

        self.load_items()

    def load_items(self):
        text = self.at_combo.currentText()
        try:
            num = int(text.split("–")[0].strip())
        except:
            QMessageBox.warning(self, "Selección inválida", "Selecciona un atajado válido.")
            return
        self.current_atajado = num

        # Prorratear cantidad total de items entre todos los atajados
        atajados = self.db.fetchall("SELECT COUNT(*) FROM atajados")[0][0] or 1

        # Obtener items activos
        rows = self.db.fetchall(
            "SELECT id, name, total, incidence FROM items WHERE active=1"
        )
        headers = ["ID","Nombre","Cant.","P.U.","Total","Act. Fechas","Inicio","Fin","Comentario","Avance (%)"]
        self.table.blockSignals(True)
        self.table.clear()
        self.table.setRowCount(len(rows))
        self.table.setColumnCount(len(headers))
        self.table.setHorizontalHeaderLabels(headers)

        for r, (iid, name, total_qty, unit_price) in enumerate(rows):
            qty = total_qty / atajados
            cost_total = qty * unit_price

            self.table.setItem(r, 0, QTableWidgetItem(str(iid)))
            self.table.setItem(r, 1, QTableWidgetItem(name))
            self.table.setItem(r, 2, QTableWidgetItem(f"{qty:.2f}"))
            self.table.setItem(r, 3, QTableWidgetItem(str(unit_price)))
            self.table.setItem(r, 4, QTableWidgetItem(f"{cost_total:.2f}"))

            chk = QTableWidgetItem()
            chk.setFlags(chk.flags() | Qt.ItemFlag.ItemIsUserCheckable)
            chk.setCheckState(Qt.CheckState.Unchecked)
            self.table.setItem(r, 5, chk)

            inicio = QDateEdit()
            inicio.setCalendarPopup(True)
            inicio.setEnabled(False)
            fin = QDateEdit()
            fin.setCalendarPopup(True)
            fin.setEnabled(False)
            self.table.setCellWidget(r, 6, inicio)
            self.table.setCellWidget(r, 7, fin)

            comment = QLineEdit()
            self.table.setCellWidget(r, 8, comment)

            combo = QComboBox()
            combo.addItems(["0%","25%","50%","75%","100%"])
            self.table.setCellWidget(r, 9, combo)

            # Cargar avance previo
            rec = self.db.fetchall(
                "SELECT quantity, start_date, end_date FROM avances WHERE atajado_id=? AND item_id=?",
                (num, iid)
            )
            if rec:
                pct_saved, sd, ed = rec[0]
                combo.setCurrentText(f"{int(pct_saved)}%")
                if sd and ed:
                    chk.setCheckState(Qt.CheckState.Checked)
                    inicio.setEnabled(True)
                    fin.setEnabled(True)
                    inicio.setDate(QDate.fromString(sd, "yyyy-MM-dd"))
                    fin.setDate(QDate.fromString(ed, "yyyy-MM-dd"))

        self.table.cellChanged.connect(self.on_cell_changed)
        self.table.blockSignals(False)

        # Cargar miniaturas
        self.img_list.clear()
        img_dir = os.path.join("images", str(num))
        if os.path.isdir(img_dir):
            for fpath in sorted(os.listdir(img_dir)):
                full = os.path.join(img_dir, fpath)
                pix = QPixmap(full)
                if not pix.isNull():
                    item = QListWidgetItem()
                    item.setIcon(QIcon(pix))
                    item.setData(Qt.ItemDataRole.UserRole, full)
                    self.img_list.addItem(item)

    def on_cell_changed(self, row, col):
        if col == 5:
            state = self.table.item(row,5).checkState()
            w1 = self.table.cellWidget(row,6)
            w2 = self.table.cellWidget(row,7)
            if w1: w1.setEnabled(state == Qt.CheckState.Checked)
            if w2: w2.setEnabled(state == Qt.CheckState.Checked)

    def attach_images(self):
        if self.current_atajado is None:
            QMessageBox.warning(self, "Error", "Carga primero un atajado.")
            return
        paths, _ = QFileDialog.getOpenFileNames(
            self, "Seleccionar imágenes", "", "Images (*.png *.jpg *.jpeg)"
        )
        img_dir = os.path.join("images", str(self.current_atajado))
        os.makedirs(img_dir, exist_ok=True)
        for p in paths:
            dst = os.path.join(img_dir, f"{datetime.now().timestamp()}_{os.path.basename(p)}")
            shutil.copy(p, dst)
            pix = QPixmap(dst)
            if not pix.isNull():
                item = QListWidgetItem()
                item.setIcon(QIcon(pix))
                item.setData(Qt.ItemDataRole.UserRole, dst)
                self.img_list.addItem(item)

    def save_progress(self):
        if self.current_atajado is None:
            QMessageBox.warning(self, "Error", "Carga primero un atajado.")
            return
        today = QDate.currentDate().toString("yyyy-MM-dd")
        for r in range(self.table.rowCount()):
            iid = int(self.table.item(r,0).text())
            combo = self.table.cellWidget(r,9)
            pct = int(combo.currentText().replace("%",""))

            chk = self.table.item(r,5)
            inicio = self.table.cellWidget(r,6)
            fin = self.table.cellWidget(r,7)
            sd = inicio.date().toString("yyyy-MM-dd") if chk.checkState() == Qt.CheckState.Checked else None
            ed = fin.date().toString("yyyy-MM-dd") if chk.checkState() == Qt.CheckState.Checked else None

            rec = self.db.fetchall(
                "SELECT id FROM avances WHERE atajado_id=? AND item_id=?",
                (self.current_atajado, iid)
            )
            if rec:
                aid = rec[0][0]
                self.db.execute(
                    "UPDATE avances SET quantity=?, date=?, start_date=?, end_date=? WHERE id=?",
                    (pct, today, sd, ed, aid)
                )
            else:
                self.db.execute(
                    "INSERT INTO avances(atajado_id,item_id,date,quantity,start_date,end_date) VALUES(?,?,?,?,?,?)",
                    (self.current_atajado, iid, today, pct, sd, ed)
                )
        QMessageBox.information(self, "Guardado", "Avances registrados correctamente.")

    def preview_image(self, item: QListWidgetItem):
        path = item.data(Qt.ItemDataRole.UserRole)
        paths = [self.img_list.item(i).data(Qt.ItemDataRole.UserRole) for i in range(self.img_list.count())]
        idx = paths.index(path)
        dlg = ImagePreviewDialog(paths, idx)
        dlg.exec()