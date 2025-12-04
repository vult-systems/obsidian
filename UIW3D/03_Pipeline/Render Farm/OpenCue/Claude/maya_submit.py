#  Copyright Contributors to the OpenCue Project
#
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.

"""
OpenCue Submit Tool for Maya 2026

Maya 2026 uses Python 3.11 which has compatibility issues with OpenCue's
gRPC/protobuf dependencies. This module provides the Maya UI and delegates
actual job submission to an external Python 3.9 process.

Usage:
    import maya_submit
    maya_submit.main()
"""

import getpass
import json
import logging
import os
import subprocess
import tempfile

import maya.cmds as cmds
import maya.utils

# Maya 2026 uses PySide6 (Qt 6.5+)
try:
    from PySide6 import QtCore, QtWidgets, QtGui
except ImportError:
    from PySide2 import QtCore, QtWidgets, QtGui

# Configuration
PYTHON_PATH = r"C:\Program Files\Python39\python.exe"
CUEBOT_HOST = "10.40.14.25:8443"
MAYA_VERSION = "2026"
UI_NAME = "OpenCueSubmit"

log = logging.getLogger(UI_NAME)
window = None


# =============================================================================
# CueSubmit Style - Dark Theme
# =============================================================================
MAIN_STYLE = """
QWidget {
    background-color: rgb(40, 50, 60);
    color: rgb(200, 200, 200);
}

QLabel {
    background-color: rgb(40, 50, 60);
    color: rgb(160, 160, 160);
    font-weight: regular;
    font-size: 10pt;
}

QLabel[accessibleName="sectionLabel"] {
    color: rgb(200, 200, 200);
    font-size: 11pt;
    font-weight: bold;
    padding: 5px 0px;
}

QLineEdit {
    color: rgb(220, 220, 220);
    border: 0px solid;
    background-color: rgb(60, 70, 80);
    border-radius: 4px;
    padding: 5px;
    min-height: 20px;
}

QLineEdit:read-only {
    color: rgb(150, 150, 150);
    background-color: rgb(50, 60, 70);
}

QSpinBox {
    color: rgb(220, 220, 220);
    border: 0px solid;
    background-color: rgb(60, 70, 80);
    border-radius: 4px;
    padding: 5px;
    min-height: 20px;
}

QComboBox {
    color: rgb(220, 220, 220);
    border: 0px solid;
    background-color: rgb(60, 70, 80);
    border-radius: 4px;
    padding: 5px;
    min-height: 20px;
}

QComboBox::drop-down {
    border: none;
    padding-right: 10px;
}

QComboBox QAbstractItemView {
    background-color: rgb(60, 70, 80);
    color: rgb(220, 220, 220);
    selection-background-color: rgb(80, 100, 120);
}

QPushButton {
    background-color: rgb(60, 70, 80);
    border-radius: 3px;
    border: 0px;
    font-size: 10pt;
    padding: 8px 35px;
    min-height: 20px;
}

QPushButton:hover {
    background-color: rgb(80, 90, 100);
}

QPushButton:pressed {
    background-color: rgb(120, 130, 140);
}

QPushButton[accessibleName="submitButton"] {
    background-color: rgb(50, 120, 180);
    font-weight: bold;
}

QPushButton[accessibleName="submitButton"]:hover {
    background-color: rgb(70, 140, 200);
}

QGroupBox {
    border: 2px solid rgb(30, 40, 50);
    border-radius: 6px;
    margin-top: 12px;
    font-size: 10pt;
    padding-top: 5px;
}

QGroupBox::title {
    subcontrol-origin: margin;
    subcontrol-position: top left;
    padding: 0 5px;
    color: rgb(180, 180, 180);
}

QFrame[accessibleName="separator"] {
    background-color: rgb(30, 40, 50);
    max-height: 2px;
    margin: 10px 0px;
}

QScrollArea {
    border: none;
}
"""


class CueLabelLine(QtWidgets.QWidget):
    """Section header with label and line separator."""

    def __init__(self, text, parent=None):
        super(CueLabelLine, self).__init__(parent)
        layout = QtWidgets.QHBoxLayout(self)
        layout.setContentsMargins(0, 15, 0, 5)

        label = QtWidgets.QLabel(text)
        label.setAccessibleName("sectionLabel")

        line = QtWidgets.QFrame()
        line.setAccessibleName("separator")
        line.setFrameShape(QtWidgets.QFrame.HLine)
        line.setFixedHeight(2)

        layout.addWidget(label)
        layout.addWidget(line, 1)


