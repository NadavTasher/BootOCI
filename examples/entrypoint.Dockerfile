FROM busybox:1.37.0-musl

# Create a weird workdir path
WORKDIR "/please/don't break"

# Create a weird path for a shell
RUN ln -s /bin/ash "ash"

# Set the weird entrypoint path
ENTRYPOINT [ "/please/don't break/ash" ]
CMD [ "-i" ]