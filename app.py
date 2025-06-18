# app.py
"""Aplicación principal Qt."""

import logging
import sys
from PyQt6.QtWidgets import QApplication, QMainWindow, QTabWidget, QMessageBox, QFileDialog
from PyQt6.QtGui import QIcon
from PyQt6.QtGui import QIcon
import qdarkstyle
import pandas as pd
from fpdf import FPDF
from docx import Document

from database       import Database
from dashboard_tab  import DashboardTab
from items_tab      import ItemsTab
from atajados_tab   import AtajadosTab
from avance_tab     import AvanceTab
from cronograma_tab import CronogramaTab
from summary_tab    import SummaryTab

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.db = Database()
        self.setWindowTitle("Supervisión de Atajados")
        # Icono de la ventana principal
        self.setWindowIcon(QIcon("resources/icono.png"))
        self.resize(1200,800)

        tabs = QTabWidget()
        self.dashboard_tab = DashboardTab(self.db)
        self.items_tab = ItemsTab(self.db)
        self.atajados_tab = AtajadosTab(self.db)
        self.avance_tab = AvanceTab(self.db, save_callback=self.refresh_all)
        self.cronograma_tab = CronogramaTab(self.db)
        self.summary_tab = SummaryTab(self.db)

        tabs.addTab(self.dashboard_tab, "Inicio")
        tabs.addTab(self.items_tab, "Ítems")
        tabs.addTab(self.atajados_tab, "Atajados")
        tabs.addTab(self.avance_tab, "Seguimiento")
        tabs.addTab(self.cronograma_tab, "Cronograma")
        tabs.addTab(self.summary_tab, "Resumen")
        self.setCentralWidget(tabs)

        m = self.menuBar().addMenu("Exportar")
        xlsx = m.addAction("A Excel"); xlsx.triggered.connect(self.to_excel)
        pdf  = m.addAction("A PDF");   pdf.triggered.connect(self.to_pdf)
        docx = m.addAction("A Word");  docx.triggered.connect(self.to_word)

    def refresh_all(self):
        """Actualizar todas las pestañas."""
        self.dashboard_tab.refresh()
        self.items_tab.refresh()
        self.atajados_tab.refresh()
        self.cronograma_tab.refresh()
        self.summary_tab.refresh()
        
    def closeEvent(self, event):
        """Cerrar conexión a la base de datos al salir."""
        self.db.close()
        super().closeEvent(event)

    def to_excel(self):
        """Exportar datos a Excel."""
        path, _ = QFileDialog.getSaveFileName(self, "Guardar", "", "*.xlsx")
        if not path:
            return
        try:
            df1 = pd.read_sql("SELECT * FROM items", self.db.conn)
            df2 = pd.read_sql("SELECT * FROM atajados", self.db.conn)

            with pd.ExcelWriter(path) as w:
                df1.to_excel(w, "Ítems", index=False)
                df2.to_excel(w, "Atajados", index=False)
            QMessageBox.information(self, "✔", "Excel generado")
            logging.info("Excel exportado a %s", path)
        except Exception as exc:
            logging.exception("Error al exportar Excel")
            QMessageBox.critical(self, "Error", str(exc))

    def to_pdf(self):
        """Generar reporte en PDF."""
        path, _ = QFileDialog.getSaveFileName(self, "Guardar", "", "*.pdf")
        if not path:
            return
        try:
            pdf = FPDF()
            pdf.add_page()
            pdf.set_font("Arial", size=12)
            pdf.cell(0, 10, "Reporte Ítems", ln=1)
            for n, t in self.db.fetchall("SELECT name,total FROM items"):
                pdf.cell(0, 8, f"{n}: {t}", ln=1)
            pdf.add_page()
            pdf.cell(0, 10, "Reporte Atajados", ln=1)
            for num, com in self.db.fetchall("SELECT number,comunidad FROM atajados"):
                pdf.cell(0, 8, f"{num} - {com}", ln=1)
            pdf.output(path)
            QMessageBox.information(self, "✔", "PDF generado")
            logging.info("PDF exportado a %s", path)
        except Exception as exc:
            logging.exception("Error al exportar PDF")
            QMessageBox.critical(self, "Error", str(exc))

    def to_word(self):
        """Generar reporte en Word."""
        path, _ = QFileDialog.getSaveFileName(self, "Guardar", "", "*.docx")
        if not path:
            return
        try:
            doc = Document()
            doc.add_heading("Reporte Ítems", level=1)
            for n, t in self.db.fetchall("SELECT name,total FROM items"):
                doc.add_paragraph(f"{n}: {t}")
            doc.add_page_break()
            doc.add_heading("Reporte Atajados", level=1)
            for num, com in self.db.fetchall("SELECT number,comunidad FROM atajados"):
                doc.add_paragraph(f"{num} - {com}")
            doc.save(path)
            QMessageBox.information(self, "✔", "Word generado")
            logging.info("Word exportado a %s", path)
        except Exception as exc:
            logging.exception("Error al exportar Word")
            QMessageBox.critical(self, "Error", str(exc))

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, filename="app.log", format="%(asctime)s %(levelname)s %(message)s")
    app = QApplication(sys.argv)
    # Nombre interno de la aplicación y organización
    app.setApplicationName("SupervisiónAtajados")
    app.setOrganizationName("WILOPRO")
    app.setStyleSheet(qdarkstyle.load_stylesheet())
    w = MainWindow(); w.show()
    sys.exit(app.exec())
