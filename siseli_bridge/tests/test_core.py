"""Coverage for core.py, which had none.

core.py was previously untestable: importing it installed signal handlers and read
/data/state.json at module scope. Both now live in functions called from __main__,
so the module imports cleanly and its packet path can be driven directly.

core.py does `from .config import *`, so every constant is a module attribute on
core itself -- patch there, never on config.
"""

import json
import os
import tempfile
import unittest
from unittest import mock

from src.siseli_bridge import core
from src.siseli_bridge import state as shared_state
from tests.captures import CAPTURE_TELEMETRY
from tests.helpers import FakeMqttClient, envelope, inverter_packet, isolated_state, publish_packet, tcp_segments

INV_IP = "192.168.1.139"
RTR_IP = "192.168.1.1"
CLOUD_IP = "8.212.18.157"
INV_MAC = "aa:bb:cc:dd:ee:01"
RTR_MAC = "aa:bb:cc:dd:ee:02"

NET = dict(
    INVERTER_IP=INV_IP,
    ROUTER_IP=RTR_IP,
    TARGET_HOST=CLOUD_IP,
    TARGET_PORT=1883,
    AUTO_INTERCEPT=True,
    SNIFF_IFACE=None,
    LOG_VERBOSE=False,
    LOG_MQTT_TOPICS=False,
    LOG_MQTT_PAYLOAD_PREVIEW=False,
    LOG_UNPARSED_PUBLISH=False,
)


class _CoreTestCase(unittest.TestCase):
    """Saves and restores every core module global the packet path mutates."""

    def setUp(self):
        self._saved = (
            core.INV_MAC,
            core.RTR_MAC,
            shared_state.RUNNING,
            core.LAST_PACKET_TS,
            set(core.KNOWN_INVERTER_MACS),
            set(core.KNOWN_ROUTER_MACS),
        )
        core.INV_MAC, core.RTR_MAC = INV_MAC, RTR_MAC
        shared_state.RUNNING = True
        core.KNOWN_INVERTER_MACS.clear()
        core.KNOWN_ROUTER_MACS.clear()

        self.sent = []
        p = mock.patch(
            "src.siseli_bridge.core.send_layer2",
            side_effect=lambda frame, iface=None: self.sent.append(frame),
        )
        p.start()
        self.addCleanup(p.stop)

        consts = mock.patch.multiple(core, **NET)
        consts.start()
        self.addCleanup(consts.stop)

        ctx = isolated_state()
        ctx.__enter__()
        self.addCleanup(lambda: ctx.__exit__(None, None, None))

        self.addCleanup(self._restore)

    def _restore(self):
        (
            core.INV_MAC,
            core.RTR_MAC,
            shared_state.RUNNING,
            core.LAST_PACKET_TS,
            known_inv,
            known_rtr,
        ) = self._saved
        core.KNOWN_INVERTER_MACS.clear()
        core.KNOWN_INVERTER_MACS.update(known_inv)
        core.KNOWN_ROUTER_MACS.clear()
        core.KNOWN_ROUTER_MACS.update(known_rtr)


class TestNormMac(unittest.TestCase):
    def test_dashes_and_case_are_normalised(self):
        self.assertEqual(core.norm_mac("AA-BB-CC-DD-EE-01"), "aa:bb:cc:dd:ee:01")

    def test_whitespace_is_stripped(self):
        self.assertEqual(core.norm_mac("  aa:bb:cc:dd:ee:01 "), "aa:bb:cc:dd:ee:01")

    def test_empty_and_none_return_none(self):
        self.assertIsNone(core.norm_mac(""))
        self.assertIsNone(core.norm_mac(None))


