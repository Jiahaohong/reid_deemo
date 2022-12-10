# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'model_zoo.ui'
#
# Created by: PyQt5 UI code generator 5.9.2
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets

class Ui_Dialog(object):
    

    def setupUi(self, Dialog):
        Dialog.setObjectName("Dialog")
        Dialog.resize(378, 306)
        self.verticalWidget = QtWidgets.QWidget(Dialog)
        self.verticalWidget.setGeometry(QtCore.QRect(60, 50, 241, 131))
        self.verticalWidget.setObjectName("verticalWidget")
        self.verticalLayout = QtWidgets.QVBoxLayout(self.verticalWidget)
        self.verticalLayout.setContentsMargins(1, 0, 0, 0)
        self.verticalLayout.setObjectName("verticalLayout")
        self.botton1 = QtWidgets.QRadioButton(self.verticalWidget)
        self.botton1.setObjectName("botton1")
        self.verticalLayout.addWidget(self.botton1)
        self.botton2 = QtWidgets.QRadioButton(self.verticalWidget)
        self.botton2.setObjectName("botton2")
        self.verticalLayout.addWidget(self.botton2)
        self.botton3 = QtWidgets.QRadioButton(self.verticalWidget)
        self.botton3.setObjectName("botton3")
        self.verticalLayout.addWidget(self.botton3)
        self.ok = QtWidgets.QPushButton(Dialog)
        self.ok.setGeometry(QtCore.QRect(60, 240, 241, 34))
        self.ok.setAutoDefault(False)
        self.ok.setObjectName("ok")

        self.retranslateUi(Dialog)
        QtCore.QMetaObject.connectSlotsByName(Dialog)

    def retranslateUi(self, Dialog):
        _translate = QtCore.QCoreApplication.translate
        Dialog.setWindowTitle(_translate("Dialog", "Dialog"))
        self.botton1.setText(_translate("Dialog", "DMRNet(AAAI21)"))
        self.botton2.setText(_translate("Dialog", "RDLR(ICCV19)"))
        self.botton3.setText(_translate("Dialog", "NAE(CVPR21)"))
        self.ok.setText(_translate("Dialog", "ok"))

