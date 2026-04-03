# syntax=docker/dockerfile:1

# Settings
{% set bios_size = 1 %}
{% set efi_size = 256 %}
{% set rootfs_size = image_size - efi_size - 16 %}

# Block to MB (1024 * 1024 / 512)
{% set block_multiplier = 1024 * 2 %}

# Calculate offsets
{% set bios_offset = 1 * block_multiplier %}
{% set efi_offset = bios_offset + bios_size * block_multiplier %}
{% set rootfs_offset = efi_offset + efi_size * block_multiplier %}

# Initialize rootfs name
{% set rootfs = "rootfs" %}

FROM {{rootfs_from_tag}} AS {{rootfs}}

{% if kernel_from_source %}
FROM {{internal_debian_image}} AS kernel-builder

# Install build dependencies
RUN apt update && \
	apt install -y build-essential flex bison libelf-dev debhelper-compat bc cpio kmod libssl-dev libssl-dev rsync wget && \
	rm -r /var/lib/apt/lists

# Change working directory to downloads
WORKDIR /downloads

# Add the kernel sources archive
RUN wget -O /downloads/linux.tar.xz https://cdn.kernel.org/pub/linux/kernel/v6.x/linux-6.12.77.tar.xz

# Change to build workdir
WORKDIR /build/sources

# Extract sources
RUN tar --strip-components=1 --extract --file /downloads/linux.tar.xz

# Create the default configuration
RUN make defconfig

# Execute the actual build
RUN make -j$(nproc) bindeb-pkg

# Change to the build output directory
WORKDIR /build

# Install the packages to an alternative directory
RUN dpkg --extract ./linux-image-*.deb /install

FROM {{rootfs}} AS {{rootfs}}-with-upstream-kernel

# Increment rootfs
{% set rootfs = rootfs + "-with-upstream-kernel" %}

# Copy artifacts from build stage
COPY --from=kernel-builder /install/lib lib
COPY --from=kernel-builder /install/boot boot
{% endif %}

{% if kernel_from_debian %}
FROM {{internal_debian_image}} AS kernel-fetcher

# Download the latest linux image
RUN apt update && \
	apt install --yes linux-image-amd64 && \
	rm -r /var/lib/apt/lists

FROM {{rootfs}} AS {{rootfs}}-with-debian-kernel

# Increment rootfs
{% set rootfs = rootfs + "-with-debian-kernel" %}

# Copy artifacts from fetch stage
COPY --from=kernel-fetcher /boot boot
COPY --from=kernel-fetcher /lib/modules lib/modules
{% endif %}

{% if init_is_ash %}
FROM {{rootfs}} AS {{rootfs}}-with-ash-as-init

# Increment rootfs
{% set rootfs = rootfs + "-with-ash-as-init" %}

# Get busybox from image
COPY --from={{internal_busybox_image}} --chmod=755 /bin/busybox /bootoci/ash

# Change to /sbin
WORKDIR /sbin

# Create link to ash
RUN --mount=type=bind,from={{internal_busybox_image}},source=/bin/busybox,destination=/bin/busybox \
	/bin/busybox ln -f -s /bootoci/ash init 
{% endif %}

{% if init_is_login %}
FROM {{rootfs}} AS {{rootfs}}-with-login-as-init

# Increment rootfs
{% set rootfs = rootfs + "-with-login-as-init" %}

# Get busybox from image
COPY --from={{internal_busybox_image}} --chmod=755 /bin/busybox /bootoci/ash
COPY --from={{internal_busybox_image}} --chmod=755 /bin/busybox /bootoci/login

# Change to /sbin
WORKDIR /sbin

# Create init file
COPY --chmod=755 <<'EOF' init
#!/bootoci/ash

while true; do
	# Prompt user to log in
	LOGIN_TIMEOUT=0 /bootoci/login
done
EOF
{% endif %}

{% if rootfs_password %}
FROM {{rootfs}} AS {{rootfs}}-with-passwords

# Increment rootfs
{% set rootfs = rootfs + "-with-passwords" %}

{% for password in rootfs_password %}
# Use busybox from external image to change password
RUN --mount=type=bind,from={{internal_busybox_image}},source=/bin/busybox,destination=/bin/busybox \
	/bin/busybox echo "{{password}}" | /bin/busybox chpasswd
{% endfor %}
{% endif %}

{% if rootfs_hostname %}
FROM {{rootfs}} AS {{rootfs}}-with-hostname

# Increment rootfs
{% set rootfs = rootfs + "-with-hostname" %}

# Write the hostname to /etc/hostname
COPY <<'EOF' /etc/hostname
{{rootfs_hostname}}
EOF

# Write the hostname to /etc/hosts
COPY <<'EOF' /etc/hosts
127.0.0.1 localhost
127.0.1.1 {{rootfs_hostname}}
EOF
{% endif %}

{% if boot_shell %}
FROM {{rootfs}} AS {{rootfs}}-with-boot-shell

# Increment rootfs
{% set rootfs = rootfs + "-with-boot-shell" %}

# Copy busybox binary for init
COPY --from={{internal_busybox_image}} --chmod=755 /bin/busybox /bootoci/ash
COPY --from={{internal_busybox_image}} --chmod=755 /bin/busybox /bootoci/cat

# Write the new init script
COPY --chmod=755 <<'EOF' /bootoci/init
#!/bootoci/ash

