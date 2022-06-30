import os
import sys
import regex
import string
import pytesseract
import pycpdflib as pypdf
from datetime import datetime
from time import sleep
from PIL import ImageFilter
from pytesseract import image_to_string
from pdf2image import convert_from_path
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QLineEdit, QFileDialog, QLabel, QShortcut,
    QDialog, QVBoxLayout, QTextEdit, QProgressBar, QPushButton, QScrollArea,
    QMessageBox, QWidget, QGridLayout,
    )
from PyQt5.QtCore import Qt, QObject, QThread, QThreadPool, pyqtSignal
from PyQt5.QtGui import QKeySequence

from utils.unskewImg import unskewImg
from dialogs import ManualInputDialog, VerificationDialog

clear_chars = string.printable[62:77] + string.printable[79:94]

'''
    TO DO LIST
    Prevent Memory Error when reading too large files
    Convert QTextEdit to QTextTable
    Add option to join singular files
    Make incremental progress grow based on file size and number of pages
'''

if getattr(sys, 'frozen', False) or globals().get('__compiled__', False):
    pytesseract.pytesseract.tesseract_cmd = r'Tesseract-OCR/tesseract.exe'
    poppler_path = r'Poppler/Library/bin'
    pypdf.loadDLL(r'dll/libpycpdf.dll')
else:
    poppler_path = r"C:\Users\ricardoribeiro\Documents\Git Hub\Python\Utilities\poppler\Library\bin"
    pypdf.loadDLL(r"C:\Users\ricardoribeiro\Documents\Git Hub\Python\Utilities\libpycpdf\libpycpdf.dll")


class MainWindow(QMainWindow):
    def __init__(self, parent=None, dropfile=None):
        super().__init__(parent)

        open_shortcut = QShortcut(QKeySequence(self.tr("Ctrl+O")), self)
        open_shortcut.activated.connect(self.fileSelect)

        self.toolbars = []
        self._filepath = []
        self.setWindowTitle("Separar e Renomear Pareceres")
        self.resize(800, 600)
        self.setAcceptDrops(True)
        self._createMenu()
        # self._createToolbar()
        self._addWidgets()
        self._createStatusBar()
        self.show()
        if dropfile:
            self._filepath.setText(dropfile)

    def dragEnterEvent(self, e):
        if e.mimeData().hasUrls():
            path = e.mimeData().urls()
            for file in path:
                if file.path().endswith('.pdf'):
                    e.accept()
                else:
                    e.ignore()
        else:
            e.ignore()

    def dropEvent(self, e):
        path = [x.toLocalFile() for x in e.mimeData().urls()]
        n = len(path)
        for i in range(n):
            self.checkRecurseFolder(path[i])

    def checkRecurseFolder(self, path):
        '''Recursively checks dropped folder for .pdf files'''
        if os.path.isfile(path):
            if '.pdf' in path:
                self.addToolBarBreak()
                self.addWidgetGroup(path)
        elif os.path.isdir(path):
            files = os.listdir(path)
            files.sort(key=self.num_sort)
            for f in files:
                if '.pdf' in f:
                    self.addToolBarBreak()
                    self.addWidgetGroup(f'{path}\\{f}')

    def _addWidgets(self):
        self._mainwidget = MainWidget(self)
        self.scroll = QScrollArea(self)
        self.scroll.setWidgetResizable(True)
        self.scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        self.scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.scroll.setWidget(self._mainwidget)
        self.setCentralWidget(self.scroll)

    def addWidgetGroup(self, filepath):
        self._mainwidget.addWidgetGroup(filepath)

    def _createMenu(self):
        self.menu = self.menuBar()
        self.menu.addAction('&Selecionar', self.fileSelect)
        self.menu.addAction('&Separar', self.split)
        self.menu.addAction('&Fechar', self.close)

    def _createStatusBar(self):
        self.status = self.statusBar()
        self.status.showMessage('Pronto!')

    def fileSelect(self):
        dlg = QFileDialog()
        dlg.setFileMode(QFileDialog.ExistingFiles)
        dlg.setAcceptMode(QFileDialog.AcceptOpen)
        filepath = dlg.getOpenFileNames(
            self, self.tr("Selecione os arquivos PDF"), "",
            self.tr("Arquivos PDF (*.pdf)")
        )
        if filepath[0]:
            n = len(filepath[0])
            filepath[0].sort()
            for i in range(n):
                self.addToolBarBreak()
                self.addWidgetGroup(filepath[0][i])
                self._filepath.append(filepath[0][i])

    def split(self):
        self._mainwidget.split()


