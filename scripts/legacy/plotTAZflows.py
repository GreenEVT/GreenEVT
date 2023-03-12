import sys
import matplotlib
import sqlite3
import xml.etree.ElementTree as ET

matplotlib.use("Qt5Agg")

from PyQt5 import QtCore, QtWidgets

from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg
from matplotlib.figure import Figure
from PyQt5.QtWidgets import *


class MplCanvas(FigureCanvasQTAgg):
    def __init__(self, parent=None, width=5, height=4, dpi=100):
        fig = Figure(figsize=(width, height), dpi=dpi)
        self.axes = fig.add_subplot(111)
        super(MplCanvas, self).__init__(fig)


class MainWindow(QtWidgets.QMainWindow):
    def update_plot(self):
        print("lets update")
        from_taz = str(self.fromtaz.currentText())
        to_taz = str(self.totaz.currentText())

        # Obtain the current plot

        conn = sqlite3.connect("../data/UDS.db")
        c = conn.cursor()

        edges_between = []
        for row in c.execute(
            "SELECT sumoedge  FROM sumoedgetaz WHERE taz = "
            + to_taz
            + " AND from_taz = "
            + from_taz
        ):
            edges_between.append(row[0])

        edges_within_from = {}
        for row in c.execute(
            "SELECT sumoedge, length  FROM sumoedgetaz WHERE taz = "
            + from_taz
            + " AND from_taz = "
            + from_taz
        ):
            edges_within_from[row[0]] = float(row[1])

        edges_within_to = {}
        for row in c.execute(
            "SELECT sumoedge, length  FROM sumoedgetaz WHERE taz = "
            + to_taz
            + " AND from_taz = "
            + to_taz
        ):
            edges_within_to[row[0]] = float(row[1])

        conn.close()

        if self.plottazonly.isChecked():
            input_file = (
                "../sumo/tazspecific/"
                + from_taz
                + "/output/citycenter_w"
                + str(self.evacwindow.currentText())
                + "_m"
                + str(self.multiplier.currentText())
                + "_edge.log.xml"
            )
        else:
            input_file = (
                "../sumo/output/citycenter_w"
                + str(self.evacwindow.currentText())
                + "_m"
                + str(self.multiplier.currentText())
                + "_edge.log.xml"
            )

        tree = ET.parse(input_file)
        root = tree.getroot()

        plottime = []
        flow = []
        from_vehicles = []
        to_vehicles = []
        for interval in root.findall("./interval"):
            sum_vehicle = 0.0
            sum_speed = 0.0
            sum_length = 0.0
            num_edges = 0.0
            sum_flow = 0.0

            sum_vehicles_from = 0.0
            sum_vehicles_to = 0.0

            for edge in interval:
                if edge.attrib["id"] in edges_between and "density" in edge.attrib:
                    # num_vehicles = float(edge.attrib['density'])*(edges[edge.attrib['id']]/1000)
                    # sum_vehicle += num_vehicles
                    # sum_speed += float(edge.attrib['speed']) * 3.6 * num_vehicles
                    # sum_length += float(edges[edge.attrib['id']])/1000
                    num_edges += 1
                    sum_flow += (
                        float(edge.attrib["speed"]) * 3.6 * float(edge.attrib["speed"])
                    )

                if edge.attrib["id"] in edges_within_from and "density" in edge.attrib:
                    sum_vehicles_from += float(edge.attrib["density"]) * (
                        edges_within_from[edge.attrib["id"]] / 1000
                    )
                if edge.attrib["id"] in edges_within_to and "density" in edge.attrib:
                    sum_vehicles_to += float(edge.attrib["density"]) * (
                        edges_within_to[edge.attrib["id"]] / 1000
                    )

            if (
                float(interval.attrib["end"]) < self.maxtime.value()
                and float(interval.attrib["end"]) > self.mintime.value()
            ):
                plottime.append(float(interval.attrib["end"]))
                flow.append(sum_flow)
                from_vehicles.append(sum_vehicles_from)
                to_vehicles.append(sum_vehicles_to)

        # print(edges)

        # x = [1,2]
        # y = [float(from_taz), float(to_taz)]

        self.sc.axes.cla()
        if self.plotflow.isChecked():
            self.sc.axes.plot(plottime, flow, label="Flow between TAZs")

        self.sc.axes.set_xlabel("Time")
        self.sc.axes.set_ylabel("Flow [veh/hour]")
        self.sc.axes.set_ylim(bottom=0)

        self.a2.cla()

        if self.plotfrom.isChecked():
            self.a2.plot(plottime, from_vehicles, "r", label="Vehicles in from")

        if self.plotto.isChecked():
            self.a2.plot(plottime, to_vehicles, "g", label="Vehicles in to")
        self.a2.set_ylabel("Number of vehicles")
        self.a2.set_ylim(bottom=0)

        self.sc.axes.legend()
        self.a2.legend(loc="upper center", bbox_to_anchor=(0.85, 0.95))
        self.sc.draw()

    def fromchange(self, i):
        print("Current from index" + str(i))
        self.update_plot()

    def tochange(self, i):
        print("Current to index" + str(i))
        self.update_plot()

    def multchange(self, i):
        self.update_plot()

    def evacchange(self, i):
        self.update_plot()

    def __init__(self, *args, **kwargs):
        super(MainWindow, self).__init__(*args, **kwargs)

        tazs = [
            "10100001",
            "10200001",
            "10300001",
            "10401001",
            "10404001",
            "10500001",
            "10602001",
            "10701001",
            "10702001",
            "10800001",
            "10900001",
            "11000001",
            "11200001",
            "11300001",
            "11400001",
            "11500001",
        ]

        self.fromtaz = QComboBox()
        self.totaz = QComboBox()

        for taz in tazs:
            self.fromtaz.addItem(taz)
            self.totaz.addItem(taz)

        self.evacwindow = QComboBox()
        self.evacwindow.addItems(["0", "1", "2", "4"])

        self.multiplier = QComboBox()
        self.multiplier.addItems(["1", "2", "4", "8"])

        self.maxtime = QSpinBox()
        self.maxtime.setMaximum(80000)
        self.maxtime.setValue(3600)

        self.mintime = QSpinBox()
        self.mintime.setMaximum(80000)
        self.mintime.setValue(0)

        self.plotflow = QCheckBox("Flow   ")
        self.plotflow.setChecked(True)

        self.plotfrom = QCheckBox("Vehicles from   ")
        self.plotfrom.setChecked(True)

        self.plotto = QCheckBox("Vehicles to   ")
        self.plotto.setChecked(True)

        self.plottazonly = QCheckBox("Disapear after from   ")
        self.plottazonly.setChecked(False)

        # Create the maptlotlib FigureCanvas object,
        # which defines a single set of axes as self.axes.
        self.sc = MplCanvas(self, width=5, height=4, dpi=100)
        self.sc.axes.plot([0, 1, 2, 3, 4], [10, 1, 20, 3, 40])
        self.a2 = self.sc.axes.twinx()

        self.fromtaz.currentIndexChanged.connect(self.fromchange)
        self.totaz.currentIndexChanged.connect(self.tochange)

        self.evacwindow.currentIndexChanged.connect(self.evacchange)
        self.multiplier.currentIndexChanged.connect(self.multchange)
        self.maxtime.valueChanged.connect(self.update_plot)
        self.mintime.valueChanged.connect(self.update_plot)
        self.plotflow.stateChanged.connect(self.update_plot)
        self.plotfrom.stateChanged.connect(self.update_plot)
        self.plotto.stateChanged.connect(self.update_plot)
        self.plottazonly.stateChanged.connect(self.update_plot)

        menubar = QHBoxLayout()

        menubar.setSpacing(0)
        menubar.addWidget(QLabel("Time window:"))
        menubar.addWidget(self.evacwindow)

        menubar.addWidget(QLabel("Multiplier:"))
        menubar.addWidget(self.multiplier)

        menubar.addWidget(QLabel("From TAZ:"))
        menubar.addWidget(self.fromtaz)
        menubar.addWidget(QLabel("To TAZ:"))
        menubar.addWidget(self.totaz)

        menubar.addWidget(QLabel("Min time:"))
        menubar.addWidget(self.mintime)

        menubar.addWidget(QLabel("Max time:"))
        menubar.addWidget(self.maxtime)

        menubar.addWidget(self.plotflow)
        menubar.addWidget(self.plotfrom)
        menubar.addWidget(self.plotto)
        menubar.addWidget(self.plottazonly)

        menubar.addStretch(1)

        layout = QVBoxLayout()

        menubar_w = QWidget()
        menubar_w.setLayout(menubar)
        layout.addWidget(menubar_w)
        layout.addWidget(self.sc)

        widget = QWidget()
        widget.setLayout(layout)

        # b1.clicked.connect(b1_clicked)

        self.setCentralWidget(widget)

        self.update_plot()
        self.show()


app = QtWidgets.QApplication(sys.argv)
w = MainWindow()
app.exec_()
