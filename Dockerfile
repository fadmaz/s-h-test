ARG BUILD_FROM=ghcr.io/hassio-addons/base:14.0.0
FROM $BUILD_FROM

# Install Python and dependencies
RUN apk add --no-cache python3 py3-pip
RUN pip3 install paho-mqtt

# Set working directory
WORKDIR /app

# Copy files
COPY powmr_bridge.py .
COPY run.sh .
RUN chmod a+x run.sh

CMD [ "./run.sh" ]