class TestLoadCachedState(unittest.TestCase):
    def test_restores_a_saved_dict(self):
        with isolated_state(), tempfile.TemporaryDirectory() as d:
            path = os.path.join(d, "state.json")
            with open(path, "w") as f:
                json.dump({"bat_v": 53.4}, f)
            shared_state.LAST_STATE.clear()
            core.load_cached_state(path)
            self.assertEqual(shared_state.LAST_STATE["bat_v"], 53.4)

    def test_missing_file_is_not_an_error(self):
        with isolated_state(), tempfile.TemporaryDirectory() as d:
            shared_state.LAST_STATE.clear()
            core.load_cached_state(os.path.join(d, "absent.json"))
            self.assertEqual(shared_state.LAST_STATE, {})

    def test_truncated_file_is_swallowed_and_logged(self):
        """CURRENT BEHAVIOUR: a torn write silently yields an empty state, which
        zeroes the cumulative energy counters."""
        with isolated_state(), tempfile.TemporaryDirectory() as d:
            path = os.path.join(d, "state.json")
            with open(path, "w") as f:
                f.write('{"bat_v": 53.4, "c_batt')
            shared_state.LAST_STATE.clear()
            with mock.patch("src.siseli_bridge.core.log") as logged:
                core.load_cached_state(path)
            self.assertEqual(shared_state.LAST_STATE, {})
            self.assertTrue(logged.called)


class TestHandleInverterTcpPacket(_CoreTestCase):
    def test_a_full_publish_reaches_the_parser(self):
        wire = publish_packet("dtu/x/pub", envelope(CAPTURE_TELEMETRY))
        pkt = inverter_packet(wire, src=INV_IP, dst=CLOUD_IP, src_mac=INV_MAC)
        with mock.patch(
            "src.siseli_bridge.core.SolarParser.parse_payload", return_value=True
        ) as parsed:
            core.handle_inverter_tcp_packet(pkt)
        parsed.assert_called_once()

    def test_a_publish_split_across_segments_is_reassembled(self):
        wire = publish_packet("dtu/x/pub", b"x" * 4096)  # forces a multi-byte varint
        with mock.patch(
            "src.siseli_bridge.core.SolarParser.parse_payload", return_value=True
        ) as parsed:
            for seq, chunk in tcp_segments(wire, mss=500):
                core.handle_inverter_tcp_packet(
                    inverter_packet(chunk, src=INV_IP, dst=CLOUD_IP, seq=seq, src_mac=INV_MAC)
                )
        parsed.assert_called_once()

    def test_payload_free_segment_is_ignored(self):
        pkt = inverter_packet(b"", src=INV_IP, dst=CLOUD_IP, src_mac=INV_MAC)
        with mock.patch("src.siseli_bridge.core.SolarParser.parse_payload") as parsed:
            core.handle_inverter_tcp_packet(pkt)
        parsed.assert_not_called()

    def test_non_publish_control_packet_does_not_reach_the_parser(self):
        pkt = inverter_packet(b"\xc0\x00", src=INV_IP, dst=CLOUD_IP, src_mac=INV_MAC)
        with mock.patch("src.siseli_bridge.core.SolarParser.parse_payload") as parsed:
            core.handle_inverter_tcp_packet(pkt)
        parsed.assert_not_called()


