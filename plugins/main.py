"""KiCad IPC action entrypoint."""
from pathlib import Path
import sys
import traceback
import tempfile

sys.path.insert(0, str(Path(__file__).resolve().parent))


def main():
    import wx
    app = wx.App(False)
    try:
        from adapter import KiCadAdapter
        from gui import MainFrame
        frame = MainFrame(KiCadAdapter())
        frame.Show()
        app.MainLoop()
    except Exception as error:
        Path(tempfile.gettempdir(), 'shark-layout-clone-error.log').write_text(traceback.format_exc(), encoding='utf-8')
        from i18n import tr
        wx.MessageBox(tr('KiCad PCB düzenleyicisiyle bağlantı kurulamadı.\n'
                      'PCB açık olmalı ve Tercihler → Genel → API içindeki API sunucusu etkin olmalı.\n\n'+str(error)),
                      tr('Yerleşim Kopyala'), wx.OK | wx.ICON_ERROR)


if __name__ == '__main__':
    main()
