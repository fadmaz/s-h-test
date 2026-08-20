"""Regression tests for the rule that a value is published only when this payload
contains evidence for it.

Each class here pins the absence of something the parser used to invent: hardcoded
presets keyed on one inverter's settings, a second writer overwriting a key with a
different quantity, a range guard that discarded the alarm condition it was meant to
catch, or a calculated value derived from a payload that carried no inputs.

Fixtures are real captures from two devices -- see tests/captures.py.
"""

import os
import tempfile
import unittest
from unittest import mock

from src.siseli_bridge import parsers as parser_module
from src.siseli_bridge import state as shared_state
from src.siseli_bridge.parsers import SolarParser
from tests import captures
from tests.helpers import envelope, isolated_state


class _ParserTestCase(unittest.TestCase):
    def setUp(self):
        ctx = isolated_state()
        ctx.__enter__()
        self.addCleanup(lambda: ctx.__exit__(None, None, None))
        shared_state.LAST_STATE.clear()
        parser_module.LAST_ENERGY_TS_BATTERY = None
        parser_module.LAST_ENERGY_TS_GRID = None


class TestNoFabricatedValues(_ParserTestCase):
    def test_yavb_does_not_fabricate_bms_fault_flags(self):
        """Twelve BMS alarm flags appeared whenever the 16-bit flag word equalled one
        exact all-clear pattern, and nothing else ever wrote them -- so they were
        structurally incapable of reporting a fault."""
        state = SolarParser._try_ascii_schema({"Yavb": captures.BLOCK_YAVB_CHARGING})

        for key in (
            "bms_allow_charging_flag", "bms_allow_discharge_flag", "bms_communication_normal",
            "bms_communication_control_function", "bms_charging_overcurrent_sign",
            "bms_discharge_overcurrent_flag", "bms_low_battery_alarm_flag",
            "bms_low_power_fault_flag", "bms_low_temperature_flag",
            "bms_temperature_too_high_flag", "battery_not_connected", "battery_voltage_higher",
        ):
            with self.subTest(key=key):
                self.assertNotIn(key, state)

        # The raw bit word is the honest artefact and is still published.
        self.assertEqual(state["yavb_flags_raw"], "1001100000000000")
        self.assertEqual(state["bms_current_soc"], 58)
        self.assertEqual(state["bms_charging_current_a"], 29.1)

    def test_battery_type_is_not_guessed_from_a_block_name(self):
        """battery_type was defaulted to "LIA" whenever a Yavb block existed."""
        state = SolarParser._try_ascii_schema({"Yavb": captures.BLOCK_YAVB_CHARGING})
        self.assertNotIn("battery_type", state)

    def test_battery_status_needs_battery_data(self):
        """A payload carrying only the grid block reported "Charge"."""
        state = SolarParser._try_ascii_schema({"WdRR": captures.BLOCK_WDRR_NO_GRID_FLOW})
        self.assertNotIn("battery_status", state)

    def test_battery_status_reports_idle_from_arithmetic(self):
        state = SolarParser._try_ascii_schema({"2ONL": captures.SYNTH_2ONL_IDLE})
        self.assertEqual(state["battery_status"], "Idle")

    def test_unknown_blocks_decode_to_nothing(self):
        """_try_ascii_schema always returned six calculated keys, so every payload
        reported success and the unparsed diagnostics were unreachable."""
        self.assertEqual(SolarParser._try_ascii_schema({}), {})
        self.assertEqual(SolarParser._try_ascii_schema({"ZZZZ": captures.SYNTH_UNKNOWN_BLOCK}), {})


