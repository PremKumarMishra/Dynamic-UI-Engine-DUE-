import urllib.request
from PyQt5.QtCore import QThread,pyqtSignal,Qt
from PyQt5.QtGui import QPixmap
import urllib
import DUE.engine.parser
from DUE.singletons import DThread

class ImageLoader(DThread):
    imageLoaded = pyqtSignal(str,QPixmap)
    def __init__(self,parent,src:str,width,height):
        super().__init__(parent)
        self.src = src
        self.width = width
        self.height = height
    
    def run(self):
        if self.src.startswith("http://") or self.src.startswith("https://"):
            try:
                req = urllib.request.Request(self.src,headers={'User-Agent': 'Mozilla/5.0'})
                r = urllib.request.urlopen(req)
                data = r.read()
            except:
                data = b""
            pixmap = QPixmap()
            pixmap.loadFromData(data)
        elif self.src.startswith("res://"):
            pixmap = QPixmap()
            pixmap.loadFromData(parser.Engine.RESOURCE[self.src[6:]])
        else:
            pixmap = QPixmap(self.src)
        
        if self.width and self.height:
            pixmap = pixmap.scaled(self.width,self.height,Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation)
        self.imageLoaded.emit(self.src,pixmap)
