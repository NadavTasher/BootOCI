import os
import json
import time
import shlex
import hashlib
import subprocess

# For typing
from typing import Optional

# For template rendering
import jinja2

# Get source date epoch
SOURCE_DATE_EPOCH = os.environ.get("SOURCE_DATE_EPOCH", int(time.time()))

# Get internal defaults
INTERNAL_KERNEL_URL = os.environ.get("BOOTOCI_KERNEL_URL", "https://cdn.kernel.org/pub/linux/kernel/v7.x/linux-7.2.13.tar.xz")
INTERNAL_FEDORA_IMAGE = os.environ.get("BOOTOCI_FEDORA_IMAGE", "docker.io/library/fedora:44")
INTERNAL_UBUNTU_IMAGE = os.environ.get("BOOTOCI_UBUNTU_IMAGE", "docker.io/library/ubuntu:26.04")
INTERNAL_DEBIAN_IMAGE = os.environ.get("BOOTOCI_DEBIAN_IMAGE", "docker.io/library/debian:13-slim")
INTERNAL_BUSYBOX_IMAGE = os.environ.get("BOOTOCI_BUSYBOX_IMAGE", "docker.io/library/busybox:1.38.0-musl")


def oci_to_bootable(
    *,

    # Disable usage of caches
    no_cache: bool = False,

    # Output file path
    output_filepath: str,

    # Only generate a Dockerfile
    generate_dockerfile: bool = False,

    # Full image size
    image_size: int = 1024,

    # Final image format
    image_format: Optional[str] = None,

    # Should the build be deterministic
    image_reproducible: bool = False,

    # Do we need to boot quietly?
    boot_quiet: bool = False,

    # Do we need a boot shell?
    boot_shell: bool = False,

    # Do we boot in debug?
    boot_debug: bool = False,

    # Do we boot to serial?
    boot_serial: bool = False,

    # Any additionall boot cmdline arguments?
    boot_cmdline: Optional[str] = None,

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

    # Are we using a specific kernel that is already installed?
    kernel_from_name: Optional[str] = None,

    # Are we using a kernel from fedora?
    kernel_from_fedora: bool = False,

    # Are we using a kernel from ubuntu?
    kernel_from_ubuntu: bool = False,

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
    internal_kernel_url: str = INTERNAL_KERNEL_URL,
    internal_fedora_image: str = INTERNAL_FEDORA_IMAGE,
    internal_ubuntu_image: str = INTERNAL_UBUNTU_IMAGE,
    internal_debian_image: str = INTERNAL_DEBIAN_IMAGE,
    internal_busybox_image: str = INTERNAL_BUSYBOX_IMAGE,
):
    # Set the source date epoch from environment, default to current epoch
    source_date_epoch = int(SOURCE_DATE_EPOCH)

    # To make reproducible builds, reset source date epoch
    if image_reproducible:
        source_date_epoch = 0

    # Decide which backend we are using
    backend = ["false"]

    if backend_docker:
        # We are using docker as our backend
        backend = ["docker"]

    if backend_podman:
        # We are using podman as our backend
        backend = ["podman"]

    # Cache options for image build
    cache = []

    if no_cache:
        # We don't want to use the cache
        cache = ["--no-cache"]

    # Let's build the base image
    if rootfs_from_dockerfile:
        # Generate tag if required
        if not rootfs_from_tag:
            rootfs_from_tag = "rootfs-" + hashlib.md5(rootfs_from_dockerfile.encode("utf-8", errors="ignore")).hexdigest()

        # Build the dockerfile
        subprocess.run(backend + ["buildx", "build", "--file", rootfs_from_dockerfile, "--tag", rootfs_from_tag] + cache + [os.path.dirname(rootfs_from_dockerfile)], check=True)
    else:
        # Check whether the image exists
        if not subprocess.run(backend + ["image", "ls", "--quiet", rootfs_from_tag], capture_output=True, check=True).stdout:
            # Pull the image
            subprocess.run(backend + ["pull", rootfs_from_tag], check=True)

    # We need to extract the rootfs information from the tag
    rootfs_configuration = json.loads(subprocess.run(backend + ["inspect", "--format", "{{json .Config}}", rootfs_from_tag], capture_output=True, text=True, check=True).stdout)

    # Create jinja2 environment
    environment = jinja2.Environment()

    # Add the shlex quote filter
    environment.filters["shlex"] = shlex.quote

    # Create jinja2 template
    with open(os.path.join(os.path.dirname(__file__), "templates", "Dockerfile"), "r", encoding="utf-8") as dockerfile:
        template = environment.from_string(dockerfile.read())

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
        kernel_from_name=kernel_from_name,
        kernel_from_fedora=kernel_from_fedora,
        kernel_from_ubuntu=kernel_from_ubuntu,
        kernel_from_debian=kernel_from_debian,
        kernel_from_source=kernel_from_source,

        # Init system selection
        init_is_ash=init_is_ash,
        init_is_login=init_is_login,
        init_is_entrypoint=init_is_entrypoint,

        # Full image size
        image_size=image_size,

        # Final image format
        image_format=image_format,

        # Boot options
        boot_quiet=boot_quiet,
        boot_shell=boot_shell,
        boot_debug=boot_debug,
        boot_serial=boot_serial,
        boot_cmdline=boot_cmdline,

        # Source date epoch
        source_date_epoch=source_date_epoch,

        # Internal options
        internal_kernel_url=internal_kernel_url,
        internal_fedora_image=internal_fedora_image,
        internal_ubuntu_image=internal_ubuntu_image,
        internal_debian_image=internal_debian_image,
        internal_busybox_image=internal_busybox_image,
    )

    # Should we just write the Dockerfile?
    if generate_dockerfile:
        # Write the dockerfile contents
        with open(output_filepath, "w", encoding="utf-8") as dockerfile:
            dockerfile.write(rendered_template)

        # Don't build!
        return

    # Now let's build the image
    subprocess.run(backend + ["buildx", "build", "--no-cache-filter", "build", "--file", "-", "--target", "output", "--output", os.path.abspath(os.path.dirname(output_filepath))] + cache + ["."], input=rendered_template, check=True, text=True)