class TestSingleWriterPerKey(_ParserTestCase):
    def test_dc_rectification_temperature_comes_from_v4w3_only(self):
        """2l0E decoded it with a `>100 -> /10` rescale that turned the live token
        01175 into 117.5 C; V4W3 carries the same reading unscaled at 51.0 C."""
        only_2l0e = SolarParser._try_ascii_schema({"2l0E": captures.BLOCK_2L0E_LOADED})
        self.assertNotIn("dc_rectification_temperature_c", only_2l0e)

        with_v4w3 = SolarParser._try_ascii_schema({
            "2l0E": captures.BLOCK_2L0E_LOADED,
            "V4W3": captures.BLOCK_V4W3_TEMPS,
        })
        self.assertEqual(with_v4w3["dc_rectification_temperature_c"], 51.0)

    def test_dhrk_does_not_write_grid_connected_current(self):
        """dHrK token 2 is a state-of-charge percentage; it was written into a sensor
        declared with unit A and device_class current."""
        state = SolarParser._try_ascii_schema({"dHrK": captures.BLOCK_DHRK_SETTINGS})
        self.assertEqual(state["parallel_mode_turn_off_soc"], 20)
        self.assertNotIn("grid_connected_current_a", state)

    def test_dhrk_does_not_write_the_mains_charging_times(self):
        """One token was written to both the start and the end time."""
        state = SolarParser._try_ascii_schema({"dHrK": captures.BLOCK_DHRK_SETTINGS})
        self.assertNotIn("mains_charging_starting_time", state)
        self.assertNotIn("mains_charging_ending_time", state)

    def test_bat_series_count_comes_from_2onl_only(self):
        from_2onl = SolarParser._try_ascii_schema({"2ONL": captures.BLOCK_2ONL_CHARGING})
        self.assertEqual(from_2onl["bat_series_count"], 4)
        from_yavb = SolarParser._try_ascii_schema({"Yavb": captures.BLOCK_YAVB_CHARGING})
        self.assertNotIn("bat_series_count", from_yavb)

    def test_low_electric_lock_voltage_comes_from_93vq_only(self):
        from_yavb = SolarParser._try_ascii_schema({"Yavb": captures.BLOCK_YAVB_CHARGING})
        self.assertNotIn("low_electric_lock_voltage_v", from_yavb)
        self.assertEqual(from_yavb["bms_discharge_voltage_limit_v"], 42.0)

    def test_cell_summary_comes_from_uxjp_only(self):
        """v09K carries at most 16 cells. This bank has 32 -- the BMS reports its
        minimum at position 32 -- so any summary derived from that list describes a
        subset of the pack."""
        cells = SolarParser._try_ascii_schema({"v09K": captures.BLOCK_V09K_CELLS_16})
        self.assertEqual(cells["bms_cell_count"], 16)
        self.assertEqual(cells["cell_1_mv"], 3321)
        for key in ("bms_min_cell_mv", "bms_max_cell_mv", "bms_min_cell_pos",
                    "bms_max_cell_pos", "bms_cell_delta_mv"):
            with self.subTest(key=key):
                self.assertNotIn(key, cells)

        summary = SolarParser._try_ascii_schema({"uxJp": captures.BLOCK_UXJP_BMS_CAPACITY})
        self.assertEqual(summary["bms_min_cell_pos"], 32)
        self.assertEqual(summary["bms_cell_delta_mv"], 7)


class TestRangeGuards(_ParserTestCase):
    def test_output_relay_can_report_off(self):
        """The else branch produced None, which is stripped before publish, so the
        relay could only ever read On."""
        closed = SolarParser._try_ascii_schema({"WdRR": captures.BLOCK_WDRR_NO_GRID_FLOW})
        self.assertEqual(closed["main_output_relay_status"], "On")
        opened = SolarParser._try_ascii_schema({"WdRR": captures.SYNTH_WDRR_RELAY_OPEN})
        self.assertEqual(opened["main_output_relay_status"], "Off")

    def test_overload_percentage_is_published(self):
        """Above 100% is exactly the reading a user needs, and it was discarded --
        leaving the last sub-100 value on screen."""
        state = SolarParser._try_ascii_schema({"2l0E": captures.SYNTH_2L0E_OVERLOADED})
        self.assertEqual(state["load_pct"], 115)

    def test_parse_garbage_is_still_rejected(self):
        """Widening the guard must not let a mis-indexed token through."""
        state = SolarParser._try_ascii_schema({"2l0E": captures.BLOCK_2L0E_LOADED})
        self.assertEqual(state["load_pct"], 7)

    def test_absurd_bms_current_is_rejected(self):
        """Unbounded current times voltage, accumulated into a total_increasing
        sensor, can never be corrected downward."""
        state = SolarParser._try_ascii_schema({"Yavb": captures.SYNTH_YAVB_ABSURD_CURRENT})
        self.assertNotIn("bms_charging_current_a", state)
        self.assertEqual(state["bms_discharge_current_a"], 0.0)

    def test_cell_list_stops_at_the_first_out_of_range_cell(self):
        """Skipping it renumbered every later cell, so cell_3_mv reported physical
        cell 4's voltage."""
        state = SolarParser._try_ascii_schema({"v09K": captures.SYNTH_V09K_CELL_3_COLLAPSED})
        self.assertEqual(state["bms_cell_count"], 2)
        self.assertEqual(state["cell_1_mv"], 3321)
        self.assertEqual(state["cell_2_mv"], 3321)
        self.assertNotIn("cell_3_mv", state)


