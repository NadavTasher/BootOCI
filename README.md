# BootOCI

## Pronounciation

It's pronounced `boot-os-ee`.

## What does it do?

BootOCI aims to create bootable ISO images from Docker images.

This project exists because I wasn't satisfied with other solutions and I really like Docker.

1. live-build - way too complicated, hard to keep track of changes
2. mkosi - never actually got it to work properly

## Installation

Currently supports Linux only.

Just run:

```bash
pip install bootoci
```

## Usage

To create a bootable Debian 12 image you can just:

```bash
# Debian 12 ISO with Debian 13 kernel
bootoci -o ./bin --docker --ash --kernel-from-debian --tag debian:12

# Debian 12 ISO with upstream kernel
bootoci -o ./bin --docker --ash --kernel-from-source --tag debian:12

# Ubuntu 24.04 ISO with Debian 13 kernel (log to serial console)
bootoci -o ./bin --docker --ash --kernel-from-debian --tag ubuntu:24.04 --serial
```

## Testing images

```bash
# Test for UEFI boot
qemu-system-x86_64 -enable-kvm -m 2G -bios /usr/share/ovmf/OVMF.fd -drive file=./bin/image.raw,format=raw

# Test for Legacy (BIOS) boot (not supported)
# qemu-system-x86_64 -enable-kvm -m 2G -drive file=./bin/image.raw,format=raw
```

## TODO

- [ ] Fix the `FROM rootfs AS rootfs` disaster
- [ ] Podman (buildah) as build backend
- [ ] init-is-systemd - Install systemd as /init
- [ ] kernel-from-debian - Real, working, Debian kernel
- [ ] kernel-from-nvidia - Kernel with nVidia drivers
- [ ] Fix slow boot issue - Kernel takes a couple of seconds to start
- [ ] Hybrid boot that supports Legacy and UEFI boot
