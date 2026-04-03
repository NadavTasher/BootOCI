import os
import hashlib
import subprocess

# For typing
from typing import Optional

# For template rendering
import jinja2


def oci_to_bootable(
    *,

    # Output directory
    output: str,

    # Full image size
    image_size: int = 1024,

    # Partition UUID for rootfs
    image_partuuid: str = "00000000-0000-0000-0000-000000000000",

    # Do we need a boot shell?
    boot_shell: bool = False,

    # Do we boot in debug?
    boot_debug: bool = False,

    # Do we boot to serial?
    boot_serial: bool = False,

    # Do we set a rootfs hostname?
    rootfs_hostname: Optional[str] = None,
    
    # Do we set a rootfs password?
    rootfs_password: Optional[list[str]] = None,

    # Are we using docker as a backend?
    backend_docker: bool = True,

    # Are we using podman as a backend?
    backend_podman: bool = False,

    # Dockerfile that builds rootfs
    rootfs_from_dockerfile: Optional[str] = None,

    # Tag that can be used as rootfs
    rootfs_from_tag: Optional[str] = None,

    # Are we using a kernel from debian?
    kernel_from_debian: bool = False,

    # Are we building a kernel from source?
    kernel_from_source: bool = True,

    # Are we using BusyBox ash as the init program?
    init_is_ash: bool = True,

    # Are we using BusyBox login as the init program?
    init_is_login: bool = False,

    # Internal options
    internal_debian_image: str = "docker.io/library/debian:13-slim",
    internal_busybox_image: str = "docker.io/library/busybox:1.37.0-musl",
):
    # Decide which backend we are using
    backend = ["false"]

    if backend_docker:
        # We are using docker as our backend
        backend = ["docker", "buildx", "build"]

    if backend_podman:
        # We are using podman as our backend
        backend = ["podman", "buildx", "build"]

    # Let's build the base image
    if rootfs_from_dockerfile:
        # Generate tag if required
        if not rootfs_from_tag:
            rootfs_from_tag = "rootfs-" + os.urandom(4).hex()

        # Build the dockerfile
        subprocess.run(backend + ["--file", rootfs_from_dockerfile, "--tag", rootfs_from_tag, os.path.dirname(rootfs_from_dockerfile)], check=True)

    # Create jinja2 template
    with open(os.path.join(os.path.dirname(__file__), "templates", "Dockerfile"), "r", encoding="utf-8") as dockerfile:
        template = jinja2.Environment().from_string(dockerfile.read())

    # Render the template
    rendered_template = template.render(
        # At this point we already have a rootfs tag
        rootfs_from_tag=rootfs_from_tag,

        # Additional rootfs options
        rootfs_password=rootfs_password,
        rootfs_hostname=rootfs_hostname,

        # Kernel source selection
        kernel_from_debian=kernel_from_debian,
        kernel_from_source=kernel_from_source,

        # Init system selection
        init_is_ash=init_is_ash,
        init_is_login=init_is_login,

        # Full image size
        image_size=image_size,

        # Partition PARTUUID
        image_partuuid=image_partuuid,

        # Boot options
        boot_shell=boot_shell,
        boot_debug=boot_debug,
        boot_serial=boot_serial,

        # Internal options
        internal_debian_image=internal_debian_image,
        internal_busybox_image=internal_busybox_image,
    )

    # Create the output directory
    os.makedirs(output, exist_ok=True)

    # Now let's build the image
    subprocess.run(backend + ["--file", "-", "--target", "output", "--output", output, "."], input=rendered_template, check=True, text=True)
