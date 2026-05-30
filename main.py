import sys
import simpy
import random
import numpy as np

from PyQt5 import QtWidgets, QtCore, QtGui
import pyqtgraph as pg

BG_COLOR     = '#1E1E2E'
PANEL_COLOR  = '#2A2B3C'
TEXT_COLOR   = '#CDD6F4'
ACCENT_BLUE  = '#89B4FA'
ACCENT_GREEN = '#A6E3A1'
ACCENT_RED   = '#F38BA8'
ACCENT_YELLOW = '#F9E2AF'
BORDER_COLOR = '#45475A'

pg.setConfigOption('background', BG_COLOR)
pg.setConfigOption('foreground', TEXT_COLOR)


def hex_to_tuple(h):
    h = h.lstrip('#')
    return tuple(int(h[i:i+2], 16) for i in (0, 2, 4))


FIELD_STYLE = f"""
    QLineEdit {{
        background: {PANEL_COLOR}; color: {TEXT_COLOR};
        border: 1px solid {ACCENT_BLUE}; border-radius: 6px;
        padding: 6px 10px; font-size: 14px;
    }}
    QLineEdit:focus {{ border: 1px solid {ACCENT_GREEN}; }}
"""

BTN_BLUE = f"""
    QPushButton {{
        background: {ACCENT_BLUE}; color: {BG_COLOR};
        border-radius: 10px; font-size: 15px; font-weight: bold; padding: 10px 24px;
    }}
    QPushButton:hover {{ background: {ACCENT_GREEN}; }}
"""

BTN_PANEL = f"""
    QPushButton {{
        background: {PANEL_COLOR}; color: {TEXT_COLOR};
        border: 1px solid {BORDER_COLOR}; border-radius: 8px;
        font-size: 13px; font-weight: bold; padding: 6px 16px;
    }}
    QPushButton:hover {{ border-color: {ACCENT_BLUE}; color: {ACCENT_BLUE}; }}
    QPushButton:checked {{ background: {ACCENT_BLUE}; color: {BG_COLOR}; border-color: {ACCENT_BLUE}; }}
"""


class InputScreen(QtWidgets.QWidget):
    start_signal = QtCore.pyqtSignal(int, float, float, int)

    def __init__(self):
        super().__init__()
        layout = QtWidgets.QVBoxLayout(self)
        layout.setAlignment(QtCore.Qt.AlignCenter)
        layout.setSpacing(16)

        title = QtWidgets.QLabel("Настройки симуляции")
        title.setStyleSheet(f"color: {TEXT_COLOR}; font-size: 24px; font-weight: bold;")
        title.setAlignment(QtCore.Qt.AlignCenter)
        layout.addWidget(title)

        self.fields = {}
        params = [
            ("Количество операторов",                "operators", "3"),
            ("Интенсивность прихода (клиентов/мин)", "intensity", "1.0"),
            ("Среднее время обслуживания (мин)",      "service",   "2.0"),
            ("Время симуляции (мин)",                 "simtime",   "100"),
        ]
        for label, key, default in params:
            row = QtWidgets.QHBoxLayout()
            lbl = QtWidgets.QLabel(label + ":")
            lbl.setStyleSheet(f"color: {TEXT_COLOR}; font-size: 14px;")
            lbl.setFixedWidth(340)
            lbl.setAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)
            inp = QtWidgets.QLineEdit(default)
            inp.setFixedWidth(130)
            inp.setStyleSheet(FIELD_STYLE)
            self.fields[key] = inp
            row.addWidget(lbl)
            row.addWidget(inp)
            layout.addLayout(row)

        btn = QtWidgets.QPushButton("Начать симуляцию")
        btn.setFixedSize(220, 48)
        btn.setCursor(QtGui.QCursor(QtCore.Qt.PointingHandCursor))
        btn.setStyleSheet(BTN_BLUE)
        btn.clicked.connect(self.emit_start)
        layout.addSpacing(20)
        layout.addWidget(btn, alignment=QtCore.Qt.AlignCenter)

    def emit_start(self):
        try:
            ops = int(self.fields["operators"].text())
            intensity = float(self.fields["intensity"].text())
            service = float(self.fields["service"].text())
            simtime = int(self.fields["simtime"].text())
            self.start_signal.emit(ops, intensity, service, simtime)
        except ValueError:
            QtWidgets.QMessageBox.warning(self, "Ошибка", "Проверь введённые значения.")


