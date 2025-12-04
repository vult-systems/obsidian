"""
OpenCue Maya userSetup.py
Add this to your Maya scripts folder to auto-load OpenCue integration.

Location:
  Windows: %USERPROFILE%\Documents\maya\<version>\scripts\userSetup.py
  Linux:   ~/maya/<version>/scripts/userSetup.py

Or add to MAYA_SCRIPT_PATH environment variable.
"""

import os
import sys
import maya.cmds as cmds
import maya.mel as mel


def setup_opencue():
    """Setup OpenCue environment for Maya."""

    # =========================================================================
    # CONFIGURATION - EDIT THESE
    # =========================================================================

    # Cuebot server hostname (for pycue to connect)
    CUEBOT_HOSTNAME = "YOUR_LINUX_SERVER_HOSTNAME"

    # Path to OpenCue Python packages (if not installed in Maya's Python)
    # Leave empty if installed via pip in Maya's Python environment
    OPENCUE_PYTHON_PATH = ""

    # =========================================================================

    # Set environment variables
    os.environ["CUEBOT_HOSTNAME"] = CUEBOT_HOSTNAME

    if OPENCUE_PYTHON_PATH and OPENCUE_PYTHON_PATH not in sys.path:
        sys.path.insert(0, OPENCUE_PYTHON_PATH)

    # Create OpenCue config if it doesn't exist
    config_dir = os.path.join(os.environ.get("APPDATA", ""), "opencue")
    config_file = os.path.join(config_dir, "opencue.yaml")

    if not os.path.exists(config_file):
        if not os.path.exists(config_dir):
            os.makedirs(config_dir)

        config_content = f"""cuebot.facility_default: local
cuebot.facility:
    local:
        - {CUEBOT_HOSTNAME}:8443
"""
        with open(config_file, "w") as f:
            f.write(config_content)
        print(f"[OpenCue] Created config: {config_file}")

    # Test connection
    try:
        import opencue
        hosts = opencue.api.getHosts()
        print(f"[OpenCue] Connected! {len(hosts)} render hosts available.")
    except ImportError:
        print("[OpenCue] WARNING: OpenCue Python modules not installed.")
        print("[OpenCue] Install with: pip install opencue-pycue opencue-pyoutline")
    except Exception as e:
        print(f"[OpenCue] WARNING: Could not connect to Cuebot: {e}")

    print("[OpenCue] Setup complete. Use 'import opencue_submit; opencue_submit.show()' to submit renders.")


def create_opencue_menu():
    """Create OpenCue menu in Maya."""

    # Wait for Maya to be ready
    if not cmds.menu("OpenCueMenu", exists=True):
        main_window = mel.eval('$temp = $gMainWindow')

        cmds.menu(
            "OpenCueMenu",
            label="OpenCue",
            parent=main_window,
            tearOff=True
        )

        cmds.menuItem(
            label="Submit Render...",
            command="import opencue_submit; opencue_submit.show()",
            annotation="Submit current scene to OpenCue render farm"
        )

        cmds.menuItem(divider=True)

        cmds.menuItem(
            label="Launch CueGUI",
            command="import subprocess; subprocess.Popen(['cuegui'])",
            annotation="Open CueGUI to monitor jobs"
        )

        cmds.menuItem(
            label="Launch CueSubmit",
            command="import subprocess; subprocess.Popen(['cuesubmit'])",
            annotation="Open CueSubmit for advanced job submission"
        )

        cmds.menuItem(divider=True)

        cmds.menuItem(
            label="Add Shelf Button",
            command="import opencue_submit; opencue_submit.create_shelf_button()",
            annotation="Add OpenCue submit button to current shelf"
        )

        cmds.menuItem(divider=True)

        cmds.menuItem(
            label="Check Connection",
            command="import opencue; hosts=opencue.api.getHosts(); print(f'Connected to {len(hosts)} hosts')",
            annotation="Test connection to Cuebot"
        )


# Run setup when Maya loads
cmds.evalDeferred(setup_opencue)
cmds.evalDeferred(create_opencue_menu)
