"""
OpenCue Maya Render Submission Script
For Maya 2026 with Arnold

This script provides a UI for submitting Maya renders to OpenCue.
Place in your Maya scripts folder or add to MAYA_SCRIPT_PATH.

Usage in Maya:
    import opencue_submit
    opencue_submit.show()
"""

import os
import sys
import re
from functools import partial

# Maya imports
import maya.cmds as cmds
import maya.mel as mel

# Add OpenCue to path if needed (adjust path as necessary)
OPENCUE_PYTHON_PATH = os.environ.get("OPENCUE_PYTHON_PATH", "")
if OPENCUE_PYTHON_PATH and OPENCUE_PYTHON_PATH not in sys.path:
    sys.path.insert(0, OPENCUE_PYTHON_PATH)

# OpenCue imports
try:
    import outline
    import outline.modules.shell
    import outline.cuerun
    import opencue
    OPENCUE_AVAILABLE = True
except ImportError as e:
    OPENCUE_AVAILABLE = False
    OPENCUE_ERROR = str(e)


# ============================================================================
# Configuration - EDIT THESE FOR YOUR ENVIRONMENT
# ============================================================================

# Default show name for jobs
DEFAULT_SHOW = "maya_renders"

# UNC path prefix for render files (how render nodes access files)
# This should point to your P4 workspace on the Linux server
UNC_PATH_PREFIX = r"\\YOUR_LINUX_SERVER\p4workspace"

# Local path prefix (what artists use locally with S: drive)
LOCAL_PATH_PREFIX = "S:"

# Maya executable on render nodes
MAYA_EXECUTABLE = "maya"

# Arnold renderer command
ARNOLD_RENDERER = "arnold"

# Default service (must match service created in OpenCue)
DEFAULT_SERVICE = "maya2026"


# ============================================================================
# Path Conversion
# ============================================================================

def convert_to_render_path(local_path):
    """Convert local path (S:\...) to UNC path for render nodes."""
    if local_path.startswith(LOCAL_PATH_PREFIX):
        return local_path.replace(LOCAL_PATH_PREFIX, UNC_PATH_PREFIX, 1)
    return local_path


def get_scene_info():
    """Get current scene information."""
    scene_file = cmds.file(query=True, sceneName=True)
    if not scene_file:
        return None

    # Get frame range
    start_frame = int(cmds.playbackOptions(query=True, animationStartTime=True))
    end_frame = int(cmds.playbackOptions(query=True, animationEndTime=True))

    # Try to get render range if set differently
    try:
        render_start = int(cmds.getAttr("defaultRenderGlobals.startFrame"))
        render_end = int(cmds.getAttr("defaultRenderGlobals.endFrame"))
        if render_start > 0 or render_end > 0:
            start_frame = render_start
            end_frame = render_end
    except:
        pass

    # Get renderer
    renderer = cmds.getAttr("defaultRenderGlobals.currentRenderer") or "arnold"

    # Get renderable cameras
    cameras = []
    for cam in cmds.ls(type="camera"):
        if cmds.getAttr(f"{cam}.renderable"):
            transform = cmds.listRelatives(cam, parent=True)[0]
            cameras.append(transform)

    # Get render layers
    layers = cmds.ls(type="renderLayer")
    render_layers = [l for l in layers if not l.startswith("defaultRenderLayer")]
    if not render_layers:
        render_layers = ["defaultRenderLayer"]

    # Get output path
    output_path = ""
    try:
        output_path = cmds.workspace(fileRuleEntry="images")
        workspace = cmds.workspace(query=True, rootDirectory=True)
        output_path = os.path.join(workspace, output_path)
    except:
        pass

    return {
        "scene_file": scene_file,
        "scene_name": os.path.splitext(os.path.basename(scene_file))[0],
        "start_frame": start_frame,
        "end_frame": end_frame,
        "renderer": renderer,
        "cameras": cameras,
        "render_layers": render_layers,
        "output_path": output_path
    }


# ============================================================================
# Submission Functions
# ============================================================================