class CueLabelLineEdit(QtWidgets.QWidget):
    """Label + LineEdit combo widget."""

    textChanged = QtCore.Signal(str)

    def __init__(self, label, defaultText="", tooltip="", parent=None):
        super(CueLabelLineEdit, self).__init__(parent)
        layout = QtWidgets.QHBoxLayout(self)
        layout.setContentsMargins(0, 2, 0, 2)

        self.label = QtWidgets.QLabel(label)
        self.label.setFixedWidth(100)
        self.lineEdit = QtWidgets.QLineEdit(defaultText)
        if tooltip:
            self.lineEdit.setToolTip(tooltip)

        layout.addWidget(self.label)
        layout.addWidget(self.lineEdit, 1)

        self.lineEdit.textChanged.connect(self.textChanged.emit)

    def text(self):
        return self.lineEdit.text()

    def setText(self, text):
        self.lineEdit.setText(text)

    def setReadOnly(self, readOnly):
        self.lineEdit.setReadOnly(readOnly)


class CueLabelComboBox(QtWidgets.QWidget):
    """Label + ComboBox combo widget."""

    def __init__(self, label, options=None, parent=None):
        super(CueLabelComboBox, self).__init__(parent)
        layout = QtWidgets.QHBoxLayout(self)
        layout.setContentsMargins(0, 2, 0, 2)

        self.label = QtWidgets.QLabel(label)
        self.label.setFixedWidth(100)
        self.comboBox = QtWidgets.QComboBox()
        if options:
            self.comboBox.addItems(options)

        layout.addWidget(self.label)
        layout.addWidget(self.comboBox, 1)

    def currentText(self):
        return self.comboBox.currentText()

    def setCurrentText(self, text):
        idx = self.comboBox.findText(text)
        if idx >= 0:
            self.comboBox.setCurrentIndex(idx)

    def addItems(self, items):
        self.comboBox.addItems(items)


class CueLabelSpinBox(QtWidgets.QWidget):
    """Label + SpinBox combo widget."""

    def __init__(self, label, value=0, minVal=0, maxVal=99999, parent=None):
        super(CueLabelSpinBox, self).__init__(parent)
        layout = QtWidgets.QHBoxLayout(self)
        layout.setContentsMargins(0, 2, 0, 2)

        self.label = QtWidgets.QLabel(label)
        self.label.setFixedWidth(100)
        self.spinBox = QtWidgets.QSpinBox()
        self.spinBox.setRange(minVal, maxVal)
        self.spinBox.setValue(value)

        layout.addWidget(self.label)
        layout.addWidget(self.spinBox, 1)

    def value(self):
        return self.spinBox.value()

    def setValue(self, value):
        self.spinBox.setValue(value)