class MainWidget(QWidget):
    def __init__(self, parent):
        super().__init__(parent)
        self.paths = {}
        self.widgetgroup = {}
        self.layout = QGridLayout(self)
        self.layout.setAlignment(Qt.AlignTop)
        self.setLayout(self.layout)

    def addWidgetGroup(self, filepath):
        label = QLabel(str(len(self.paths)+1) + ".")
        label.setMinimumWidth(20)
        path = QLineEdit(filepath)
        movefileup = QPushButton("↑")
        movefiledown = QPushButton("↓")
        movefileup.setMaximumWidth(20)
        movefiledown.setMaximumWidth(20)
        remove = QPushButton("Remover")
        remove.position = len(self.paths)
        movefileup.position = len(self.paths)
        movefiledown.position = len(self.paths)

        self.paths[len(self.paths)] = [label, path, movefileup, movefiledown, remove]
        
        self.layout.addWidget(label, len(self.paths), 0, 1, 1)
        self.layout.addWidget(movefileup, len(self.paths), 2, 1, 1)
        self.layout.addWidget(movefiledown, len(self.paths), 3, 1, 1)
        self.layout.addWidget(path, len(self.paths), 1, 1, 1)
        self.layout.addWidget(remove, len(self.paths), 4, 1, 1)

        remove.clicked.connect(self.removeWidgetGroup)
        movefileup.clicked.connect(self.moveFileUp)
        movefiledown.clicked.connect(self.moveFileDown)

        path.setFocus()

    def removeWidgetGroup(self):
        pos = self.sender().position
        for widget in self.paths[pos]:
            widget.deleteLater()
        del self.paths[pos]

    def moveFileUp(self):
        pos = self.sender().position
        try:
            self.paths[pos-1]
            pos2 = pos-1
        except KeyError:
            pos2 = len(self.paths)-1
        path1 = self.paths[pos][1].text()
        path2 = self.paths[pos2][1].text()
        self.paths[pos2][1].setText(path1)
        self.paths[pos][1].setText(path2)

    def moveFileDown(self):
        pos = self.sender().position
        try:
            self.paths[pos+1]
            pos2 = pos+1
        except KeyError:
            pos2 = 0
        path1 = self.paths[pos][1].text()
        path2 = self.paths[pos2][1].text()
        self.paths[pos2][1].setText(path1)
        self.paths[pos][1].setText(path2)

    def split(self):
        dlg = QFileDialog()
        savepath = dlg.getExistingDirectory(self,
                                            self.tr(
                                            "Selecione onde deseja salvar"),
                                            "")
        if savepath:
            QApplication.setOverrideCursor(Qt.WaitCursor)
            paths = [x[1][1].text() for x in self.paths.items()]
            dlg = ProgressDialog(self, paths, savepath)
            dlg.exec()
            QApplication.restoreOverrideCursor()


