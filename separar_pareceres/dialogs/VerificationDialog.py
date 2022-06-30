import os
import pycpdflib as pypdf

from PyQt5.QtWidgets import (QApplication, QMainWindow, QToolBar, QSpinBox,
                             QLineEdit, QFileDialog, QLabel, QShortcut,
                             QDialog, QVBoxLayout, QTextEdit, QProgressBar,
                             QPushButton, QHBoxLayout, QScrollArea,
                             QMessageBox, QWidget, QGridLayout, QTableWidget,
                             QTableWidgetItem)
from PyQt5.QtCore import Qt, QObject, QThread, QThreadPool, pyqtSignal
from PyQt5.QtGui import QKeySequence, QPixmap
from pdf2image import convert_from_path
from PIL.ImageQt import ImageQt

from separar_pareceres.utils import TableWidget


class VerificationDialog(QDialog):
    '''Use this to add table with registry and name for each page
    table must be sortable, default sort is name add photo of name and registry
    on the side for verification'''
    def __init__(self, parent, data, file, savepath):
        super().__init__()
        self.setWindowTitle("Verificação")
        self.setModal(True)

        files = []
        for f in file:
            files.append(pypdf.fromFile(f, ''))
        self.file = pypdf.mergeSimple(files)
        self.savepath = savepath

        self.table = TableWidget(len(data), 5, self)
        self.table.setHorizontalHeaderLabels(["Página", "Registro", "Imagem",
                                              "Nome", "Imagem"])

        i = 0
        for item in data.keys():
            page = QTableWidgetItem(str(item))
            registro = QTableWidgetItem(str(data[item]['Registro'][0]))
            nome = QTableWidgetItem(str(data[item]['Nome'][0]))
            registro_img = data[item]['Registro'][1]
            nome_img = data[item]['Nome'][1]
            registro_img.save(os.getenv("temp") + "registro.jpg", "JPEG")
            nome_img.save(os.getenv("temp") + "nome.jpg", "JPEG")
            self.table.setItem(i, 0, page)
            self.table.setItem(i, 1, registro)  # Text
            self.table.setImage(i, 2, os.getenv("temp") + "registro.jpg")  # Image
            self.table.setItem(i, 3, nome)  # Text
            self.table.setImage(i, 4, os.getenv("temp") + "nome.jpg")  # Image
            i += 1
        
        self.table.resizeColumnsToContents()
        self.table.resizeRowsToContents()
        self.table.sortItems(3)

        self.confirm = QPushButton("Confirmar")
        self.confirm.pressed.connect(self.saveFiles)

        self.layout = QVBoxLayout(self)
        self.layout.addWidget(self.table)
        self.layout.addWidget(self.confirm)

        width = 0
        for column in range(self.table.columnCount()):
            width += self.table.columnWidth(column)
        self.resize(width, 600)

        self.exec()

    def saveFiles(self):
        output = {}
        for row in range(self.table.rowCount()):
            page = int(self.table.item(row, 0).text())
            registro = self.table.item(row, 1).text()
            nome = self.table.item(row, 3).text()
            name = f"{registro} - {nome.upper()}.pdf"
            if registro in output.keys():
                    output[registro]['writer'].append(pypdf.selectPages(self.file, [page]))
            else:
                output[registro] = {'name': f'{name}.pdf', 'writer': [pypdf.selectPages(self.file, [page])]}
        for file in output.values():
            path = f"{self.savepath}/{file['name']}"
            merged = pypdf.mergeSimple(file['writer'])
            pypdf.toFile(merged, f"{path}", False, False)
        self.close()

if __name__ == '__main__':
    app = QApplication([])
    window = VerificationDialog(None, {1: {'Registro': [5068792, None], 'Nome': ['ARI DE SA CARVALHO', None]}}, None, None)
    window.show()
    app.exec_()
