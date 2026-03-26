import unittest
import sys
import os

# Add parent directory to path to allow importing src
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.siseli_bridge.sensors import SENSORS

class TestSensors(unittest.TestCase):
    def test_sensors_schema(self):
        """Ensure all sensors have a name and valid configuration."""
        for key, config in SENSORS.items():
            with self.subTest(key=key):
                self.assertIn("name", config, f"Sensor {key} is missing a name")
                self.assertIsInstance(config["name"], str)
                
                # Check for common optional keys type correctness
                if "unit" in config:
                    self.assertIsInstance(config["unit"], str)
                if "icon" in config:
                    self.assertIsInstance(config["icon"], str)
                    self.assertTrue(config["icon"].startswith("mdi:"), f"Icon for {key} should start with mdi:")
                if "device_class" in config:
                    self.assertIsInstance(config["device_class"], str)
                if "state_class" in config:
                    self.assertIsInstance(config["state_class"], str)

    def test_unique_sensor_names(self):
        """Ensure no two sensors share the same Home Assistant name to avoid collisions."""
        names = {}
        for key, config in SENSORS.items():
            name = config["name"]
            if name in names:
                self.fail(f"Duplicate sensor name '{name}' found for keys '{names[name]}' and '{key}'")
            names[name] = key

    def test_entity_categories(self):
        """Ensure entity categories are valid."""
        valid_categories = {None, "diagnostic", "config"}
        for key, config in SENSORS.items():
            category = config.get("entity_category")
            self.assertIn(category, valid_categories, f"Invalid entity_category '{category}' for sensor {key}")

if __name__ == '__main__':
    unittest.main()