class TestEnergyDomainGating(_ParserTestCase):
    def test_grid_only_payload_does_not_zero_battery_power(self):
        """One combined gate would let this through, find no battery current, and
        write 0 W -- flapping battery power to zero on every grid-only payload."""
        state = SolarParser._try_ascii_schema({"WdRR": captures.BLOCK_WDRR_NO_GRID_FLOW})
        self.assertNotIn("c_battery_charge_power_w", state)
        self.assertNotIn("c_battery_discharge_power_w", state)
        self.assertEqual(state["c_grid_import_power_w"], 0)

    def test_identity_payload_writes_no_calculated_values(self):
        """The real second payload from a live install. It carries no battery voltage
        or current at all, yet it published a changed energy total."""
        shared_state.LAST_STATE.update({"bat_v": 53.4, "bms_charging_current_a": 29.1})
        parser_module.LAST_ENERGY_TS_BATTERY = 100.0

        state = SolarParser._try_ascii_schema(dict(captures.CAPTURE_IDENTITY))

        self.assertEqual([k for k in state if k.startswith("c_")], [])
        self.assertEqual(
            parser_module.LAST_ENERGY_TS_BATTERY, 100.0, "battery clock must not advance"
        )

    def test_the_two_clocks_are_independent(self):
        """A shared clock plus per-domain gating loses energy: a grid-only payload
        would consume the interval the battery integrator needed."""
        SolarParser._apply_energy_dashboard_calculations({"mains_wdrr_value": 100}, now_ts=0.0)
        SolarParser._apply_energy_dashboard_calculations({"mains_wdrr_value": 100}, now_ts=60.0)

        self.assertEqual(parser_module.LAST_ENERGY_TS_GRID, 60.0)
        self.assertIsNone(parser_module.LAST_ENERGY_TS_BATTERY)

        state = {"bat_v": 50.0, "bms_charging_current_a": 10.0}
        SolarParser._apply_energy_dashboard_calculations(state, now_ts=60.0)
        SolarParser._apply_energy_dashboard_calculations(state, now_ts=120.0)
        # 500 W across the full 60 s the battery clock waited, not a truncated slice.
        self.assertAlmostEqual(
            state["c_battery_charge_energy_kwh"], 500 * 60 / 3_600_000, places=6
        )

    def test_legacy_current_fallback_is_scaled_like_every_other_sensor(self):
        """BMS figures are whole-bank; 2ONL figures are per-inverter. Without scaling
        the fallback, reported power steps whenever the BMS block is absent."""
        state = {"bat_v": 48.0, "bat_charge_current": 5.0, "dischg_current": 4.0}
        with mock.patch("src.siseli_bridge.parsers.INVERTER_COUNT", 2):
            SolarParser._apply_energy_dashboard_calculations(state, now_ts=1.0)
        self.assertEqual(state["c_battery_charge_power_w"], 480)
        self.assertEqual(state["c_battery_discharge_power_w"], 384)

    def test_cached_current_no_longer_overrides_a_fresh_reading(self):
        """A cached BMS current used to win over a fresh inverter current in the same
        payload, integrating a stale rate indefinitely."""
        shared_state.LAST_STATE.update({"bms_charging_current_a": 29.1})
        state = {"bat_v": 53.4, "bat_charge_current": 0.0, "dischg_current": 0.0}
        with mock.patch("src.siseli_bridge.parsers.INVERTER_COUNT", 1):
            SolarParser._apply_energy_dashboard_calculations(state, now_ts=1.0)
        self.assertEqual(state["c_battery_charge_power_w"], 0)

    def test_disagreeing_current_sources_are_logged_not_silently_resolved(self):
        """No ground truth exists -- the official app displays both and they differ by
        about 2x on the reference unit and 4x on another."""
        state = {"bat_v": 53.4, "bms_charging_current_a": 29.1, "bat_charge_current": 7.0}
        with mock.patch("src.siseli_bridge.parsers.log_kv") as logged:
            SolarParser._apply_energy_dashboard_calculations(state, now_ts=1.0)
        tags = [call.args[0] for call in logged.call_args_list if call.args]
        self.assertIn("[ENERGY SOURCE DISAGREEMENT]", tags)
        self.assertEqual(state["c_battery_charge_power_w"], round(53.4 * 29.1))


