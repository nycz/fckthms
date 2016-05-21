#!/usr/bin/env python3

from collections import OrderedDict
import re
import sys

from typing import Dict, List

from PyQt4 import QtGui, QtCore
from PyQt4.QtCore import Qt

from libsyntyche import common

from canvas import Canvas

class MainWindow(QtGui.QFrame):
    def __init__(self, themefile, styleconfig, activation_event):
        super().__init__()
        self.setWindowTitle('fckthms and not in a good way')
        self.themefile = themefile
        validate_theme(themefile, styleconfig)
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
        listlayout.addWidget(self.listwidget)
        highlightbtn = QtGui.QPushButton('Highlight items')
        highlightbtn.setCheckable(True)
        highlightbtn.toggled.connect(self.listwidget.set_highlight)
        listlayout.addWidget(highlightbtn)
        colorbtn = QtGui.QPushButton('Set color')
        colorbtn.clicked.connect(self.listwidget.set_color)
        listlayout.addWidget(colorbtn)
        resetbtn = QtGui.QPushButton('Reset color')
        resetbtn.clicked.connect(self.listwidget.reset_color)
        listlayout.addWidget(resetbtn)
        layout.addLayout(listlayout)
        self.show()

    def reload_data(self):
        paintstack = generate_paintstack(self.themefile)
        self.canvas.update_paintstack(paintstack)
        self.listwidget.update_list(paintstack)


def validate_theme(themefile: str, styleconfig: Dict[str, str]) -> None:
    rx = r'color \S+ "[^"]+" "([^"]+)" \S+\s*'
    with open(themefile) as f:
        rawsettings = [re.fullmatch(rx, l).group(1) for l in f.readlines()
                       if l.startswith('color')]
    settings = set(rawsettings)
    if len(rawsettings) != len(settings):
        print('WARNING: some colors where defined twice')
    styleconfig = common.read_json(styleconfig)
    rest = settings - set(styleconfig.keys())
    if rest:
        print('ERROR: some colors wasn\'t found in the styleconfig:')
        print(*rest, sep='\n')
        sys.exit(1)


class ColorList(QtGui.QListWidget):
    request_repaint = QtCore.pyqtSignal()

    def __init__(self, parent, paintstack):
        super().__init__(parent)
        self.highlight = False
        self.colors = None
        self.itemSelectionChanged.connect(self.request_repaint.emit)
        # self.itemEntered.connect(self.focus_item)
        #self.buttons = []
        #self.mainwidget = QtGui.QWidget(self)
        #self.layout = QtGui.QVBoxLayout(self.mainwidget)
        #common.kill_theming(self.layout)
        #self.layout.addStretch()
        # self.mainwidget.setLayout(self.layout)
        #self.setWidget(self.mainwidget)
        #self.setWidgetResizable(True)
        self.update_list(paintstack)
        # self.setMouseTracking(True)
        self.setSelectionMode(QtGui.QListWidget.ExtendedSelection)
        #self.setStyleSheet('QPushButton {outline: 0;}')
        # self.selected = None

    def update_list(self, paintstack):
        oldcolors = self.colors
        self.colors = OrderedDict()
        n = 0
        for cmd in paintstack:
            if cmd['name'] != 'color':
                continue
            self.colors[cmd['id']] = {
                'num': n, # UGLY PIECE OF SHIT
                'def color': cmd['color'],
                'color': oldcolors[cmd['id']]['color'] if oldcolors is not None else cmd['color'],
                'title': cmd['title'],
                'setting': cmd['setting'],
            }
            n += 1 # need to do this b/c the continue part
        self.clear()
        self.addItems([x['title'] for x in self.colors.values()])
        #while len(self.colors) > len(self.buttons):
        #    b = QtGui.QPushButton('')
        #    b.setFixedHeight(20)
        #    b.setFlat(True)
        #    b.setStyleSheet('QPushButton {outline: 0;}')
        #    self.buttons.append(b)
        #    self.layout.insertWidget(self.layout.count()-1,b)
        #while len(self.colors) < len(self.buttons):
        #    b = self.buttons.pop()
        #    self.layout.removeWidget(b)
        #for n, title in enumerate(sorted(x['title'] for x in self.colors.values())):
        #    self.buttons[n].setText(title)
        self.update()

            # self.addItem(cmd['title'])
        # self.setMaximumHeight(self.sizeHintForRow(0)*self.count() + 2*self.frameWidth())

    def set_highlight(self, checked):
        self.highlight = checked
        self.request_repaint.emit()

    def set_color(self, _):
        rows = self.selectionModel().selectedRows()
        if not rows:
            return
        if len(rows) == 1:
            defcolor = QtGui.QColor(list(self.colors.values())[rows[0].row()]['color'])
        else:
            defcolor = Qt.white
        color = QtGui.QColorDialog.getColor(defcolor)
        if not color.isValid():
            return
        colorkeys = list(self.colors.keys())
        for r in rows:
            index = colorkeys[r.row()]
            self.colors[index]['color'] = color.name()
        self.request_repaint.emit()

    def reset_color(self, _):
        rows = self.selectionModel().selectedRows()
        if not rows:
            return
        colorkeys = list(self.colors.keys())
        for r in rows:
            index = colorkeys[r.row()]
            self.colors[index]['color'] = self.colors[index]['def color']
        self.request_repaint.emit()

    def get_color(self, index: str):
        selmod = self.selectionModel()
        if self.highlight and selmod.isRowSelected(self.colors[index]['num'], self.rootIndex()):
        #print(self.selectedIndexes())
        #if self.indexAt(QtCore.QPoint(0,index)) in self.selectedIndexes() and self.highlight:
            return 'red'
        # if self.selected == index:
        #     return 'red'
        else:
            return self.colors[index]['color']

    def focus_item(self, item):
        i = self.row(item)
        self.selected = list(self.colors.keys())[i]
        self.request_repaint.emit()

    def leaveEvent(self, ev):
        self.selected = None
        self.request_repaint.emit()


def generate_paintstack(fname: str) -> List[Dict[str, str]]:
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

    out = [] # type: List[Dict[str, str]]
    for l in lines:
        for rx in regexes:
            match = re.fullmatch(rx.format(**options), l)
            if match:
                out.append(match.groupdict())
                break
        else:
            print('NO MATCH', l)
    return out


def main() -> None:
    import argparse, os.path, sys
    parser = argparse.ArgumentParser()
    def valid_file(fname: str) -> str:
        if os.path.isfile(fname):
            return fname
        parser.error('File does not exist: {}'.format(fname))
    parser.add_argument('theme', type=valid_file)
    parser.add_argument('styleconfig', type=valid_file)
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

    window = MainWindow(args.theme, args.styleconfig, app.event_filter.activation_event)

    app.setActiveWindow(window)
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
