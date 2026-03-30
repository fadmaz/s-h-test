import unittest
import sys
import os
from unittest import mock
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.siseli_bridge.parsers import decode_remaining_length, extract_mqtt_packets_from_stream, validate_publish_packet, SolarParser
from src.siseli_bridge import parsers as parser_module
from src.siseli_bridge import state as shared_state

class TestParsers(unittest.TestCase):
    def setUp(self):
        self._last_state_backup = dict(shared_state.LAST_STATE)
        self._last_energy_ts_backup = parser_module.LAST_ENERGY_TS

    def tearDown(self):
        shared_state.LAST_STATE.clear()
        shared_state.LAST_STATE.update(self._last_state_backup)
        parser_module.LAST_ENERGY_TS = self._last_energy_ts_backup

    def test_decode_remaining_length_single_byte(self):
        # Length 5 takes 1 byte
        buf = b'\x03\x05\x01\x02\x03\x04\x05'
        val, idx = decode_remaining_length(buf, 1)
        self.assertEqual(val, 5)
        self.assertEqual(idx, 2)

    def test_decode_remaining_length_multi_byte(self):
        # Length 321 evaluates to \xc1\x02
        buf = b'\x03\xc1\x02' + b'x' * 321
        val, idx = decode_remaining_length(buf, 1)
        self.assertEqual(val, 321)
        self.assertEqual(idx, 3)

    def test_validate_publish_packet_valid(self):
        # Type 3 (Publish), Length 6 -> total 8 bytes
        # Topic len is 3 ("a/b") -> 97, 47, 98 -> \x00\x03a/b
        packet = b'\x30\x06\x00\x03a/b\x99'
        self.assertTrue(validate_publish_packet(packet))

    def test_validate_publish_packet_invalid_type(self):
        packet = b'\x40\x06\x00\x03a/b\x99' # Type 4
        self.assertFalse(validate_publish_packet(packet))

    def test_solar_parser_safe_b64decode(self):
        self.assertEqual(SolarParser._safe_b64decode("dGVzdA=="), b"test")
        self.assertEqual(SolarParser._safe_b64decode("dGVzdA"), b"test")
        self.assertIsNone(SolarParser._safe_b64decode(""))

    def test_stream_assembler(self):
        stream = bytearray(b'\x30\x06\x00\x03a/b\x99') # Valid Pub
        stream.extend(b'\x30\x06') # Partial Pub
        
        packets = extract_mqtt_packets_from_stream(stream)
        self.assertEqual(len(packets), 1)
        self.assertEqual(packets[0], b'\x30\x06\x00\x03a/b\x99')
        
        # Assert partial bytes were properly left intact in stream
        self.assertEqual(stream, bytearray(b'\x30\x06'))

    def test_scale_main_power_uses_count_only(self):
        with mock.patch("src.siseli_bridge.parsers.INVERTER_COUNT", 3):
            self.assertEqual(SolarParser._scale_main_power(100), 300)

    def test_ascii_schema_normalizes_software_version(self):
        state = SolarParser._try_ascii_schema({
            "hR6Y": b"(0010.11 20250630 14)"
        })

        self.assertEqual(state["firmware_version"], "0010.11")
        self.assertEqual(state["software_version"], "10.11")

    def test_ascii_schema_rounds_output_set_frequency_to_app_style(self):
        state = SolarParser._try_ascii_schema({
            "2l0E": b"(229.8 49.9 252 129 2 24 11000 006.1 0044)"
        })

        self.assertEqual(state["out_hz"], 49.9)
        self.assertEqual(state["output_set_frequency"], 50)

    def test_ascii_schema_93vq_preset_sets_charging_light_to_flicker(self):
        state = SolarParser._try_ascii_schema({
            "93VQ": b"(1 050 010 13310110230 011 1 1 0 1 1 015 035 050 025 056.4 056.4 042.0 020 0 0)"
        })

        self.assertEqual(state["charging_light_status"], "Flicker")
        self.assertEqual(state["mains_light_status"], "Flicker")

    def test_ascii_schema_eo8w_preset_sets_charging_light_to_flicker(self):
        state = SolarParser._try_ascii_schema({
            "eo8w": b"(00 B0100000000000 20211002110B117020000)"
        })

        self.assertEqual(state["charging_light_status"], "Flicker")
        self.assertEqual(state["mains_light_status"], "Flicker")

    def test_ascii_schema_parses_bms_average_temperature_from_yavb_tail(self):
        state = SolarParser._try_ascii_schema({
            "Yavb": b"(04 1001100000000000 042.0 057.6 195.0 054 0022.3 0000.0 02921 000000 18.95)"
        })

        self.assertEqual(state["bms_current_soc"], 54)
        self.assertEqual(state["bms_charging_current_a"], 22.3)
        self.assertEqual(state["bms_discharge_current_a"], 0.0)
        self.assertEqual(state["bms_avg_temp_c"], 18.95)

    def test_ascii_schema_yavb_without_tail_keeps_bms_average_temperature_absent(self):
        state = SolarParser._try_ascii_schema({
            "Yavb": b"(04 1001100000000000 042.0 057.6 195.0 054 0022.3 0000.0 02921 000000)"
        })

        self.assertNotIn("bms_avg_temp_c", state)

    def test_energy_dashboard_calculations_use_bms_currents_and_scale(self):
        shared_state.LAST_STATE.clear()
        shared_state.LAST_STATE.update({
            "c_battery_charge_energy_kwh": 1.0,
            "c_battery_discharge_energy_kwh": 2.0,
            "c_grid_import_energy_kwh": 3.0,
        })
        parser_module.LAST_ENERGY_TS = 100.0

        state = {
            "bat_v": 50.0,
            "bms_charging_current_a": 10.0,
            "bms_discharge_current_a": 2.0,
            "mains_wdrr_value": 100,
        }

        with mock.patch("src.siseli_bridge.parsers.INVERTER_COUNT", 2):
            SolarParser._apply_energy_dashboard_calculations(state, now_ts=110.0)

        self.assertEqual(state["c_battery_charge_power_w"], 500)
        self.assertEqual(state["c_battery_discharge_power_w"], 100)
        self.assertEqual(state["c_grid_import_power_w"], 200)
        self.assertAlmostEqual(state["c_battery_charge_energy_kwh"], 1.001389, places=6)
        self.assertAlmostEqual(state["c_battery_discharge_energy_kwh"], 2.000278, places=6)
        self.assertAlmostEqual(state["c_grid_import_energy_kwh"], 3.000556, places=6)

    def test_energy_dashboard_calculations_fallback_and_no_export_import(self):
        shared_state.LAST_STATE.clear()
        shared_state.LAST_STATE.update({
            "bat_v": 48.0,
            "bat_charge_current": 5.0,
            "dischg_current": 4.0,
            "mains_wdrr_value": -120,
            "c_battery_charge_energy_kwh": 0.0,
            "c_battery_discharge_energy_kwh": 0.0,
            "c_grid_import_energy_kwh": 0.0,
        })
        parser_module.LAST_ENERGY_TS = 0.0

        state = {}
        with mock.patch("src.siseli_bridge.parsers.INVERTER_COUNT", 1):
            SolarParser._apply_energy_dashboard_calculations(state, now_ts=5.0)

        self.assertEqual(state["c_battery_charge_power_w"], 240)
        self.assertEqual(state["c_battery_discharge_power_w"], 192)
        self.assertEqual(state["c_grid_import_power_w"], 0)
        self.assertGreater(state["c_battery_charge_energy_kwh"], 0.0)
        self.assertGreater(state["c_battery_discharge_energy_kwh"], 0.0)
        self.assertEqual(state["c_grid_import_energy_kwh"], 0.0)

    def test_energy_dashboard_calculations_first_call_sets_baseline_only(self):
        shared_state.LAST_STATE.clear()
        shared_state.LAST_STATE.update({
            "c_battery_charge_energy_kwh": 0.7,
            "c_battery_discharge_energy_kwh": 0.8,
            "c_grid_import_energy_kwh": 0.9,
        })
        parser_module.LAST_ENERGY_TS = None

        state = {
            "bat_v": 52.0,
            "bms_charging_current_a": 8.0,
            "bms_discharge_current_a": 1.0,
            "mains_wdrr_value": 200,
        }
        SolarParser._apply_energy_dashboard_calculations(state, now_ts=100.0)

        self.assertEqual(state["c_battery_charge_energy_kwh"], 0.7)
        self.assertEqual(state["c_battery_discharge_energy_kwh"], 0.8)
        self.assertEqual(state["c_grid_import_energy_kwh"], 0.9)

if __name__ == '__main__':
    unittest.main()
