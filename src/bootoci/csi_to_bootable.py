import os
import subprocess

# For template rendering
import jinja2


def csi_to_bootable(*, output: str = None, serial: bool = None, docker: bool = None, podman: bool = None, dockerfile: str = None, tag: str = None, kernel_from_host: bool = None, kernel_from_source: bool = None, kernel_from_debian: bool = None, ash: bool = None, systemd: bool = None):
    # Decide which runtime we are using
    runtime = ["false"]

    if docker:
        # We are using docker as our runtime
        runtime = ["docker"]

    if podman:
        # We are using podman as our runtime
        raise NotImplementedError()

    # Let's build the base image
    if dockerfile:
        # Generate input tag
        tag = "rootfs-" + os.urandom(5).hex()

        # Build the dockerfile
        subprocess.run(runtime + ["build", "--file", dockerfile, "--tag", tag, os.path.dirname(dockerfile)], check=True)

    if kernel_from_host:
        # We'll use the host's kernel
        raise NotImplementedError()

    # Create jinja2 template
    with open(os.path.join(os.path.dirname(__file__), "templates", "Dockerfile"), "r", encoding="utf-8") as dockerfile:
        template = jinja2.Environment().from_string(dockerfile.read())

    # Render the template
    rendered_template = template.render(
        # Base rootfs tag
        tag=tag,

        # Kernel source selection
        kernel_from_host=kernel_from_host,
        kernel_from_debian=kernel_from_debian,
        kernel_from_source=kernel_from_source,

        # Init system selection
        ash=ash,
        systemd=systemd,

        # Serial for kernel boot?
        serial=serial,
    )

    # Create the output directory
    os.makedirs(output, exist_ok=True)

    # Now let's build the image
    subprocess.run(runtime + ["build", "--file", "-", "--output", output, "."], input=rendered_template, check=True, text=True)