class TestLiveCaptureParity(_ParserTestCase):
    """The full telemetry payload from a live 2x-parallel install must still decode to
    exactly the values that installation published."""

    def test_telemetry_capture_decodes_to_the_recorded_values(self):
        with mock.patch("src.siseli_bridge.parsers.INVERTER_COUNT", 2):
            state = SolarParser._try_ascii_schema(dict(captures.CAPTURE_TELEMETRY))

        for key, expected in captures.EXPECTED_TELEMETRY.items():
            with self.subTest(key=key):
                self.assertEqual(state.get(key), expected)

        for key, expected in captures.EXPECTED_TELEMETRY_SCALED.items():
            with self.subTest(key=key):
                self.assertEqual(state.get(key), expected)

    def test_identity_capture_decodes_to_the_recorded_values(self):
        state = SolarParser._try_ascii_schema(dict(captures.CAPTURE_IDENTITY))
        for key, expected in captures.EXPECTED_IDENTITY.items():
            with self.subTest(key=key):
                self.assertEqual(state.get(key), expected)


class TestPublishThrottle(unittest.TestCase):
    """UPDATE_INTERVAL_SEC never suppressed a publish: the gate was
    `changed or interval elapsed`, and something always changed."""

    def setUp(self):
        ctx = isolated_state()
        ctx.__enter__()
        self.addCleanup(lambda: ctx.__exit__(None, None, None))
        shared_state.LAST_STATE.clear()
        shared_state.DISCOVERY_PUBLISHED = True
        parser_module.LAST_ENERGY_TS_BATTERY = None
        parser_module.LAST_ENERGY_TS_GRID = None
        parser_module.PENDING_PUBLISH = False

        self.publish_state = mock.Mock()
        self.publish_discovery = mock.Mock()
        p = mock.patch.object(
            parser_module, "_get_mqtt_publish",
            return_value=(self.publish_discovery, self.publish_state),
        )
        p.start()
        self.addCleanup(p.stop)

        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        c = mock.patch.object(parser_module, "STATE_CACHE_FILE", os.path.join(self.tmp.name, "state.json"))
        c.start()
        self.addCleanup(c.stop)

    def _payload(self, bat_cap):
        # Derived from the real capture so the framing stays byte-faithful.
        return envelope(
            {"2ONL": captures.BLOCK_2ONL_CHARGING.replace(b"058", b"0%d" % bat_cap)}
        )

    def test_a_change_inside_the_window_is_deferred_not_dropped(self):
        parser_module.LAST_PUBLISH_TS = 1000.0
        with mock.patch.object(parser_module, "UPDATE_INTERVAL_SEC", 10),              mock.patch.object(parser_module, "EXPIRE_AFTER_SEC", 600),              mock.patch.object(parser_module.time, "time", return_value=1002.0):
            SolarParser.parse_payload(self._payload(58))
            SolarParser.parse_payload(self._payload(59))
        self.publish_state.assert_not_called()
        self.assertTrue(parser_module.PENDING_PUBLISH, "the change must be remembered")

        with mock.patch.object(parser_module, "UPDATE_INTERVAL_SEC", 10),              mock.patch.object(parser_module, "EXPIRE_AFTER_SEC", 600),              mock.patch.object(parser_module.time, "time", return_value=1011.0):
            SolarParser.parse_payload(self._payload(60))
        self.publish_state.assert_called_once()
        self.assertFalse(parser_module.PENDING_PUBLISH)

    def test_heartbeat_republishes_when_nothing_changes(self):
        """Without this, a steady inverter publishes nothing and expire_after marks
        every entity unavailable."""
        parser_module.LAST_PUBLISH_TS = 1000.0
        with mock.patch.object(parser_module, "UPDATE_INTERVAL_SEC", 10),              mock.patch.object(parser_module, "EXPIRE_AFTER_SEC", 600),              mock.patch.object(parser_module.time, "time", return_value=1000.0):
            SolarParser.parse_payload(self._payload(58))
        self.publish_state.reset_mock()
        parser_module.PENDING_PUBLISH = False
        parser_module.LAST_PUBLISH_TS = 1000.0

        # Same values again, one full heartbeat interval later (600 // 3 = 200 s).
        with mock.patch.object(parser_module, "UPDATE_INTERVAL_SEC", 10),              mock.patch.object(parser_module, "EXPIRE_AFTER_SEC", 600),              mock.patch.object(parser_module.time, "time", return_value=1201.0):
            SolarParser.parse_payload(self._payload(58))
        self.publish_state.assert_called_once()

    def test_payload_with_no_recognised_blocks_reports_failure(self):
        self.assertFalse(SolarParser.parse_payload(envelope({"ZZZZ": b"(1 2 3)"})))
        self.publish_state.assert_not_called()


