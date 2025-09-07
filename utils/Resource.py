import ctypes
from ctypes import *
import time

#C Resource Structure For MORF
class Resource(Structure):
    _fields_ = [
        ("filename", c_char_p),
        ("namelen", c_int),
        ("filesize", c_long),
        ("data", POINTER(c_ubyte))
    ]


def loadResource(src:str) -> dict:
    #Return Dict
    res_dict = dict()

    # Load Resource
    dll = ctypes.CDLL("MORF.dll",winmode=0)

    # Set return types
    dll.listResource.restype = POINTER(Resource)
    dll.listResource.argtypes = [c_char_p, POINTER(c_int)]
    dll.freeResources.argtypes = [POINTER(Resource), c_int]

    # Call function
    count = c_int(0)
    resources = dll.listResource(src.encode(), byref(count))
    
    #Iterate Over Resource Structure
    for i in range(count.value):
        res = resources[i]
        buf = (c_ubyte * res.filesize).from_address(addressof(res.data.contents))
        res_dict[res.filename.decode()] = bytearray(buf)
    
    # Clean up
    dll.freeResources(resources, count)
    return res_dict
