from PyQt5.QtCore import QThread
from abc import ABC,abstractmethod

#Singleton Thread Class Keeping Track Of All Threads In The Entire Program
class DThread(QThread):
    __threads__ = []
    def __init__(self,parent=None):
        super().__init__(parent)
        self.__class__.__threads__.append(self)
    
    @classmethod
    def getActiveThreads(cls):
        """Get All Active Threads"""
        return cls.__threads__
    
    @classmethod
    def terminateActiveThreads(cls):
        """Terminate All Active Threads And Empty Thread Cache"""
        for thread in cls.__threads__:
            thread.terminate()
            thread.deleteLater()
        cls.__threads__.clear()
    
    @abstractmethod
    def run(self):
        """SubClasses Must Implement This Abstract Function"""
        pass
