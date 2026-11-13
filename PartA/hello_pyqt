import sys
from PyQt6.QtWidgets import QApplication, QLabel, QPushButton, QVBoxLayout, QWidget

app = QApplication(sys.argv)
window = QWidget()
window.setWindowTitle("Hello - PyQt6")
window.resize(300, 150)

label = QLabel("Hello, World!")
button = QPushButton("Click me")
button.clicked.connect(lambda: label.setText("Button clicked!"))

layout = QVBoxLayout(window)
layout.addWidget(label)
layout.addWidget(button)

window.show()
sys.exit(app.exec())
