# Partition sizes
{%- set bios_size = 1 %}
{%- set efi_size = 256 %}
{%- set rootfs_size = image_size - efi_size - 16 %}

# Calculate partition offsets
{%- set block_multiplier = 1024 * 2 %}
{%- set bios_offset = 1 * block_multiplier %}
{%- set efi_offset = bios_offset + bios_size * block_multiplier %}
{%- set rootfs_offset = efi_offset + efi_size * block_multiplier %}

{% if kernel_from_source %}
FROM {{internal_debian_image}} AS kernel-from-source

# Install build dependencies
RUN <<'EOF'
# Exit on failure
set -ex

apt --option='Acquire::Check-Valid-Until=false' update
apt install --yes xz-utils build-essential flex bison bc kmod libelf-dev libssl-dev --no-install-suggests --no-install-recommends
rm -r /var/lib/apt/lists
EOF

# Change working directory to downloads
WORKDIR /downloads

# Add the kernel sources archive
ADD "{{internal_kernel_url}}" /downloads/linux.tar.xz

# Change to build workdir
WORKDIR /build/linux

# Extract sources
RUN tar --strip-components=1 --extract --file /downloads/linux.tar.xz

# Create the default configuration
RUN make defconfig

# Patch the configuration to enable EFI framebuffer console
RUN <<'EOF'
cat <<'CONFIGURATION' >> .config
CONFIG_FB=y
CONFIG_FB_CORE=y
CONFIG_FB_EFI=y
CONFIG_FRAMEBUFFER_CONSOLE=y
CONFIGURATION
EOF

# Fix the configuration
RUN make olddefconfig

# Execute the actual build
RUN make -j$(nproc) dir-pkg
{% endif %}

{% if kernel_from_debian %}
FROM {{internal_debian_image}} AS kernel-from-debian

# Download the latest linux image
RUN <<'EOF'
# Exit on failure
set -e

apt --option='Acquire::Check-Valid-Until=false' update
apt install --yes linux-image-amd64
rm -r /var/lib/apt/lists
EOF
{% endif %}

# Actually generate the rootfs
FROM {{rootfs_from_tag}} AS rootfs

# Get busybox from image
COPY --from={{internal_busybox_image}} --chmod=755 /bin/busybox /bootoci/busybox

{% if kernel_from_source %}
# Install kernel artifacts from build stage
COPY --from=kernel-from-source /build/linux/tar-install/boot /boot
COPY --from=kernel-from-source /build/linux/tar-install/lib/modules /lib/modules
{% endif %}

{% if kernel_from_debian %}
# Install kernel artifacts from fetch stage
COPY --from=kernel-from-debian /boot /boot
COPY --from=kernel-from-debian /lib/modules /lib/modules
{% endif %}

{% if rootfs_password %}
{% for password in rootfs_password %}
# Use busybox from external image to change password
RUN /bootoci/busybox echo "{{password}}" | /bootoci/busybox chpasswd
{% endfor %}
{% endif %}

{% if rootfs_hostname %}
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

{% if init_is_ash %}
# Delete original /sbin/init file
RUN /bootoci/busybox rm -f /sbin/init

# Create init file
COPY --chmod=755 <<'EOF' /sbin/init
#!/bootoci/busybox ash

# Present user with shell
exec /bootoci/busybox ash -i
EOF
{% endif %}

{% if init_is_login %}
# Delete original /sbin/init file
RUN /bootoci/busybox rm -f /sbin/init

# Create init file
COPY --chmod=755 <<'EOF' /sbin/init
#!/bootoci/busybox ash

while true; do
	# Prompt user to log in
	LOGIN_TIMEOUT=0 /bootoci/busybox login
done
EOF
{% endif %}

{% if init_is_entrypoint %}
# Create workdir marker for entrypoint
RUN /bootoci/busybox ln -s $(/bootoci/busybox pwd) /bootoci/workdir

# Delete original /sbin/init file
RUN /bootoci/busybox rm -f /sbin/init

# Create init file
COPY --chmod=755 <<'EOF' /sbin/init
#!/bootoci/busybox ash

# Exit on failure
set -e

# Enter original working directory
cd -P /bootoci/workdir

# Add environment variables
export {{Env | join(" ")}}

# Execute entrypoint with cmd
{{Entrypoint | join(" ")}} {{Cmd | join(" ")}}
EOF
{% endif %}

{% if boot_shell %}
# Write the new init script
COPY --chmod=755 <<'EOF' /bootoci/init
#!/bootoci/busybox ash

