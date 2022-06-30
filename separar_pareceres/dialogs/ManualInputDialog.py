import os
from PyQt5.QtWidgets import (
    QApplication, QLineEdit, QLabel, QDialog, QVBoxLayout, QPushButton, 
    QHBoxLayout, QScrollArea,
    )
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPixmap


class ManualInputDialog(QDialog):
    ''''''
    def __init__(self, image, registro, nome):
        super().__init__()
        self.setWindowTitle("Nomear manual")
        self.setModal(True)
        self.t_registro = QLabel('Registro:')
        self.registro = QLineEdit(registro)
        self.t_nome = QLabel('Nome:')
        self.nome = QLineEdit(nome)
        self.imglabel = QLabel()
        image.save(os.getenv("temp") + "/temp.jpg", "JPEG")
        self.img = QPixmap(os.getenv("temp") + "/temp.jpg")
        self.imglabel.setPixmap(self.img)
        self.confirm = QPushButton("Confirmar")
        self.cancel = QPushButton("Cancelar")

        self.confirm.pressed.connect(self.accept)
        self.cancel.pressed.connect(self.reject)

        scrollArea = ScrollArea()
        scrollArea.setWidget(self.imglabel)

        self.hlayout1 = QHBoxLayout()
        self.hlayout1.addWidget(self.t_nome)
        self.hlayout1.addWidget(self.nome)
        self.hlayout1.addWidget(self.t_registro)
        self.hlayout1.addWidget(self.registro)
        
        self.hlayout2 = QHBoxLayout()
        self.hlayout2.addWidget(self.confirm)
        self.hlayout2.addWidget(self.cancel)

        self.layout = QVBoxLayout()
        self.layout.addLayout(self.hlayout1)
        self.layout.addWidget(scrollArea)
        self.layout.addLayout(self.hlayout2)
        self.setLayout(self.layout)


class ScrollArea(QScrollArea):
    def __init__(self):
        super().__init__()

    def wheelEvent(self, evt):

        delta = evt.angleDelta().y()

        if evt.modifiers() == Qt.ShiftModifier:
            x = self.horizontalScrollBar().value()
            self.horizontalScrollBar().setValue(x - delta)
        else:
            y = self.verticalScrollBar().value()
            self.verticalScrollBar().setValue(y - delta)


if __name__ == '__main__':
    app = QApplication([])
    window = ManualInputDialog(None, img, None, None)
    window.show()
    app.exec_()
