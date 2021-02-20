# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file '/Users/blogin/PycharmProjects/DMT-git/src/ui/ui_hw_setup_dlg.ui'
#
# Created by: PyQt5 UI code generator 5.9
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets


class Ui_HwSetupDlg(object):
    def setupUi(self, HwSetupDlg):
        HwSetupDlg.setObjectName("HwSetupDlg")
        HwSetupDlg.resize(492, 189)
        self.verticalLayout = QtWidgets.QVBoxLayout(HwSetupDlg)
        self.verticalLayout.setContentsMargins(8, 8, 8, 6)
        self.verticalLayout.setSpacing(8)
        self.verticalLayout.setObjectName("verticalLayout")
        self.gridLayout = QtWidgets.QGridLayout()
        self.gridLayout.setSpacing(4)
        self.gridLayout.setObjectName("gridLayout")
        self.btnEnDisPassAlwaysOnDevice = QtWidgets.QPushButton(HwSetupDlg)
        self.btnEnDisPassAlwaysOnDevice.setObjectName("btnEnDisPassAlwaysOnDevice")
        self.gridLayout.addWidget(self.btnEnDisPassAlwaysOnDevice, 3, 2, 1, 1)
        self.lblPinStatus = QtWidgets.QLabel(HwSetupDlg)
        self.lblPinStatus.setObjectName("lblPinStatus")
        self.gridLayout.addWidget(self.lblPinStatus, 1, 1, 1, 1)
        self.lblPassAlwaysOnDeviceLabel = QtWidgets.QLabel(HwSetupDlg)
        font = QtGui.QFont()
        font.setBold(True)
        font.setWeight(75)
        self.lblPassAlwaysOnDeviceLabel.setFont(font)
        self.lblPassAlwaysOnDeviceLabel.setObjectName("lblPassAlwaysOnDeviceLabel")
        self.gridLayout.addWidget(self.lblPassAlwaysOnDeviceLabel, 3, 0, 1, 1)
        self.btnEnDisPin = QtWidgets.QPushButton(HwSetupDlg)
        self.btnEnDisPin.setAutoDefault(False)
        self.btnEnDisPin.setObjectName("btnEnDisPin")
        self.gridLayout.addWidget(self.btnEnDisPin, 1, 2, 1, 1)
        self.lblPassStatusLabel = QtWidgets.QLabel(HwSetupDlg)
        font = QtGui.QFont()
        font.setBold(True)
        font.setWeight(75)
        self.lblPassStatusLabel.setFont(font)
        self.lblPassStatusLabel.setObjectName("lblPassStatusLabel")
        self.gridLayout.addWidget(self.lblPassStatusLabel, 2, 0, 1, 1)
        self.lblPassStatus = QtWidgets.QLabel(HwSetupDlg)
        self.lblPassStatus.setObjectName("lblPassStatus")
        self.gridLayout.addWidget(self.lblPassStatus, 2, 1, 1, 1)
        self.lblFirmwareVersionLabel = QtWidgets.QLabel(HwSetupDlg)
        font = QtGui.QFont()
        font.setBold(True)
        font.setWeight(75)
        self.lblFirmwareVersionLabel.setFont(font)
        self.lblFirmwareVersionLabel.setObjectName("lblFirmwareVersionLabel")
        self.gridLayout.addWidget(self.lblFirmwareVersionLabel, 0, 0, 1, 1)
        self.lblVersion = QtWidgets.QLabel(HwSetupDlg)
        self.lblVersion.setMinimumSize(QtCore.QSize(128, 0))
        self.lblVersion.setObjectName("lblVersion")
        self.gridLayout.addWidget(self.lblVersion, 0, 1, 1, 3)
        self.btnChangePin = QtWidgets.QPushButton(HwSetupDlg)
        self.btnChangePin.setAutoDefault(False)
        self.btnChangePin.setObjectName("btnChangePin")
        self.gridLayout.addWidget(self.btnChangePin, 1, 3, 1, 1)
        self.lblPinStatusLabel = QtWidgets.QLabel(HwSetupDlg)
        font = QtGui.QFont()
        font.setBold(True)
        font.setWeight(75)
        self.lblPinStatusLabel.setFont(font)
        self.lblPinStatusLabel.setObjectName("lblPinStatusLabel")
        self.gridLayout.addWidget(self.lblPinStatusLabel, 1, 0, 1, 1)
        self.lblPassAlwaysOnDeviceStatus = QtWidgets.QLabel(HwSetupDlg)
        self.lblPassAlwaysOnDeviceStatus.setObjectName("lblPassAlwaysOnDeviceStatus")
        self.gridLayout.addWidget(self.lblPassAlwaysOnDeviceStatus, 3, 1, 1, 1)
        self.btnEnDisPass = QtWidgets.QPushButton(HwSetupDlg)
        self.btnEnDisPass.setAutoDefault(False)
        self.btnEnDisPass.setObjectName("btnEnDisPass")
        self.gridLayout.addWidget(self.btnEnDisPass, 2, 2, 1, 1)
        self.btnEnDisWipeCode = QtWidgets.QPushButton(HwSetupDlg)
        self.btnEnDisWipeCode.setObjectName("btnEnDisWipeCode")
        self.gridLayout.addWidget(self.btnEnDisWipeCode, 4, 2, 1, 1)
        self.lblWipeCodeLabel = QtWidgets.QLabel(HwSetupDlg)
        font = QtGui.QFont()
        font.setBold(True)
        font.setWeight(75)
        self.lblWipeCodeLabel.setFont(font)
        self.lblWipeCodeLabel.setObjectName("lblWipeCodeLabel")
        self.gridLayout.addWidget(self.lblWipeCodeLabel, 4, 0, 1, 1)
        self.lblWipeCodeStatus = QtWidgets.QLabel(HwSetupDlg)
        self.lblWipeCodeStatus.setObjectName("lblWipeCodeStatus")
        self.gridLayout.addWidget(self.lblWipeCodeStatus, 4, 1, 1, 1)
        self.verticalLayout.addLayout(self.gridLayout)
        self.lblMessage = QtWidgets.QLabel(HwSetupDlg)
        self.lblMessage.setStyleSheet("color:red")
        self.lblMessage.setObjectName("lblMessage")
        self.verticalLayout.addWidget(self.lblMessage)
        self.buttonBox = QtWidgets.QDialogButtonBox(HwSetupDlg)
        self.buttonBox.setStandardButtons(QtWidgets.QDialogButtonBox.Ok)
        self.buttonBox.setObjectName("buttonBox")
        self.verticalLayout.addWidget(self.buttonBox)

        self.retranslateUi(HwSetupDlg)
        QtCore.QMetaObject.connectSlotsByName(HwSetupDlg)

    def retranslateUi(self, HwSetupDlg):
        _translate = QtCore.QCoreApplication.translate
        HwSetupDlg.setWindowTitle(_translate("HwSetupDlg", "Dialog"))
        self.btnEnDisPassAlwaysOnDevice.setText(_translate("HwSetupDlg", "Disable"))
        self.lblPinStatus.setText(_translate("HwSetupDlg", "enabled"))
        self.lblPassAlwaysOnDeviceLabel.setText(_translate("HwSetupDlg", "Passphrase always on device:"))
        self.btnEnDisPin.setText(_translate("HwSetupDlg", "Disable"))
        self.lblPassStatusLabel.setText(_translate("HwSetupDlg", "Passphrase:"))
        self.lblPassStatus.setText(_translate("HwSetupDlg", "enabled"))
        self.lblFirmwareVersionLabel.setText(_translate("HwSetupDlg", "Firmware version:"))
        self.lblVersion.setText(_translate("HwSetupDlg", "?"))
        self.lblMessage.setText(_translate("HwSetupDlg", "PIN/passphrase features is not available for Ledger devices."))
        self.btnChangePin.setText(_translate("HwSetupDlg", "Change"))
        self.lblPinStatusLabel.setText(_translate("HwSetupDlg", "PIN:"))
        self.lblPassAlwaysOnDeviceStatus.setText(_translate("HwSetupDlg", "enabled"))
        self.btnEnDisPass.setText(_translate("HwSetupDlg", "Disable"))
        self.btnEnDisWipeCode.setText(_translate("HwSetupDlg", "Disable"))
        self.lblWipeCodeLabel.setText(_translate("HwSetupDlg", "Wipe code:"))
        self.lblWipeCodeStatus.setText(_translate("HwSetupDlg", "enabled"))
        self.lblMessage.setText(_translate("HwSetupDlg", "PIN/passphrase features is not available for Ledger devices."))
