ARG BUILD_FROM=ghcr.io/hassio-addons/base:14.0.0
FROM $BUILD_FROM

# Install dependencies including dos2unix to fix line endings
RUN apk add --no-cache python3 py3-pip iptables libpcap-dev dos2unix
RUN pip3 install paho-mqtt scapy

# Set working directory
WORKDIR /app

# Copy all files from the add-on directory
COPY . .

# Fix line endings for shell scripts and make them executable
RUN dos2unix run.sh && chmod a+x run.sh

CMD [ "./run.sh" ]
