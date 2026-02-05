
from PySide6.QtWidgets import QGraphicsView, QGraphicsScene, QGraphicsRectItem, QGraphicsPixmapItem, QGraphicsEllipseItem, QGraphicsPolygonItem
from PySide6.QtCore import Qt, QPointF
from PySide6.QtGui import QPainter, QBrush, QColor, QPen, QPolygonF

class HandleItem(QGraphicsEllipseItem):
    def __init__(self, x, y, radius=30, parent_selector=None):
        diameter = radius * 2
        super().__init__(-radius, -radius, diameter, diameter) # Centered
        self.setPos(x, y)
        self.setBrush(QBrush(QColor("yellow")))
        self.setPen(QPen(Qt.black))
        self.setFlag(QGraphicsEllipseItem.ItemIsMovable)
        self.setFlag(QGraphicsEllipseItem.ItemSendsGeometryChanges)
        self.parent_selector = parent_selector

    def itemChange(self, change, value):
        if change == QGraphicsEllipseItem.ItemPositionChange and self.parent_selector:
            self.parent_selector.update_polygon()
        return super().itemChange(change, value)

class GraphicsArea(QGraphicsView):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.scene = QGraphicsScene(self)
        self.setScene(self.scene)
        
        # Set a large scene rect
        self.scene.setSceneRect(0, 0, 800, 600)
        
        # Anti-aliasing for smoother graphics
        self.setRenderHint(QPainter.Antialiasing)
        
        # Visual style
        self.setBackgroundBrush(QBrush(QColor(30, 30, 30))) # Dark background
        
    def add_rect(self):
        # Add a movable rectangle to the center
        rect = QGraphicsRectItem(0, 0, 100, 100)
        rect.setPos(self.scene.width() / 2 - 50, self.scene.height() / 2 - 50)
        rect.setBrush(QBrush(QColor(100, 200, 255)))
        rect.setPen(QPen(Qt.NoPen))
        rect.setFlag(QGraphicsRectItem.ItemIsMovable)
        rect.setFlag(QGraphicsRectItem.ItemIsSelectable)
        self.scene.addItem(rect)

    def add_image_placeholder(self):
        # In a real app, we'd load an image. Here we'll just add a placeholder text item or color
        # For this demo, let's add a different colored rect representing an "image"
        rect = QGraphicsRectItem(0, 0, 150, 100)
        rect.setPos(self.scene.width() / 2, self.scene.height() / 2)
        rect.setBrush(QBrush(QColor(255, 100, 100)))
        rect.setFlag(QGraphicsRectItem.ItemIsMovable)
        rect.setFlag(QGraphicsRectItem.ItemIsSelectable)
        self.scene.addItem(rect)
        
    def clear_scene(self):
        self.scene.clear()

    def display_image(self, pixmap):
        self.clear_scene()
        item = QGraphicsPixmapItem(pixmap)
        item.setTransformationMode(Qt.SmoothTransformation)
        self.scene.addItem(item)
        self.scene.setSceneRect(item.boundingRect())
        self.fitInView(item, Qt.KeepAspectRatio)

    def start_parallax_mode(self):
        # Create a large transparent rectangle (polygon) in the center with 4 handles
        # We need to base coordinates on current scene rect
        
        rect = self.scene.sceneRect()
        cx, cy = rect.center().x(), rect.center().y()
        w, h = rect.width() * 0.5, rect.height() * 0.5 # start size
        
        # Initial points
        p1 = QPointF(cx - w/2, cy - h/2)
        p2 = QPointF(cx + w/2, cy - h/2)
        p3 = QPointF(cx + w/2, cy + h/2)
        p4 = QPointF(cx - w/2, cy + h/2)
        
        self.parallax_handles = [
            HandleItem(p1.x(), p1.y(), parent_selector=self),
            HandleItem(p2.x(), p2.y(), parent_selector=self),
            HandleItem(p3.x(), p3.y(), parent_selector=self),
            HandleItem(p4.x(), p4.y(), parent_selector=self)
        ]
        
        self.parallax_polygon = QGraphicsPolygonItem()
        self.parallax_polygon.setPen(QPen(QColor("cyan"), 2))
        self.parallax_polygon.setBrush(QBrush(QColor(0, 255, 255, 50))) # Transparent Cyan
        
        self.scene.addItem(self.parallax_polygon)
        for h in self.parallax_handles:
            self.scene.addItem(h)
            
        self.update_polygon()

    def update_polygon(self):
        if not hasattr(self, 'parallax_handles'):
            return
        poly = QPolygonF()
        for h in self.parallax_handles:
            poly.append(h.pos())
        self.parallax_polygon.setPolygon(poly)

    def get_parallax_coordinates(self):
        if not hasattr(self, 'parallax_handles'):
            return None
        return [h.pos() for h in self.parallax_handles]

    def clear_parallax_selector(self):
        if hasattr(self, 'parallax_handles'):
            for h in self.parallax_handles:
                self.scene.removeItem(h)
            del self.parallax_handles
            
        if hasattr(self, 'parallax_polygon'):
            self.scene.removeItem(self.parallax_polygon)
            del self.parallax_polygon
