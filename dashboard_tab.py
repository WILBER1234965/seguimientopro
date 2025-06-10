from PyQt6.QtWidgets import QWidget, QHBoxLayout, QVBoxLayout, QLabel, QApplication
from PyQt6.QtGui import QIcon, QPixmap
from PyQt6.QtCore import Qt
import pyqtgraph as pg
from database import Database

class DashboardTab(QWidget):
    def __init__(self, db: Database):
        super().__init__()
        self.db = db

        # Layout principal
        main_layout = QVBoxLayout(self)
        title = QLabel("<h1>Dashboard de Supervisión</h1>")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(title)

        # Layout de métricas con iconos
        metrics_layout = QHBoxLayout()
        metrics = [
            ("Total Atajados", "icons/total.png", lambda: self.get_count()),
            ("Ejecutados",    "icons/executed.png", lambda: self.get_count("Ejecutado")),
            ("En ejecución",  "icons/running.png",  lambda: self.get_count("En ejecución")),
            ("Pendientes",    "icons/pending.png",  lambda: self.get_pending())
        ]
        self.metric_labels = []
        for label_text, icon_path, func in metrics:
            widget = QWidget()
            v = QVBoxLayout(widget)
            icon_lbl = QLabel()
            icon = QPixmap(icon_path).scaled(48, 48, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            icon_lbl.setPixmap(icon)
            icon_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            text_lbl = QLabel(f"<b>{func()}</b>")
            text_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            caption = QLabel(label_text)
            caption.setAlignment(Qt.AlignmentFlag.AlignCenter)
            v.addWidget(icon_lbl)
            v.addWidget(text_lbl)
            v.addWidget(caption)
            metrics_layout.addWidget(widget)
            self.metric_labels.append((text_lbl, func))            

        main_layout.addLayout(metrics_layout)

        # Avance global del proyecto
        self.progress_label = QLabel(f"Avance del Proyecto: {self.db.get_project_progress():.0f}%")
        self.progress_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(self.progress_label)

        # Gráfico de resumen de atajados
        chart = pg.PlotWidget()
        counts = [
            self.get_count(),
            self.get_count("Ejecutado"),
            self.get_count("En ejecución"),
            self.get_pending(),
        ]
        self.bar = pg.BarGraphItem(x=list(range(4)), height=counts, width=0.6, brush="skyblue")
        chart.addItem(self.bar)
        ticks = [
            (0, "Total"),
            (1, "Ejecutado"),
            (2, "En ejec."),
            (3, "Pendiente"),
        ]
        chart.getAxis("bottom").setTicks([ticks])
        main_layout.addWidget(chart)
        main_layout.addStretch()

    def refresh(self):
        for lbl, func in self.metric_labels:
            lbl.setText(f"<b>{func()}</b>")
        counts = [
            self.get_count(),
            self.get_count("Ejecutado"),
            self.get_count("En ejecución"),
            self.get_pending(),
        ]
        self.bar.setOpts(height=counts)
        self.progress_label.setText(f"Avance del Proyecto: {self.db.get_project_progress():.0f}%")

    def get_count(self, status=None) -> int:
        if status:
            return self.db.fetchall("SELECT COUNT(*) FROM atajados WHERE status=?", (status,))[0][0]
        return self.db.fetchall("SELECT COUNT(*) FROM atajados")[0][0]

    def get_pending(self) -> int:
        total = self.get_count()
        executed = self.get_count("Ejecutado")
        running = self.get_count("En ejecución")
        return total - executed - running
