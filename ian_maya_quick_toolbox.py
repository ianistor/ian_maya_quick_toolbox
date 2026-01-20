import sys
import os
import maya.cmds as cmds
import maya.OpenMayaUI as omui
import maya.utils as utils
from shiboken2 import wrapInstance
from PySide2 import QtCore, QtGui, QtWidgets

# Constants
WINDOW_WIDTH = 300
WINDOW_HEIGHT = 250
DEFAULT_NEAR_CLIP = 1
DEFAULT_FAR_CLIP = 1000000000
AUTHOR = 'ndrnistor@gmail.com'
TOOL_NAME = 'IAN Maya Quick Toolbox'
VERSION = "1.1"

def maya_main_window():
    """Return the Maya main window as QMainWindow"""
    main_window = omui.MQtUtil.mainWindow()
    if sys.version_info.major >= 3:
        return wrapInstance(int(main_window), QtWidgets.QWidget)
    else:
        return wrapInstance(long(main_window), QtWidgets.QWidget) # type: ignore

class ToolWindow(QtWidgets.QDialog):
    """
    A custom tool window for Maya that provides various utility functions
    for scene management and workflow optimization.
    """
    
    def __init__(self):
        super(ToolWindow, self).__init__(maya_main_window())
        self.setWindowTitle(TOOL_NAME)
        self.setWindowFlags(self.windowFlags())
        self.resize(WINDOW_WIDTH, WINDOW_HEIGHT)
        self.is_right_handed = True

        self.create_ui_widgets()
        self.create_ui_layout()
        self.create_ui_connections()
        self.load_settings()
        self.center_window()
        
        if cmds.about(macOS=True):
            self.setWindowFlags(QtCore.Qt.Tool)

    def create_ui_widgets(self):
        """Create all UI widgets"""
        self.normal_group = QtWidgets.QGroupBox("Normal Settings")
        self.tangent_group = QtWidgets.QGroupBox("Tangent Space Settings")
        self.namespace_group = QtWidgets.QGroupBox("Namespace")
        self.settings_group = QtWidgets.QGroupBox("Scene Settings")

        self.tangent_left = QtWidgets.QPushButton("Set Left Handed")
        self.tangent_right = QtWidgets.QPushButton("Set Right Handed")
        self.namespace_button = QtWidgets.QPushButton("Merge Namespace to Root")
        
        self.camera_button = QtWidgets.QPushButton("Set Camera Clip Planes")
        self.color_management_button = QtWidgets.QPushButton("Disable Color Management")

        self.log_msg = QtWidgets.QLabel("")
        self.log_msg.setAlignment(QtCore.Qt.AlignCenter)
        self.log_msg.setWordWrap(True)

        self.reference_group = QtWidgets.QGroupBox("Reference Tools")
        self.ref_path = QtWidgets.QLineEdit("path/to/ref.ma")
        self.browse_button = QtWidgets.QPushButton("...")
        self.create_ref_button = QtWidgets.QPushButton("Create Reference")
        self.remove_ref_button = QtWidgets.QPushButton("Remove Reference")

    def create_ui_layout(self):
        """Create and setup all UI layouts"""
        tangent_layout = QtWidgets.QHBoxLayout()
        tangent_layout.addWidget(self.tangent_left)
        tangent_layout.addWidget(self.tangent_right)
        self.tangent_group.setLayout(tangent_layout)

        namespace_layout = QtWidgets.QVBoxLayout()
        namespace_layout.addWidget(self.namespace_button)
        self.namespace_group.setLayout(namespace_layout)

        settings_layout = QtWidgets.QVBoxLayout()
        settings_layout.addWidget(self.camera_button)
        settings_layout.addWidget(self.color_management_button)
        self.settings_group.setLayout(settings_layout)

        reference_layout = QtWidgets.QVBoxLayout()
        path_layout = QtWidgets.QHBoxLayout()
        path_layout.addWidget(QtWidgets.QLabel("File Path:"))
        path_layout.addWidget(self.ref_path)
        path_layout.addWidget(self.browse_button)
        reference_layout.addLayout(path_layout)
        reference_layout.addWidget(self.create_ref_button)
        reference_layout.addWidget(self.remove_ref_button)
        self.reference_group.setLayout(reference_layout)    

        main_layout = QtWidgets.QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.addWidget(self.tangent_group)
        main_layout.addWidget(self.namespace_group)
        main_layout.addWidget(self.settings_group)
        main_layout.addWidget(self.reference_group)
        main_layout.addWidget(self.log_msg)

    def create_ui_connections(self):
        """Create all UI signal connections"""
        self.tangent_left.clicked.connect(lambda: self.set_tangent_space("left"))
        self.tangent_right.clicked.connect(lambda: self.set_tangent_space("right"))
        self.namespace_button.clicked.connect(self.remove_namespaces)
        self.camera_button.clicked.connect(self.set_camera_settings)
        self.color_management_button.clicked.connect(self.set_color_management)
        self.browse_button.clicked.connect(self.browse_file)
        self.create_ref_button.clicked.connect(self.create_reference)
        self.remove_ref_button.clicked.connect(self.remove_reference)

    def center_window(self):
        """Center the window on the screen"""
        frame_geo = self.frameGeometry()
        screen = QtWidgets.QApplication.desktop().screenNumber(
            QtWidgets.QApplication.desktop().cursor().pos())
        center_point = QtWidgets.QApplication.desktop().screenGeometry(screen).center()
        frame_geo.moveCenter(center_point)
        self.move(frame_geo.topLeft())

    def save_settings(self):
        """Save window settings"""
        settings = QtCore.QSettings(AUTHOR, TOOL_NAME)
        settings.setValue('geometry', self.saveGeometry())
        settings.setValue('last_path', self.ref_path.text())

    def load_settings(self):
        """Load window settings"""
        settings = QtCore.QSettings(AUTHOR, TOOL_NAME)
        geometry = settings.value('geometry')
        if geometry:
            self.restoreGeometry(geometry)
        last_path = settings.value('last_path')
        if last_path:
            self.ref_path.setText(last_path)

    def browse_file(self):
        """Open file browser dialog"""
        file_path = cmds.fileDialog2(fileMode=1, fileFilter="Maya Files (*.ma *.mb)")
        if file_path:
            self.ref_path.setText(file_path[0])
            self.save_settings()

    def create_reference(self):
        """Create a reference from the specified file path"""
        file_path = self.ref_path.text()
        if not os.path.exists(file_path):
            self.update_log("File does not exist!", False)
            return

        try:
            cmds.file(file_path, reference=True, namespace=':')
            self.update_log(f"Successfully referenced: {file_path}")
        except Exception as e:
            self.update_log(f"Error creating reference: {str(e)}", False)

    def remove_reference(self):
        """Remove the specified reference from the scene"""
        file_path = self.ref_path.text()
        try:
            references = cmds.ls(type="reference")
            for ref in references:
                ref_path = cmds.referenceQuery(ref, filename=True)
                if file_path in ref_path:
                    cmds.file(ref_path, removeReference=True)
                    self.update_log(f"Successfully removed reference: {file_path}")
                    return
            self.update_log(f"No reference found with path: {file_path}", False)
        except Exception as e:
            self.update_log(f"Error removing reference: {str(e)}", False)

    def set_camera_settings(self):
        """Set the far and near clip planes for all cameras"""
        try:
            all_cameras = cmds.ls(type='camera')
            if not all_cameras:
                self.update_log('No cameras found in the scene.', False)
                return
                
            for cam in all_cameras:
                cmds.setAttr(cam + '.nearClipPlane', DEFAULT_NEAR_CLIP)
                cmds.setAttr(cam + '.farClipPlane', DEFAULT_FAR_CLIP)
            
            self.update_log(f'Camera clip planes set for {len(all_cameras)} camera(s).')
        except Exception as e:
            self.update_log(f'Error setting camera settings: {str(e)}', False)

    def set_color_management(self):
        """Disable Color Management"""
        try:
            cmds.colorManagementPrefs(edit=True, cmEnabled=False)
            self.update_log('Color Management has been disabled.')
        except Exception as e:
            self.update_log(f'Error disabling color management: {str(e)}', False)

    def set_tangent_space(self, mode):
        """Set the tangent space coordinate system for visible mesh shapes"""
        try:
            all_meshes = cmds.ls(type='mesh', long=True)
            meshes = [mesh for mesh in all_meshes if not cmds.getAttr(f"{mesh}.intermediateObject")]
            
            if not meshes:
                self.update_log('No visible meshes in the scene.', False)
                return

            value = 2 if mode == "left" else 1  # 2 for Left Handed, 1 for Right Handed
            
            for mesh in meshes:
                cmds.setAttr(mesh + '.tangentSpace', value)

            self.update_log(f'Tangent space set to {mode}-handed on {len(meshes)} visible mesh(es).')
        except Exception as e:
            self.update_log(f'Error setting tangent space: {str(e)}', False)

    def remove_namespaces(self):
        """Merge namespaces to root with progress feedback"""
        try:
            allNodes = cmds.ls()
            allNamespaces = list(set([node.split(':')[0] for node in allNodes if ':' in node]))
            
            if not allNamespaces:
                self.update_log('No namespaces found.', False)
                return
                
            progress_dialog = QtWidgets.QProgressDialog("Removing namespaces...", "Cancel", 0, len(allNamespaces), self)
            progress_dialog.setWindowModality(QtCore.Qt.WindowModal)
            
            for i, namespace in enumerate(allNamespaces):
                if progress_dialog.wasCanceled():
                    break
                try:
                    cmds.namespace(removeNamespace=namespace, mergeNamespaceWithRoot=True)
                    progress_dialog.setValue(i + 1)
                except Exception as e:
                    self.update_log(f'Error removing namespace {namespace}: {str(e)}', False)
                    
            self.update_log('Namespaces merged to root.')
        except Exception as e:
            self.update_log(f'Error in namespace operation: {str(e)}', False)

    def update_log(self, message, success=True):
        """Update the status label with the given message"""
        color = "green" if success else "red"
        self.log_msg.setStyleSheet(f"color: {color}; font-weight: bold;")
        self.log_msg.setText(message)
        QtCore.QTimer.singleShot(3000, lambda: self.log_msg.setText(""))

    def closeEvent(self, event):
        """Cleanup on window close"""
        self.save_settings()
        self.deleteLater()
        event.accept()

def start():
    global tool_ui
    try:
        tool_ui.close()
        tool_ui.deleteLater()
    except:
        pass
    tool_ui = ToolWindow()
    tool_ui.show()

if __name__ == "__main__":
    start()