class TestBatteryStatusMatchesReportedPower(_ParserTestCase):
    """battery_status used to come from the inverter's own ammeter while the power
    sensors came from the BMS. On a live installation the two disagreed: the status
    read "Idle" in the same publish that reported 344 W flowing into the battery.

    It is now derived from the calculated power, so the contradiction is impossible
    rather than merely unlikely.
    """

    def _resolve(self, state, count=2):
        with mock.patch("src.siseli_bridge.parsers.INVERTER_COUNT", count):
            SolarParser._apply_energy_dashboard_calculations(state, now_ts=1.0)
            SolarParser._derive_battery_status(state)
        return state

    def test_the_live_case_that_reported_idle_while_charging(self):
        """Values taken verbatim from a running installation."""
        state = self._resolve({
            "bat_v": 53.7,
            "bat_charge_current": 0.0,      # the inverter's ammeter
            "dischg_current": 0.0,
            "bms_charging_current_a": 6.4,  # the BMS
            "bms_discharge_current_a": 0.0,
        })
        self.assertEqual(state["c_battery_charge_power_w"], 344)
        self.assertEqual(state["battery_status"], "Charge")

    def test_status_and_power_can_never_contradict(self):
        for label, inputs, expected in (
            ("idle", {"bat_v": 53.7, "bat_charge_current": 0.0, "dischg_current": 0.0}, "Idle"),
            ("charging", {"bat_v": 53.7, "bat_charge_current": 5.0, "dischg_current": 0.0}, "Charge"),
            ("discharging", {"bat_v": 53.7, "bat_charge_current": 0.0, "dischg_current": 10.0}, "Discharge"),
        ):
            with self.subTest(case=label):
                state = self._resolve(dict(inputs))
                status = state["battery_status"]
                charge = state["c_battery_charge_power_w"]
                discharge = state["c_battery_discharge_power_w"]
                self.assertEqual(status, expected)
                if status == "Charge":
                    self.assertGreater(charge, 0)
                elif status == "Discharge":
                    self.assertGreater(discharge, 0)
                else:
                    self.assertEqual((charge, discharge), (0, 0))

    def test_no_battery_data_means_no_status(self):
        state = self._resolve({"mains_wdrr_value": 100})
        self.assertNotIn("battery_status", state)

    def test_one_source_reading_zero_is_reported(self):
        """A ratio test cannot express this, and it is the most informative
        disagreement there is -- it is what produced the Idle-while-charging case."""
        state = {"bat_v": 53.7, "bat_charge_current": 0.0, "bms_charging_current_a": 6.4}
        with mock.patch("src.siseli_bridge.parsers.log_kv") as logged:
            SolarParser._apply_energy_dashboard_calculations(state, now_ts=1.0)
        tags = [call.args[0] for call in logged.call_args_list if call.args]
        self.assertIn("[ENERGY SOURCE DISAGREEMENT]", tags)

    def test_agreeing_sources_stay_quiet(self):
        state = {"bat_v": 53.7, "bat_charge_current": 3.0, "bms_charging_current_a": 6.0}
        with mock.patch("src.siseli_bridge.parsers.log_kv") as logged:
            with mock.patch("src.siseli_bridge.parsers.INVERTER_COUNT", 2):
                SolarParser._apply_energy_dashboard_calculations(state, now_ts=1.0)
        tags = [call.args[0] for call in logged.call_args_list if call.args]
        self.assertNotIn("[ENERGY SOURCE DISAGREEMENT]", tags)


if __name__ == "__main__":
    unittest.main()
