"""
屏幕工具 — 截图与显示器信息

Windows 下使用 ctypes + gdi32 实现，不依赖 Pillow 等外部库。
"""
import ctypes
import os
import struct
import asyncio
from concurrent.futures import ThreadPoolExecutor
from typing import Dict, Any


# BITMAPFILEHEADER + BITMAPINFOHEADER 常量
_BI_RGB = 0
_DIB_RGB_COLORS = 0


def screen_info() -> Dict[str, Any]:
    """返回主显示器分辨率信息。"""
    user32 = ctypes.windll.user32
    width = user32.GetSystemMetrics(0)
    height = user32.GetSystemMetrics(1)
    return {
        "width": width,
        "height": height,
        "resolution": f"{width}x{height}",
    }


def _save_bitmap(hbitmap, width, height, path: str):
    """将 GDI 位图保存为 BMP 文件（Bottom-up DIB）。"""
    hdc = ctypes.windll.user32.GetDC(None)
    memdc = ctypes.windll.gdi32.CreateCompatibleDC(hdc)
    old = ctypes.windll.gdi32.SelectObject(memdc, hbitmap)

    row_size = ((width * 3 + 3) // 4) * 4
    pixel_data_size = row_size * height

    # BITMAPINFOHEADER (40 bytes)
    info_header = struct.pack(
        "<IIIHHIIIIII",
        40,          # biSize
        width,       # biWidth
        height,      # biHeight
        1,           # biPlanes
        24,          # biBitCount
        _BI_RGB,     # biCompression
        pixel_data_size,  # biSizeImage
        0, 0, 0, 0   # biXPelsPerMeter, biYPelsPerMeter, biClrUsed, biClrImportant
    )

    # BITMAPFILEHEADER (14 bytes)
    file_header = struct.pack(
        "<2sIHHI",
        b"BM",
        14 + 40 + pixel_data_size,  # bfSize
        0,                          # bfReserved1
        0,                          # bfReserved2
        14 + 40                     # bfOffBits
    )

    # 读取像素数据（BMP 是 bottom-up，GDI 也是 bottom-up，直接按行读取即可）
    buf = ctypes.create_string_buffer(pixel_data_size)
    ctypes.windll.gdi32.GetDIBits(
        memdc, hbitmap, 0, height, buf,
        info_header, _DIB_RGB_COLORS,
    )

    ctypes.windll.gdi32.SelectObject(memdc, old)
    ctypes.windll.gdi32.DeleteDC(memdc)
    ctypes.windll.user32.ReleaseDC(None, hdc)

    os.makedirs(os.path.dirname(os.path.abspath(path)) or ".", exist_ok=True)
    with open(path, "wb") as f:
        f.write(file_header)
        f.write(info_header)
        f.write(buf.raw)


def screen_capture(path: str = "screenshot.bmp") -> Dict[str, Any]:
    """
    截取主屏幕并保存为 BMP 文件。

    Args:
        path: 保存路径，默认 screenshot.bmp

    Returns:
        {"path": 绝对路径, "width": 宽, "height": 高, "format": "bmp"}
    """
    user32 = ctypes.windll.user32
    gdi32 = ctypes.windll.gdi32

    hdc = user32.GetDC(None)
    width = user32.GetSystemMetrics(0)
    height = user32.GetSystemMetrics(1)

    memdc = gdi32.CreateCompatibleDC(hdc)
    hbitmap = gdi32.CreateCompatibleBitmap(hdc, width, height)
    old = gdi32.SelectObject(memdc, hbitmap)

    # SRCCOPY = 0x00CC0020
    gdi32.BitBlt(memdc, 0, 0, width, height, hdc, 0, 0, 0x00CC0020)

    gdi32.SelectObject(memdc, old)
    gdi32.DeleteDC(memdc)
    user32.ReleaseDC(None, hdc)

    abs_path = os.path.abspath(path)
    _save_bitmap(hbitmap, width, height, abs_path)
    gdi32.DeleteObject(hbitmap)

    return {
        "path": abs_path,
        "width": width,
        "height": height,
        "format": "bmp",
    }


async def arun_screen_capture(path: str = "screenshot.bmp", cpu_executor: ThreadPoolExecutor = None) -> Dict[str, Any]:
    """screen_capture 的异步包装，避免阻塞事件循环。"""
    loop = asyncio.get_event_loop()
    if cpu_executor is not None:
        return await loop.run_in_executor(cpu_executor, screen_capture, path)
    return await loop.run_in_executor(None, screen_capture, path)