# Write the welcome message
/bootoci/busybox cat <<'BANNER'

===================================================
| BootOCI - boot paused before calling real init. |
|     Enter 'exit' when you are ready to boot     |
===================================================

BANNER

# Pause boot before mounting rootfs
/bootoci/busybox ash -i

# Execute real init
for file in /init /sbin/init /etc/init /bin/init; do
	/bootoci/busybox test -x "${file}" && exec "${file}" $@
done
EOF
{% endif %}

FROM {{internal_debian_image}} AS image-builder

# Install build dependencies
RUN <<'EOF'
# Exit on failure
set -e

apt --option='Acquire::Check-Valid-Until=false' update
apt install --yes gdisk dracut e2fsprogs mtools dosfstools grub-efi-amd64-bin grub-efi-amd64-signed qemu-utils
rm -r /var/lib/apt/lists
EOF

# Change to build directory
WORKDIR /build

# Create the EFI partition
RUN <<'EOF'
# Exit on failure
set -e

# Create the partition file
truncate --size "{{efi_size}}M" efi

# Format the partition
mkfs.vfat -F 32 efi

# Create EFI directories
mmd -i efi ::/EFI ::/EFI/BOOT ::/boot ::/boot/grub

# Generate grub EFI image and copy it into the EFI partition
grub-mkimage --format x86_64-efi --prefix /boot/grub fat part_gpt linux normal | mcopy -i efi - ::/EFI/BOOT/BOOTX64.EFI

# Generate grub configuration and copy it into the EFI partition
mcopy -i efi - ::/boot/grub/grub.cfg <<'CONFIGURATION'
set timeout=5
set default=0

menuentry "BootOCI - {{rootfs_from_tag}}" {
	# Where is our kernel?
	linux /boot/vmlinuz {% if boot_cmdline %}{{boot_cmdline}}{% endif %} root=PARTUUID={{image_partuuid}} {% if boot_shell %}init=/bootoci/init{% endif %} {% if boot_serial %}console=ttyS0,115200{% endif %} {% if boot_debug %}debug ignore_loglevel{% endif %}

	# Path to initrd
	initrd /boot/initrd
}
CONFIGURATION
EOF

RUN --mount=type=bind,from=rootfs,source=/,destination=/rootfs <<'EOF'
# Exit on failure
set -e

# Decide kernel name
kernel_name=$(basename -a /rootfs/lib/modules/{{kernel_from_name or '*'}} | sort | tail -1)

# Copy kernel into EFI partition
mcopy -i efi "/rootfs/boot/vmlinuz-${kernel_name}" ::/boot/vmlinuz

# Generate initrd using dracut
dracut --no-compress --reproducible --filesystems ext4 --modules "rootfs-block kernel-modules" --kmoddir "/rootfs/lib/modules/${kernel_name}" initrd "${kernel_name}"

# Copy initrd into EFI partition
mcopy -i efi initrd ::/boot/initrd

# Create the rootfs partition file
truncate --size "{{rootfs_size}}M" rootfs

# Format the partition and copy files
mkfs.ext4 -d /rootfs -F rootfs
EOF

# Partition the disk
RUN <<'EOF'
# Exit on failure
set -e

# Create the image file
truncate --size "{{image_size}}M" image

# Create partition table
sgdisk --zap-all --clear image

# # Create BIOS partition
# sgdisk --new="1:{{bios_offset}}:{{efi_offset - 1}}"	--typecode="1:ef02" image

# Create EFI partition
sgdisk --new="2:{{efi_offset}}:{{rootfs_offset - 1}}" --typecode="2:ef00" image

# Create rootfs partition
sgdisk --new="3:{{rootfs_offset}}:0" --typecode="3:8300" --partition-guid="3:{{image_partuuid}}" image

# Move second header to end of image
sgdisk --move-second-header image

# Write EFI partition to image
dd if=efi of=image conv=notrunc bs=512 "seek={{efi_offset}}"

# Write rootfs partition to image
dd if=rootfs of=image conv=notrunc bs=512 "seek={{rootfs_offset}}"

{% if image_format %}
# Format image from raw to output format
qemu-img convert -f raw -O "{{image_format}}" image "image.{{image_format}}"

# Replace the original image
mv "image.{{image_format}}" image
{% endif %}
EOF

FROM scratch AS output

# Copy the output ISO
COPY --from=image-builder /build/image /{{output_filename}}
