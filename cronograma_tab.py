from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QScrollArea
)
from PyQt6.QtCore import Qt
from database import Database

# Importar FigureCanvas y Toolbar para PyQt6
try:
    from matplotlib.backends.backend_qt6agg import (
        FigureCanvasQTAgg as FigureCanvas,
        NavigationToolbar2QT as NavigationToolbar
    )
except ImportError:
    from matplotlib.backends.backend_qt5agg import (
        FigureCanvasQTAgg as FigureCanvas,
        NavigationToolbar2QT as NavigationToolbar
    )

import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime

# Aplicar estilo profesional
try:
    plt.style.use('seaborn-whitegrid')
except OSError:
    plt.style.use('ggplot')

class CronogramaTab(QWidget):
    """Tab que muestra únicamente el diagrama de Gantt profesional con scroll e interacción."""
    def __init__(self, db: Database):
        super().__init__()
        self.db = db
        self._setup_ui()
        self.refresh()

    def _setup_ui(self):
        layout = QVBoxLayout(self)

        # Configurar figura y ejes
        self.figure, self.ax = plt.subplots(figsize=(16, 10), dpi=100)
        self.figure.patch.set_facecolor('white')
        self.ax.set_facecolor('#f9f9f9')
        self.canvas = FigureCanvas(self.figure)
        self.toolbar = NavigationToolbar(self.canvas, self)

        # Área de scroll para el Gantt
        scroll = QScrollArea()
        scroll.setWidgetResizable(False)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        container = QWidget()
        vbox = QVBoxLayout(container)
        vbox.setContentsMargins(0, 0, 0, 0)
        vbox.addWidget(self.toolbar)
        vbox.addWidget(self.canvas)
        container.setLayout(vbox)

        # Fijar tamaño del canvas para habilitar scroll
        width, height = self.figure.get_size_inches()
        dpi = self.figure.dpi
        self.canvas.setFixedSize(int(width * dpi), int(height * dpi))

        scroll.setWidget(container)
        layout.addWidget(scroll)

    def refresh(self):
        # Obtener tareas para Gantt
        tasks, y_labels = self._gather_gantt_data()
        self._plot_gantt(tasks, y_labels)

    def _gather_gantt_data(self):
        """Recoge hitos y avances agrupados sin repetir items."""
        tasks = []
        y_labels = []
        y = 0

        # Hitos (cronograma)
        cronos = self.db.fetchall("SELECT hito, date FROM cronograma")
        for hito, fecha in cronos:
            try:
                d = datetime.strptime(fecha, "%Y-%m-%d")
            except ValueError:
                continue
            tasks.append((d, d, y, hito))
            y_labels.append(hito)
            y += 1

        # Avances agrupados por item: un rango único
        rows = self.db.fetchall(
            """
            SELECT i.name,
                   MIN(a.start_date), MAX(a.end_date)
              FROM avances a
              JOIN items i ON a.item_id = i.id
             WHERE i.active = 1
             GROUP BY i.name
            """
        )
        for name, start_str, end_str in rows:
            if name in y_labels:
                continue  # evitar duplicados
            try:
                start = datetime.strptime(start_str, "%Y-%m-%d")
                end = datetime.strptime(end_str, "%Y-%m-%d")
            except (TypeError, ValueError):
                continue
            tasks.append((start, end, y, name))
            y_labels.append(name)
            y += 1

        return tasks, y_labels

    def _plot_gantt(self, tasks, y_labels):
        self.ax.clear()

        # Ajustar límites con margen
        dates = [t[0] for t in tasks] + [t[1] for t in tasks]
        if dates:
            mn, mx = min(dates), max(dates)
            span = mx - mn
            self.ax.set_xlim(mn - span * 0.05, mx + span * 0.05)

        # Dibujar barras y etiquetas
        for start, end, y_pos, label in tasks:
            duration = (end - start).days or 1
            self.ax.broken_barh(
                [(mdates.date2num(start), duration)],
                (y_pos - 0.4, 0.8),
                facecolors='tab:blue', edgecolors='black', lw=0.8
            )
            self.ax.text(
                mdates.date2num(start) + 0.1, y_pos,
                label, va='center', ha='left', fontsize=9, color='#222'
            )

        # Etiquetas Y
        self.ax.set_yticks(range(len(y_labels)))
        self.ax.set_yticklabels(y_labels, fontsize=10)

        # Eje X: meses arriba, días abajo
        self.ax.xaxis.set_major_locator(mdates.MonthLocator())
        self.ax.xaxis.set_major_formatter(mdates.DateFormatter('%b %Y'))
        self.ax.xaxis.set_minor_locator(mdates.DayLocator())
        self.ax.xaxis.set_minor_formatter(mdates.DateFormatter('%d'))
        self.ax.xaxis.tick_top()
        self.ax.xaxis.set_label_position('top')
        self.ax.tick_params(axis='x', which='major', length=10, pad=20, labelsize=11)
        self.ax.tick_params(axis='x', which='minor', length=5, pad=5, labelsize=8, rotation=90)

        # Grid estilo oficial
        self.ax.grid(which='major', axis='x', linestyle='-', color='gray', linewidth=1)
        self.ax.grid(which='minor', axis='x', linestyle=':', color='gray', linewidth=0.5)
        self.ax.grid(which='major', axis='y', linestyle='--', color='lightgray', linewidth=0.5)

        self.ax.invert_yaxis()
        self.figure.tight_layout(rect=[0, 0, 1, 0.95])
        self.ax.set_title('CRONOGRAMA TENTATIVO DE ACTIVIDADES', fontsize=16, pad=20)
        self.canvas.draw()
