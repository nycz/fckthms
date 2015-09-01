#!/usr/bin/env python3

from collections import OrderedDict
import re

from PyQt4 import QtGui, QtCore
from PyQt4.QtCore import Qt

from libsyntyche import common

from canvas import Canvas

class MainWindow(QtGui.QFrame):
    def __init__(self, themefile, activation_event):
        super().__init__()
        self.setWindowTitle('fckthms and not in a good way')
        self.themefile = themefile
        activation_event.connect(self.reload_data)
        layout = QtGui.QHBoxLayout(self)
        common.kill_theming(layout)
        paintstack = generate_paintstack(themefile)
        self.listwidget = ColorList(self, paintstack)
        self.canvas = Canvas(self, paintstack, self.listwidget.get_color)
        self.listwidget.request_repaint.connect(self.canvas.update)
        layout.addWidget(self.canvas, stretch=1)
        listlayout = QtGui.QVBoxLayout()
        common.kill_theming(listlayout)
        listlayout.addWidget(self.listwidget, stretch=0)
        listlayout.addStretch(stretch=1)
        layout.addLayout(listlayout)
        self.show()

    def reload_data(self):
        paintstack = generate_paintstack(self.themefile)
        self.canvas.update_paintstack(paintstack)
        self.listwidget.update_list(paintstack)


class ColorList(QtGui.QListWidget):
    request_repaint = QtCore.pyqtSignal()

    def __init__(self, parent, paintstack):
        super().__init__(parent)
        self.itemEntered.connect(self.focus_item)
        self.update_list(paintstack)
        self.setMouseTracking(True)
        self.setSelectionMode(QtGui.QListWidget.NoSelection)
        self.setStyleSheet('QListView {outline: 0;}')
        self.selected = None

    def update_list(self, paintstack):
        self.clear()
        self.colors = OrderedDict()
        for cmd in paintstack:
            if cmd['name'] != 'color':
                continue
            self.colors[cmd['id']] = {
                'def color': cmd['color'],
                'color': cmd['color'],
                'title': cmd['title'],
                'setting': cmd['setting']
            }
            self.addItem(cmd['title'])
        self.setMaximumHeight(self.sizeHintForRow(0)*self.count() + 2*self.frameWidth())

    def get_color(self, index):
        if self.selected == index:
            return 'red'
        else:
            return self.colors[index]['color']

    def focus_item(self, item):
        return
        i = self.row(item)
        self.selected = list(self.colors.keys())[i]
        self.request_repaint.emit()

    def leaveEvent(self, ev):
        self.selected = None
        self.request_repaint.emit()


def generate_paintstack(fname):
    """
    Extract all relevant lines (not empty non-comment) from the theme file
    and return a list of each line split in relevant chunks.
    """
    with open(fname) as f:
        lines = [l.rstrip('\n') for l in f.readlines()
                 if not l.startswith('#') and l.rstrip()]
    options = {
        'coord': r'\d+((\.\d+)?%)?([+-]\d+((\.\d+)?%)?)?',
        'color': r'([a-z]+|#[0-9a-f]{3}([0-9a-f]{3})?)',
        'string': r'[^"]+',
        'align': r'((?i)c|nw|n|ne|e|se|s|sw|w)',
        'fontstyle': r'(normal|{styles}(\|{styles})*)'.format(styles='(bold|italic|strikethrough|underline)')
    }

    regexes = [
        r'(?P<name>fill) (?P<id>\S+) (?P<x>{coord}) (?P<y>{coord}) (?P<w>{coord}) (?P<h>{coord})',
        r'(?P<name>text) (?P<id>\S+) (?P<x>{coord}) (?P<y>{coord}) (?P<w>{coord}) (?P<h>{coord}) (?P<align>{align}) "(?P<text>{string})"',
        r'(?P<name>font) "(?P<family>{string})" (?P<size>\d+(\.\d+)?) (?P<style>{fontstyle})',
        r'(?P<name>color) (?P<id>\S+) "(?P<title>{string})" "(?P<setting>{string})" (?P<color>{color})'
    ]

    out = []
    for l in lines:
        for rx in regexes:
            match = re.fullmatch(rx.format(**options), l)
            if match:
                out.append(match.groupdict())
                break
        else:
            print('NO MATCH', l)
    return out


def main():
    import argparse, os.path, sys
    parser = argparse.ArgumentParser()
    def valid_file(fname):
        if os.path.isfile(fname):
            return fname
        parser.error('File does not exist: {}'.format(fname))
    parser.add_argument('file', type=valid_file)
    args = parser.parse_args()
    app = QtGui.QApplication([])
    class AppEventFilter(QtCore.QObject):
        activation_event = QtCore.pyqtSignal()
        def eventFilter(self, object, event):
            if event.type() == QtCore.QEvent.ApplicationActivate:
                self.activation_event.emit()
            return False
    app.event_filter = AppEventFilter()
    app.installEventFilter(app.event_filter)

    window = MainWindow(args.file, app.event_filter.activation_event)

    app.setActiveWindow(window)
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
