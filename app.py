# app.py
import sys, logging, math
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QTabWidget, QMessageBox, QFileDialog, QWidget
)
from PyQt6.QtGui import QAction, QIcon, QPainter, QColor, QPen
from PyQt6.QtCore import Qt
import pandas as pd
from fpdf import FPDF
from docx import Document

from database       import Database
from dashboard_tab  import DashboardTab   # requiere set_theme()
from items_tab      import ItemsTab
from atajados_tab   import AtajadosTab
from avance_tab     import AvanceTab
from cronograma_tab import CronogramaTab
from summary_tab    import SummaryTab

# ---------- QSS claro / oscuro ----------
LIGHT_QSS = """
QWidget { background:#ffffff; color:#202020; font-family:Segoe UI; font-size:12pt; }
QGroupBox { border:1px solid #ccc; border-radius:10px; padding:10px; }
QPushButton { background:#1976D2; color:#fff; border-radius:6px; padding:6px 14px; }
QPushButton:hover { background:#1259a4; }
QLineEdit { background:#fafafa; border:1px solid #aaa; border-radius:6px; padding:5px; }
QTableWidget { background:#f9f9f9; alternate-background-color:#e8f0fe; border:1px solid #ccc; }
QHeaderView::section { background:#d0e8ff; padding:4px; font-weight:bold; border:1px solid #ccc; }
"""
DARK_QSS = """
QWidget { background:#1e1e1e; color:#e0e0e0; font-family:Segoe UI; font-size:12pt; }
QGroupBox { background:#252525; border:1px solid #444; border-radius:10px; padding:10px; }
QPushButton { background:#0d6efd; color:#fff; border-radius:6px; padding:6px 14px; }
QPushButton:hover { background:#1a75ff; }
QLineEdit { background:#2a2a2a; border:1px solid #555; border-radius:6px; padding:5px; color:#e0e0e0; }
QTableWidget { background:#272727; alternate-background-color:#1f1f1f; color:#e0e0e0; border:1px solid #444; }
QHeaderView::section { background:#353535; padding:4px; font-weight:bold; border:1px solid #444; color:#e0e0e0; }
"""

# ---------- Interruptor sol / luna ----------
class ThemeToggle(QWidget):
    def __init__(self):
        super().__init__()
        self.setFixedSize(42, 26)
        self.dark = False

    def mousePressEvent(self, _):    # cambiar estado al hacer clic
        self.dark = not self.dark
        self.repaint()
        # siempre encuentra MainWindow:
        self.window().apply_theme(self.dark)

    def paintEvent(self, _):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        r = self.rect()

        # fondo deslizador
        p.setBrush(QColor("#505050") if self.dark else QColor("#cccccc"))
        p.setPen(QPen(QColor("#666666"), 1))   # contorno para que se vea
        p.drawRoundedRect(r, 13, 13)

        # knob
        knob_x = r.right()-24 if self.dark else r.left()+2
        p.setBrush(QColor("#ffffff"))
        p.setPen(Qt.PenStyle.NoPen)
        p.drawEllipse(knob_x, 2, 22, 22)

        # icono
        p.setPen(QPen(QColor("#000000"), 2))
        cx, cy = knob_x+11, 13
        if self.dark:                 # luna
            p.drawArc(cx-5, cy-5, 10, 10, 30*16, 300*16)
        else:                         # sol
            p.drawEllipse(cx-5, cy-5, 10, 10)
            for a in range(0, 360, 45):
                x1 = cx + 8 * math.cos(a*math.pi/180)
                y1 = cy - 8 * math.sin(a*math.pi/180)
                x2 = cx + 10 * math.cos(a*math.pi/180)
                y2 = cy - 10 * math.sin(a*math.pi/180)
                p.drawLine(int(x1), int(y1), int(x2), int(y2))
        p.end()

