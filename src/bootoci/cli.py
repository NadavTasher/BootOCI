import uuid
import argparse

from .oci_to_bootable import oci_to_bootable


def parse_arguments():
    # Create argument parser
    parser = argparse.ArgumentParser()

    # Output directory
    parser.add_argument("--output", "-o", action="store", default="bin", help="Output directory")

    # How are we building this?
    backend_group = parser.add_mutually_exclusive_group(required=True)
    backend_group.add_argument("--backend-docker", "--docker", action="store_true", help="Use docker to build image")
    backend_group.add_argument("--backend-podman", "--podman", action="store_true", help="Use podman to build image")

    # Where does the rootfs come from?
    rootfs_group = parser.add_mutually_exclusive_group(required=True)
    rootfs_group.add_argument("--rootfs-from-tag", "--tag", "-t", action="store", help="Tag to build from")
    rootfs_group.add_argument("--rootfs-from-dockerfile", "--dockerfile", "-f", action="store", help="Path to Dockerfile")

    # Where does the kernel come from? Optional. Image can already have kernel.
    kernel_group = parser.add_mutually_exclusive_group(required=False)
    kernel_group.add_argument("--kernel-from-debian", action="store_true", help="Use debian's kernel")
    kernel_group.add_argument("--kernel-from-source", action="store_true", help="Build kernel from upstream source")

    # Where does init come from? Optional. Image can already have init.
    init_group = parser.add_mutually_exclusive_group(required=False)
    init_group.add_argument("--init-is-ash", "--ash", action="store_true", help="Boot to shell")
    init_group.add_argument("--init-is-login", "--login", action="store_true", help="Boot to login")
    init_group.add_argument("--init-is-systemd", "--systemd", action="store_true", help="Boot to systemd")

    # GUID for rootfs partition
    parser.add_argument("--image-partuuid", "--partuuid", action="store", default="00000000-0000-0000-0000-000000000000", help="Partition identifier for rootfs")

    # Desired image size (affects rootfs size)
    parser.add_argument("--image-size", "--size", type=int, action="store", default=1024, help="Full image size in MB")

    # Use debug for kernel boot?
    parser.add_argument("--boot-debug", "--debug", action="store_true", help="Boot kernel in debug mode")

    # Use serial for kernel boot?
    parser.add_argument("--boot-serial", "--serial", action="store_true", help="Use serial for kernel boot")

    # Change password in rootfs?
    parser.add_argument("--rootfs-password", "--password", action="store", help="Password to set in USER:PASSWORD format")

    # Change hostname in rootfs?
    parser.add_argument("--rootfs-hostname", "--hostname", action="store", help="Hostname for system")

    # TODO --secure-boot forces --kernel-from-debian

    # Parse the arguments
    arguments = parser.parse_args()

    # Return the parsed arguments
    return arguments._get_kwargs()


def main():
    oci_to_bootable(**dict(parse_arguments()))


if __name__ == "__main__":
    # Just call the main function
    main()
