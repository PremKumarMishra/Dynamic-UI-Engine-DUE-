
from ctypes import CDLL,c_void_p,c_double,c_bool,c_int

from PyQt5.QtCore import Qt,QSize,QPointF,QRectF
from PyQt5.QtGui import QColor,QTransform,QImage,QPainter
from PyQt5.QtWidgets import QGraphicsEffect
from PyQt5.sip import unwrapinstance,delete


class QGraphicsGlowEffect(QGraphicsEffect):
    _qt_blurImage  = getattr(CDLL(r"Qt5Widgets.dll"),'?qt_blurImage@@YAXPAVQPainter@@AAVQImage@@N_N2H@Z')
    def __init__(self,parent=None):
        super().__init__(parent)
        self._distance=4.0
        self._blurRadius=10.0
        self._color=QColor (0, 0, 0, 80)
    def setBlurRadius(self, blurRadius:float) :
        self._blurRadius = blurRadius
        self.updateBoundingRect()  
    def blurRadius(self) ->float:
        return self._blurRadius  
    def setColor(self, color):
         self._color = color
    def color(self) :
         return self._color
    def setDistance(self,distance:float) :
        self._distance = distance
        self. updateBoundingRect()
    def distance(self)->float:
         return self._distance
    def boundingRectFor( self,rect) :
        delta = self.blurRadius() + self.distance()
        return rect.united(rect.adjusted(-delta, -delta, delta, delta))
       
        
    #def qt_blurImage(self,p, blurImage, radius, quality, alphaOnly, transposed = 0 ):   
    def draw(self, painter):

        # if nothing to show outside the item, just draw source
        if ((self.blurRadius() + self.distance()) <= 0) :
            self.drawSource(painter);
            return;
        
        
        mode = QGraphicsEffect.PadToEffectiveBoundingRect #return PixmapPadMode
        # offset=QPoint()
        px,offset = self.sourcePixmap(Qt.DeviceCoordinates, mode)

        # return if no source
        if (px.isNull()):
            return
        
        #save world transform
        restoreTransform = painter.worldTransform() #return QTransform
        painter.setWorldTransform(QTransform())

        #Calculate size for the background image
        szi=QSize (int(px.size().width() + 2 * self.distance()), int(px.size().height() + 2 * self.distance()))

        tmp=QImage(szi, QImage.Format_ARGB32_Premultiplied)
        scaled = px.scaled(szi) #return QPixmap
        tmp.fill(0)
        tmpPainter=QPainter(tmp)
        tmpPainter.setCompositionMode(QPainter.CompositionMode_Source)
        tmpPainter.drawPixmap(QPointF(-self.distance(), -self.distance()), scaled)
        tmpPainter.end()

        #blur the alpha channel
        blurred=QImage(tmp.size(), QImage.Format_ARGB32_Premultiplied)
        blurred.fill(0)
        blurPainter=QPainter(blurred)
        self.applyBlurEffect(blurPainter, tmp, self.blurRadius(), False, True)
        blurPainter.end()

        tmp = blurred

        #blacken the image...
        tmpPainter.begin(tmp)
        tmpPainter.setCompositionMode(QPainter.CompositionMode_SourceIn)
        tmpPainter.fillRect(tmp.rect(), self.color())
        tmpPainter.end()

        #draw the blurred shadow...
        painter.drawImage(offset, tmp)

        #draw the actual pixmap...
        painter.drawPixmap(offset, px, QRectF())

        #restore world transform
        painter.setWorldTransform(restoreTransform)
    def applyBlurEffect(self, painter,blurImage, radius, quality, alphaOnly, transposed=0 ):
        blurImage = c_void_p(unwrapinstance(blurImage))
        radius = c_double(radius)
        quality = c_bool(quality)
        alphaOnly = c_bool(alphaOnly)
        transposed = c_int(transposed)
        if painter:
            painter = c_void_p(unwrapinstance(painter))
        self._qt_blurImage(painter, blurImage, radius, quality, alphaOnly, transposed)
