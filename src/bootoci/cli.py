import argparse

from .oci_to_bootable import oci_to_bootable


def parse_arguments():
    # Create argument parser
    parser = argparse.ArgumentParser()

    # Output directory
    parser.add_argument("-o", "--output", action="store", default="bin", help="Output directory")

    # Use serial for kernel boot?
    parser.add_argument("--serial", action="store_true", help="Use serial for kernel boot")

    # How are we building this?
    runtime_group = parser.add_mutually_exclusive_group(required=True)
    runtime_group.add_argument("--docker", action="store_true", help="Use docker to build image")
    runtime_group.add_argument("--podman", action="store_true", help="Use podman to build image")

    # Where does the kernel come from?
    kernel_group = parser.add_mutually_exclusive_group(required=True)
    kernel_group.add_argument("--kernel-from-host", action="store_true", help="Use host's kernel")
    kernel_group.add_argument("--kernel-from-debian", action="store_true", help="Use debian's kernel")
    kernel_group.add_argument("--kernel-from-source", action="store_true", help="Build kernel from upstream source")

    # Where does the rootfs come from?
    rootfs_group = parser.add_mutually_exclusive_group(required=True)
    rootfs_group.add_argument("-t", "--tag", action="store", help="Tag to build from")
    rootfs_group.add_argument("-f", "--dockerfile", action="store", help="Path to Dockerfile")

    # Where does init come from?
    init_group = parser.add_mutually_exclusive_group(required=True)
    init_group.add_argument("--ash", action="store_true", help="Boot directly into BusyBox ash, statically compiled")
    init_group.add_argument("--systemd", action="store_true", help="Boot using systemd")

    # TODO --secure-boot forces --kernel-from-debian

    # Parse the arguments
    arguments = parser.parse_args()

    # Return the parsed arguments
    return arguments._get_kwargs()


def main():
    oci_to_bootable(**dict(parse_arguments()))
