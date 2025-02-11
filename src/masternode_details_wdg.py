from typing import Callable, Optional

import bitcoin
from PyQt5 import QtCore
from PyQt5.QtCore import pyqtSlot, Qt, QTimer
from PyQt5.QtGui import QTextDocument
from PyQt5.QtWidgets import QWidget, QLineEdit, QMessageBox, QAction, QApplication, QActionGroup

import dash_utils
import hw_intf
from app_config import MasternodeConfig, DMN_ROLE_OWNER, DMN_ROLE_OPERATOR, DMN_ROLE_VOTING, InputKeyType, AppConfig
from app_defs import DispMessage, AppTextMessageType
from bip44_wallet import Bip44Wallet, BreakFetchTransactionsException
from common import CancelException
from dashd_intf import DashdInterface
from find_coll_tx_dlg import ListCollateralTxsDlg
from thread_fun_dlg import CtrlObject
from ui import ui_masternode_details_wdg
from wnd_utils import WndUtils


class WdgMasternodeDetails(QWidget, ui_masternode_details_wdg.Ui_WdgMasternodeDetails):
    name_modified = QtCore.pyqtSignal(object, str)
    data_changed = QtCore.pyqtSignal(object)
    role_modified = QtCore.pyqtSignal()
    label_width_changed = QtCore.pyqtSignal(int)
    app_text_message_sent = QtCore.pyqtSignal(int, str, object)

    def __init__(self, parent, app_config: AppConfig, dashd_intf: DashdInterface, hw_session: hw_intf.HwSessionInfo):
        QWidget.__init__(self, parent)
        ui_masternode_details_wdg.Ui_WdgMasternodeDetails.__init__(self)
        self.parent = parent
        self.app_config = app_config
        self.dashd_intf = dashd_intf
        self.hw_session = hw_session
        self.masternode = MasternodeConfig()  # temporary object to avoid changing attributes of the global
        # mn object, since user has the ability to cancel edition
        self.updating_ui = False
        self.edit_mode = False
        self.owner_key_invalid = False
        self.operator_key_invalid = False
        self.voting_key_invalid = False
        self.setupUi(self)

    def setupUi(self, widget: QWidget):
        ui_masternode_details_wdg.Ui_WdgMasternodeDetails.setupUi(self, self)
        WndUtils.set_icon(self.parent, self.btnShowOwnerPrivateKey, 'eye@16px.png')
        WndUtils.set_icon(self.parent, self.btnShowOperatorPrivateKey, 'eye@16px.png')
        WndUtils.set_icon(self.parent, self.btnShowVotingPrivateKey, 'eye@16px.png')
        WndUtils.set_icon(self.parent, self.btnCopyOwnerKey, 'content-copy@16px.png')
        WndUtils.set_icon(self.parent, self.btnCopyOperatorKey, 'content-copy@16px.png')
        WndUtils.set_icon(self.parent, self.btnCopyVotingKey, 'content-copy@16px.png')
        WndUtils.set_icon(self.parent, self.btnCopyProtxHash, 'content-copy@16px.png')
        WndUtils.set_icon(self.parent, self.btnShowCollateralPathAddress, 'eye@16px.png')

        self.act_view_as_owner_private_key = QAction('View as private key', self)
        self.act_view_as_owner_private_key.setData('privkey')
        self.act_view_as_owner_private_key.triggered.connect(self.on_owner_view_key_type_changed)
        self.act_view_as_owner_public_address = QAction('View as Dash address', self)
        self.act_view_as_owner_public_address.setData('address')
        self.act_view_as_owner_public_address.triggered.connect(self.on_owner_view_key_type_changed)
        self.act_view_as_owner_public_key = QAction('View as public key', self)
        self.act_view_as_owner_public_key.setData('pubkey')
        self.act_view_as_owner_public_key.triggered.connect(self.on_owner_view_key_type_changed)
        self.act_view_as_owner_public_key_hash = QAction('View as public key hash', self)
        self.act_view_as_owner_public_key_hash.setData('pubkeyhash')
        self.act_view_as_owner_public_key_hash.triggered.connect(self.on_owner_view_key_type_changed)
        self.ag_owner_key = QActionGroup(self)
        self.act_view_as_owner_private_key.setCheckable(True)
        self.act_view_as_owner_public_address.setCheckable(True)
        self.act_view_as_owner_public_key.setCheckable(True)
        self.act_view_as_owner_public_key_hash.setCheckable(True)
        self.act_view_as_owner_private_key.setActionGroup(self.ag_owner_key)
        self.act_view_as_owner_public_address.setActionGroup(self.ag_owner_key)
        self.act_view_as_owner_public_key.setActionGroup(self.ag_owner_key)
        self.act_view_as_owner_public_key_hash.setActionGroup(self.ag_owner_key)
        self.btnShowOwnerPrivateKey.addActions(
            (self.act_view_as_owner_private_key, self.act_view_as_owner_public_address,
             self.act_view_as_owner_public_key, self.act_view_as_owner_public_key_hash))

        self.act_view_as_voting_private_key = QAction('View as private key', self)
        self.act_view_as_voting_private_key.setData('privkey')
        self.act_view_as_voting_private_key.triggered.connect(self.on_voting_view_key_type_changed)
        self.act_view_as_voting_public_address = QAction('View as Dash address', self)
        self.act_view_as_voting_public_address.setData('address')
        self.act_view_as_voting_public_address.triggered.connect(self.on_voting_view_key_type_changed)
        self.act_view_as_voting_public_key = QAction('View as public key', self)
        self.act_view_as_voting_public_key.setData('pubkey')
        self.act_view_as_voting_public_key.triggered.connect(self.on_voting_view_key_type_changed)
        self.act_view_as_voting_public_key_hash = QAction('View as public key hash', self)
        self.act_view_as_voting_public_key_hash.setData('pubkeyhash')
        self.act_view_as_voting_public_key_hash.triggered.connect(self.on_voting_view_key_type_changed)
        self.ag_voting_key = QActionGroup(self)
        self.act_view_as_voting_private_key.setCheckable(True)
        self.act_view_as_voting_public_address.setCheckable(True)
        self.act_view_as_voting_public_key.setCheckable(True)
        self.act_view_as_voting_public_key_hash.setCheckable(True)
        self.act_view_as_voting_private_key.setActionGroup(self.ag_voting_key)
        self.act_view_as_voting_public_address.setActionGroup(self.ag_voting_key)
        self.act_view_as_voting_public_key.setActionGroup(self.ag_voting_key)
        self.act_view_as_voting_public_key_hash.setActionGroup(self.ag_voting_key)
        self.btnShowVotingPrivateKey.addActions((self.act_view_as_voting_private_key,
                                                 self.act_view_as_voting_public_address,
                                                 self.act_view_as_voting_public_key,
                                                 self.act_view_as_voting_public_key_hash))

        self.act_view_as_operator_private_key = QAction('View as private key', self)
        self.act_view_as_operator_private_key.setData('privkey')
        self.act_view_as_operator_private_key.triggered.connect(self.on_operator_view_key_type_changed)
        self.act_view_as_operator_public_key = QAction('View as public key', self)
        self.act_view_as_operator_public_key.setData('pubkey')
        self.act_view_as_operator_public_key.triggered.connect(self.on_operator_view_key_type_changed)
        self.ag_operator_key = QActionGroup(self)
        self.act_view_as_operator_private_key.setCheckable(True)
        self.act_view_as_operator_public_key.setCheckable(True)
        self.act_view_as_operator_private_key.setActionGroup(self.ag_operator_key)
        self.act_view_as_operator_public_key.setActionGroup(self.ag_operator_key)
        self.btnShowOperatorPrivateKey.addActions((self.act_view_as_operator_private_key,
                                                   self.act_view_as_operator_public_key))

        self.update_ui_controls_state()

    def showEvent(self, QShowEvent):
        def apply():
            self.update_key_controls_state()
            self.lblOwnerKey.fontMetrics()
            self.set_buttons_height()

        QTimer.singleShot(100, apply)

    def set_buttons_height(self):
        h = self.edtName.height()
        self.btnCopyOwnerKey.setFixedHeight(h)
        self.btnShowOwnerPrivateKey.setFixedHeight(h)
        self.btnGenerateOwnerPrivateKey.setFixedHeight(h)

        self.btnCopyOperatorKey.setFixedHeight(h)
        self.btnShowOperatorPrivateKey.setFixedHeight(h)
        self.btnGenerateOperatorPrivateKey.setFixedHeight(h)

        self.btnCopyVotingKey.setFixedHeight(h)
        self.btnShowVotingPrivateKey.setFixedHeight(h)
        self.btnGenerateVotingPrivateKey.setFixedHeight(h)
        self.btnCopyProtxHash.setFixedHeight(h)

        self.btnGetMNDataByIP.setFixedHeight(h)
        self.btnShowCollateralPathAddress.setFixedHeight(h)
        self.btnBip32PathToAddress.setFixedHeight(h)
        self.btnLocateCollateral.setFixedHeight(h)

    def update_ui_controls_state(self):
        """Update visibility and enabled/disabled state of the UI controls.
        """
        self.lblDMNTxHash.setVisible(self.masternode is not None)
        self.edtDMNTxHash.setVisible(self.masternode is not None)
        self.btnGetMNDataByIP.setVisible(self.masternode is not None and self.edit_mode)

        self.lblCollateral.setVisible(self.masternode is not None and
                                      (self.masternode.dmn_user_roles & DMN_ROLE_OWNER > 0))
        self.btnLocateCollateral.setVisible(self.masternode is not None and self.edit_mode and
                                            (self.masternode.dmn_user_roles & DMN_ROLE_OWNER > 0))
        self.btnBip32PathToAddress.setVisible(self.masternode is not None and self.edit_mode and
                                              (self.masternode.dmn_user_roles & DMN_ROLE_OWNER > 0))
        self.btnShowCollateralPathAddress.setVisible(self.masternode is not None and
                                                     (self.masternode.dmn_user_roles & DMN_ROLE_OWNER > 0))
        self.edtCollateralAddress.setVisible(self.masternode is not None and
                                             (self.masternode.dmn_user_roles & DMN_ROLE_OWNER > 0))
        self.lblCollateralPath.setVisible(self.masternode is not None and
                                          (self.masternode.dmn_user_roles & DMN_ROLE_OWNER > 0))
        self.edtCollateralPath.setVisible(self.masternode is not None and
                                          (self.masternode.dmn_user_roles & DMN_ROLE_OWNER > 0))

        self.lblOwnerKey.setVisible(self.masternode is not None and
                                    (self.masternode.dmn_user_roles & DMN_ROLE_OWNER > 0))
        self.edtOwnerKey.setVisible(self.masternode is not None and
                                    (self.masternode.dmn_user_roles & DMN_ROLE_OWNER > 0))
        self.btnShowOwnerPrivateKey.setVisible(self.masternode is not None and
                                               self.edit_mode is False and
                                               (self.masternode.dmn_user_roles & DMN_ROLE_OWNER > 0))
        self.btnCopyOwnerKey.setVisible(self.masternode is not None and
                                        (self.masternode.dmn_user_roles & DMN_ROLE_OWNER > 0))
        self.lblOperatorKey.setVisible(self.masternode is not None and
                                       (self.masternode.dmn_user_roles & DMN_ROLE_OPERATOR > 0))
        self.edtOperatorKey.setVisible(self.masternode is not None and
                                       (self.masternode.dmn_user_roles & DMN_ROLE_OPERATOR > 0))
        self.btnShowOperatorPrivateKey.setVisible(self.masternode is not None and
                                                  self.edit_mode is False and
                                                  (self.masternode.dmn_user_roles & DMN_ROLE_OPERATOR > 0))
        self.btnCopyOperatorKey.setVisible(self.masternode is not None and
                                           (self.masternode.dmn_user_roles & DMN_ROLE_OPERATOR > 0))
        self.lblVotingKey.setVisible(self.masternode is not None and
                                     (self.masternode.dmn_user_roles & DMN_ROLE_VOTING > 0))
        self.edtVotingKey.setVisible(self.masternode is not None and
                                     (self.masternode.dmn_user_roles & DMN_ROLE_VOTING > 0))
        self.btnShowVotingPrivateKey.setVisible(self.masternode is not None and
                                                self.edit_mode is False and
                                                (self.masternode.dmn_user_roles & DMN_ROLE_VOTING > 0))
        self.btnCopyVotingKey.setVisible(self.masternode is not None and
                                         (self.masternode.dmn_user_roles & DMN_ROLE_VOTING > 0))

        self.act_view_as_owner_private_key.setVisible(self.masternode is not None and
                                                      self.masternode.dmn_owner_key_type == InputKeyType.PRIVATE)
        self.act_view_as_owner_public_key.setVisible(self.masternode is not None and
                                                     self.masternode.dmn_owner_key_type == InputKeyType.PRIVATE)
        self.act_view_as_operator_private_key.setVisible(self.masternode is not None and
                                                         self.masternode.dmn_operator_key_type == InputKeyType.PRIVATE)
        self.act_view_as_voting_private_key.setVisible(self.masternode is not None and
                                                       self.masternode.dmn_voting_key_type == InputKeyType.PRIVATE)
        self.act_view_as_voting_public_key.setVisible(self.masternode is not None and
                                                      self.masternode.dmn_voting_key_type == InputKeyType.PRIVATE)

        self.btnGenerateOwnerPrivateKey.setVisible(
            self.masternode is not None and self.edit_mode and
            self.masternode.dmn_owner_key_type == InputKeyType.PRIVATE and
            self.masternode.dmn_user_roles & DMN_ROLE_OWNER > 0)

        self.btnGenerateOperatorPrivateKey.setVisible(
            self.masternode is not None and self.edit_mode and
            self.masternode.dmn_operator_key_type == InputKeyType.PRIVATE and
            self.masternode.dmn_user_roles & DMN_ROLE_OPERATOR > 0)

        self.btnGenerateVotingPrivateKey.setVisible(
            self.masternode is not None and self.edit_mode and
            self.masternode.dmn_voting_key_type == InputKeyType.PRIVATE and
            self.masternode.dmn_user_roles & DMN_ROLE_VOTING > 0)

        self.lblUserRole.setVisible(self.masternode is not None)
        self.chbRoleOwner.setVisible(self.masternode is not None)
        self.chbRoleOperator.setVisible(self.masternode is not None)
        self.chbRoleVoting.setVisible(self.masternode is not None)

        self.btnCopyProtxHash.setVisible(self.masternode is not None)

        # self.btnFindCollateral.setVisible(self.masternode is not None)
        self.lblIP.setVisible(self.masternode is not None)
        self.edtIP.setVisible(self.masternode is not None)
        self.lblPort.setVisible(self.masternode is not None)
        self.edtPort.setVisible(self.masternode is not None)
        self.lblName.setVisible(self.masternode is not None)
        self.edtName.setVisible(self.masternode is not None)
        self.lblCollateralTxHash.setVisible(self.masternode is not None)
        self.edtCollateralTxHash.setVisible(self.masternode is not None)
        self.lblCollateralTxIndex.setVisible(self.masternode is not None)
        self.edtCollateralTxIndex.setVisible(self.masternode is not None)

        self.chbRoleVoting.setEnabled(self.edit_mode)
        self.chbRoleOperator.setEnabled(self.edit_mode)
        self.chbRoleOwner.setEnabled(self.edit_mode)
        self.edtName.setReadOnly(self.edit_mode is False)
        self.edtIP.setReadOnly(self.edit_mode is False)
        self.edtPort.setReadOnly(self.edit_mode is False)
        self.edtCollateralAddress.setReadOnly(self.edit_mode is False)
        self.edtCollateralPath.setReadOnly(self.edit_mode is False)
        self.edtCollateralTxHash.setReadOnly(self.edit_mode is False)
        self.edtCollateralTxIndex.setReadOnly(self.edit_mode is False)
        self.edtDMNTxHash.setReadOnly(self.edit_mode is False)
        self.edtOwnerKey.setReadOnly(self.edit_mode is False)
        self.edtOperatorKey.setReadOnly(self.edit_mode is False)
        self.edtVotingKey.setReadOnly(self.edit_mode is False)
        self.btnGenerateOwnerPrivateKey.setEnabled(self.edit_mode is True)
        self.btnGenerateOperatorPrivateKey.setEnabled(self.edit_mode is True)
        self.btnGenerateVotingPrivateKey.setEnabled(self.edit_mode is True)
        self.btnLocateCollateral.setEnabled(self.edit_mode)
        col_btn_visible = self.masternode is not None and (not self.masternode.collateral_tx or
                                                           not self.masternode.collateral_address or
                                                           not self.masternode.collateral_bip32_path)
        self.update_key_controls_state()

    def update_dynamic_labels(self):
        def style_to_color(style: str) -> str:
            if style == 'hl1':
                color = 'color:#00802b'
            elif style == 'hl2':
                color = 'color:#0047b3'
            else:
                color = ''
            return color

        def get_label_text(prefix: str, cur_key_type: str, tooltip_anchor: str, group: QActionGroup, style: str,
                           error_msg: Optional[str] = None):
            lbl = '???'
            if self.edit_mode:
                change_mode = f'<td>(<a href="{tooltip_anchor}">use {tooltip_anchor}</a>)</td>'
            else:
                a = group.checkedAction()
                if a:
                    cur_key_type = a.data()
                change_mode = ''

            if cur_key_type == 'privkey':
                lbl = prefix + ' private key'
            elif cur_key_type == 'address':
                lbl = prefix + ' Dash address'
            elif cur_key_type == 'pubkey':
                lbl = prefix + ' public key'
            elif cur_key_type == 'pubkeyhash':
                lbl = prefix + ' public key hash'

            if error_msg:
                err = '<td style="color:red">' + error_msg + '</td>'
            else:
                err = ''
            return f'<table style="float:right;{style_to_color(style)}"><tr><td>{lbl}</td>{change_mode}{err}</tr></table>'

        if self.masternode:
            style = ''
            if self.masternode.dmn_owner_key_type == InputKeyType.PRIVATE:
                key_type, tooltip_anchor, placeholder_text = ('privkey', 'address', 'Enter the owner private key')
                if not self.edit_mode and not self.act_view_as_owner_private_key.isChecked():
                    style = 'hl2'
            else:
                key_type, tooltip_anchor, placeholder_text = ('address', 'privkey', 'Enter the owner Dash address')
                if not self.edit_mode:
                    style = 'hl1' if self.act_view_as_owner_public_address.isChecked() else 'hl2'
            self.lblOwnerKey.setText(get_label_text(
                'Owner', key_type, tooltip_anchor, self.ag_owner_key, style,
                '[invalid key format]' if self.owner_key_invalid else ''))
            self.edtOwnerKey.setPlaceholderText(placeholder_text)

            style = ''
            if self.masternode.dmn_operator_key_type == InputKeyType.PRIVATE:
                key_type, tooltip_anchor, placeholder_text = ('privkey', 'pubkey', 'Enter the operator private key')
                if not self.edit_mode and not self.act_view_as_operator_private_key.isChecked():
                    style = 'hl2'
            else:
                key_type, tooltip_anchor, placeholder_text = ('pubkey', 'privkey', 'Enter the operator public key')
                if not self.edit_mode:
                    style = 'hl1' if self.act_view_as_operator_public_key.isChecked() else 'hl2'
            self.lblOperatorKey.setText(get_label_text(
                'Operator', key_type, tooltip_anchor, self.ag_operator_key,
                style, '[invalid key format]' if self.operator_key_invalid else ''))
            self.edtOperatorKey.setPlaceholderText(placeholder_text)

            style = ''
            if self.masternode.dmn_voting_key_type == InputKeyType.PRIVATE:
                key_type, tooltip_anchor, placeholder_text = ('privkey', 'address', 'Enter the voting private key')
                if not self.edit_mode and not self.act_view_as_voting_private_key.isChecked():
                    style = 'hl2'
            else:
                key_type, tooltip_anchor, placeholder_text = ('address', 'privkey', 'Enter the voting Dash address')
                if not self.edit_mode:
                    style = 'hl1' if self.act_view_as_voting_public_address.isChecked() else 'hl2'
            self.lblVotingKey.setText(get_label_text(
                'Voting', key_type, tooltip_anchor, self.ag_voting_key, style,
                '[invalid key format]' if self.voting_key_invalid else ''))
            self.edtVotingKey.setPlaceholderText(placeholder_text)

            self.set_left_label_width(self.get_max_left_label_width())

    def update_key_controls_state(self):
        self.edtOwnerKey.setEchoMode(QLineEdit.Normal if self.btnShowOwnerPrivateKey.isChecked() or
                                                         self.edit_mode else QLineEdit.Password)

        self.edtOperatorKey.setEchoMode(QLineEdit.Normal if self.btnShowOperatorPrivateKey.isChecked() or
                                                            self.edit_mode else QLineEdit.Password)

        self.edtVotingKey.setEchoMode(QLineEdit.Normal if self.btnShowVotingPrivateKey.isChecked() or
                                                          self.edit_mode else QLineEdit.Password)

        self.update_dynamic_labels()

    def masternode_data_to_ui(self, reset_key_view_type: bool = False):
        if self.masternode:
            if self.masternode.dmn_owner_key_type == InputKeyType.PRIVATE:
                self.act_view_as_owner_private_key.setChecked(True)
            else:
                self.act_view_as_owner_public_address.setChecked(True)

            if self.masternode.dmn_operator_key_type == InputKeyType.PRIVATE:
                self.act_view_as_operator_private_key.setChecked(True)
            else:
                self.act_view_as_operator_public_key.setChecked(True)

            if self.masternode.dmn_voting_key_type == InputKeyType.PRIVATE:
                self.act_view_as_voting_private_key.setChecked(True)
            else:
                self.act_view_as_voting_public_address.setChecked(True)
            if reset_key_view_type:
                self.btnShowOwnerPrivateKey.setChecked(False)
                self.btnShowOperatorPrivateKey.setChecked(False)
                self.btnShowVotingPrivateKey.setChecked(False)

            self.chbRoleOwner.setChecked(self.masternode.dmn_user_roles & DMN_ROLE_OWNER)
            self.chbRoleOperator.setChecked(self.masternode.dmn_user_roles & DMN_ROLE_OPERATOR)
            self.chbRoleVoting.setChecked(self.masternode.dmn_user_roles & DMN_ROLE_VOTING)
            self.edtName.setText(self.masternode.name)
            self.edtIP.setText(self.masternode.ip)
            self.edtPort.setText(self.masternode.port)
            self.edtCollateralAddress.setText(self.masternode.collateral_address)
            self.edtCollateralPath.setText(self.masternode.collateral_bip32_path)
            self.edtCollateralTxHash.setText(self.masternode.collateral_tx)
            self.edtCollateralTxIndex.setText(self.masternode.collateral_tx_index)
            self.edtDMNTxHash.setText(self.masternode.dmn_tx_hash)
            self.edtOwnerKey.setText(self.get_owner_key_to_display())
            self.edtVotingKey.setText(self.get_voting_key_to_display())
            self.edtOperatorKey.setText(self.get_operator_key_to_display())
            self.updating_ui = False
            self.set_buttons_height()
        else:
            for e in self.findChildren(QLineEdit):
                e.setText('')
        self.update_ui_controls_state()

    def get_owner_key_to_display(self) -> str:
        ret = ''
        if self.masternode:
            if self.edit_mode:
                if self.masternode.dmn_owner_key_type == InputKeyType.PRIVATE:
                    ret = self.masternode.dmn_owner_private_key
                else:
                    ret = self.masternode.dmn_owner_address
            else:
                try:
                    if self.masternode.dmn_owner_key_type == InputKeyType.PRIVATE:
                        if self.act_view_as_owner_private_key.isChecked():
                            ret = self.masternode.dmn_owner_private_key
                        elif self.act_view_as_owner_public_address.isChecked():
                            if self.masternode.dmn_owner_private_key:
                                ret = dash_utils.wif_privkey_to_address(self.masternode.dmn_owner_private_key,
                                                                        self.app_config.dash_network)
                        elif self.act_view_as_owner_public_key.isChecked():
                            if self.masternode.dmn_owner_private_key:
                                ret = dash_utils.wif_privkey_to_pubkey(self.masternode.dmn_owner_private_key)
                        elif self.act_view_as_owner_public_key_hash.isChecked():
                            if self.masternode.dmn_owner_private_key:
                                pubkey = dash_utils.wif_privkey_to_pubkey(self.masternode.dmn_owner_private_key)
                                pubkey_bin = bytes.fromhex(pubkey)
                                pub_hash = bitcoin.bin_hash160(pubkey_bin)
                                ret = pub_hash.hex()
                        else:
                            ret = '???'
                    else:
                        if self.act_view_as_owner_public_address.isChecked():
                            ret = self.masternode.dmn_owner_address
                        elif self.act_view_as_owner_public_key_hash.isChecked():
                            ret = self.masternode.get_dmn_owner_pubkey_hash()
                        else:
                            ret = '???'
                except Exception as e:
                    msg = str(e)
                    if not msg:
                        msg = 'Key conversion error.'
                    WndUtils.error_msg(msg)

        return ret

    def get_voting_key_to_display(self) -> str:
        ret = ''
        if self.masternode:
            if self.edit_mode:
                if self.masternode.dmn_voting_key_type == InputKeyType.PRIVATE:
                    ret = self.masternode.dmn_voting_private_key
                else:
                    ret = self.masternode.dmn_voting_address
            else:
                try:
                    if self.masternode.dmn_voting_key_type == InputKeyType.PRIVATE:
                        if self.act_view_as_voting_private_key.isChecked():
                            ret = self.masternode.dmn_voting_private_key
                        elif self.act_view_as_voting_public_address.isChecked():
                            if self.masternode.dmn_voting_private_key:
                                ret = dash_utils.wif_privkey_to_address(self.masternode.dmn_voting_private_key,
                                                                        self.app_config.dash_network)
                        elif self.act_view_as_voting_public_key.isChecked():
                            if self.masternode.dmn_voting_private_key:
                                ret = dash_utils.wif_privkey_to_pubkey(self.masternode.dmn_voting_private_key)
                        elif self.act_view_as_voting_public_key_hash.isChecked():
                            if self.masternode.dmn_voting_private_key:
                                pubkey = dash_utils.wif_privkey_to_pubkey(self.masternode.dmn_voting_private_key)
                                pubkey_bin = bytes.fromhex(pubkey)
                                pub_hash = bitcoin.bin_hash160(pubkey_bin)
                                ret = pub_hash.hex()
                        else:
                            ret = '???'
                    else:
                        if self.act_view_as_voting_public_address.isChecked():
                            ret = self.masternode.dmn_voting_address
                        elif self.act_view_as_voting_public_key_hash.isChecked():
                            ret = self.masternode.get_dmn_voting_pubkey_hash()
                        else:
                            ret = '???'
                except Exception as e:
                    msg = str(e)
                    if not msg:
                        msg = 'Key conversion error.'
                    WndUtils.error_msg(msg)
        return ret

    def get_operator_key_to_display(self) -> str:
        ret = ''
        if self.masternode:
            if self.edit_mode:
                if self.masternode.dmn_operator_key_type == InputKeyType.PRIVATE:
                    ret = self.masternode.dmn_operator_private_key
                else:
                    ret = self.masternode.dmn_operator_public_key
            else:
                try:
                    if self.masternode.dmn_operator_key_type == InputKeyType.PRIVATE:
                        if self.act_view_as_operator_private_key.isChecked():
                            ret = self.masternode.dmn_operator_private_key
                        elif self.act_view_as_operator_public_key.isChecked():
                            ret = self.masternode.get_dmn_operator_pubkey()
                        else:
                            ret = '???'
                    else:
                        if self.act_view_as_operator_public_key.isChecked():
                            ret = self.masternode.dmn_operator_public_key
                        else:
                            ret = '???'
                except Exception as e:
                    msg = str(e)
                    if not msg:
                        msg = 'Key conversion error.'
                    WndUtils.error_msg(msg)
        return ret

    @pyqtSlot(str)
    def on_lblOwnerKey_linkActivated(self, link):
        if self.masternode and self.edit_mode:
            if self.masternode.dmn_owner_key_type == InputKeyType.PRIVATE:
                self.masternode.dmn_owner_key_type = InputKeyType.PUBLIC
                self.edtOwnerKey.setText(self.masternode.dmn_owner_address)
                self.act_view_as_owner_private_key.setChecked(True)
            else:
                self.masternode.dmn_owner_key_type = InputKeyType.PRIVATE
                self.edtOwnerKey.setText(self.masternode.dmn_owner_private_key)
                self.act_view_as_owner_public_address.setChecked(True)
            self.on_mn_data_modified()
            self.update_ui_controls_state()

    @pyqtSlot(str)
    def on_lblOperatorKey_linkActivated(self, link):
        if self.masternode and self.edit_mode:
            if self.masternode.dmn_operator_key_type == InputKeyType.PRIVATE:
                self.masternode.dmn_operator_key_type = InputKeyType.PUBLIC
                self.edtOperatorKey.setText(self.masternode.dmn_operator_public_key)
                self.act_view_as_operator_private_key.setChecked(True)
            else:
                self.masternode.dmn_operator_key_type = InputKeyType.PRIVATE
                self.edtOperatorKey.setText(self.masternode.dmn_operator_private_key)
                self.act_view_as_operator_public_key.setChecked(True)
            self.on_mn_data_modified()
            self.update_ui_controls_state()

    @pyqtSlot(str)
    def on_lblVotingKey_linkActivated(self, link):
        if self.masternode and self.edit_mode:
            if self.masternode.dmn_voting_key_type == InputKeyType.PRIVATE:
                self.masternode.dmn_voting_key_type = InputKeyType.PUBLIC
                self.edtVotingKey.setText(self.masternode.dmn_voting_address)
                self.act_view_as_voting_private_key.setChecked(True)
            else:
                self.masternode.dmn_voting_key_type = InputKeyType.PRIVATE
                self.edtVotingKey.setText(self.masternode.dmn_voting_private_key)
                self.act_view_as_voting_public_address.setChecked(True)
            self.on_mn_data_modified()
            self.update_ui_controls_state()

    @pyqtSlot(str)
    def on_lblOwnerKey_linkHovered(self, link):
        if link == 'address':
            tt = 'Change input type to Dash address'
        else:
            tt = 'Change input type to private key'
        self.lblOwnerKey.setToolTip(tt)

    @pyqtSlot(str)
    def on_lblOperatorKey_linkHovered(self, link):
        if link == 'pub':
            tt = 'Change input type to public key'
        else:
            tt = 'Change input type to private key'
        self.lblOperatorKey.setToolTip(tt)

    @pyqtSlot(str)
    def on_lblVotingKey_linkHovered(self, link):
        if link == 'address':
            tt = 'Change input type to Dash address'
        else:
            tt = 'Change input type to private key'
        self.lblVotingKey.setToolTip(tt)

    def get_max_left_label_width(self):
        doc = QTextDocument(self)
        doc.setDocumentMargin(0)
        doc.setDefaultFont(self.lblOwnerKey.font())
        doc.setHtml('Test')

        def get_lbl_text_width(lbl):
            nonlocal doc
            doc.setHtml(lbl.text())
            return int(doc.size().width() + 5)

        w = max(get_lbl_text_width(self.lblName),
                get_lbl_text_width(self.lblIP),
                get_lbl_text_width(self.lblCollateral),
                get_lbl_text_width(self.lblCollateralTxHash),
                get_lbl_text_width(self.lblDMNTxHash),
                get_lbl_text_width(self.lblOwnerKey),
                get_lbl_text_width(self.lblOperatorKey),
                get_lbl_text_width(self.lblVotingKey))

        return w

    def set_left_label_width(self, width):
        if self.lblName.width() != width:
            self.label_width_changed.emit(width)

        self.lblUserRole.setFixedWidth(width)
        self.lblName.setFixedWidth(width)
        self.lblIP.setFixedWidth(width)
        self.lblCollateral.setFixedWidth(width)
        self.lblCollateralTxHash.setFixedWidth(width)
        self.lblDMNTxHash.setFixedWidth(width)
        self.lblOwnerKey.setFixedWidth(width)
        self.lblOperatorKey.setFixedWidth(width)
        self.lblVotingKey.setFixedWidth(width)

    def set_masternode(self, src_masternode: Optional[MasternodeConfig]):
        self.updating_ui = True
        if src_masternode:
            self.masternode.copy_from(src_masternode)
            self.masternode.modified = False
            self.validate_keys()
            self.masternode_data_to_ui(True)

    def get_masternode_data(self, dest_masternode: MasternodeConfig):
        """Copies masternode data from the internal MasternodeConfig object to dest_masternode.
          Used to get modified data and pass it to the global MasternodeConfig object.
        """
        dest_masternode.copy_from(self.masternode)

    def set_edit_mode(self, enabled: bool):
        if self.edit_mode != enabled:
            self.edit_mode = enabled
            self.masternode_data_to_ui(True if enabled else False)
            if not self.edit_mode:
                self.lblOwnerKey.setToolTip('')
                self.lblOperatorKey.setToolTip('')
                self.lblVotingKey.setToolTip('')

    def is_modified(self) -> bool:
        return self.masternode and self.masternode.modified

    def on_mn_data_modified(self):
        if self.masternode and not self.updating_ui:
            self.masternode.set_modified()
            self.data_changed.emit(self.masternode)

    @pyqtSlot(bool)
    def on_chbRoleOwner_toggled(self, checked):
        if not self.updating_ui:
            if checked:
                self.masternode.dmn_user_roles |= DMN_ROLE_OWNER
            else:
                self.masternode.dmn_user_roles &= ~DMN_ROLE_OWNER
            self.update_ui_controls_state()
            self.on_mn_data_modified()
            self.role_modified.emit()

    @pyqtSlot(bool)
    def on_chbRoleOperator_toggled(self, checked):
        if not self.updating_ui:
            if checked:
                self.masternode.dmn_user_roles |= DMN_ROLE_OPERATOR
            else:
                self.masternode.dmn_user_roles &= ~DMN_ROLE_OPERATOR
            self.update_ui_controls_state()
            self.on_mn_data_modified()
            self.role_modified.emit()

    @pyqtSlot(bool)
    def on_chbRoleVoting_toggled(self, checked):
        if not self.updating_ui:
            if checked:
                self.masternode.dmn_user_roles |= DMN_ROLE_VOTING
            else:
                self.masternode.dmn_user_roles &= ~DMN_ROLE_VOTING
            self.update_ui_controls_state()
            self.on_mn_data_modified()
            self.role_modified.emit()

    @pyqtSlot(str)
    def on_edtName_textEdited(self, text):
        if self.masternode and not self.updating_ui:
            self.on_mn_data_modified()
            self.masternode.name = text.strip()
            self.name_modified.emit(self.masternode, text)

    @pyqtSlot(str)
    def on_edtIP_textEdited(self, text):
        if self.masternode and not self.updating_ui:
            self.on_mn_data_modified()
            self.masternode.ip = text.strip()

    @pyqtSlot(str)
    def on_edtPort_textEdited(self, text):
        if self.masternode and not self.updating_ui:
            self.on_mn_data_modified()
            self.masternode.port = text.strip()

    @pyqtSlot(str)
    def on_edtCollateralAddress_textEdited(self, text):
        if self.masternode and not self.updating_ui:
            update_ui = ((not text) != (not self.masternode.collateral_address))
            self.on_mn_data_modified()
            self.masternode.collateral_address = text.strip()
            if update_ui:
                self.update_ui_controls_state()

    @pyqtSlot(str)
    def on_edtCollateralPath_textEdited(self, text):
        if self.masternode and not self.updating_ui:
            update_ui = ((not text) != (not self.masternode.collateral_bip32_path))
            self.on_mn_data_modified()
            self.masternode.collateral_bip32_path = text.strip()
            if update_ui:
                self.update_ui_controls_state()

    @pyqtSlot(str)
    def on_edtCollateralTxHash_textEdited(self, text):
        if self.masternode and not self.updating_ui:
            update_ui = ((not text) != (not self.masternode.collateral_tx))
            self.on_mn_data_modified()
            self.masternode.collateral_tx = text.strip()
            if update_ui:
                self.update_ui_controls_state()

    @pyqtSlot(str)
    def on_edtCollateralTxIndex_textEdited(self, text):
        if self.masternode and not self.updating_ui:
            self.on_mn_data_modified()
            self.masternode.collateral_tx_index = text.strip()

    @pyqtSlot(str)
    def on_edtDMNTxHash_textEdited(self, text):
        if self.masternode and not self.updating_ui:
            self.on_mn_data_modified()
            self.masternode.dmn_tx_hash = text.strip()

    @pyqtSlot(bool)
    def on_btnGetMNDataByIP_clicked(self, _):
        if self.masternode and not self.updating_ui:
            if not (self.masternode.ip and self.masternode.port):
                WndUtils.error_msg('Enter the masternode IP address and TCP port number.')
                return

            cache_max_age = 500
            self.dashd_intf.get_masternodelist('json', data_max_age=cache_max_age, protx_data_max_age=cache_max_age)
            mn = self.masternode
            updated_fields = []

            ip_port = mn.ip + ':' + mn.port
            mn_info = self.dashd_intf.masternodes_by_ip_port.get(ip_port)
            modified = False
            keys_modified = []
            if mn_info:
                if mn_info.protx:
                    protx = mn_info.protx
                    if mn.collateral_address != protx.collateral_address:
                        updated_fields.append('collateral address')
                        # self.edtCollateralAddress.setText(protx.collateral_address)
                        mn.collateral_address = protx.collateral_address
                        modified = True

                    if mn.dmn_tx_hash != protx.protx_hash:
                        updated_fields.append('protx hash')
                        # self.edtDMNTxHash.setText(protx.protx_hash)
                        self.masternode.dmn_tx_hash = protx.protx_hash
                        modified = True

                    if mn.collateral_tx != protx.collateral_hash or str(mn.collateral_tx_index) != \
                            str(protx.collateral_index):
                        updated_fields.append('collateral hash/index')
                        # self.edtCollateralTxHash.setVisible(protx.collateral_hash)
                        mn.collateral_tx = protx.collateral_hash
                        # self.edtCollateralTxIndex.setText(str(protx.collateral_index))
                        mn.collateral_tx_index = str(protx.collateral_index)
                        modified = True

                    if mn.dmn_user_roles & DMN_ROLE_OWNER > 0 and \
                            ((not mn.dmn_owner_private_key and mn.dmn_owner_key_type == InputKeyType.PRIVATE) or
                             (not mn.dmn_owner_address and mn.dmn_owner_key_type == InputKeyType.PUBLIC)):
                        mn.dmn_owner_key_type = InputKeyType.PUBLIC
                        mn.dmn_owner_address = protx.owner_address
                        modified = True
                        keys_modified.append('owner')

                    if mn.dmn_user_roles & DMN_ROLE_OPERATOR > 0 and \
                        ((not mn.dmn_operator_private_key and mn.dmn_operator_key_type == InputKeyType.PRIVATE) or
                         (not mn.dmn_operator_public_key and mn.dmn_operator_key_type == InputKeyType.PUBLIC)):
                        mn.dmn_operator_key_type = InputKeyType.PUBLIC
                        mn.dmn_operator_public_key = protx.pubkey_operator
                        modified = True
                        keys_modified.append('operator')

                    if mn.dmn_user_roles & DMN_ROLE_VOTING > 0 and \
                        ((not mn.dmn_voting_private_key and mn.dmn_voting_key_type == InputKeyType.PRIVATE) or
                         (not mn.dmn_voting_address and mn.dmn_voting_key_type == InputKeyType.PUBLIC)):
                        mn.dmn_voting_key_type = InputKeyType.PUBLIC
                        mn.dmn_voting_address = protx.voting_address
                        modified = True
                        keys_modified.append('voting')

                if modified:
                    self.masternode_data_to_ui()
                    self.on_mn_data_modified()
                    self.app_text_message_sent.emit(
                        DispMessage.OTHER_1, 'The following mn data has been set: ' + ', '.join(updated_fields),
                        AppTextMessageType.INFO)

                    if keys_modified:
                        self.app_text_message_sent.emit(
                            DispMessage.OTHER_2,
                            'We\'ve set <b>public</b> keys for ' + ', '.join(keys_modified) +
                            '. You need to enter <b>private</b> keys instead, to have access to some of the features.',
                            AppTextMessageType.WARN)
            else:
                WndUtils.warn_msg(
                    'Couldn\'t find this masternode in the list of registered deterministic masternodes.')

    @pyqtSlot(bool)
    def on_btnBip32PathToAddress_clicked(self, checked):
        if self.masternode.collateral_bip32_path:
            if self.hw_session.connect_hardware_wallet():
                try:
                    addr = hw_intf.get_address(self.hw_session, self.masternode.collateral_bip32_path,
                                               show_display=True)
                    if addr:
                        self.masternode.collateral_address = addr.strip()
                        self.edtCollateralAddress.setText(addr.strip())
                        self.on_mn_data_modified()
                        self.update_ui_controls_state()
                except CancelException:
                    pass

    @pyqtSlot(bool)
    def on_btnShowCollateralPathAddress_clicked(self, checked):
        if self.masternode.collateral_bip32_path:
            try:
                if self.hw_session.connect_hardware_wallet():
                    addr = hw_intf.get_address(
                        self.hw_session, self.masternode.collateral_bip32_path, True,
                        f'Displaying address for the BIP32 path <b>{self.masternode.collateral_bip32_path}</b>.'
                        f'<br>Click the confirmation button on your device.')
            except CancelException:
                pass

    @pyqtSlot(str)
    def on_edtOwnerKey_textEdited(self, text):
        if self.masternode and not self.updating_ui:
            if self.masternode.dmn_owner_key_type == InputKeyType.PRIVATE:
                self.masternode.dmn_owner_private_key = text.strip()
            else:
                self.masternode.dmn_owner_address = text.strip()
            self.validate_keys()
            self.update_dynamic_labels()
            self.on_mn_data_modified()

    @pyqtSlot(str)
    def on_edtOperatorKey_textEdited(self, text):
        if self.masternode and not self.updating_ui:
            if self.masternode.dmn_operator_key_type == InputKeyType.PRIVATE:
                self.masternode.dmn_operator_private_key = text.strip()
            else:
                self.masternode.dmn_operator_public_key = text.strip()
            self.validate_keys()
            self.update_dynamic_labels()
            self.on_mn_data_modified()

    @pyqtSlot(str)
    def on_edtVotingKey_textEdited(self, text):
        if self.masternode and not self.updating_ui:
            if self.masternode.dmn_voting_key_type == InputKeyType.PRIVATE:
                self.masternode.dmn_voting_private_key = text.strip()
            else:
                self.masternode.dmn_voting_address = text.strip()
            self.validate_keys()
            self.update_dynamic_labels()
            self.on_mn_data_modified()

    def validate_keys(self):
        self.owner_key_invalid = False
        self.operator_key_invalid = False
        self.voting_key_invalid = False

        if self.masternode:
            if self.masternode.dmn_owner_key_type == InputKeyType.PRIVATE:
                if self.masternode.dmn_owner_private_key:
                    self.owner_key_invalid = not dash_utils.validate_wif_privkey(self.masternode.dmn_owner_private_key,
                                                                                 self.app_config.dash_network)
            else:
                if self.masternode.dmn_owner_address:
                    self.owner_key_invalid = not dash_utils.validate_address(self.masternode.dmn_owner_address,
                                                                             self.app_config.dash_network)

            if self.masternode.dmn_operator_key_type == InputKeyType.PRIVATE:
                if self.masternode.dmn_operator_private_key:
                    self.operator_key_invalid = not dash_utils.validate_bls_privkey(
                        self.masternode.dmn_operator_private_key)
            else:
                if self.masternode.dmn_operator_public_key:
                    self.operator_key_invalid = not dash_utils.validate_bls_pubkey(
                        self.masternode.dmn_operator_public_key)

            if self.masternode.dmn_voting_key_type == InputKeyType.PRIVATE:
                if self.masternode.dmn_voting_private_key:
                    self.voting_key_invalid = not dash_utils.validate_wif_privkey(self.masternode.dmn_voting_private_key,
                                                                                  self.app_config.dash_network)
            else:
                if self.masternode.dmn_voting_address:
                    self.voting_key_invalid = not dash_utils.validate_address(self.masternode.dmn_voting_address,
                                                                              self.app_config.dash_network)

    def generate_priv_key(self, pk_type: str, edit_control: QLineEdit, compressed: bool):
        if edit_control.text():
            if WndUtils.query_dlg(
                    f'This will overwrite the current {pk_type} private key value. Do you really want to proceed?',
                    buttons=QMessageBox.Yes | QMessageBox.Cancel,
                    default_button=QMessageBox.Yes, icon=QMessageBox.Warning) != QMessageBox.Yes:
                return None

        if pk_type == 'operator':
            pk = dash_utils.generate_bls_privkey()
        else:
            pk = dash_utils.generate_wif_privkey(self.app_config.dash_network, compressed=compressed)
        edit_control.setText(pk)
        return pk

    @pyqtSlot(bool)
    def on_btnGenerateOwnerPrivateKey_clicked(self, checked):
        if self.masternode:
            pk = self.generate_priv_key('owner', self.edtOwnerKey, True)
            if pk:
                self.masternode.dmn_owner_private_key = pk
                self.btnShowOwnerPrivateKey.setChecked(True)
                self.on_mn_data_modified()

    @pyqtSlot(bool)
    def on_btnGenerateOperatorPrivateKey_clicked(self, checked):
        if self.masternode:

            pk = self.generate_priv_key('operator', self.edtOperatorKey, True)
            if pk:
                self.masternode.dmn_operator_private_key = pk
                self.btnShowOperatorPrivateKey.setChecked(True)
                self.on_mn_data_modified()

    @pyqtSlot(bool)
    def on_btnGenerateVotingPrivateKey_clicked(self, checked):
        if self.masternode:
            pk = self.generate_priv_key('voting', self.edtVotingKey, True)
            if pk:
                self.masternode.dmn_voting_private_key = pk
                self.btnShowVotingPrivateKey.setChecked(True)
                self.on_mn_data_modified()

    @pyqtSlot(bool)
    def on_btnShowOwnerPrivateKey_toggled(self, checked):
        self.edtOwnerKey.setEchoMode(QLineEdit.Normal if checked else QLineEdit.Password)
        self.update_key_controls_state()

    @pyqtSlot(bool)
    def on_btnShowOperatorPrivateKey_toggled(self, checked):
        self.edtOperatorKey.setEchoMode(QLineEdit.Normal if checked else QLineEdit.Password)
        self.update_key_controls_state()

    @pyqtSlot(bool)
    def on_btnShowVotingPrivateKey_toggled(self, checked):
        self.edtVotingKey.setEchoMode(QLineEdit.Normal if checked else QLineEdit.Password)
        self.update_key_controls_state()

    @pyqtSlot(bool)
    def on_btnLocateCollateral_clicked(self, checked):
        try:
            break_scanning = False

            if not self.hw_session.connect_hardware_wallet():
                return

            def do_break_scanning():
                nonlocal break_scanning
                break_scanning = True
                return False

            def check_break_scanning():
                nonlocal break_scanning
                return break_scanning

            def apply_utxo(utxo):
                self.masternode.collateral_address = utxo.address
                self.edtCollateralAddress.setText(utxo.address)
                self.masternode.collateral_bip32_path = utxo.bip32_path
                self.edtCollateralPath.setText(utxo.bip32_path)
                self.masternode.collateral_tx = utxo.txid
                self.edtCollateralTxHash.setText(utxo.txid)
                self.masternode.collateral_tx_index = str(utxo.output_index)
                self.edtCollateralTxIndex.setText(str(utxo.output_index))
                self.update_ui_controls_state()
                self.on_mn_data_modified()

            bip44_wallet = Bip44Wallet(self.app_config.hw_coin_name, self.hw_session,
                                       self.app_config.db_intf, self.dashd_intf, self.app_config.dash_network)

            utxos = WndUtils.run_thread_dialog(
                self.get_collateral_tx_address_thread,
                (bip44_wallet, check_break_scanning, self.edtCollateralAddress.text()),
                True, force_close_dlg_callback=do_break_scanning)

            if utxos:
                if len(utxos) == 1 and \
                        (not self.masternode.collateral_address or
                         (utxos[0].address_obj and self.masternode.collateral_address == utxos[0].address_obj.address)) \
                        and (not self.masternode.collateral_tx or utxos[0].txid == self.masternode.collateral_tx):
                    apply_utxo(utxos[0])
                    return

                dlg = ListCollateralTxsDlg(self, self.masternode, self.app_config, False, utxos)
                if dlg.exec_():
                    utxo = dlg.get_selected_utxo()
                    if utxo:
                        apply_utxo(utxo)
            else:
                if utxos is not None:
                    WndUtils.warn_msg('Couldn\'t find any 1000 Dash UTXO in your wallet.')
        except Exception as e:
            WndUtils.error_msg(str(e))

    def get_collateral_tx_address_thread(self, ctrl: CtrlObject,
                                         bip44_wallet: Bip44Wallet,
                                         check_break_scanning_ext: Callable[[], bool],
                                         src_address: str):
        utxos = []
        break_scanning = False
        txes_cnt = 0
        msg = 'Scanning wallet transactions for 1000 Dash UTXOs.<br>' \
              'This may take a while (<a href="break">break</a>)....'
        ctrl.dlg_config(dlg_title="Scanning wallet", show_progress_bar=False)
        ctrl.display_msg(msg)

        def check_break_scanning():
            nonlocal break_scanning
            if break_scanning:
                # stop the scanning process if the dialog finishes or the address/bip32path has been found
                raise BreakFetchTransactionsException()
            if check_break_scanning_ext is not None and check_break_scanning_ext():
                raise BreakFetchTransactionsException()

        def fetch_txes_feedback(tx_cnt: int):
            nonlocal msg, txes_cnt
            txes_cnt += tx_cnt
            ctrl.display_msg(msg + '<br><br>' + 'Number of transactions fetched so far: ' + str(txes_cnt))

        def on_msg_link_activated(link: str):
            nonlocal break_scanning
            if link == 'break':
                break_scanning = True

        lbl = ctrl.get_msg_label_control()
        if lbl:
            def set():
                lbl.setOpenExternalLinks(False)
                lbl.setTextInteractionFlags(lbl.textInteractionFlags() & ~Qt.TextSelectableByMouse)
                lbl.linkActivated.connect(on_msg_link_activated)
                lbl.repaint()

            WndUtils.call_in_main_thread(set)

        try:
            bip44_wallet.on_fetch_account_txs_feedback = fetch_txes_feedback
            if src_address:
                # limit transactions only to the specific address
                # addr = bip44_wallet.get_address_item(src_address, False)
                addr = bip44_wallet.scan_wallet_for_address(src_address, check_break_scanning,
                                                            feedback_fun=fetch_txes_feedback)

                if addr and addr.tree_id == bip44_wallet.get_tree_id():
                    bip44_wallet.fetch_addresses_txs([addr], check_break_scanning)
                    for utxo in bip44_wallet.list_utxos_for_addresses([addr.id], filter_by_satoshis=int(1e11)):
                        utxos.append(utxo)

            if not utxos:
                bip44_wallet.fetch_all_accounts_txs(check_break_scanning)
                for utxo in bip44_wallet.list_utxos_for_account(account_id=None, filter_by_satoshis=int(1e11)):
                    utxos.append(utxo)

        except BreakFetchTransactionsException:
            return None
        return utxos

    def on_owner_view_key_type_changed(self):
        self.btnShowOwnerPrivateKey.setChecked(True)
        self.update_key_controls_state()
        self.edtOwnerKey.setText(self.get_owner_key_to_display())

    def on_voting_view_key_type_changed(self):
        self.btnShowVotingPrivateKey.setChecked(True)
        self.update_key_controls_state()
        self.edtVotingKey.setText(self.get_voting_key_to_display())

    def on_operator_view_key_type_changed(self):
        self.btnShowOperatorPrivateKey.setChecked(True)
        self.update_key_controls_state()
        self.edtOperatorKey.setText(self.get_operator_key_to_display())

    @pyqtSlot()
    def on_btnCopyOwnerKey_clicked(self):
        cl = QApplication.clipboard()
        cl.setText(self.edtOwnerKey.text())

    @pyqtSlot()
    def on_btnCopyVotingKey_clicked(self):
        cl = QApplication.clipboard()
        cl.setText(self.edtVotingKey.text())

    @pyqtSlot()
    def on_btnCopyOperatorKey_clicked(self):
        cl = QApplication.clipboard()
        cl.setText(self.edtOperatorKey.text())

    @pyqtSlot()
    def on_btnCopyProtxHash_clicked(self):
        cl = QApplication.clipboard()
        cl.setText(self.edtDMNTxHash.text())
