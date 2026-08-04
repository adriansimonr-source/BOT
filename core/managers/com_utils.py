import ctypes

import comtypes


IID_ICLOSABLE = comtypes.GUID(
    "{30D5A829-7FA4-4026-83BB-D75BAE4EA99E}"
)


def get_vtable(interface):
    return ctypes.cast(
        interface,
        ctypes.POINTER(ctypes.POINTER(ctypes.c_void_p)),
    ).contents


def release_com(interface):
    if not interface:
        return
    release = ctypes.WINFUNCTYPE(
        ctypes.c_ulong,
        ctypes.c_void_p,
    )(get_vtable(interface)[2])
    release(interface)


def close_winrt(interface):
    if not interface:
        return False

    query_interface = ctypes.WINFUNCTYPE(
        ctypes.HRESULT,
        ctypes.c_void_p,
        ctypes.POINTER(comtypes.GUID),
        ctypes.POINTER(ctypes.c_void_p),
    )(get_vtable(interface)[0])
    closable = ctypes.c_void_p()
    hr = query_interface(
        interface,
        ctypes.byref(IID_ICLOSABLE),
        ctypes.byref(closable),
    )
    if hr != 0 or not closable.value:
        return False

    try:
        close = ctypes.WINFUNCTYPE(
            ctypes.HRESULT,
            ctypes.c_void_p,
        )(get_vtable(closable)[6])
        return close(closable) == 0
    finally:
        release_com(closable)
