from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from DUE.pybass.pybass import *
from DUE.utils.loader import ImageLoader
from DUE.utils.cache import ImageCache

from DUE.pybass.pybass import *
import time
import os
import ctypes

#Audio Widget
class Audio:
    def __init__(self):
        self._src = None
        self._volume = 100
        self._loop = False
        self._autoplay = True
        self._stream = None
    
    @staticmethod
    def audio_init():
        if not BASS_Init(-1,44100,0,0,0):
            raise SystemError("Failed To Initialise Audio System")
    
    @property
    def stream(self) -> object:
        return self._stream

    @stream.setter
    def stream(self,v):
        self._stream = v
        # if self._stream == 0:
        #     self._stream = None

    @property
    def src(self) -> str:
        return self._src

    @src.setter
    def src(self,v):
        self._src = v
        if self.src.startswith(b"http://") or self.src.startswith(b"https://"):
            # Define the DOWNLOADPROC type
            DOWNLOADPROC =  ctypes.WINFUNCTYPE(ctypes.c_void_p, ctypes.c_void_p, ctypes.c_ulong, ctypes.c_void_p) 
            self.stream = BASS_StreamCreateURL(self.src,0,0,DOWNLOADPROC(0),0)
        else:
            self.stream = BASS_StreamCreateFile(False,os.path.expandvars(self.src),0,0,0)

    @property
    def volume(self) -> float:
        return self._volume

    @volume.setter
    def volume(self,v):
        self._volume = v
        BASS_ChannelSetAttribute(self.stream,BASS_ATTRIB_VOL,self.volume)

    @property
    def loop(self) -> bool:
        return self._loop

    @loop.setter
    def loop(self,v):
        self._loop = v
        BASS_ChannelFlags(self.stream, BASS_SAMPLE_LOOP, BASS_SAMPLE_LOOP)

    @property
    def autoplay(self) -> bool:
        return self._autoplay

    @autoplay.setter
    def autoplay(self,v):
        self._autoplay = v
    
    def play(self):
        if BASS_ChannelIsActive(self.stream) == BASS_ACTIVE_PAUSED:
            BASS_ChannelStart(self.stream)
        elif BASS_ChannelIsActive(self.stream) == BASS_ACTIVE_STOPPED:
            BASS_ChannelPlay(self.stream, False)
    
    def pause(self):
        if BASS_ChannelIsActive(self.stream) == BASS_ACTIVE_PLAYING:
            BASS_ChannelPause(self.stream)
    
    def stop(self):
        BASS_ChannelStop(self.stream)

    def getFFTData(self,fft_buffer):
        BASS_ChannelGetData(self.stream, fft_buffer, BASS_DATA_FFT2048)
        return list(fft_buffer)


#Custom Class For Image Widget
class Image(QLabel):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.antialiasing = True
        self.autoScale = False
        self.radius = 0
        self.alt = None
        self._pixmap = None
        self.setScaledContents(True)  # Important for layout compatibility
        self.setMinimumSize(1, 1)

    def setRadius(self, radius):
        self.radius = radius
        self.update()

    def setAntialiasing(self, value):
        self.antialiasing = value
        self.update()
    
    def setAutoScale(self,value:bool):
        self.autoScale = value

    def setAlternative(self, value):
        self.alt = value

    def setPixmap(self, pixmap: QPixmap):
        self._pixmap = pixmap
        if self.autoScale and self._pixmap:
            size = self._pixmap.size()
            max_w = self.maximumWidth()
            max_h = self.maximumHeight()
            if max_w < 16777215 and max_h < 16777215:
                size.scale(max_w,max_h,Qt.AspectRatioMode.KeepAspectRatio)
            self.setFixedSize(size)
        self.update()

    def paintEvent(self, event):
        if not self._pixmap:
            return super().paintEvent(event)

        painter = QPainter(self)
        if self.antialiasing:
            painter.setRenderHint(QPainter.Antialiasing, True)
            painter.setRenderHint(QPainter.HighQualityAntialiasing, True)
            painter.setRenderHint(QPainter.SmoothPixmapTransform, True)

        path = QPainterPath()
        path.addRoundedRect(QRectF(self.rect()), self.radius, self.radius)
        painter.setClipPath(path)
        
        scaled = self._pixmap.scaled(self.size(), Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation) #Qt.KeepAspectRatioByExpanding
        painter.drawPixmap(self.rect(), scaled)

    def drawPixmap(self, src: str):
        if ImageCache.has(src):
            self.setPixmap(ImageCache.get(src))
        else:
            # Don't force width/height if autoScale is enabled
            w = self.width() if not self.autoScale else None
            h = self.height() if not self.autoScale else None
            loader = ImageLoader(self.parent(), src, w, h)
            loader.imageLoaded.connect(self.onImageReady)
            loader.start()

    def onImageReady(self, src: str, pixmap: QPixmap):
        if not pixmap.isNull():
            ImageCache.add(src, pixmap)
            self.setPixmap(pixmap)
        else:
            if self.alt:
                self.drawPixmap(self.alt)
            else:
                fallback = self.style().standardIcon(QStyle.SP_FileIcon).pixmap(self.size())
                self.setPixmap(fallback)