def submit_render(job_name, show, shot, start_frame, end_frame,
                  scene_file, renderer, camera, chunk_size=1,
                  min_cores=4, min_memory=8192, priority=100,
                  render_layers=None):
    """Submit a render job to OpenCue."""

    if not OPENCUE_AVAILABLE:
        cmds.error(f"OpenCue not available: {OPENCUE_ERROR}")
        return None

    # Convert scene path for render nodes
    render_scene_path = convert_to_render_path(scene_file)

    # Create job
    job = outline.Outline(
        name=job_name,
        shot=shot,
        show=show,
        user=os.environ.get("USERNAME", os.environ.get("USER", "maya_user"))
    )
    job.set_priority(priority)

    # Build render command
    if renderer.lower() == "arnold":
        # Arnold batch render
        cmd = [
            MAYA_EXECUTABLE, "-batch",
            "-file", render_scene_path,
            "-renderer", "arnold",
            "-camera", camera,
            "-s", "#IFRAME#",
            "-e", "#IFRAME#"
        ]
    else:
        # Generic Maya batch render
        cmd = [
            MAYA_EXECUTABLE, "-batch",
            "-file", render_scene_path,
            "-renderer", renderer,
            "-camera", camera,
            "-s", "#IFRAME#",
            "-e", "#IFRAME#"
        ]

    # Create render layer
    render_layer = outline.modules.shell.Shell(
        name="render",
        command=cmd,
        range=f"{start_frame}-{end_frame}",
        chunk=chunk_size
    )

    # Set resource requirements
    render_layer.set_min_cores(min_cores)
    render_layer.set_min_memory(min_memory)
    render_layer.set_service(DEFAULT_SERVICE)

    # Set environment variables for render nodes
    render_layer.set_env("MAYA_LOCATION", os.environ.get("MAYA_LOCATION", ""))
    render_layer.set_env("ARNOLD_PATH", os.environ.get("ARNOLD_PATH", ""))

    job.add_layer(render_layer)

    # Submit
    try:
        job_ids = outline.cuerun.launch(job, use_pycuerun=False)
        print(f"Submitted job: {job_name}")
        print(f"Job IDs: {job_ids}")
        return job_name
    except Exception as e:
        cmds.error(f"Failed to submit job: {e}")
        return None


# ============================================================================
# Maya UI
# ============================================================================

WINDOW_NAME = "opencueSubmitWindow"


