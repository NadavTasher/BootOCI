FROM debian:13

RUN apt update && \
	apt install systemd gnome && \
	rm -r /var/lib/apt/lists

RUN adduser user