#Modern Switch Widget
class QSwitch(QAbstractButton):
    switched = pyqtSignal(bool)
    def __init__(self,*args,**kwargs):
        super().__init__(*args,**kwargs)
        self._position = 0.0
        self._duration = 200
        self._margin = 2
        self._switch_on = QColor("#00C853")
        self._switch_off = QColor("#9E9E9E")
        self._handle_col = QColor("#FFFFFF")
        
        self._animation = QPropertyAnimation(self,b"position",self)
        self._animation.setDuration(self._duration)
        self._animation.setEasingCurve(QEasingCurve.Type.InOutQuad)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

        self.setMinimumSize(60,30)
        self.setCheckable(True)
        self.toggled.connect(self._start_animation)
    
    def sizeHint(self):
        return QSize(60,30)
    
    @pyqtProperty(float)
    def position(self) -> float:
        return self._position
    
    @position.setter
    def position(self,val):
        self._position = val
        self.update()

    @pyqtProperty(int)
    def duration(self) -> int:
        return self._duration
    
    @duration.setter
    def duration(self,val):
        self._duration = val
        self.update()

    @pyqtProperty(int)
    def margin(self) -> int:
        return self._margin
    
    @margin.setter
    def margin(self,val):
        self._margin = val
        self.update()
    
    @pyqtProperty(QColor)
    def switchon(self) -> QColor:
        return self._switch_on
    
    @switchon.setter
    def switchon(self,val):
        self._switch_on = val
        self.update()

    @pyqtProperty(QColor)
    def switchoff(self) -> QColor:
        return self._switch_off
    
    @switchoff.setter
    def switchoff(self,val):
        self._switch_off = val
        self.update()

    @pyqtProperty(QColor)
    def handle(self) -> QColor:
        return self._handle_col
    
    @handle.setter
    def handle(self,val):
        self._handle_col = val
        self.update()
    
    def _start_animation(self,state):
        self._animation.stop()
        self._animation.setStartValue(self._position)
        self._animation.setEndValue(1.0 if state else 0.0)
        self._animation.setDuration(self._duration)
        self._animation.start()
    
        self.switched.emit(state)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        width = self.width()
        height = self.height()

        radius = self.height() / 2
        handle_radius =  radius - self._margin

        bg_color = self._switch_on if self.isChecked() else self._switch_off
        painter.setBrush(bg_color)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawRoundedRect(0,0,width,height,radius,radius)

        x_pos = int(self._margin + self._position * (width - 2 * (self._margin + handle_radius)))
        painter.setBrush(self._handle_col)
        painter.drawEllipse(x_pos,self._margin,int(handle_radius * 2), int(handle_radius * 2))


