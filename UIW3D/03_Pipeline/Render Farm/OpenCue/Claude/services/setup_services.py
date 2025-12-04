#!/usr/bin/env python
"""
OpenCue Service Setup Script
Creates the necessary services for Maya 2026 and Arnold rendering.

Run this AFTER Cuebot is installed and running.

Usage:
    python setup_services.py --cuebot your-linux-server:8443

Or set environment variable:
    CUEBOT_HOSTS=your-linux-server:8443
    python setup_services.py
"""

import os
import sys
import argparse


def setup_environment(cuebot_host):
    """Setup OpenCue environment."""
    os.environ["CUEBOT_HOSTS"] = cuebot_host

    # Try to find and import OpenCue
    try:
        import opencue
        return True
    except ImportError:
        print("ERROR: OpenCue Python modules not found.")
        print("Install with: pip install opencue-pycue")
        return False


def create_maya2026_service():
    """Create Maya 2026 service."""
    import opencue
    from opencue.compiled_proto import service_pb2

    service = service_pb2.Service()
    service.name = "maya2026"
    service.threadable = True  # Can run multiple frames per host
    service.min_cores = 200    # 2 cores minimum (100 units = 1 core)
    service.max_cores = 800    # 8 cores maximum
    service.min_memory = 8589934592  # 8 GB in bytes
    service.min_gpu_memory = 0
    service.min_gpus = 0
    service.max_gpus = 0
    service.min_memory_increase = 2097152  # 2 GB increment
    service.timeout = 0  # No timeout
    service.timeout_llu = 0
    service.tags.extend(["maya", "maya2026", "dcc"])

    try:
        # Check if service already exists
        existing = opencue.api.getService("maya2026")
        print(f"  Service 'maya2026' already exists. Updating...")
        # Update existing service
        existing.update(service)
        return existing
    except:
        # Create new service
        created = opencue.api.createService(service)
        print(f"  Created service: maya2026")
        return created


def create_arnold_service():
    """Create Arnold renderer service."""
    import opencue
    from opencue.compiled_proto import service_pb2

    service = service_pb2.Service()
    service.name = "arnold"
    service.threadable = False  # Arnold is not threadable
    service.min_cores = 400     # 4 cores minimum
    service.max_cores = 1600    # 16 cores maximum
    service.min_memory = 17179869184  # 16 GB in bytes
    service.min_gpu_memory = 0  # Set if using GPU rendering
    service.min_gpus = 0        # Set to 1 for GPU rendering
    service.max_gpus = 0
    service.min_memory_increase = 2097152  # 2 GB increment
    service.timeout = 3600      # 1 hour timeout
    service.timeout_llu = 1800  # 30 min LLU timeout
    service.tags.extend(["arnold", "renderer", "cpu"])

    try:
        existing = opencue.api.getService("arnold")
        print(f"  Service 'arnold' already exists. Updating...")
        existing.update(service)
        return existing
    except:
        created = opencue.api.createService(service)
        print(f"  Created service: arnold")
        return created


def create_shell_service():
    """Create generic shell service for testing."""
    import opencue
    from opencue.compiled_proto import service_pb2

    service = service_pb2.Service()
    service.name = "shell"
    service.threadable = True
    service.min_cores = 100    # 1 core
    service.max_cores = 0      # Unlimited
    service.min_memory = 1073741824  # 1 GB
    service.min_gpu_memory = 0
    service.min_gpus = 0
    service.max_gpus = 0
    service.min_memory_increase = 1073741824  # 1 GB increment
    service.timeout = 0
    service.timeout_llu = 0
    service.tags.extend(["shell", "utility"])

    try:
        existing = opencue.api.getService("shell")
        print(f"  Service 'shell' already exists.")
        return existing
    except:
        created = opencue.api.createService(service)
        print(f"  Created service: shell")
        return created


def create_show(show_name="maya_renders"):
    """Create a show for Maya renders."""
    import opencue

    try:
        show = opencue.api.findShow(show_name)
        print(f"  Show '{show_name}' already exists.")
        return show
    except:
        show = opencue.api.createShow(show_name)
        print(f"  Created show: {show_name}")
        return show


def verify_setup():
    """Verify the setup is correct."""
    import opencue

    print("\n" + "=" * 50)
    print("Verification")
    print("=" * 50)

    # List services
    print("\nAvailable Services:")
    services = opencue.api.getDefaultServices()
    for svc in services:
        print(f"  - {svc.name()}: cores={svc.minCores()/100}-{svc.maxCores()/100}, "
              f"mem={svc.minMemory()/1024/1024/1024:.0f}GB")

    # List shows
    print("\nAvailable Shows:")
    shows = opencue.api.getShows()
    for show in shows:
        print(f"  - {show.name()}")

    # List hosts
    print("\nRegistered Hosts:")
    hosts = opencue.api.getHosts()
    if hosts:
        for host in hosts:
            print(f"  - {host.name()}: {host.coresTotal()/100:.0f} cores, "
                  f"{host.memory()/1024/1024/1024:.1f}GB, state={host.state()}")
    else:
        print("  (No hosts registered yet)")

    print("\n" + "=" * 50)


def main():
    parser = argparse.ArgumentParser(description="Setup OpenCue services for Maya/Arnold")
    parser.add_argument("--cuebot", "-c",
                        default=os.environ.get("CUEBOT_HOSTS", "localhost:8443"),
                        help="Cuebot host:port (default: localhost:8443)")
    parser.add_argument("--show", "-s",
                        default="maya_renders",
                        help="Show name to create (default: maya_renders)")

    args = parser.parse_args()

    print("=" * 50)
    print("OpenCue Service Setup")
    print("=" * 50)
    print(f"Cuebot: {args.cuebot}")
    print()

    # Setup environment
    if not setup_environment(args.cuebot):
        sys.exit(1)

    # Create services
    print("Creating services...")
    create_shell_service()
    create_maya2026_service()
    create_arnold_service()

    # Create show
    print("\nCreating show...")
    create_show(args.show)

    # Verify
    verify_setup()

    print("\nSetup complete!")
    print(f"\nNext steps:")
    print(f"1. Deploy RQD to Windows render nodes")
    print(f"2. Configure Maya submission scripts with show='{args.show}'")
    print(f"3. Test with a simple render job")


if __name__ == "__main__":
    main()
