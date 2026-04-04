import os
import json
import hashlib
import subprocess

# For typing
from typing import Optional

# For template rendering
import jinja2


def oci_to_bootable(
    *,

    # Output file path
    output_filepath: str,

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

    # Are we using the image's original entrypoint as the init program?
    init_is_entrypoint: bool = False,

    # Internal options
    internal_debian_image: str = "docker.io/library/debian:13-slim",
    internal_busybox_image: str = "docker.io/library/busybox:1.37.0-musl",
):
    # Decide which backend we are using
    backend = ["false"]

    if backend_docker:
        # We are using docker as our backend
        backend = ["docker"]

    if backend_podman:
        # We are using podman as our backend
        backend = ["podman"]

    # Let's build the base image
    if rootfs_from_dockerfile:
        # Generate tag if required
        if not rootfs_from_tag:
            rootfs_from_tag = "rootfs-" + hashlib.md5(rootfs_from_dockerfile.encode("utf-8", errors="ignore")).hexdigest()

        # Build the dockerfile
        subprocess.run(backend + ["buildx", "build", "--file", rootfs_from_dockerfile, "--tag", rootfs_from_tag, os.path.dirname(rootfs_from_dockerfile)], check=True)
    else:
        # Pull the image
        # TODO: check if the tag exists and only then pull
        subprocess.run(backend + ["pull", rootfs_from_tag])

    # We need to extract the rootfs information from the tag
    rootfs_configuration = json.loads(subprocess.run(backend + ["inspect", "--format", "{{json .Config}}", rootfs_from_tag], capture_output=True, text=True, check=True).stdout)

    # Create jinja2 template
    with open(os.path.join(os.path.dirname(__file__), "templates", "Dockerfile"), "r", encoding="utf-8") as dockerfile:
        template = jinja2.Environment().from_string(dockerfile.read())

    # Render the template
    rendered_template = template.render(
        # Add rootfs configuation
        **rootfs_configuration,

        # Output filename
        output_filename=os.path.basename(output_filepath),

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
        init_is_entrypoint=init_is_entrypoint,

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
    os.makedirs(os.path.dirname(output_filepath), exist_ok=True)

    # Now let's build the image
    subprocess.run(backend + ["buildx", "build", "--file", "-", "--target", "output", "--output", os.path.dirname(output_filepath), "."], input=rendered_template, check=True, text=True)
