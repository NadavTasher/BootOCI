FROM ubuntu:24.04

RUN apt update && \
	apt install --yes linux-image-unsigned-6.8.0-40-generic linux-image-unsigned-6.8.0-40-lowlatency && \
	rm -r /var/lib/apt/lists
