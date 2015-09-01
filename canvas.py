import re

from PyQt4 import QtGui, QtCore
from PyQt4.QtGui import QBrush, QColor, QPen, QFont
from PyQt4.QtCore import pyqtSignal, Qt


class Canvas(QtGui.QWidget):

    def __init__(self, parent, paintstack, get_color):
        super().__init__(parent)
        self.paintstack = paintstack
        self.get_color = get_color
        self.show()

    def update_paintstack(self, paintstack):
        self.paintstack = paintstack
        self.update()

    def paintEvent(self, ev):
        p = QtGui.QPainter(self)
        p.setRenderHints(QtGui.QPainter.Antialiasing | QtGui.QPainter.TextAntialiasing)
        for cmd in self.paintstack:
            if cmd['name'] == 'fill':
                x = parse(cmd['x'], self.width())
                y = parse(cmd['y'], self.height())
                w = parse(cmd['w'], self.width())
                h = parse(cmd['h'], self.height())
                p.fillRect(x, y, w, h, QColor(self.get_color(cmd['id'])))
            elif cmd['name'] == 'font':
                f = QtGui.QFont(cmd['family'])
                f.setPixelSize(float(cmd['size']))
                styles = cmd['style'].split('|')
                if 'italic' in styles:
                    f.setItalic(True)
                if 'bold' in styles:
                    f.setWeight(QFont.Bold)
                if 'underline' in styles:
                    f.setUnderline(True)
                if 'strikethrough' in styles:
                    f.setStrikeOut(True)
                p.setFont(f)
            elif cmd['name'] == 'text':
                p.setPen(QColor(self.get_color(cmd['id'])))
                x = parse(cmd['x'], self.width())
                y = parse(cmd['y'], self.height())
                w = parse(cmd['w'], self.width())
                h = parse(cmd['h'], self.height())
                alignflags = parsealign(cmd['align'])
                p.drawText(x, y, w, h, alignflags, cmd['text'])
        p.end()

def parse(s, maxnum):
    # Normal numbers (positive ints) should be returned directly
    if s.isdigit():
        return int(s)
    # Expand/replace all percents
    def replace_percent(mo):
        return str(int(float(mo.group(1))*maxnum/100))
    s = re.sub(r'(\d+.?\d*)%', replace_percent, s)
    # Evaluate the shit if there's a plus or minus in the expression
    e = re.fullmatch(r'(\d+)(\+|-)(\d+)', s)
    if e:
        if e.group(2) == '+':
            return int(e.group(1)) + int(e.group(3))
        elif e.group(2) == '-':
            return int(e.group(1)) - int(e.group(3))
    elif s.isdigit():
        return int(s)
    else:
        raise ValueError('Incorrect format: {}'.format(s))

def parsealign(s):
    d = {
        'n': Qt.AlignTop|Qt.AlignHCenter,
        'ne': Qt.AlignTop|Qt.AlignRight,
        'e': Qt.AlignVCenter|Qt.AlignRight,
        'se': Qt.AlignRight|Qt.AlignBottom,
        's': Qt.AlignHCenter|Qt.AlignBottom,
        'sw': Qt.AlignLeft|Qt.AlignBottom,
        'w': Qt.AlignLeft|Qt.AlignVCenter,
        'nw': Qt.AlignLeft|Qt.AlignTop,
        'c': Qt.AlignCenter
    }
    return d[s.lower()]