class TestPacketCallback(_CoreTestCase):
    def _cloud_packet(self, **kw):
        kw.setdefault("src_mac", INV_MAC)
        return inverter_packet(publish_packet("dtu/x/pub", b"{}"), src=INV_IP, dst=CLOUD_IP, **kw)

    def test_inverter_to_cloud_is_parsed_and_forwarded_to_the_router(self):
        with mock.patch(
            "src.siseli_bridge.core.SolarParser.parse_payload", return_value=True
        ) as parsed:
            core.packet_callback(self._cloud_packet())
        parsed.assert_called_once()
        self.assertEqual(len(self.sent), 1)

    def test_traffic_to_another_destination_is_neither_parsed_nor_forwarded(self):
        pkt = inverter_packet(publish_packet(), src=INV_IP, dst="1.2.3.4", src_mac=INV_MAC)
        with mock.patch("src.siseli_bridge.core.SolarParser.parse_payload") as parsed:
            core.packet_callback(pkt)
        parsed.assert_not_called()
        self.assertEqual(self.sent, [], "non-broker inverter traffic is currently dropped")

    def test_a_frame_claiming_the_inverter_ip_from_another_mac_is_rejected(self):
        with mock.patch("src.siseli_bridge.core.SolarParser.parse_payload") as parsed:
            core.packet_callback(self._cloud_packet(src_mac="de:ad:be:ef:00:01"))
        parsed.assert_not_called()

    def test_router_to_inverter_is_forwarded(self):
        pkt = inverter_packet(b"", src=CLOUD_IP, dst=INV_IP, src_mac=RTR_MAC)
        core.packet_callback(pkt)
        self.assertEqual(len(self.sent), 1)

    def test_nothing_is_forwarded_when_auto_intercept_is_off(self):
        with mock.patch.multiple(core, AUTO_INTERCEPT=False), mock.patch(
            "src.siseli_bridge.core.SolarParser.parse_payload", return_value=True
        ):
            core.packet_callback(self._cloud_packet())
        self.assertEqual(self.sent, [])

    def test_last_packet_timestamp_advances(self):
        core.LAST_PACKET_TS = 0.0
        core.packet_callback(inverter_packet(b"", src=CLOUD_IP, dst=INV_IP, src_mac=RTR_MAC))
        self.assertGreater(core.LAST_PACKET_TS, 0.0)

    def test_known_macs_record_the_senders_seen(self):
        with mock.patch("src.siseli_bridge.core.SolarParser.parse_payload", return_value=True):
            core.packet_callback(self._cloud_packet())
        core.packet_callback(inverter_packet(b"", src=CLOUD_IP, dst=INV_IP, src_mac=RTR_MAC))
        self.assertIn(INV_MAC, core.KNOWN_INVERTER_MACS)
        self.assertIn(RTR_MAC, core.KNOWN_ROUTER_MACS)

    def test_macs_are_learned_from_the_first_frame_when_unset(self):
        core.INV_MAC = None
        core.RTR_MAC = None
        core.packet_callback(inverter_packet(b"", src=CLOUD_IP, dst=INV_IP, src_mac=RTR_MAC))
        self.assertEqual(core.RTR_MAC, RTR_MAC)

    def test_a_rejected_frame_does_not_pollute_the_known_macs(self):
        """Recording happened before the identity guard, so every rejected frame still
        landed in the set the health line reports."""
        with mock.patch("src.siseli_bridge.core.SolarParser.parse_payload") as parsed:
            core.packet_callback(self._cloud_packet(src_mac="de:ad:be:ef:00:01"))
        parsed.assert_not_called()
        self.assertNotIn("de:ad:be:ef:00:01", core.KNOWN_INVERTER_MACS)

    def test_our_own_re_emitted_frames_are_ignored(self):
        """Forwarded frames carry our MAC but the inverter's IP. They used to be
        indistinguishable from real inverter traffic, which is why the live health
        line listed the bridge's own MAC as both an inverter and a router address."""
        with mock.patch("src.siseli_bridge.core.resolve_own_mac", return_value="0a:0b:0c:0d:0e:0f"), \
             mock.patch("src.siseli_bridge.core.SolarParser.parse_payload") as parsed:
            core.packet_callback(self._cloud_packet(src_mac="0a:0b:0c:0d:0e:0f"))
        parsed.assert_not_called()
        self.assertEqual(core.KNOWN_INVERTER_MACS, set())
        self.assertEqual(self.sent, [])

    def test_a_forwarding_failure_does_not_propagate(self):
        with mock.patch(
            "src.siseli_bridge.core.send_layer2", side_effect=OSError("no route")
        ), mock.patch("src.siseli_bridge.core.SolarParser.parse_payload", return_value=True):
            core.packet_callback(self._cloud_packet())  # must not raise

    def test_a_parser_exception_does_not_kill_the_capture_thread(self):
        with mock.patch(
            "src.siseli_bridge.core.SolarParser.parse_payload", side_effect=ValueError("boom")
        ):
            core.packet_callback(self._cloud_packet())  # must not raise
        self.assertEqual(len(self.sent), 1, "forwarding still happens after a parse error")


