
import sys
from PySide6.QtWidgets import QApplication
from ui.mainwindow import MainWindow

def main():
    app = QApplication(sys.argv)
    
    # Modern font setup if available could go here
    
    window = MainWindow()
    window.show()
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
