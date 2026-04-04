FROM ubuntu:24.04

# Install required packages
RUN apt update && \
	apt install --yes systemd ubuntu-desktop-minimal && \
	rm -r /var/lib/apt/lists

# Create user because GNOME does not allow root login
RUN adduser user