class SubmitWidget(QtWidgets.QWidget):
    """Main submission widget following CueSubmit patterns."""

    def __init__(self, filename=None, cameras=None, parent=None):
        super(SubmitWidget, self).__init__(parent)
        self.filename = filename or ""
        self.cameras = cameras or []
        self.setupUi()
        self.setupConnections()
        self.loadSceneDefaults()

    def setupUi(self):
        """Create the widget layout matching CueSubmit."""
        mainLayout = QtWidgets.QVBoxLayout(self)
        mainLayout.setContentsMargins(0, 0, 0, 0)
        mainLayout.setSpacing(0)

        # Scroll area
        scrollArea = QtWidgets.QScrollArea()
        scrollArea.setWidgetResizable(True)
        scrollArea.setFrameShape(QtWidgets.QFrame.NoFrame)

        scrollWidget = QtWidgets.QWidget()
        scrollLayout = QtWidgets.QVBoxLayout(scrollWidget)
        scrollLayout.setContentsMargins(10, 10, 10, 10)
        scrollLayout.setSpacing(0)

        # Logo placeholder - use text for now
        titleLabel = QtWidgets.QLabel("OpenCue")
        titleLabel.setStyleSheet("""
            font-size: 24pt;
            font-weight: bold;
            color: rgb(100, 180, 255);
            padding: 10px;
        """)
        scrollLayout.addWidget(titleLabel)

        # === Job Info Section ===
        scrollLayout.addWidget(CueLabelLine("Job Info"))

        jobInfoLayout = QtWidgets.QVBoxLayout()
        jobInfoLayout.setContentsMargins(20, 0, 0, 0)
        jobInfoLayout.setSpacing(5)

        self.jobNameInput = CueLabelLineEdit(
            "Job Name:",
            tooltip="Job names must be unique, have more than 3 characters, and contain no spaces."
        )
        jobInfoLayout.addWidget(self.jobNameInput)

        # Show and Shot row
        showShotLayout = QtWidgets.QHBoxLayout()
        self.showInput = CueLabelLineEdit("Show:", "testing")
        self.shotInput = CueLabelLineEdit("Shot:", "shot01")
        showShotLayout.addWidget(self.showInput)
        showShotLayout.addWidget(self.shotInput)
        jobInfoLayout.addLayout(showShotLayout)

        # Username
        self.userNameInput = CueLabelLineEdit(
            "User Name:",
            getpass.getuser(),
            tooltip="User name that should be associated with this job."
        )
        jobInfoLayout.addWidget(self.userNameInput)

        scrollLayout.addLayout(jobInfoLayout)

        # === Layer Info Section ===
        scrollLayout.addWidget(CueLabelLine("Layer Info"))

        layerInfoLayout = QtWidgets.QVBoxLayout()
        layerInfoLayout.setContentsMargins(20, 0, 0, 0)
        layerInfoLayout.setSpacing(5)

        self.layerNameInput = CueLabelLineEdit("Layer Name:", "render")
        layerInfoLayout.addWidget(self.layerNameInput)

        # Frame Range row
        frameLayout = QtWidgets.QHBoxLayout()
        frameLabel = QtWidgets.QLabel("Frame Range:")
        frameLabel.setFixedWidth(100)
        self.startFrameInput = QtWidgets.QSpinBox()
        self.startFrameInput.setRange(0, 99999)
        self.startFrameInput.setFixedWidth(80)
        dashLabel = QtWidgets.QLabel("-")
        dashLabel.setFixedWidth(15)
        dashLabel.setAlignment(QtCore.Qt.AlignCenter)
        self.endFrameInput = QtWidgets.QSpinBox()
        self.endFrameInput.setRange(0, 99999)
        self.endFrameInput.setFixedWidth(80)

        chunkLabel = QtWidgets.QLabel("Chunk:")
        chunkLabel.setFixedWidth(50)
        self.chunkInput = QtWidgets.QSpinBox()
        self.chunkInput.setRange(1, 1000)
        self.chunkInput.setValue(1)
        self.chunkInput.setFixedWidth(60)

        frameLayout.addWidget(frameLabel)
        frameLayout.addWidget(self.startFrameInput)
        frameLayout.addWidget(dashLabel)
        frameLayout.addWidget(self.endFrameInput)
        frameLayout.addSpacing(20)
        frameLayout.addWidget(chunkLabel)
        frameLayout.addWidget(self.chunkInput)
        frameLayout.addStretch()
        layerInfoLayout.addLayout(frameLayout)

        # Services
        self.servicesInput = CueLabelLineEdit("Services:", "maya")
        layerInfoLayout.addWidget(self.servicesInput)

        scrollLayout.addLayout(layerInfoLayout)

        # === Maya Options Section ===
        scrollLayout.addWidget(CueLabelLine("Maya Options"))

        mayaLayout = QtWidgets.QVBoxLayout()
        mayaLayout.setContentsMargins(20, 0, 0, 0)
        mayaLayout.setSpacing(5)

        self.mayaFileInput = CueLabelLineEdit("Maya File:")
        self.mayaFileInput.setReadOnly(True)
        mayaLayout.addWidget(self.mayaFileInput)

        self.rendererInput = CueLabelComboBox(
            "Renderer:",
            ["file", "arnold", "redshift", "mayaHardware2"]
        )
        mayaLayout.addWidget(self.rendererInput)

        self.cameraInput = CueLabelComboBox("Camera:")
        self.cameraInput.comboBox.addItem("")  # Empty option
        self.cameraInput.comboBox.addItems(self.cameras)
        mayaLayout.addWidget(self.cameraInput)

        scrollLayout.addLayout(mayaLayout)

        # === Submission Details Section ===
        scrollLayout.addWidget(CueLabelLine("Submission Details"))

        detailsLayout = QtWidgets.QVBoxLayout()
        detailsLayout.setContentsMargins(20, 0, 0, 0)

        # Command preview
        self.commandPreview = QtWidgets.QTextEdit()
        self.commandPreview.setReadOnly(True)
        self.commandPreview.setMaximumHeight(60)
        self.commandPreview.setStyleSheet("""
            QTextEdit {
                background-color: rgb(30, 35, 40);
                color: rgb(150, 150, 150);
                border: none;
                border-radius: 4px;
                font-family: Consolas, monospace;
                font-size: 9pt;
                padding: 5px;
            }
        """)
        detailsLayout.addWidget(self.commandPreview)

        scrollLayout.addLayout(detailsLayout)

        # Spacer
        scrollLayout.addStretch()

        # Buttons
        buttonLayout = QtWidgets.QHBoxLayout()
        buttonLayout.setContentsMargins(20, 20, 20, 10)
        buttonLayout.addStretch()

        self.cancelButton = QtWidgets.QPushButton("Cancel")
        self.submitButton = QtWidgets.QPushButton("Submit")
        self.submitButton.setAccessibleName("submitButton")

        buttonLayout.addWidget(self.cancelButton)
        buttonLayout.addWidget(self.submitButton)
        scrollLayout.addLayout(buttonLayout)

        scrollArea.setWidget(scrollWidget)
        mainLayout.addWidget(scrollArea)

    def setupConnections(self):
        """Connect widget signals."""
        self.submitButton.clicked.connect(self.submit)
        self.cancelButton.clicked.connect(self.cancel)

        # Update command preview on changes
        self.mayaFileInput.textChanged.connect(self.updateCommandPreview)
        self.rendererInput.comboBox.currentTextChanged.connect(self.updateCommandPreview)
        self.cameraInput.comboBox.currentTextChanged.connect(self.updateCommandPreview)
        self.startFrameInput.valueChanged.connect(self.updateCommandPreview)
        self.endFrameInput.valueChanged.connect(self.updateCommandPreview)

    def loadSceneDefaults(self):
        """Load defaults from the current Maya scene."""
        self.mayaFileInput.setText(self.filename)

        if self.filename:
            jobName = os.path.splitext(os.path.basename(self.filename))[0]
            self.jobNameInput.setText(jobName)

        # Get frame range from render globals
        try:
            startFrame = int(cmds.getAttr("defaultRenderGlobals.startFrame"))
            endFrame = int(cmds.getAttr("defaultRenderGlobals.endFrame"))
            self.startFrameInput.setValue(startFrame)
            self.endFrameInput.setValue(endFrame)
        except Exception:
            self.startFrameInput.setValue(1)
            self.endFrameInput.setValue(100)

        # Get current renderer
        try:
            renderer = cmds.getAttr("defaultRenderGlobals.currentRenderer")
            self.rendererInput.setCurrentText(renderer)
        except Exception:
            pass

        self.updateCommandPreview()

    def updateCommandPreview(self):
        """Update the command preview text."""
        mayaFile = self.mayaFileInput.text()
        renderer = self.rendererInput.currentText()
        camera = self.cameraInput.currentText()

        cmd = "Render -r {} -s #FRAME_START# -e #FRAME_END#".format(renderer)
        if camera:
            cmd += " -cam {}".format(camera)
        if mayaFile:
            cmd += ' "{}"'.format(mayaFile)

        self.commandPreview.setText(cmd)

    def validate(self):
        """Validate the submission data."""
        errors = []

        if not self.jobNameInput.text().strip():
            errors.append("Job name is required")

        if not self.mayaFileInput.text().strip():
            errors.append("Maya file is required (save your scene first)")

        if not self.showInput.text().strip():
            errors.append("Show is required")

        if self.startFrameInput.value() > self.endFrameInput.value():
            errors.append("Start frame must be less than or equal to end frame")

        return errors

    def getJobData(self):
        """Collect all job data into a dictionary."""
        frameRange = "{}-{}".format(
            self.startFrameInput.value(),
            self.endFrameInput.value()
        )

        # Build layer data
        layerData = {
            "name": self.layerNameInput.text(),
            "layerType": "Maya",
            "layerRange": frameRange,
            "chunk": self.chunkInput.value(),
            "services": [s.strip() for s in self.servicesInput.text().split(",") if s.strip()],
            "cmd": {
                "mayaFile": self.mayaFileInput.text(),
                "camera": self.cameraInput.currentText(),
                "renderer": self.rendererInput.currentText(),
            }
        }

        jobData = {
            "name": self.jobNameInput.text(),
            "show": self.showInput.text(),
            "shot": self.shotInput.text(),
            "username": self.userNameInput.text(),
            "layers": [layerData],
        }

        return jobData

    def submit(self):
        """Submit the job to OpenCue via external Python process."""
        errors = self.validate()
        if errors:
            QtWidgets.QMessageBox.warning(
                self, "Validation Error",
                "\n".join(errors)
            )
            return

        jobData = self.getJobData()

        # Write job data to temp file
        with tempfile.NamedTemporaryFile(
            mode='w', suffix='.json', delete=False, encoding='utf-8'
        ) as f:
            json.dump(jobData, f, indent=2)
            jobDataFile = f.name

        try:
            # Call external submitter
            submitterScript = os.path.join(
                os.path.dirname(__file__), "maya_submit_worker.py"
            )

            result = subprocess.run(
                [PYTHON_PATH, submitterScript, jobDataFile, CUEBOT_HOST],
                capture_output=True,
                text=True
            )

            if result.returncode == 0:
                # Success dialog matching CueSubmit style
                msg = QtWidgets.QMessageBox(self)
                msg.setWindowTitle("Submitted Job Data")
                msg.setText("Submitted Job to OpenCue.\n\n{}".format(result.stdout))
                msg.setStyleSheet(MAIN_STYLE)
                msg.exec_()
                self.window().close()
            else:
                msg = QtWidgets.QMessageBox(self)
                msg.setWindowTitle("Failed Job Submission")
                msg.setText("Failed to submit job!\n\n{}".format(
                    result.stderr or result.stdout
                ))
                msg.setIcon(QtWidgets.QMessageBox.Critical)
                msg.setStyleSheet(MAIN_STYLE)
                msg.exec_()
        finally:
            # Clean up temp file
            try:
                os.unlink(jobDataFile)
            except Exception:
                pass

    def cancel(self):
        """Close the dialog."""
        self.window().close()


