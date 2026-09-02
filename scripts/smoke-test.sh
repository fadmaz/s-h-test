#!/usr/bin/env bash
# Start the built add-on image and wait for it to report a running sniffer.
#
# This exists because "the image builds" and "the tests pass" were both true of a
# release that crash-looped on every start. The failure was a NameError in the
# startup banner, which lived in the `__main__` body that no test executes, in a file
# carrying a ruff F405 exemption -- so neither guard could see it. Only running the
# thing catches that class of fault.
#
# The Supervisor API is not reachable outside Home Assistant, so bashio::config would
# return null for every option. Configuration is therefore passed as environment
# variables and the Python entrypoint is invoked directly. run.sh is covered instead
# by tests/test_packaging.py, which asserts every option is exported from it.
set -euo pipefail

IMAGE="${IMAGE:-siseli-bridge:smoke}"
CONTAINER="${CONTAINER:-siseli-smoke-$$}"
TIMEOUT="${TIMEOUT:-60}"
# Long enough to cover the first health-loop tick at T+10s.
SETTLE="${SETTLE:-15}"
READY_MARKER="[Bridge] Sniffer started"

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

# Read the base image out of the Dockerfile rather than restating it. The pin used to
# be written here as well, and Dependabot's docker ecosystem only ever bumps the
# Dockerfile -- so every bot PR left this script building against the superseded base
# and failed the parity test that existed to notice.
BUILD_FROM="${BUILD_FROM:-$(sed -n 's/^ARG BUILD_FROM=//p' "$HERE/siseli_bridge/Dockerfile" | head -1)}"
if [[ -z "$BUILD_FROM" ]]; then
    echo "!!! Could not read ARG BUILD_FROM from siseli_bridge/Dockerfile" >&2
    exit 1
fi

cleanup() {
    docker rm -f "$CONTAINER" >/dev/null 2>&1 || true
}
trap cleanup EXIT

echo "==> Building $IMAGE"
docker build -q -t "$IMAGE" "$HERE/siseli_bridge" --build-arg BUILD_FROM="$BUILD_FROM" >/dev/null

echo "==> Starting container"
docker run -d --name "$CONTAINER" \
    --cap-add=NET_ADMIN --cap-add=NET_RAW \
    -e MQTT_HOST=127.0.0.1 -e MQTT_PORT=1883 \
    -e TARGET_HOST=8.212.18.157 -e TARGET_PORT=1883 \
    -e INVERTER_IP=192.168.1.139 -e ROUTER_IP=192.168.1.1 \
    -e INVERTER_MAC=aa:bb:cc:dd:ee:01 -e ROUTER_MAC=aa:bb:cc:dd:ee:02 \
    -e AUTO_INTERCEPT=false \
    -e MQTT_DISCOVERY_PREFIX=homeassistant -e DEVICE_ID=siseli_inverter_1 \
    -e DEVICE_NAME="Siseli Inverter 1" -e MODEL_NAME="Siseli Inverter 1" \
    -e MANUFACTURER="Siseli Compatible" -e ENTITY_PREFIX=Siseli \
    -e INVERTER_COUNT=1 -e BATTERY_COUNT=1 -e BATTERY_CAPACITY_PER_BATTERY_AH=0.0 \
    -e LOG_LEVEL=info \
    -e MQTT_RETAIN=true \
    --entrypoint python3 "$IMAGE" -u -m src.siseli_bridge.core >/dev/null

# AUTO_INTERCEPT is off on purpose: the point is to reach a running sniffer, not to
# poison a CI runner's ARP tables.

echo "==> Waiting up to ${TIMEOUT}s for: ${READY_MARKER}"
deadline=$(( SECONDS + TIMEOUT ))
while (( SECONDS < deadline )); do
    if docker logs "$CONTAINER" 2>&1 | grep -qF "$READY_MARKER"; then
        echo "==> Started successfully"

        # The marker prints unconditionally, whether or not the capture thread
        # survived, so reaching it proves less than it looks. Since 2.6.20 the health
        # loop stops the add-on when capture will not stay up -- which means a bug in
        # that check could stop a perfectly healthy add-on, and this script would have
        # exited seconds earlier none the wiser. The first health tick is at T+10s.
        echo "==> Confirming it is still running ${SETTLE}s later"
        sleep "$SETTLE"
        status="$(docker inspect -f '{{.State.Status}}' "$CONTAINER" 2>/dev/null || echo missing)"
        if [[ "$status" != "running" ]]; then
            code="$(docker inspect -f '{{.State.ExitCode}}' "$CONTAINER" 2>/dev/null || echo '?')"
            echo "!!! Container stopped itself after starting (status=$status, code=$code)" >&2
            echo "--- container output ---" >&2
            docker logs "$CONTAINER" 2>&1 | tail -40 >&2
            exit 1
        fi

        echo "--- container output ---"
        docker logs "$CONTAINER" 2>&1 | grep -vE '^\s*$' | tail -20
        exit 0
    fi

    # An exited container will never print the marker, so fail immediately rather
    # than burning the whole timeout.
    status="$(docker inspect -f '{{.State.Status}}' "$CONTAINER" 2>/dev/null || echo missing)"
    if [[ "$status" != "running" ]]; then
        code="$(docker inspect -f '{{.State.ExitCode}}' "$CONTAINER" 2>/dev/null || echo '?')"
        echo "!!! Container exited (status=$status, code=$code) before starting the sniffer" >&2
        echo "--- container output ---" >&2
        docker logs "$CONTAINER" 2>&1 | tail -40 >&2
        exit 1
    fi
    sleep 1
done

echo "!!! Timed out after ${TIMEOUT}s without reaching: ${READY_MARKER}" >&2
echo "--- container output ---" >&2
docker logs "$CONTAINER" 2>&1 | tail -40 >&2
exit 1