class TestShutdown(_CoreTestCase):
    def test_marks_offline_disconnects_and_is_idempotent(self):
        client = FakeMqttClient()
        with mock.patch("src.siseli_bridge.core.client", client), \
             mock.patch("src.siseli_bridge.mqtt.client", client), \
             mock.patch("src.siseli_bridge.core.time.sleep"):
            core.shutdown()
            core.shutdown()

        offline = [p for p in client.published if p.payload == "offline"]
        self.assertEqual(len(offline), 1, "one availability topic covers every entity")
        self.assertTrue(offline[0].retain)
        self.assertTrue(client.disconnected)
        self.assertFalse(shared_state.RUNNING)

    def test_a_broker_failure_during_shutdown_is_swallowed(self):
        client = FakeMqttClient()
        client.raise_on_publish = OSError("broker gone")
        with mock.patch("src.siseli_bridge.core.client", client):
            core.shutdown()  # must not raise
        self.assertFalse(shared_state.RUNNING)

    def test_the_sniffer_is_stopped(self):
        sniffer = mock.Mock()
        client = FakeMqttClient()
        with mock.patch("src.siseli_bridge.core.client", client), mock.patch(
            "src.siseli_bridge.core.sniffer", sniffer
        ):
            core.shutdown()
        sniffer.stop.assert_called_once()

    def test_corrective_arp_is_sent_to_both_peers(self):
        """Without this both caches stay poisoned until they age out, and the inverter
        cannot reach the cloud for that whole window."""
        client = FakeMqttClient()
        with mock.patch("src.siseli_bridge.core.client", client), \
             mock.patch("src.siseli_bridge.mqtt.client", client), \
             mock.patch("src.siseli_bridge.core.time.sleep"):
            core.shutdown()

        self.assertEqual(len(self.sent), 10, "five corrective pairs")
        for frame in self.sent:
            self.assertEqual(int(frame["ARP"].op), 2)
        # hwsrc must name the true peer. The poisoning replies omit it so scapy fills
        # in our own MAC; the corrective ones must not.
        hwsrcs = {frame["ARP"].hwsrc for frame in self.sent}
        self.assertEqual(hwsrcs, {INV_MAC, RTR_MAC})

    def test_no_arp_is_sent_when_interception_is_disabled(self):
        client = FakeMqttClient()
        with mock.patch("src.siseli_bridge.core.client", client), \
             mock.patch("src.siseli_bridge.mqtt.client", client), \
             mock.patch.multiple(core, AUTO_INTERCEPT=False), \
             mock.patch("src.siseli_bridge.core.time.sleep"):
            core.shutdown()
        self.assertEqual(self.sent, [])

    def test_an_arp_failure_does_not_block_the_mqtt_teardown(self):
        client = FakeMqttClient()
        with mock.patch("src.siseli_bridge.core.client", client), \
             mock.patch("src.siseli_bridge.mqtt.client", client), \
             mock.patch("src.siseli_bridge.core.send_layer2", side_effect=OSError("down")), \
             mock.patch("src.siseli_bridge.core.time.sleep"):
            core.shutdown()
        self.assertTrue(client.disconnected)


class TestSignalHandlerInstallation(unittest.TestCase):
    def test_importing_core_does_not_install_handlers(self):
        """Module-level signal.signal() made core.py untestable: it hijacked the
        test runner's SIGINT and raised ValueError off the main thread."""
        import signal

        before = signal.getsignal(signal.SIGINT)
        import importlib

        importlib.reload(core)
        self.assertIs(signal.getsignal(signal.SIGINT), before)

    def test_install_signal_handlers_is_callable(self):
        self.assertTrue(callable(core.install_signal_handlers))