class ProgressDialog(QDialog):

    pause = pyqtSignal(bool)
    confirm = pyqtSignal(bool, list)
    save_signal = pyqtSignal(bool)

    def __init__(self, parent, pdffile, path, dpi=300):
        super().__init__(parent)

        self.setWindowTitle(r'0 % concluído')
        self.setModal(True)
        self.resize(500, 400)
        
        self.threadpool = QThreadPool()
        self.thread_1 = QThread()
        self.thread_2 = QThread()
        self.value = 0
        
        self.worker_1 = Worker(self, pdffile, path, dpi)
        self.worker_1.moveToThread(self.thread_1)

        self.worker_1.error.connect(self.error)
        self.worker_1.progress.connect(self.updateProgress)
        self.worker_1.text.connect(self.updateText)
        self.worker_1.label.connect(self.updateLabel)
        self.worker_1.identify.connect(self.ManualInputDialog)

        self.worker_2 = IncrementProgress(self)
        self.worker_2.moveToThread(self.thread_2)

        self.worker_2.value.connect(self.progressSlowly)
        
        self.thread_1.started.connect(self.worker_1.loop)
        self.thread_2.started.connect(self.worker_2.loop)
        self.thread_1.finished.connect(self.worker_1.deleteLater)
        self.thread_2.finished.connect(self.worker_2.deleteLater)

        self._addWidgets()
        try:
            self.thread_1.start()
            self.thread_2.start()
        except Exception as e:
            line_number = sys.exc_info()[-1].tb_lineno
            error = f'Linha: {line_number}\nErro: {e}'
            with open('errorlog.txt', 'a+') as f:
                f.write(error)
            self.updateProgress(0)
            self.error(e)

    def _addWidgets(self):
        self.label = QLabel(r"Separando arquivos")
        
        self.text = QTextEdit()
        self.text.setReadOnly(True)
        
        self.pbar = QProgressBar(self)
        self.pbar.setRange(0, 100)
        self.pbar.setValue(0)
        
        self.bt_ok = QPushButton('OK')
        self.bt_ok.setHidden(True)
        self.bt_ok.pressed.connect(self.close)
        
        self.bt_cancel = QPushButton('Cancelar')
        self.bt_cancel.pressed.connect(self.cancel)

        self.layout = QVBoxLayout()
        self.layout.addWidget(self.label)
        self.layout.addWidget(self.pbar)
        self.layout.addWidget(self.text)
        self.layout.addWidget(self.bt_cancel)
        self.layout.addWidget(self.bt_ok)
        self.setLayout(self.layout)
        self.show()

    def cancel(self):
        QApplication.restoreOverrideCursor()
        self.pause.emit(True)
        dlg = QMessageBox()
        dlg.setWindowTitle("Separar Pareceres")
        dlg.setInformativeText("Deseja realmente encerrar o processo?")
        dlg.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
        dlg.setDefaultButton(QMessageBox.No)
        match dlg.exec():
            case QMessageBox.Yes:
                save_dlg = QMessageBox()
                save_dlg.setWindowTitle("Separar Pareceres")
                save_dlg.setInformativeText("Deseja salvar os arquivos já separados?")
                save_dlg.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
                save_dlg.setDefaultButton(QMessageBox.Yes)
                self.save_signal.emit(save_dlg.exec() == QMessageBox.Yes)
            case QMessageBox.No:
                QApplication.setOverrideCursor(Qt.WaitCursor)
                self.pause.emit(False)

    def error(self, e):
        self.thread_1.exit()
        self.thread_2.exit()
        self.thread_2.terminate()
        self.text.insertHtml(f"<h2>Erro durante o processo!</h2>\n<p><h4>Erro:</h4>{e}</p>")
        QApplication.restoreOverrideCursor()
        self.bt_ok.setHidden(False)
        self.bt_cancel.setHidden(True)

    def progressSlowly(self, e):
        self.value += e
        self.updateProgress(self.value)

    def updateProgress(self, e):
        self.value = e
        self.setWindowTitle(rf'{self.value:.2f} % concluído')
        self.pbar.setValue(int(self.value))
        if e == 100:
            self.finish()

    def updateLabel(self, text):
        self.label.setText(text)

    def updateText(self, text):
        self.text.insertHtml(f"<p>{text}</p><br>")
        bar_max = self.text.verticalScrollBar().maximum()
        self.text.verticalScrollBar().setValue(bar_max)

    def ManualInputDialog(self, args):
        QApplication.restoreOverrideCursor()
        self.pause.emit(True)
        dlg = ManualInputDialog(args[0], args[1], args[2])
        if dlg.exec():
            self.confirm.emit(True, [dlg.registro.text(), dlg.nome.text()])
        else:
            self.confirm.emit(False, [None])
        self.pause.emit(False)
        QApplication.setOverrideCursor(Qt.WaitCursor)

    def finish(self):
        self.thread_1.exit()
        self.thread_2.exit()
        self.thread_2.terminate()
        QApplication.restoreOverrideCursor()
        self.bt_ok.setHidden(False)
        self.bt_cancel.setHidden(True)


class IncrementProgress(QObject):
    value = pyqtSignal(float)

    def __init__(self, owner):
        super().__init__()
        self.owner = owner
        self.paused = False
        self.owner.pause.connect(self.pause)

    def loop(self):
        while True:
            if not self.paused:
                self.value.emit(0.25)
            sleep(1)

    def pause(self, signal):
        self.paused = signal


