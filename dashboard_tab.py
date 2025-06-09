from PyQt6.QtWidgets import QWidget, QHBoxLayout, QVBoxLayout, QLabel, QApplication
from PyQt6.QtGui import QIcon, QPixmap
from PyQt6.QtCore import Qt
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

        main_layout.addLayout(metrics_layout)
        main_layout.addStretch()

    def get_count(self, status=None) -> int:
        if status:
            return self.db.fetchall("SELECT COUNT(*) FROM atajados WHERE status=?", (status,))[0][0]
        return self.db.fetchall("SELECT COUNT(*) FROM atajados")[0][0]

    def get_pending(self) -> int:
        total = self.get_count()
        executed = self.get_count("Ejecutado")
        running = self.get_count("En ejecución")
        return total - executed - running
