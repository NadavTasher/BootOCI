FROM busybox:1.37.0-musl

ENTRYPOINT [ "/bin/ash" ]
CMD [ "-i" ]