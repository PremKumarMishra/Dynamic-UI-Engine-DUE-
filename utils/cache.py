from PyQt5.QtGui import QPixmap
class ImageCache:
    _cache_ = {}

    @classmethod
    def get(cls,src:str) -> QPixmap:
        return cls._cache_[src]
    
    @classmethod
    def add(cls,src:str,pixmap:QPixmap) -> None:
        cls._cache_[src] = pixmap

    @classmethod
    def has(cls,src:str) -> bool:
        return src in cls._cache_