class CueSubmitMainWindow(QtWidgets.QMainWindow):
    """Main window for the submission UI."""

    def __init__(self, name, filename=None, cameras=None, parent=None):
        super(CueSubmitMainWindow, self).__init__(parent)
        self.setWindowFlags(QtCore.Qt.Window)
        self.setProperty('saveWindowPref', True)
        self.submitWidget = SubmitWidget(
            filename=filename,
            cameras=cameras,
            parent=self
        )
        self.setStyleSheet(MAIN_STYLE)
        self.setCentralWidget(self.submitWidget)
        self.setWindowTitle(name)
        self.setMinimumWidth(650)
        self.resize(650, 700)


def getFilename():
    """Return the current Maya scene filename."""
    return cmds.file(q=True, sn=True)


def getCameras():
    """Return a list of cameras in the current Maya scene."""
    cameraShapes = cmds.ls(type='camera')
    if cameraShapes:
        return cmds.listRelatives(cameraShapes, p=True) or []
    return []


def deleteExistingUi():
    """Delete the existing UI before launching a new one."""
    controlName = UI_NAME + 'WorkspaceControl'
    if cmds.workspaceControl(controlName, q=True, exists=True):
        cmds.workspaceControl(controlName, e=True, close=True)
        cmds.deleteUI(controlName, control=True)


def setupLogging():
    """Enable logging."""
    if not log.handlers:
        log.propagate = False
        handler = maya.utils.MayaGuiLogHandler()
        handler.setLevel(logging.INFO)
        formatter = logging.Formatter('%(asctime)s [%(name)s] - %(message)s')
        handler.setFormatter(formatter)
        log.addHandler(handler)


def main():
    """Launch the submit dialog."""
    global window
    deleteExistingUi()
    setupLogging()

    # Get Maya window as parent
    parent = None
    for widget in QtWidgets.QApplication.topLevelWidgets():
        if widget.objectName() == "MayaWindow":
            parent = widget
            break

    window = CueSubmitMainWindow(
        'Submit to OpenCue',
        filename=getFilename(),
        cameras=getCameras(),
        parent=parent
    )
    window.show()


# Convenience aliases
show = main
launch = main
