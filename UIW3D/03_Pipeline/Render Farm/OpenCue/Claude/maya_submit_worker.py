#!/usr/bin/env python
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
OpenCue submission worker for Maya 2026.

This script runs in Python 3.9 where OpenCue libraries work correctly.
It receives job data from the Maya UI and submits directly via opencue API
to avoid wrapper script path issues on Windows.

Usage:
    python maya_submit_worker.py <job_data.json> <cuebot_host>
"""

import json
import os
import sys

# Add OpenCue libraries to path
SITE_PACKAGES = r"C:\Program Files\Python39\Lib\site-packages"
sys.path.insert(0, SITE_PACKAGES)

# Import OpenCue after path setup
from opencue.cuebot import Cuebot
import opencue


# Frame tokens used by OpenCue
FRAME_TOKEN = "#IFRAME#"
FRAME_START_TOKEN = "#FRAME_START#"
FRAME_END_TOKEN = "#FRAME_END#"

# Log path configuration
LOG_ROOT = r"\\10.40.14.25\RenderOutputRepo\OpenCue\Logs"

# Maya configuration
MAYA_RENDER_EXE = r"C:/Program Files/Autodesk/Maya2026/bin/Render.exe"


def buildMayaCmd(layerData):
    """Build a Maya Render command from layer data."""
    cmd = layerData.get("cmd", {})
    mayaFile = cmd.get("mayaFile", "")
    camera = cmd.get("camera", "")
    renderer = cmd.get("renderer", "file")

    if not mayaFile:
        raise ValueError("No Maya file provided")

    # Build render command - use forward slashes for consistency
    mayaFile = mayaFile.replace("\\", "/")

    renderCmd = '"{}" -r {} -s {} -e {}'.format(
        MAYA_RENDER_EXE,
        renderer,
        FRAME_START_TOKEN,
        FRAME_END_TOKEN
    )

    if camera:
        renderCmd += " -cam {}".format(camera)

    renderCmd += ' "{}"'.format(mayaFile)

    return renderCmd


def buildJobSpec(jobData):
    """Build an XML job spec for direct submission to OpenCue."""
    show = jobData.get("show", "testing")
    shot = jobData.get("shot", "shot01")
    jobName = jobData.get("name", "maya_job")
    username = jobData.get("username", "render")
    # Use UID 1000+ to avoid root (0) rejection - typical non-root user range
    uid = 1000

    layers_xml = ""
    for layerData in jobData.get("layers", []):
        layerName = layerData.get("name", "render")
        frameRange = layerData.get("layerRange", "1-1")
        chunk = layerData.get("chunk", 1)
        services = layerData.get("services", ["maya"])
        service = services[0] if services else "maya"

        if layerData.get("layerType") == "Maya":
            command = buildMayaCmd(layerData)
        else:
            raise ValueError("Unsupported layer type: {}".format(layerData.get("layerType")))

        layers_xml += """
      <layer name="{name}" type="Render">
        <cmd>{cmd}</cmd>
        <range>{range}</range>
        <chunk>{chunk}</chunk>
        <services>
          <service>{service}</service>
        </services>
      </layer>""".format(
            name=layerName,
            cmd=command,
            range=frameRange,
            chunk=chunk,
            service=service
        )

    spec = """<?xml version="1.0"?>
<!DOCTYPE spec PUBLIC "SPI Cue Specification Language" "http://localhost:8080/spcue/dtd/cjsl-1.12.dtd">
<spec>
  <facility>local</facility>
  <show>{show}</show>
  <shot>{shot}</shot>
  <user>{user}</user>
  <uid>{uid}</uid>
  <job name="{jobName}">
    <paused>False</paused>
    <os>Windows</os>
    <layers>{layers}
    </layers>
  </job>
</spec>""".format(
        show=show,
        shot=shot,
        user=username,
        uid=uid,
        jobName=jobName,
        layers=layers_xml
    )

    return spec


def getLogPath(jobData, jobName):
    """Build the log file path for a job."""
    show = jobData.get("show", "testing")
    shot = jobData.get("shot", "shot01")
    # Log path format: LOG_ROOT/show/shot/logs/jobName
    return os.path.join(LOG_ROOT, show, shot, "logs", jobName)


def submitJob(jobData):
    """Submit a job directly using opencue.api.launchSpecAndWait."""
    spec = buildJobSpec(jobData)
    jobs = opencue.api.launchSpecAndWait(spec)
    return jobs


def main():
    if len(sys.argv) < 3:
        print("Usage: maya_submit_worker.py <job_data.json> <cuebot_host>", file=sys.stderr)
        sys.exit(1)

    jobDataFile = sys.argv[1]
    cuebotHost = sys.argv[2]

    # Configure Cuebot connection
    Cuebot.setHosts([cuebotHost])

    # Load job data
    with open(jobDataFile, 'r', encoding='utf-8') as f:
        jobData = json.load(f)

    # Submit the job
    try:
        jobs = submitJob(jobData)
        if jobs:
            for job in jobs:
                jobName = job.name()
                jobId = job.id()
                logPath = getLogPath(jobData, jobName)
                print("Job Name: {}".format(jobName))
                print("Job ID: {}".format(jobId))
                print("Log Path: {}".format(logPath))
        else:
            print("Job submitted successfully")
    except Exception as e:
        import traceback
        print("Submission error: {}".format(e), file=sys.stderr)
        traceback.print_exc(file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
