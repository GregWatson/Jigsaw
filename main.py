
import sys
from PySide6.QtWidgets import QApplication
from ui.mainwindow import MainWindow

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Jigsaw Puzzle App")
    parser.add_argument("-bi", "--box-image", help="Path to the box cover image", type=str)
    parser.add_argument("-ji", "--jigsaw-image", help="Path to the currently assembled jigsaw image", type=str)
    parser.add_argument("-pi", "--piece-image", help="Path to the remaining unplaced pieces image", type=str)
    
    # We need to handle QApp args vs our args. 
    # Usually PySide6 handles its own args, but argparse might conflict if not careful.
    # A common pattern is to parse known args.
    
    # However, since we are taking sys.argv for QApplication, we should be careful.
    # Let's extract our args first or just pass everything to QApplication and then parse?
    # QApplication consumes some args (like -style). 
    
    # Better approach: 
    app = QApplication(sys.argv)
     
    # Now parse our specific arguments from sys.argv (excluding the program name)
    # But argparse might partial parse? 
    # Safe way: use parse_known_args
    
    args, unknown = parser.parse_known_args()
    
    window = MainWindow()
    
    if args.box_image:
        window.load_box_cover(args.box_image)
    if args.jigsaw_image:
        window.load_jigsaw_image(args.jigsaw_image)
    if args.piece_image:
        window.load_piece_image(args.piece_image)

    window.show()
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main()

# python .\main.py -bi .\Images\By_12_Box.jpg -ji .\Images\By_12_SoFar6.jpg -pi .\Images\By_12_Pieces6.jpg