class TestAvailabilityWatchdog(_CoreTestCase):
    """Availability is driven by decoded telemetry age. LAST_PACKET_TS is useless for
    this: it is set for any packet matching the capture filter, bare ACKs included."""

    def setUp(self):
        super().setUp()
        core._AVAILABILITY_ONLINE = True
        self.addCleanup(lambda: setattr(core, "_AVAILABILITY_ONLINE", True))

    def test_fresh_telemetry_keeps_sensors_available(self):
        shared_state.LAST_TELEMETRY_TS = 1000.0
        self.assertTrue(core.telemetry_is_fresh(now=1000.0 + core.TELEMETRY_TIMEOUT_SEC - 1))

    def test_stale_telemetry_marks_sensors_unavailable(self):
        shared_state.LAST_TELEMETRY_TS = 1000.0
        self.assertFalse(core.telemetry_is_fresh(now=1000.0 + core.TELEMETRY_TIMEOUT_SEC + 1))

    def test_a_restart_does_not_immediately_blank_every_sensor(self):
        """Without a grace period every restart shows ~200 unavailable entities for
        the whole timeout."""
        shared_state.LAST_TELEMETRY_TS = 0.0
        with mock.patch.object(core, "PROCESS_START_TS", 5000.0):
            self.assertTrue(core.telemetry_is_fresh(now=5010.0))
            self.assertFalse(core.telemetry_is_fresh(now=5000.0 + core.TELEMETRY_TIMEOUT_SEC + 1))

    def test_availability_is_published_only_on_a_transition(self):
        shared_state.LAST_TELEMETRY_TS = 1000.0
        stale = 1000.0 + core.TELEMETRY_TIMEOUT_SEC + 1

        with mock.patch("src.siseli_bridge.core.publish_availability") as pub:
            self.assertIsNone(core.availability_watchdog_tick(now=1000.0))
            pub.assert_not_called()

            self.assertIs(core.availability_watchdog_tick(now=stale), False)
            pub.assert_called_once_with(False)

            pub.reset_mock()
            self.assertIsNone(core.availability_watchdog_tick(now=stale + 1))
            pub.assert_not_called()

            shared_state.LAST_TELEMETRY_TS = stale + 2
            self.assertIs(core.availability_watchdog_tick(now=stale + 2), True)
            pub.assert_called_once_with(True)


class TestNonBrokerTraffic(_CoreTestCase):
    """ARP interception makes the add-on the inverter's gateway for everything, but
    only broker traffic was ever relayed -- DNS and NTP were silently blackholed."""

    def setUp(self):
        super().setUp()
        core.DROPPED_NON_TARGET.clear()
        self.addCleanup(core.DROPPED_NON_TARGET.clear)

    def _dns(self):
        from scapy.all import IP, UDP, Ether

        return Ether(src=INV_MAC, dst="0a:0b:0c:0d:0e:0f") / IP(src=INV_IP, dst=RTR_IP) / UDP(dport=53)

    def test_dropped_traffic_is_counted_for_diagnosis(self):
        with mock.patch("src.siseli_bridge.core.resolve_own_mac", return_value="0a:0b:0c:0d:0e:0f"):
            core.packet_callback(self._dns())
        self.assertEqual(core.DROPPED_NON_TARGET.get("UDP:53"), 1)
        self.assertEqual(self.sent, [], "forwarding is opt-in and off by default")

    def test_opt_in_forwarding_relays_the_packet(self):
        with mock.patch.multiple(core, FORWARD_ALL_INVERTER_TRAFFIC=True), \
             mock.patch("src.siseli_bridge.core.resolve_own_mac", return_value="0a:0b:0c:0d:0e:0f"):
            core.packet_callback(self._dns())
        self.assertEqual(len(self.sent), 1)

    def test_broadcast_traffic_is_never_re_emitted(self):
        """Re-emitting it would duplicate what the real router already received."""
        from scapy.all import IP, UDP, Ether

        frame = Ether(src=INV_MAC, dst="ff:ff:ff:ff:ff:ff") / IP(src=INV_IP, dst="255.255.255.255") / UDP(dport=67)
        with mock.patch.multiple(core, FORWARD_ALL_INVERTER_TRAFFIC=True), \
             mock.patch("src.siseli_bridge.core.resolve_own_mac", return_value="0a:0b:0c:0d:0e:0f"):
            core.packet_callback(frame)
        self.assertEqual(self.sent, [])

    def test_broker_traffic_is_not_counted_as_dropped(self):
        with mock.patch("src.siseli_bridge.core.resolve_own_mac", return_value="0a:0b:0c:0d:0e:0f"), \
             mock.patch("src.siseli_bridge.core.SolarParser.parse_payload", return_value=True):
            core.packet_callback(
                inverter_packet(publish_packet("dtu/x", b"{}"), src=INV_IP, dst=CLOUD_IP, src_mac=INV_MAC)
            )
        self.assertEqual(core.DROPPED_NON_TARGET, {})


if __name__ == "__main__":
    unittest.main()
