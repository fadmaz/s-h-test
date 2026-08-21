ARG BUILD_FROM=ghcr.io/hassio-addons/base:14.0.0
FROM $BUILD_FROM

# Install system dependencies.
#
# iptables and libcap were dropped in 2.6.13: nothing in src/, run.sh or this file
# invokes iptables, setcap or getcap. The add-on used to do NAT redirection; that
# code is gone, and the bridge now only sniffs and sends raw frames, both of which
# come from the NET_RAW/NET_ADMIN capabilities rather than from a binary.
#
# iproute2 stays. Nothing here calls `ip` either, but scapy can, and the smoke test
# runs with AUTO_INTERCEPT=false and so never exercises sendp(). Removing it would be
# unverifiable short of a real installation.
RUN apk add --no-cache python3 py3-pip libpcap-dev dos2unix iproute2

# Install Python libraries with the flag for modern Alpine (PEP 668)
COPY requirements.txt /tmp/requirements.txt
RUN pip3 install --no-cache-dir --break-system-packages -r /tmp/requirements.txt

# Set working directory
WORKDIR /app

# Copy all files from the add-on directory
COPY . .

# Fix line endings for shell scripts and make them executable
RUN dos2unix run.sh && chmod a+x run.sh

CMD [ "./run.sh" ]