# ---------- MainWindow ----------
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.db = Database()
        self.setWindowTitle("Supervisión de Atajados")
        self.setWindowIcon(QIcon("resources/icono.png"))
        self.resize(1200, 800)

        # Pestañas
        self.tabs = QTabWidget()
        self.dashboard_tab = DashboardTab(self.db)
        self.tabs.addTab(self.dashboard_tab, "Inicio")
        self.tabs.addTab(ItemsTab(self.db), "Ítems")
        self.tabs.addTab(AtajadosTab(self.db), "Atajados")
        self.tabs.addTab(AvanceTab(self.db, save_callback=self.refresh_all), "Seguimiento")
        self.tabs.addTab(CronogramaTab(self.db), "Cronograma")
        self.tabs.addTab(SummaryTab(self.db), "Resumen")
        self.setCentralWidget(self.tabs)

        # Barra de menú
        bar = self.menuBar()
        bar.addMenu("Archivo")
        bar.addMenu("Datos")
        bar.addMenu("Estado")
        bar.addMenu("Reportes")
        exp = bar.addMenu("Exportar")
        exp.addAction("A Excel").triggered.connect(self.to_excel)
        exp.addAction("A PDF").triggered.connect(self.to_pdf)
        exp.addAction("A Word").triggered.connect(self.to_word)

        # Interruptor en esquina
        bar.setCornerWidget(ThemeToggle(), Qt.Corner.TopRightCorner)
        self.apply_theme(False)

    # ------ Tema global ------
    def apply_theme(self, dark: bool):
        app = QApplication.instance()
        app.setStyleSheet("")                       # limpia
        app.setStyleSheet(DARK_QSS if dark else LIGHT_QSS)
        self.dashboard_tab.set_theme(dark)          # actualiza gráfica

    # ------ Actualizar ------
    def refresh_all(self):
        self.dashboard_tab.refresh()

    # ------ Exportar ------
    def to_excel(self):
        path, _ = QFileDialog.getSaveFileName(self, "Guardar", "", "*.xlsx")
        if path:
            try:
                items = pd.read_sql("SELECT * FROM items", self.db.conn)
                ataj  = pd.read_sql("SELECT * FROM atajados", self.db.conn)
                with pd.ExcelWriter(path) as w:
                    items.to_excel(w, "Ítems", index=False)
                    ataj.to_excel(w, "Atajados", index=False)
                QMessageBox.information(self, "✔", "Excel generado")
            except Exception as e:
                logging.exception(e); QMessageBox.critical(self, "Error", str(e))

    def to_pdf(self):
        path, _ = QFileDialog.getSaveFileName(self, "Guardar", "", "*.pdf")
        if not path: return
        try:
            pdf = FPDF(); pdf.add_page(); pdf.set_font("Arial", size=12)
            pdf.cell(0, 10, "Reporte Ítems", ln=1)
            for n, t in self.db.fetchall("SELECT name,total FROM items"):
                pdf.cell(0, 8, f"{n}: {t}", ln=1)
            pdf.add_page(); pdf.cell(0, 10, "Reporte Atajados", ln=1)
            for n, c in self.db.fetchall("SELECT number,comunidad FROM atajados"):
                pdf.cell(0, 8, f"{n} - {c}", ln=1)
            pdf.output(path)
            QMessageBox.information(self, "✔", "PDF generado")
        except Exception as e:
            logging.exception(e); QMessageBox.critical(self, "Error", str(e))

    def to_word(self):
        path, _ = QFileDialog.getSaveFileName(self, "Guardar", "", "*.docx")
        if not path: return
        try:
            doc = Document(); doc.add_heading("Reporte Ítems", level=1)
            for n, t in self.db.fetchall("SELECT name,total FROM items"): doc.add_paragraph(f"{n}: {t}")
            doc.add_page_break(); doc.add_heading("Reporte Atajados", level=1)
            for n, c in self.db.fetchall("SELECT number,comunidad FROM atajados"): doc.add_paragraph(f"{n} - {c}")
            doc.save(path); QMessageBox.information(self, "✔", "Word generado")
        except Exception as e:
            logging.exception(e); QMessageBox.critical(self, "Error", str(e))

    def closeEvent(self, e):
        self.db.close(); super().closeEvent(e)

# ---------- Lanzador ----------
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, filename="app.log", format="%(asctime)s %(levelname)s %(message)s")
    app = QApplication(sys.argv)
    app.setApplicationName("SupervisiónAtajados"); app.setOrganizationName("WILOPRO")
    w = MainWindow(); w.show()
    sys.exit(app.exec())