def show():
    """Show the OpenCue submission window."""

    if not OPENCUE_AVAILABLE:
        cmds.confirmDialog(
            title="OpenCue Error",
            message=f"OpenCue Python modules not found.\n\n{OPENCUE_ERROR}\n\nEnsure pycue and pyoutline are installed.",
            button=["OK"]
        )
        return

    # Close existing window
    if cmds.window(WINDOW_NAME, exists=True):
        cmds.deleteUI(WINDOW_NAME)

    # Get scene info
    scene_info = get_scene_info()
    if not scene_info:
        cmds.confirmDialog(
            title="No Scene",
            message="Please save your scene before submitting.",
            button=["OK"]
        )
        return

    # Create window
    window = cmds.window(WINDOW_NAME, title="OpenCue Render Submission", widthHeight=(450, 500))
    main_layout = cmds.columnLayout(adjustableColumn=True, rowSpacing=5)

    # Header
    cmds.text(label="OpenCue Render Submission", font="boldLabelFont", height=30)
    cmds.separator(style="in")

    # Job Information
    cmds.frameLayout(label="Job Information", collapsable=True, collapse=False)
    cmds.columnLayout(adjustableColumn=True, rowSpacing=3)

    job_name = cmds.textFieldGrp(
        label="Job Name:",
        text=f"maya-{scene_info['scene_name']}-v001",
        columnWidth=[(1, 100), (2, 300)]
    )

    show_field = cmds.textFieldGrp(
        label="Show:",
        text=DEFAULT_SHOW,
        columnWidth=[(1, 100), (2, 300)]
    )

    shot_field = cmds.textFieldGrp(
        label="Shot:",
        text=scene_info['scene_name'].split("_")[0] if "_" in scene_info['scene_name'] else "shot",
        columnWidth=[(1, 100), (2, 300)]
    )

    cmds.setParent("..")
    cmds.setParent("..")

    # Render Settings
    cmds.frameLayout(label="Render Settings", collapsable=True, collapse=False)
    cmds.columnLayout(adjustableColumn=True, rowSpacing=3)

    cmds.text(label=f"Scene: {scene_info['scene_file']}", align="left")
    cmds.text(label=f"(Render path: {convert_to_render_path(scene_info['scene_file'])})",
              align="left", font="smallObliqueLabelFont")

    start_frame_field = cmds.intFieldGrp(
        label="Start Frame:",
        value1=scene_info['start_frame'],
        columnWidth=[(1, 100), (2, 100)]
    )

    end_frame_field = cmds.intFieldGrp(
        label="End Frame:",
        value1=scene_info['end_frame'],
        columnWidth=[(1, 100), (2, 100)]
    )

    chunk_size_field = cmds.intFieldGrp(
        label="Chunk Size:",
        value1=1,
        columnWidth=[(1, 100), (2, 100)],
        annotation="Frames per task (1 = one frame per task)"
    )

    camera_menu = cmds.optionMenuGrp(label="Camera:", columnWidth=[(1, 100)])
    for cam in scene_info['cameras']:
        cmds.menuItem(label=cam)

    renderer_menu = cmds.optionMenuGrp(label="Renderer:", columnWidth=[(1, 100)])
    cmds.menuItem(label="arnold")
    cmds.menuItem(label="mayaHardware2")
    cmds.menuItem(label="mayaSoftware")

    cmds.setParent("..")
    cmds.setParent("..")

    # Resource Settings
    cmds.frameLayout(label="Resource Requirements", collapsable=True, collapse=False)
    cmds.columnLayout(adjustableColumn=True, rowSpacing=3)

    cores_field = cmds.intSliderGrp(
        label="Min Cores:",
        field=True,
        value=4,
        minValue=1,
        maxValue=32,
        fieldMinValue=1,
        fieldMaxValue=64,
        columnWidth=[(1, 100), (2, 50), (3, 200)]
    )

    memory_field = cmds.intSliderGrp(
        label="Min Memory (MB):",
        field=True,
        value=8192,
        minValue=2048,
        maxValue=65536,
        fieldMinValue=1024,
        fieldMaxValue=131072,
        columnWidth=[(1, 100), (2, 60), (3, 190)]
    )

    priority_field = cmds.intSliderGrp(
        label="Priority:",
        field=True,
        value=100,
        minValue=1,
        maxValue=200,
        columnWidth=[(1, 100), (2, 50), (3, 200)]
    )

    cmds.setParent("..")
    cmds.setParent("..")

    cmds.separator(style="in", height=20)

    # Buttons
    cmds.rowLayout(numberOfColumns=2, columnWidth=[(1, 220), (2, 220)])

    def do_submit(*args):
        """Submit button callback."""
        result = submit_render(
            job_name=cmds.textFieldGrp(job_name, query=True, text=True),
            show=cmds.textFieldGrp(show_field, query=True, text=True),
            shot=cmds.textFieldGrp(shot_field, query=True, text=True),
            start_frame=cmds.intFieldGrp(start_frame_field, query=True, value1=True),
            end_frame=cmds.intFieldGrp(end_frame_field, query=True, value1=True),
            scene_file=scene_info['scene_file'],
            renderer=cmds.optionMenuGrp(renderer_menu, query=True, value=True),
            camera=cmds.optionMenuGrp(camera_menu, query=True, value=True),
            chunk_size=cmds.intFieldGrp(chunk_size_field, query=True, value1=True),
            min_cores=cmds.intSliderGrp(cores_field, query=True, value=True),
            min_memory=cmds.intSliderGrp(memory_field, query=True, value=True),
            priority=cmds.intSliderGrp(priority_field, query=True, value=True)
        )

        if result:
            cmds.confirmDialog(
                title="Job Submitted",
                message=f"Successfully submitted job:\n{result}\n\nCheck CueGUI to monitor progress.",
                button=["OK"]
            )
            cmds.deleteUI(WINDOW_NAME)

    cmds.button(label="Submit to OpenCue", command=do_submit, height=40, backgroundColor=[0.2, 0.5, 0.2])
    cmds.button(label="Cancel", command=lambda x: cmds.deleteUI(WINDOW_NAME), height=40)

    cmds.setParent("..")
    cmds.setParent("..")

    cmds.showWindow(window)


# ============================================================================
# Shelf Button Creation
# ============================================================================

def create_shelf_button():
    """Create an OpenCue shelf button in the current shelf."""
    current_shelf = mel.eval('tabLayout -q -selectTab $gShelfTopLevel')

    cmds.shelfButton(
        parent=current_shelf,
        label="OpenCue",
        annotation="Submit render to OpenCue",
        image="render.png",  # Use a default Maya icon
        command="import opencue_submit; opencue_submit.show()",
        sourceType="python"
    )

    print(f"OpenCue shelf button added to {current_shelf}")


# ============================================================================
# Auto-run when imported
# ============================================================================

if __name__ == "__main__":
    show()
