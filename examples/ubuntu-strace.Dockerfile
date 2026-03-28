FROM ubuntu:22.04

# Install required packages
RUN apt update && \
	apt install --yes strace && \
	rm -r /var/lib/apt/lists
