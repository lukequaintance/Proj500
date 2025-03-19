import sys
import csv
import random
import pandas as pd
import folium
from PyQt6.QtWidgets import (QApplication, QMainWindow, QVBoxLayout, QWidget, QPushButton, QFileDialog)
from PyQt6.QtWebEngineWidgets import QWebEngineView
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
import matplotlib.pyplot as plt

class SensorDataApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Soil & Plant Analysis")
        self.setGeometry(100, 100, 900, 700)
        
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.layout = QVBoxLayout(self.central_widget)
        
        # Upload Button
        self.upload_button = QPushButton("Upload Data File")
        self.upload_button.clicked.connect(self.upload_file)
        self.layout.addWidget(self.upload_button)
        
        # Heatmap Viewer
        self.map_view = QWebEngineView()
        self.layout.addWidget(self.map_view)
        
        # Matplotlib Graph for NPK, pH, Temp, Moisture
        self.figure, self.ax = plt.subplots()
        self.canvas = FigureCanvas(self.figure)
        self.layout.addWidget(self.canvas)
        
        self.data_file = "sensor_data.csv"
        self.update_visuals()
    
    def upload_file(self):
        """Allow user to upload a CSV file and update the visuals."""
        options = QFileDialog.Options()
        file_name, _ = QFileDialog.getOpenFileName(self, "Open Data File", "", "CSV Files (*.csv)", options=options)
        if file_name:
            self.data_file = file_name
            self.update_visuals()
    
    def update_visuals(self):
        """Update heatmap and graph based on uploaded data."""
        try:
            df = pd.read_csv(self.data_file)
            self.update_heatmap(df)
            self.update_graph(df)
        except Exception as e:
            print("Error updating visuals:", e)
    
    def update_heatmap(self, df):
        """Generate heatmap of soil readings and mark harmful plants."""
        map_object = folium.Map(location=[51.5, -0.12], zoom_start=14)
        
        for _, row in df.iterrows():
            color = "red" if row["Harmful"] == 1 else "blue"
            folium.CircleMarker(
                location=[row["Latitude"], row["Longitude"]],
                radius=5,
                color=color,
                fill=True,
                fill_color=color
            ).add_to(map_object)
        
        map_object.save("map.html")
        self.map_view.setHtml(open("map.html").read())
    
    def update_graph(self, df):
        """Plot NPK, pH, Temperature, and Moisture readings."""
        self.ax.clear()
        self.ax.plot(df["N"], label="Nitrogen", marker='o')
        self.ax.plot(df["P"], label="Phosphorus", marker='o')
        self.ax.plot(df["K"], label="Potassium", marker='o')
        self.ax.plot(df["pH"], label="pH Level", marker='o')
        self.ax.plot(df["Temperature"], label="Temperature", marker='o')
        self.ax.plot(df["Moisture"], label="Moisture", marker='o')
        self.ax.set_title("Soil Readings")
        self.ax.legend()
        self.canvas.draw()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = SensorDataApp()
    window.show()
    sys.exit(app.exec())