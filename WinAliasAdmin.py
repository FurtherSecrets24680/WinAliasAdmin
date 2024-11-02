import sys
import os
import winreg
import ctypes
import subprocess
from typing import Optional, Dict, List, Tuple
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QTreeWidget, QTreeWidgetItem,
    QFileDialog, QMessageBox, QFrame, QGroupBox, QComboBox
)
from PySide6.QtCore import Qt
import re

MANIFEST = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<assembly xmlns="urn:schemas-microsoft-com:asm.v1" manifestVersion="1.0">
    <assemblyIdentity version="1.0.0.0" processorArchitecture="X86"
        name="WinAliasAdmin" type="win32"/>
    <description>Windows App Execution Alias Admin</description>
    <trustInfo xmlns="urn:schemas-microsoft-com:asm.v3">
        <security>
            <requestedPrivileges>
                <requestedExecutionLevel level="requireAdministrator" uiAccess="false"/>
            </requestedPrivileges>
        </security>
    </trustInfo>
</assembly>
'''

def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

def create_manifest():
    try:
        manifest_path = os.path.join(os.path.dirname(os.path.abspath(sys.argv[0])), 'alias_admin.manifest')
        with open(manifest_path, 'w') as f:
            f.write(MANIFEST)
        return manifest_path
    except Exception as e:
        print(f"Failed to create manifest: {e}")
        return None

class AliasManager(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("WinAliasAdmin")
        self.setMinimumSize(1000, 700)

        # Registry paths
        self.REG_PATHS = {
            "HKEY_LOCAL_MACHINE": (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths"),
            "HKEY_CURRENT_USER": (winreg.HKEY_CURRENT_USER, r"SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths")
        }

        self.setup_ui()
        self.refresh_aliases()

    def setup_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)

        aliases_group = QGroupBox("System and User Aliases")
        aliases_layout = QVBoxLayout(aliases_group)

        self.tree = QTreeWidget()
        self.tree.setHeaderLabels(["Location", "Alias", "Path"])
        self.tree.setColumnWidth(0, 150)
        self.tree.setColumnWidth(1, 200)
        self.tree.setColumnWidth(2, 500)
        self.tree.setAlternatingRowColors(True)
        aliases_layout.addWidget(self.tree)

        add_group = QGroupBox("Add or Edit Alias")
        add_layout = QVBoxLayout(add_group)

        location_layout = QHBoxLayout()
        location_label = QLabel("Location:")
        self.location_combo = QComboBox()
        self.location_combo.addItems(list(self.REG_PATHS.keys()))
        location_layout.addWidget(location_label)
        location_layout.addWidget(self.location_combo)
        location_layout.addStretch()
        add_layout.addLayout(location_layout)

        alias_layout = QHBoxLayout()
        alias_label = QLabel("Alias Name:")
        self.alias_input = QLineEdit()
        self.alias_input.setPlaceholderText("Enter alias name (e.g., myapp)")
        alias_layout.addWidget(alias_label)
        alias_layout.addWidget(self.alias_input)
        add_layout.addLayout(alias_layout)

        path_layout = QHBoxLayout()
        path_label = QLabel("Program Path:")
        self.path_input = QLineEdit()
        self.path_input.setPlaceholderText("Select program path")
        browse_button = QPushButton("Browse...")
        browse_button.clicked.connect(self.browse_file)
        path_layout.addWidget(path_label)
        path_layout.addWidget(self.path_input)
        path_layout.addWidget(browse_button)
        add_layout.addLayout(path_layout)

        buttons_layout = QHBoxLayout()
        buttons_layout.setContentsMargins(0, 10, 0, 0)

        add_button = QPushButton("Add Alias")
        add_button.setMinimumWidth(120)
        add_button.clicked.connect(self.add_alias)

        edit_button = QPushButton("Edit Selected")
        edit_button.setMinimumWidth(120)
        edit_button.clicked.connect(self.edit_alias)

        remove_button = QPushButton("Remove Selected")
        remove_button.setMinimumWidth(120)
        remove_button.clicked.connect(self.remove_alias)

        refresh_button = QPushButton("Refresh List")
        refresh_button.setMinimumWidth(120)
        refresh_button.clicked.connect(self.refresh_aliases)

        buttons_layout.addWidget(add_button)
        buttons_layout.addWidget(edit_button)
        buttons_layout.addWidget(remove_button)
        buttons_layout.addWidget(refresh_button)
        buttons_layout.addStretch()

        main_layout.addWidget(aliases_group)
        main_layout.addWidget(add_group)
        main_layout.addLayout(buttons_layout)

        self.statusBar().showMessage("Ready")

    def get_aliases_from_hive(self, hive_key: int, reg_path: str) -> List[Tuple[str, str]]:
        aliases = []
        try:
            key = winreg.OpenKey(hive_key, reg_path, 0, winreg.KEY_READ)
            index = 0
            
            while True:
                try:
                    alias_name = winreg.EnumKey(key, index)
                    alias_key = winreg.OpenKey(hive_key, os.path.join(reg_path, alias_name), 0, winreg.KEY_READ)
                    alias_path = winreg.QueryValue(alias_key, None)
                    winreg.CloseKey(alias_key)
                    aliases.append((alias_name, alias_path))
                    index += 1
                except WindowsError:
                    break
                    
            winreg.CloseKey(key)
        except WindowsError as e:
            if e.winerror != 2:
                raise
        return aliases

    def refresh_aliases(self):
        self.tree.clear()
        self.statusBar().showMessage("Refreshing aliases...")
        
        try:
            location_items = {}
            for location_name in self.REG_PATHS:
                item = QTreeWidgetItem([location_name])
                item.setExpanded(True)
                self.tree.addTopLevelItem(item)
                location_items[location_name] = item
            
            for location_name, (hive_key, reg_path) in self.REG_PATHS.items():
                try:
                    aliases = self.get_aliases_from_hive(hive_key, reg_path)
                    for alias_name, alias_path in aliases:
                        item = QTreeWidgetItem([location_name, alias_name, alias_path])
                        location_items[location_name].addChild(item)
                except Exception as e:
                    print(f"Error loading aliases from {location_name}: {e}")

            for i in range(self.tree.topLevelItemCount()):
                self.tree.topLevelItem(i).setExpanded(True)
            
            self.statusBar().showMessage("Ready")
            
        except Exception as e:
            self.statusBar().showMessage("Error loading aliases")
            QMessageBox.critical(self, "Error", f"Failed to load aliases: {str(e)}")

    def add_alias(self):
        location = self.location_combo.currentText()
        alias = self.alias_input.text().strip()
        path = self.path_input.text().strip()
        
        if not alias or not path:
            QMessageBox.warning(self, "Error", "Please provide both alias name and program path")
            return
            
        if not alias.endswith('.exe'):
            alias += '.exe'
            
        try:
            hive_key, reg_path = self.REG_PATHS[location]
            key_path = os.path.join(reg_path, alias)
            key = winreg.CreateKeyEx(hive_key, key_path, 0, winreg.KEY_WRITE)
            
            winreg.SetValueEx(key, "", 0, winreg.REG_SZ, path)
            
            dir_path = os.path.dirname(path)
            winreg.SetValueEx(key, "Path", 0, winreg.REG_SZ, dir_path)
            
            winreg.CloseKey(key)
            
            QMessageBox.information(self, "Success", f"Alias '{alias}' added successfully to {location}")
            
            self.alias_input.clear()
            self.path_input.clear()
            self.refresh_aliases()
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to add alias: {str(e)}")

    def edit_alias(self):
        selected_items = self.tree.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "Warning", "Please select an alias to edit")
            return
            
        item = selected_items[0]
        if item.parent() is None:
            QMessageBox.warning(self, "Warning", "Please select an alias, not a location")
            return
            
        location = item.text(0)
        old_alias = item.text(1)
        old_path = item.text(2)

        self.location_combo.setCurrentText(location)
        self.alias_input.setText(old_alias)
        self.path_input.setText(old_path)

        self.alias_input.setEnabled(True)
        self.path_input.setEnabled(True)

        update_button = QPushButton("Update Alias")
        update_button.clicked.connect(lambda: self.update_alias(location, old_alias))
        update_button.setMinimumWidth(120)
        
        self.findChild(QHBoxLayout).addWidget(update_button)

    def update_alias(self, location: str, old_alias: str):
        new_alias = self.alias_input.text().strip()
        new_path = self.path_input.text().strip()
        
        if not new_alias or not new_path:
            QMessageBox.warning(self, "Error", "Please provide both alias name and program path")
            return
            
        if not new_alias.endswith('.exe'):
            new_alias += '.exe'
        
        try:
            hive_key, reg_path = self.REG_PATHS[location]
            key_path = os.path.join(reg_path, old_alias)

            winreg.DeleteKey(hive_key, key_path)

            key = winreg.CreateKeyEx(hive_key, os.path.join(reg_path, new_alias), 0, winreg.KEY_WRITE)
            winreg.SetValueEx(key, "", 0, winreg.REG_SZ, new_path)
            winreg.SetValueEx(key, "Path", 0, winreg.REG_SZ, os.path.dirname(new_path))
            winreg.CloseKey(key)
            
            QMessageBox.information(self, "Success", f"Alias '{new_alias}' updated successfully in {location}")
            self.refresh_aliases()

            self.alias_input.clear()
            self.path_input.clear()
            self.alias_input.setEnabled(True)
            self.path_input.setEnabled(True)

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to update alias: {str(e)}")

    def remove_alias(self):
        selected_items = self.tree.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "Warning", "Please select an alias to remove")
            return
            
        item = selected_items[0]
        if item.parent() is None:
            QMessageBox.warning(self, "Warning", "Please select an alias, not a location")
            return
            
        location = item.text(0)
        alias = item.text(1)

        confirmation = QMessageBox.question(self, "Confirm Removal",
                                             f"Are you sure you want to remove alias '{alias}'?",
                                             QMessageBox.Yes | QMessageBox.No)

        if confirmation == QMessageBox.Yes:
            try:
                hive_key, reg_path = self.REG_PATHS[location]
                winreg.DeleteKey(hive_key, os.path.join(reg_path, alias))
                QMessageBox.information(self, "Success", f"Alias '{alias}' removed successfully")
                self.refresh_aliases()
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to remove alias: {str(e)}")

    def browse_file(self):
        path, _ = QFileDialog.getOpenFileName(self, "Select Program", "", "Executable Files (*.exe);;All Files (*)")
        if path:
            self.path_input.setText(path)

if __name__ == "__main__":
    if not is_admin():
        manifest_path = create_manifest()
        if manifest_path:
            subprocess.Popen(["powershell.exe", "-Command", f"Start-Process '{sys.executable}' -ArgumentList '{__file__}' -Verb RunAs"])
    else:
        app = QApplication(sys.argv)
        alias_manager = AliasManager()
        alias_manager.show()
        sys.exit(app.exec())