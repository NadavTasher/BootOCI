# BootOCI

## What does it do?

BootOCI aims to create bootable disk images from OCI images (Docker container images).

It leverages the build cache feature of buildx / buildah to create efficient and fast builds.

This project exists because I wasn't satisfied with other solutions and I really like Docker.

1. live-build - way too complicated, hard to keep track of changes
2. mkosi - never actually got it to work properly

## Tech stack

- Build backend: [buildx](https://github.com/docker/buildx) or [buildah](https://github.com/containers/buildah)
- Bootloader: [GRUB](https://www.gnu.org/software/grub/grub.html)
- Initramfs: [dracut-ng](https://github.com/dracut-ng/dracut-ng)

## Installation

Currently supports Linux only.

Just run:

```bash
pip install bootoci
```

## Usage examples

Debian 12 that boots into a shell:

```bash
bootoci -o ./bin/disk.img --docker --ash --kernel-from-debian --tag debian:12 --size 1024
```

Debian 12 with an upstream kernel:

```bash
bootoci -o ./bin/disk.img --docker --ash --kernel-from-source --tag debian:12 --size 1024
```

Ubuntu 24.04 with a serial ash shell:

```bash
bootoci -o ./bin/disk.img --docker --ash --kernel-from-debian --tag ubuntu:24.04 --serial
```

Debian 13 with GNOME, hostname and user passwords:

```bash
bootoci -o ./bin/disk.img --docker --kernel-from-debian --tag debian-gnome --dockerfile ./examples/debian-gnome.Dockerfile --size 8192 --password root:12345678 --password user:12345678 --serial
```

Postgres server that starts on boot:

```bash
bootoci -o ./bin/disk.img --docker --kernel-from-debian --tag postgres --dockerfile ./examples/postgres-alpine.Dockerfile --size 1024 --entrypoint --serial
```

### Usage in development

```bash
# Build a fully-fledged ubuntu desktop machine
python3 -m src.bootoci.cli --docker --kernel-from-debian -f ./examples/ubuntu-desktop.Dockerfile --size 4096 --serial --password "root:12345678"
```

## Testing images

```bash
# Test for UEFI boot
qemu-system-x86_64 -enable-kvm -M q35 -m 2G -bios /usr/share/ovmf/OVMF.fd -drive file=./bin/disk.img,format=raw

# Test for Legacy (BIOS) boot (not supported)
# qemu-system-x86_64 -enable-kvm -M q35 -m 2G -drive file=./bin/image.raw,format=raw
```

## TODO

- [ ] Hybrid boot that supports Legacy and UEFI boot
