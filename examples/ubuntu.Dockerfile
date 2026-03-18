FROM ubuntu:24.04

# Install required packages
RUN apt update && \
	apt install --yes systemd ubuntu-desktop-minimal && \
	rm -r /var/lib/apt/lists

# Link systemd to init
RUN ln -s /usr/lib/systemd/systemd /init