class Worker(QObject):

    error = pyqtSignal(str)
    progress = pyqtSignal(float)
    text = pyqtSignal(str)
    label = pyqtSignal(str)
    identify = pyqtSignal(list)

    def __init__(self, owner, pdffile, path, dpi):
        super().__init__()
        self.owner = owner
        self.pdffile = pdffile
        self.path = path
        self.dpi = dpi
        self.waiting = False
        self.finish = False
        self.save = True
        self.owner.confirm.connect(self.defineContinue)
        self.owner.pause.connect(self.pause)
        self.owner.save_signal.connect(self.endProcess)

    def loop(self):
        try:
            outputs = self.OCR()
            if self.save:
                self.saveFiles(outputs)
        except Exception as e:
            line_number = sys.exc_info()[-1].tb_lineno
            error = f'Date:{datetime.now()}| Linha: {line_number}| Erro: {e}'
            with open('errorlog.txt', 'a+') as f:
                f.write(error)
            self.progress.emit(0)
            self.error.emit(error)
        self.progress.emit(100)
        
    def OCR(self):
        outputs = {}
        pages = 0
        imgs = [ ]
        i = 0
        merged = [ ]
        for f in self.pdffile:
            i += 1
            file = pypdf.fromFile(f, '')
            pages += pypdf.pages(file)
            self.label.emit(f"Lendo o arquivo selecionado {self.pdffile.index(f)+1}/{len(self.pdffile)}")
            imgs.extend(convert_from_path(f, dpi=self.dpi, poppler_path=poppler_path))
            self.progress.emit(i/len(self.pdffile)*40)
            merged.append(file)
        file = pypdf.mergeSimple(merged)
        self.text.emit(f"<b>Total de páginas:</b> {len(imgs)}")
        for img in imgs:
            while self.waiting:
                sleep(0.2)
            
            if self.finish:
                break

            registro = None
            nome = None
            page = imgs.index(img)+1
            
            self.label.emit(f"Página {page} de {len(imgs)}")
            self.text.emit(f"<b>Alinhando página:</b> {page}")
            image = unskewImg(img)
            image = image.crop((0, 130*self.dpi/200, image.width, 460*self.dpi/200)).filter(ImageFilter.SMOOTH_MORE)
            
            self.text.emit(f"<b>Identificando texto da página:</b> {page}")
            txt = image_to_string(image, config="--psm 6", lang='por')
            txt = regex.subn(f"[{regex.escape(clear_chars)}]", "", txt)[0]
            print(txt)
            self.progress.emit(((page)/pages*50)+40)
            try:
                registro = regex.search(r"(?i)(Registro:|Atendimento) (\d{7}|\d\.\d{3}\.\d{3})", txt)
                registro = registro[2].replace(".", "")
                nome = regex.search(r"(?i)iente:? ?([A-Za-z ]+)(\s|Atendimento|Registro)", txt)
                nome = regex.sub("\s+Atendimento", "", nome[1]).strip()
            except TypeError:
                self.waiting = True
                self.identify.emit([image, registro, nome])
                while self.waiting:
                    sleep(0.2)
                if self.confirm:
                    registro = self.values[0]
                    nome = self.values[1]
                else:
                    continue
            if not registro:
                continue
            self.text.emit(f"<b>Registro:</b> {registro}")
            self.text.emit(f"<b>Paciente:</b> {nome.upper()}")
            if registro in outputs.keys():
                outputs[registro]['writer'].append(pypdf.selectPages(file, [page]))
            else:
                outputs[registro] = {'name': f'{registro} - {nome.upper()}.pdf', 'writer': [pypdf.selectPages(file, [page])]}
        
        return outputs

    def saveFiles(self, outputs):
        for output in outputs.values():
            path = f"{self.path}/{output['name']}"
            merged = pypdf.mergeSimple(output['writer'])
            self.text.emit(f"<b>Salvando arquivo:</b> {output['name']}")
            pypdf.toFile(merged, f"{path}", False, False)
        for output in outputs.values():
            if len(output['writer']) < 2:
                self.text.emit(f"<b>{output['name']}</b> contém somente uma página!")
        self.finish = True

    def defineContinue(self, signal, values):
        self.waiting = False
        self.confirm = signal
        self.values = values

    def pause(self, signal):
        self.waiting = signal

    def endProcess(self, signal):
        self.waiting = False
        self.finish = True
        self.save = signal


if __name__ == '__main__':
    dropfile = sys.argv[1] if len(sys.argv) > 1 else None
    app = QApplication([])
    window = MainWindow(None, dropfile)
    window.show()
    app.exec_()
