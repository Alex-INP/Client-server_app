# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'application/client/client_gui.ui'
#
# Created by: PyQt5 UI code generator 5.15.0
#
# WARNING: Any manual changes made to this file will be lost when pyuic5 is
# run again.  Do not edit this file unless you know what you are doing.


from PyQt5 import QtCore, QtWidgets



class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        MainWindow.setObjectName("MainWindow")
        MainWindow.resize(810, 639)
        self.centralwidget = QtWidgets.QWidget(MainWindow)
        self.centralwidget.setObjectName("centralwidget")
        self.lineEdit = QtWidgets.QLineEdit(self.centralwidget)
        self.lineEdit.setGeometry(QtCore.QRect(15, 470, 491, 81))
        self.lineEdit.setObjectName("lineEdit")
        self.sendButton = QtWidgets.QPushButton(self.centralwidget)
        self.sendButton.setGeometry(QtCore.QRect(20, 570, 111, 31))
        self.sendButton.setObjectName("sendButton")
        self.addContactButton = QtWidgets.QPushButton(self.centralwidget)
        self.addContactButton.setGeometry(QtCore.QRect(530, 570, 111, 31))
        self.addContactButton.setObjectName("addContactButton")
        self.deleteContactButton = QtWidgets.QPushButton(self.centralwidget)
        self.deleteContactButton.setGeometry(QtCore.QRect(680, 570, 111, 31))
        self.deleteContactButton.setObjectName("deleteContactButton")
        self.usernameLabel = QtWidgets.QLabel(self.centralwidget)
        self.usernameLabel.setGeometry(QtCore.QRect(20, 2, 481, 41))
        self.usernameLabel.setObjectName("usernameLabel")

        self.contactsLabel = QtWidgets.QLabel(self.centralwidget)
        self.contactsLabel.setGeometry(QtCore.QRect(530, 2, 481, 41))
        self.contactsLabel.setObjectName("usernameLabel")

        self.chatList = QtWidgets.QTableWidget(self.centralwidget)
        self.chatList.setGeometry(QtCore.QRect(15, 50, 491, 391))
        self.chatList.setObjectName("chatList")
        self.contactsList = QtWidgets.QListWidget(self.centralwidget)
        self.contactsList.setGeometry(QtCore.QRect(530, 50, 256, 501))
        self.contactsList.setObjectName("contactsList")
        MainWindow.setCentralWidget(self.centralwidget)
        self.statusbar = QtWidgets.QStatusBar(MainWindow)
        self.statusbar.setObjectName("statusbar")
        MainWindow.setStatusBar(self.statusbar)

        self.retranslateUi(MainWindow)
        QtCore.QMetaObject.connectSlotsByName(MainWindow)


    def retranslateUi(self, MainWindow):
        _translate = QtCore.QCoreApplication.translate
        MainWindow.setWindowTitle(_translate("MainWindow", "Messenger client"))
        self.sendButton.setText(_translate("MainWindow", "Send"))
        self.addContactButton.setText(_translate("MainWindow", "Add contact"))
        self.deleteContactButton.setText(_translate("MainWindow", "Delete contact"))
        self.usernameLabel.setText(_translate("MainWindow", "You are:"))
        self.contactsLabel.setText(_translate("MainWindow", "Contact list"))