# Write the welcome message
/bootoci/cat <<BANNER

===================================================
| BootOCI - boot paused before calling real init. |
|     Enter 'exit' when you are ready to boot     |
===================================================

BANNER

# Pause boot before mounting rootfs
/bootoci/ash -i

# Execute real init
for file in /init /sbin/init /etc/init /bin/init; do
	[ -x "${file}" ] && exec "${file}" $@
done
EOF
{% endif %}

FROM {{internal_debian_image}} AS bootfs-builder

# Install archiving utilties
RUN apt update && \
	apt install --yes dracut && \
	rm -r /var/lib/apt/lists

# Create initrd using dracut
RUN --mount=type=bind,from={{rootfs}},source=/,destination=/rootfs \
	dracut --filesystems ext4 --modules "rootfs-block kernel-modules" --kmoddir /rootfs/lib/modules/* /boot/bootfs $(ls /rootfs/lib/modules)

FROM {{internal_debian_image}} AS rootfs-builder

# Install archiving utilties
RUN apt update && \
	apt install --yes e2fsprogs && \
	rm -r /var/lib/apt/lists

# Change to build directory
WORKDIR /build

# Create the partition file
RUN truncate --size "{{rootfs_size}}M" rootfs

# Archive from the rootfs layer
RUN --mount=type=bind,from={{rootfs}},source=/,destination=/rootfs \
	mkfs.ext4 -d /rootfs -F rootfs

FROM {{internal_debian_image}} AS grub-builder

# Install build dependencies
RUN apt update && \
	apt install --yes grub-pc-bin grub-efi-amd64-bin grub-efi-amd64-signed && \
	rm -r /var/lib/apt/lists

# Change to working directory
WORKDIR /build

# Generate GRUB EFI image
RUN grub-mkimage --format x86_64-efi --output grub.efi --prefix /boot/grub fat part_gpt linux normal

FROM {{internal_debian_image}} AS efi-builder

# Install build dependencies
RUN apt update && \
	apt install --yes mtools dosfstools && \
	rm -r /var/lib/apt/lists

# Change to build directory
WORKDIR /build

# Create EFI partition file
RUN truncate --size "{{efi_size}}M" efi

# Format EFI partition
RUN mkfs.vfat -F 32 efi

# Create EFI directories
RUN mmd -i efi ::/EFI ::/EFI/BOOT ::/boot ::/boot/grub

# Copy GRUB EFI image into EFI partition
RUN --mount=type=bind,from=grub-builder,source=/build/grub.efi,destination=grub.efi \
	mcopy -i efi grub.efi ::/EFI/BOOT/BOOTX64.EFI

# Create GRUB configuration
COPY <<'EOF' grub.cfg
set timeout=5
set default=0

menuentry "BootOCI - {{rootfs_from_tag}}" {
	# Where is our kernel?
	linux /boot/vmlinuz root=PARTUUID={{image_partuuid}} {% if boot_shell %}init=/bootoci/init{% endif %} {% if boot_serial %}console=ttyS0,115200{% endif %} {% if boot_debug %}debug ignore_loglevel{% endif %}

	# We boot to bootfs
	initrd /boot/bootfs
}
EOF

# Copy GRUB configuration into EFI partition
RUN mcopy -i efi grub.cfg ::/boot/grub/grub.cfg

# Copy kernel into EFI partition
RUN --mount=type=bind,from={{rootfs}},source=/,destination=/rootfs \
	mcopy -i efi /rootfs/boot/vmlinuz* ::/boot/vmlinuz

# Copy bootfs (initrd) into EFI partition
RUN --mount=type=bind,from=bootfs-builder,source=/boot/bootfs,destination=/bootfs \
	mcopy -i efi /bootfs ::/boot/bootfs

FROM {{internal_debian_image}} AS image-builder

# Install build dependencies
RUN apt update && \
	apt install --yes gdisk && \
	rm -r /var/lib/apt/lists

# Change to the build directory
WORKDIR /build

# Create the image file
RUN truncate --size "{{image_size}}M" image.raw

# Create partition table
RUN sgdisk --zap-all --clear image.raw

# # Create BIOS partition
# RUN sgdisk --new="1:{{bios_offset}}:{{efi_offset - 1}}"	--typecode="1:ef02" image.raw

# Create UEFI partition
RUN sgdisk --new="2:{{efi_offset}}:{{rootfs_offset - 1}}" --typecode="2:ef00" image.raw

# Create rootfs partition (full size - UEFI - BIOS - padding)
RUN sgdisk --new="3:{{rootfs_offset}}:0" --typecode="3:8300" --partition-guid="3:{{image_partuuid}}" image.raw

# Move second header to end of image
RUN sgdisk --move-second-header image.raw

# Write EFI partition to image
RUN --mount=type=bind,from=efi-builder,source=/build/efi,destination=efi \
	dd if=efi of=image.raw conv=notrunc bs=512 "seek={{efi_offset}}"

# Write rootfs partition to image
RUN --mount=type=bind,from=rootfs-builder,source=/build/rootfs,destination=rootfs \
	dd if=rootfs of=image.raw conv=notrunc bs=512 "seek={{rootfs_offset}}"

FROM scratch AS output

# Copy the output ISO
COPY --from=image-builder /build/image.raw /
