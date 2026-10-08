"""Export the existing vector artwork at KiCad toolbar sizes using wxPython."""
from pathlib import Path
import wx
import wx.svg


def render(root=None):
    root=Path(root or Path(__file__).resolve().parents[1]/'plugins')
    app=wx.App(False)
    artwork=wx.svg.SVGimage.CreateFromFile(str(root/'icon.svg'))
    for size in (24,48):
        bitmap=artwork.ConvertToBitmap(scale=size/64,width=size,height=size)
        path=root/f'toolbar-{size}.png'
        if not bitmap.SaveFile(str(path),wx.BITMAP_TYPE_PNG):
            raise RuntimeError(f'Could not save {path}')
        print(path)


if __name__=='__main__':
    render()
