from PyQt5 import QtWidgets, QtGui


class ImageWidget(QtWidgets.QWidget):

    def __init__(self, imagePath, parent):
        super(ImageWidget, self).__init__(parent)
        self.picture = QtGui.QPixmap(imagePath)
        self.setSizePolicy(self.picture.width(), self.picture.height())
        self.setMinimumWidth(self.picture.width())
        self.setMinimumHeight(self.picture.height())

    def paintEvent(self, event):
        painter = QtGui.QPainter(self)
        painter.drawPixmap(0, 0, self.picture)


class TableWidget(QtWidgets.QTableWidget):

    def setImage(self, row, col, imagePath):
        image = ImageWidget(imagePath, self)
        self.setCellWidget(row, col, image)