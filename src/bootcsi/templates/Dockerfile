FROM {{ tag }} AS rootfs

{% if kernel_from_source %}
FROM debian:13 AS kernel-builder

# Install build dependencies
RUN apt update && \
	apt install -y build-essential flex bison libelf-dev debhelper-compat bc cpio kmod libssl-dev libssl-dev rsync && \
	rm -r /var/lib/apt/lists
	
# Add the kernel sources archive
ADD https://cdn.kernel.org/pub/linux/kernel/v6.x/linux-6.12.77.tar.xz /downloads/sources.tar.xz
	
# Change to build workdir
WORKDIR /build/sources

# Extract sources
RUN tar --strip-components=1 --extract --file /downloads/sources.tar.xz

# Create the default configuration
RUN make defconfig

# Execute the actual build
RUN make -j$(nproc) bindeb-pkg

# Change to the build output directory
WORKDIR /build

# Install the packages to an alternative directory
RUN dpkg --extract ./linux-image-*.deb /install

FROM rootfs AS rootfs-with-kernel

# Copy artifacts from build stage
COPY --from=kernel-builder /install/lib lib
COPY --from=kernel-builder /install/boot boot

FROM rootfs-with-kernel AS rootfs
{% endif %}

{% if kernel_from_debian %}
FROM debian:13 AS kernel-fetcher

# Download the latest linux image
RUN apt update && \
	apt install --download-only --yes linux-image-amd64 && \
	rm -r /var/lib/apt/lists

# Extract the linux image
RUN dpkg --extract /var/cache/apt/archives/linux-image-*+*.deb /install

FROM rootfs AS rootfs-with-kernel

# Copy artifacts from fetch stage
COPY --from=kernel-fetcher /install/lib lib
COPY --from=kernel-fetcher /install/boot boot

FROM rootfs-with-kernel AS rootfs
{% endif %}

{% if ash %}
FROM rootfs AS rootfs-with-ash

# Get busybox from image
COPY --from=busybox:1.37.0-musl /bin/busybox /busybox

# Create init file
COPY --chmod=0755 <<EOF /init
#!/busybox ash

# Just open a shell
/busybox ash -i
EOF

FROM rootfs-with-ash AS rootfs
{% endif %}

{% if systemd %}
FROM debian:13 AS systemd-fetcher

RUN apt update && \
	apt install -y systemd

FROM rootfs AS rootfs-with-systemd

# Copy the actual systemd files
COPY --from=systemd-fetcher / /systemd

# Create an init file


FROM rootfs-with-systemd AS rootfs
{% endif %}

{% if password %}

{% endif %}

FROM debian:13 AS initrd-builder

# Install archiving utilties
RUN apt update && \
	apt install --yes cpio && \
	rm -r /var/lib/apt/lists

# Change to rootfs working directory
WORKDIR /rootfs

# Copy from the rootfs layer
RUN --mount=type=bind,from=rootfs,source=/,destination=/rootfs \
	find . | cpio --quiet -o -H newc > /boot/initrd

FROM debian:13 AS iso-builder

# Install build dependencies
RUN apt update && \
	apt install --yes grub-pc-bin grub-efi-amd64-bin xorriso mtools && \
	rm -r /var/lib/apt/lists

# Change to the build directory
WORKDIR /iso

# Create GRUB configuration
COPY <<EOF boot/grub/grub.cfg
set timeout=5
set default=0

menuentry "Bootable '{{ tag }}' image" {
	# Where is our kernel?
	linux /boot/vmlinuz {% if serial %}console=ttyS0,115200{% endif %} loglevel=7

	# Where is our initramdisk?
	initrd /boot/initrd
}
EOF

# Copy the kernel files
COPY --from=rootfs boot boot

# Kernel has to have a consistent name
COPY --from=rootfs boot/vmlinuz* boot/vmlinuz

# Copy the initramdisk
COPY --from=initrd-builder boot/initrd boot/initrd

# Create the bootable ISO
RUN grub-mkrescue -o /output.iso /iso

FROM scratch AS iso

# Copy the output ISO
COPY --from=iso-builder /output.iso /