class CSlider(QAbstractSlider):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setOrientation(Qt.Orientation.Horizontal)
        self.setMinimum(0)
        self.setMaximum(100)
        self.setMouseTracking(True)
        self.setFocusPolicy(Qt.NoFocus)
        
        #Properties
        self._handle_radius = 10
        self._track_thickness = 6

        # Colors
        self._bg_color = QColor("#001144")
        self._highlight_color = QColor("#00bfff") 
        self._track_color = QColor("#0044dd")
        self._handle_border_color = QColor("#222222")
        self._handle_color = QColor("#33aaff")

    def sizeHint(self):
        return self.minimumSizeHint()

    def minimumSizeHint(self):
        if self.orientation() == Qt.Horizontal:
            return QSize(self._handle_radius * 4, self._handle_radius * 2)
        else:
            return QSize(self._handle_radius * 2, self._handle_radius * 4)
        
    @pyqtProperty(int)
    def hradius(self) -> int:
        return self._handle_radius
    
    @hradius.setter
    def hradius(self,val):
        self._handle_radius = val
        self.update()

    @pyqtProperty(int)
    def tthickness(self) -> int:
        return self._track_thickness
    
    @tthickness.setter
    def tthickness(self,val):
        self._track_thickness = val
        self.update()
    
    @pyqtProperty(QColor)
    def background(self) -> QColor:
        return self._bg_color
    
    @background.setter
    def background(self,val):
        self._bg_color = val
        self.update()

    @pyqtProperty(QColor)
    def track(self) -> QColor:
        return self._track_color
    
    @track.setter
    def track(self,val):
        self._track_color = val
        self.update()

    @pyqtProperty(QColor)
    def highlight(self) -> QColor:
        return self._highlight_color
    
    @highlight.setter
    def highlight(self,val):
        self._highlight_color = val
        self.update()

    @pyqtProperty(QColor)
    def handle(self) -> QColor:
        return self._handle_color
    
    @handle.setter
    def handle(self,val):
        self._handle_color = val
        self.update()

    @pyqtProperty(QColor)
    def handle_border(self) -> QColor:
        return self._handle_border_color
    
    @handle_border.setter
    def handle_border(self,val):
        self._handle_border_color = val
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.fillRect(self.rect(), self._bg_color)
        painter.setPen(Qt.NoPen)

        # Calculate track rect and handle position
        if self.orientation() == Qt.Horizontal:
            track_left = self._handle_radius
            track_width = self.width() - 2 * self._handle_radius
            track_y = self.height() / 2 - self._track_thickness / 2
            track_rect = QRectF(track_left, track_y, track_width, self._track_thickness)

            handle_x = track_left + (track_width * (self.value() - self.minimum()) / (self.maximum() - self.minimum()))
            handle_center = QPointF(handle_x, self.height() / 2)

            # Highlight portion
            highlight_rect = QRectF(track_left, track_y, handle_x - track_left, self._track_thickness)
            base_rect = QRectF(handle_x, track_y, track_rect.right() - handle_x, self._track_thickness)
        else:
            track_top = self._handle_radius
            track_height = self.height() - 2 * self._handle_radius
            track_x = self.width() / 2 - self._track_thickness / 2
            track_rect = QRectF(track_x, track_top, self._track_thickness, track_height)

            handle_y = track_rect.bottom() - (track_height * (self.value() - self.minimum()) / (self.maximum() - self.minimum()))
            handle_center = QPointF(self.width() / 2, handle_y)

            # Highlight portion
            highlight_rect = QRectF(track_x, handle_y, self._track_thickness, track_rect.bottom() - handle_y)
            base_rect = QRectF(track_x, track_top, self._track_thickness, handle_y - track_top)

        # Draw base track (after handle)
        painter.setBrush(self._track_color)
        painter.drawRoundedRect(base_rect, 3, 3)

        # Draw highlight track (before handle)
        painter.setBrush(self._highlight_color)
        painter.drawRoundedRect(highlight_rect, 3, 3)

        # Draw handle
        painter.setBrush(self._handle_color)
        painter.setPen(QPen(self._handle_border_color, 4))
        painter.drawEllipse(handle_center, self._handle_radius, self._handle_radius)

    def mousePressEvent(self, event):
        self._update_value_from_pos(event.pos())
        self.update()

    def mouseMoveEvent(self, event):
        if event.buttons() & Qt.LeftButton:
            self._update_value_from_pos(event.pos())
            self.update()

    def _update_value_from_pos(self, pos):
        if self.orientation() == Qt.Horizontal:
            usable_width = self.width() - 2 * self._handle_radius
            if usable_width <= 0:
                return
            ratio = (pos.x() - self._handle_radius) / usable_width
        else:
            usable_height = self.height() - 2 * self._handle_radius
            if usable_height <= 0:
                return
            ratio = 1 - ((pos.y() - self._handle_radius) / usable_height)

        ratio = max(0.0, min(1.0, ratio))
        new_value = int(self.minimum() + ratio * (self.maximum() - self.minimum()))
        self.setValue(new_value)


if __name__ == "__main__":
    app = QApplication([])
    slider = NeonGlide()
    slider.resize(400, 40)
    slider.show()
    app.exec_()
