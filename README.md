# BootCSI

## Pronounciation

It's pronounced `boots-ee`.

## What does it do?

BootCSI aims to create bootable ISO images from Docker images.

This project exists because I wasn't satisfied with other solutions and I really like Docker.

1. live-build - way to complicated, hard to keep track of changes
2. mkosi - never actually got it to work properly

## Installation

Currently supports Linux only.

Just run:

```bash
pip install bootcsi
```

## Usage

To create a bootable Debian 12 image you can just:

```bash
# Debian 12 ISO with Debian 13 kernel
bootcsi -o ./bin --docker --ash --kernel-from-debian --tag debian:12

# Debian 12 ISO with upstream kernel
bootcsi -o ./bin --docker --ash --kernel-from-source --tag debian:12

# Ubuntu 24.04 ISO with Debian 13 kernel (log to serial console)
bootcsi -o ./bin --docker --ash --kernel-from-debian --tag ubuntu:24.04 --serial
```

## Limitations

Currently, only `initrd` packing is supported. This essentially limits the image size supported. In the future, pivot root support will be added.