class ResultsDialog(QtWidgets.QDialog):
    restart_signal = QtCore.pyqtSignal()

    def __init__(self, parent, total_served, avg_w, max_w, util):
        super().__init__(parent)
        self.setWindowTitle("Результаты")
        self.setModal(True)
        self.setFixedSize(480, 460)
        self.setStyleSheet(f"background: {BG_COLOR}; color: {TEXT_COLOR};")

        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(32, 32, 32, 24)
        layout.setSpacing(0)

        title = QtWidgets.QLabel("Итоги работы отделения")
        title.setStyleSheet(f"color: {TEXT_COLOR}; font-size: 20px; font-weight: bold;")
        title.setAlignment(QtCore.Qt.AlignCenter)
        layout.addWidget(title)
        layout.addSpacing(28)

        metrics = [
            ("Обслужено клиентов",    f"{total_served}",  ACCENT_BLUE),
            ("Среднее ожидание",      f"{avg_w:.2f} мин", ACCENT_GREEN),
            ("Максимальное ожидание", f"{max_w:.2f} мин", ACCENT_YELLOW),
            ("Загрузка операторов",   f"{util:.1f}%",     ACCENT_RED if util > 85 else ACCENT_GREEN),
        ]

        grid = QtWidgets.QGridLayout()
        grid.setSpacing(12)
        for i, (label, value, color) in enumerate(metrics):
            card = QtWidgets.QFrame()
            card.setStyleSheet(f"""
                QFrame {{
                    background: {PANEL_COLOR};
                    border: 1px solid {BORDER_COLOR};
                    border-radius: 10px;
                }}
            """)
            card_layout = QtWidgets.QVBoxLayout(card)
            card_layout.setContentsMargins(16, 14, 16, 14)
            card_layout.setSpacing(4)
            val_lbl = QtWidgets.QLabel(value)
            val_lbl.setStyleSheet(f"color: {color}; font-size: 22px; font-weight: bold; border: none;")
            val_lbl.setAlignment(QtCore.Qt.AlignCenter)
            name_lbl = QtWidgets.QLabel(label)
            name_lbl.setStyleSheet(f"color: {BORDER_COLOR}; font-size: 11px; border: none;")
            name_lbl.setAlignment(QtCore.Qt.AlignCenter)
            card_layout.addWidget(val_lbl)
            card_layout.addWidget(name_lbl)
            grid.addWidget(card, i // 2, i % 2)

        layout.addLayout(grid)
        layout.addSpacing(20)

        util_label = QtWidgets.QLabel(f"Загрузка операторов: {util:.1f}%")
        util_label.setStyleSheet(f"color: {TEXT_COLOR}; font-size: 13px;")
        layout.addWidget(util_label)
        layout.addSpacing(6)

        bar_color = ACCENT_RED if util > 85 else ACCENT_GREEN
        bar = QtWidgets.QProgressBar()
        bar.setValue(int(util))
        bar.setTextVisible(False)
        bar.setFixedHeight(10)
        bar.setStyleSheet(f"""
            QProgressBar {{ background: {PANEL_COLOR}; border-radius: 5px; border: none; }}
            QProgressBar::chunk {{ background: {bar_color}; border-radius: 5px; }}
        """)
        layout.addWidget(bar)
        layout.addSpacing(20)

        btn_row = QtWidgets.QHBoxLayout()
        btn_row.setSpacing(12)

        restart_btn = QtWidgets.QPushButton("Повторить")
        restart_btn.setStyleSheet(BTN_PANEL)
        restart_btn.setFixedHeight(42)
        restart_btn.clicked.connect(self._on_restart)
        btn_row.addWidget(restart_btn)

        close_btn = QtWidgets.QPushButton("Закрыть")
        close_btn.setStyleSheet(BTN_BLUE)
        close_btn.setFixedHeight(42)
        close_btn.clicked.connect(self.accept)
        btn_row.addWidget(close_btn)

        layout.addLayout(btn_row)

    def _on_restart(self):
        self.restart_signal.emit()
        self.accept()


class SimScreen(QtWidgets.QWidget):
    restart_signal = QtCore.pyqtSignal()

    def __init__(self, ops, intensity, service, simtime):
        super().__init__()
        self.ops = ops
        self.intensity = intensity
        self.service = service
        self.simtime = simtime
        self.speed = 1
        self.paused = False
        self.real_elapsed = 0.0

        self._init_sim()
        self._build_ui()

        self.timer = QtCore.QTimer()
        self.timer.setInterval(50)
        self.timer.timeout.connect(self._step)
        self.timer.start()

        self.clock_timer = QtCore.QTimer()
        self.clock_timer.setInterval(100)
        self.clock_timer.timeout.connect(self._tick_clock)
        self.clock_timer.start()

    def _init_sim(self):
        self.wait_times = []
        self.queue_times = [0.0]
        self.queue_vals = [0]
        self.total_served = 0
        self.total_busy_time = 0.0
        self.update_step = 0.5

        random.seed(42)
        self.env = simpy.Environment()
        self.operators = simpy.Resource(self.env, capacity=self.ops)
        self.env.process(self._customer_gen())

    def _customer_gen(self):
        cid = 0
        while True:
            yield self.env.timeout(random.expovariate(self.intensity))
            cid += 1
            self.env.process(self._customer(cid))

    def _customer(self, cid):
        arrival = self.env.now
        with self.operators.request() as req:
            yield req
            self.wait_times.append(self.env.now - arrival)
            dur = random.expovariate(1.0 / self.service)
            self.total_busy_time += dur
            yield self.env.timeout(dur)
            self.total_served += 1

    def _build_ui(self):
        main = QtWidgets.QVBoxLayout(self)
        main.setContentsMargins(12, 12, 12, 8)
        main.setSpacing(8)

        ctrl = QtWidgets.QHBoxLayout()
        ctrl.setSpacing(10)

        box_style = f"""
            QFrame {{
                background: {PANEL_COLOR}; border: 1px solid {BORDER_COLOR};
                border-radius: 8px;
            }}
        """
        lbl_title_style = f"color: {BORDER_COLOR}; font-size: 9px; letter-spacing: 1px; border: none;"

        timer_box = QtWidgets.QFrame()
        timer_box.setStyleSheet(box_style)
        timer_layout = QtWidgets.QVBoxLayout(timer_box)
        timer_layout.setContentsMargins(14, 6, 14, 6)
        timer_layout.setSpacing(0)
        clock_title = QtWidgets.QLabel("РЕАЛЬНОЕ ВРЕМЯ")
        clock_title.setStyleSheet(lbl_title_style)
        self.clock_label = QtWidgets.QLabel("00:00")
        self.clock_label.setStyleSheet(f"color: {ACCENT_BLUE}; font-size: 22px; font-weight: bold; border: none;")
        timer_layout.addWidget(clock_title)
        timer_layout.addWidget(self.clock_label)
        ctrl.addWidget(timer_box)

        sim_box = QtWidgets.QFrame()
        sim_box.setStyleSheet(box_style)
        sim_layout = QtWidgets.QVBoxLayout(sim_box)
        sim_layout.setContentsMargins(14, 6, 14, 6)
        sim_layout.setSpacing(0)
        sim_title = QtWidgets.QLabel("МОДЕЛЬНОЕ ВРЕМЯ")
        sim_title.setStyleSheet(lbl_title_style)
        self.sim_time_label = QtWidgets.QLabel(f"0 / {self.simtime} мин")
        self.sim_time_label.setStyleSheet(f"color: {ACCENT_GREEN}; font-size: 22px; font-weight: bold; border: none;")
        sim_layout.addWidget(sim_title)
        sim_layout.addWidget(self.sim_time_label)
        ctrl.addWidget(sim_box)

        prog_box = QtWidgets.QFrame()
        prog_box.setStyleSheet(box_style)
        prog_box.setFixedWidth(200)
        prog_layout = QtWidgets.QVBoxLayout(prog_box)
        prog_layout.setContentsMargins(14, 8, 14, 8)
        prog_layout.setSpacing(4)
        prog_title = QtWidgets.QLabel("ПРОГРЕСС")
        prog_title.setStyleSheet(lbl_title_style)
        self.progress_bar = QtWidgets.QProgressBar()
        self.progress_bar.setRange(0, self.simtime)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setFixedHeight(8)
        self.progress_bar.setStyleSheet(f"""
            QProgressBar {{ background: {BG_COLOR}; border-radius: 4px; border: none; }}
            QProgressBar::chunk {{ background: {ACCENT_BLUE}; border-radius: 4px; }}
        """)
        prog_layout.addWidget(prog_title)
        prog_layout.addWidget(self.progress_bar)
        ctrl.addWidget(prog_box)

        ctrl.addStretch()

        speed_label = QtWidgets.QLabel("СКОРОСТЬ:")
        speed_label.setStyleSheet(f"color: {BORDER_COLOR}; font-size: 10px; letter-spacing: 1px;")
        ctrl.addWidget(speed_label)

        self.speed_btns = []
        for mult, label in [(1, "1x"), (2, "2x"), (5, "5x")]:
            btn = QtWidgets.QPushButton(label)
            btn.setCheckable(True)
            btn.setFixedSize(52, 36)
            btn.setStyleSheet(BTN_PANEL + "QPushButton { font-family: 'Courier New'; }")
            btn.clicked.connect(lambda checked, m=mult: self._set_speed(m))
            self.speed_btns.append((mult, btn))
            ctrl.addWidget(btn)
        self.speed_btns[0][1].setChecked(True)

        self.pause_btn = QtWidgets.QPushButton()
        self.pause_btn.setIcon(self.style().standardIcon(QtWidgets.QStyle.SP_MediaPause))
        self.pause_btn.setIconSize(QtCore.QSize(18, 18))
        self.pause_btn.setFixedSize(36, 36)
        self.pause_btn.setStyleSheet(BTN_PANEL + "QPushButton { padding: 0px; }")
        self.pause_btn.clicked.connect(self._toggle_pause)
        ctrl.addWidget(self.pause_btn)

        main.addLayout(ctrl)

        pen_blue = pg.mkPen(color=hex_to_tuple(ACCENT_BLUE), width=2)
        pen_red = pg.mkPen(color=hex_to_tuple(ACCENT_RED), width=1.5, style=QtCore.Qt.DashLine)
        pen_yellow = pg.mkPen(color=hex_to_tuple(ACCENT_YELLOW), width=2.5)

        self.plot1 = pg.PlotWidget(title="Время ожидания клиентов")
        self.plot1.setLabel('left', 'Мин')
        self.plot1.showGrid(x=True, y=True, alpha=0.3)
        self.curve1 = self.plot1.plot(pen=pen_blue, symbol='o', symbolSize=5,
                                      symbolBrush=hex_to_tuple(ACCENT_BLUE))
        self.avg_line = self.plot1.addLine(y=0, pen=pen_red)
        main.addWidget(self.plot1)

        self.plot2 = pg.PlotWidget(title="Размер очереди")
        self.plot2.setLabel('left', 'Человек')
        self.plot2.showGrid(x=True, y=True, alpha=0.3)
        self.curve2 = self.plot2.plot(pen=pen_yellow, stepMode='right',
                                      fillLevel=0,
                                      brush=(*hex_to_tuple(ACCENT_YELLOW), 40))
        main.addWidget(self.plot2)

        self.plot3 = pg.PlotWidget(title="Загрузка операторов")
        self.plot3.setXRange(0, 110)
        self.plot3.setYRange(-0.5, 1.8)
        self.plot3.getAxis('left').setTicks([[(0, 'Загрузка'), (1, 'Простой')]])
        self.plot3.showGrid(x=True, y=False, alpha=0.3)
        self.bar_load = pg.BarGraphItem(x0=0, y=0, height=0.5, width=0, brush=hex_to_tuple(ACCENT_GREEN))
        self.bar_idle = pg.BarGraphItem(x0=0, y=1, height=0.5, width=100, brush='#45475A')
        self.util_text = pg.TextItem("0%", color=TEXT_COLOR, anchor=(0, 0.5))
        self.plot3.addItem(self.bar_load)
        self.plot3.addItem(self.bar_idle)
        self.plot3.addItem(self.util_text)
        main.addWidget(self.plot3)

        self.result_btn = QtWidgets.QPushButton("Показать результаты")
        self.result_btn.setStyleSheet(BTN_BLUE)
        self.result_btn.setFixedHeight(44)
        self.result_btn.clicked.connect(self._show_results)
        self.result_btn.hide()
        main.addWidget(self.result_btn)

    def _set_speed(self, mult):
        self.speed = mult
        self.timer.setInterval(max(10, 50 // mult))
        for m, btn in self.speed_btns:
            btn.setChecked(m == mult)

    def _toggle_pause(self):
        self.paused = not self.paused
        if self.paused:
            self.pause_btn.setIcon(self.style().standardIcon(QtWidgets.QStyle.SP_MediaPlay))
            self.clock_timer.stop()
        else:
            self.pause_btn.setIcon(self.style().standardIcon(QtWidgets.QStyle.SP_MediaPause))
            self.clock_timer.start()

    def _tick_clock(self):
        self.real_elapsed += 0.1
        mins = int(self.real_elapsed) // 60
        secs = int(self.real_elapsed) % 60
        self.clock_label.setText(f"{mins:02d}:{secs:02d}")

    def _step(self):
        if self.paused:
            return
        if self.env.now >= self.simtime:
            self.timer.stop()
            self.clock_timer.stop()
            self.result_btn.show()
            return

        step = self.update_step * self.speed
        self.env.run(until=self.env.now + step)
        t = self.env.now

        q = len(self.operators.queue)
        self.queue_times.append(t)
        self.queue_vals.append(q)

        avg_wait = float(np.mean(self.wait_times)) if self.wait_times else 0.0
        util = min(100.0, (self.total_busy_time / (self.ops * t)) * 100) if t > 0 else 0.0

        self.curve1.setData(list(range(len(self.wait_times))), self.wait_times)
        self.avg_line.setValue(avg_wait)
        self.curve2.setData(self.queue_times, self.queue_vals)
        self.bar_load.setOpts(width=util)
        self.bar_idle.setOpts(width=100 - util)
        self.util_text.setPos(util + 1, 0)
        self.util_text.setText(f"{util:.1f}%")

        self.sim_time_label.setText(f"{t:.0f} / {self.simtime} мин")
        self.progress_bar.setValue(int(t))
        self.plot1.setTitle(f"Время ожидания | Обслужено: {self.total_served}  |  среднее: {avg_wait:.2f} мин")
        self.plot2.setTitle(f"Размер очереди | Сейчас: {q}")

    def _show_results(self):
        util = min(100.0, (self.total_busy_time / (self.ops * self.simtime)) * 100)
        avg_w = float(np.mean(self.wait_times)) if self.wait_times else 0.0
        max_w = float(np.max(self.wait_times)) if self.wait_times else 0.0
        dlg = ResultsDialog(self, self.total_served, avg_w, max_w, util)
        dlg.restart_signal.connect(self._on_restart)
        dlg.exec_()

    def _on_restart(self):
        self.timer.stop()
        self.clock_timer.stop()
        self.restart_signal.emit()


class MainWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Симуляция работы банка")
        self.resize(1200, 900)
        self.setStyleSheet(f"background: {BG_COLOR};")

        self.stack = QtWidgets.QStackedWidget()
        self.setCentralWidget(self.stack)

        self._show_input()

    def _show_input(self):
        input_screen = InputScreen()
        input_screen.start_signal.connect(self._go_to_sim)
        self.stack.addWidget(input_screen)
        self.stack.setCurrentWidget(input_screen)

    def _go_to_sim(self, ops, intensity, service, simtime):
        sim = SimScreen(ops, intensity, service, simtime)
        sim.restart_signal.connect(self._on_restart)
        self.stack.addWidget(sim)
        self.stack.setCurrentWidget(sim)

    def _on_restart(self):
        old_sim = self.stack.currentWidget()
        self._show_input()
        self.stack.removeWidget(old_sim)
        old_sim.deleteLater()


if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    app.setStyle("Fusion")
    win = MainWindow()
    win.show()
    sys.exit(app.exec_())