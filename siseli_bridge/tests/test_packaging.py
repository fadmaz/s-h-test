"""Guards for the invariants that previously had to be checked by hand.

Every failure here is something that used to reach users silently: a version that
Supervisor never offers because config.yaml lagged, an option the UI accepts that
makes validate_config() exit, or an option documented in one file and missing from
another.
"""

import pathlib
import re
import unittest

import yaml

ROOT = pathlib.Path(__file__).resolve().parents[2]
ADDON = ROOT / "siseli_bridge"
CONFIG_PY = ADDON / "src" / "siseli_bridge" / "config.py"


def _load_yaml(path):
    return yaml.safe_load(path.read_text(encoding="utf-8"))


class TestVersionConsistency(unittest.TestCase):
    """The release version lives in more than one file because Supervisor reads
    config.yaml directly and cannot import Python. These must never drift: if
    config.yaml lags, the update is never offered while the log claims otherwise."""

    def setUp(self):
        from src.siseli_bridge.version import __version__

        self.version = __version__

    def test_config_yaml_matches(self):
        self.assertEqual(_load_yaml(ADDON / "config.yaml")["version"], self.version)

    def test_readme_badge_matches(self):
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        self.assertIn(f"version-{self.version}-blue", readme)

    def test_changelog_head_matches(self):
        """The add-on copy is canonical -- it is what Supervisor renders on the add-on's
        Changelog tab, and .dockerignore already re-includes only that file."""
        heads = re.findall(
            r"^## \[([0-9][^\]]*)\]", (ADDON / "CHANGELOG.md").read_text(encoding="utf-8"), re.M
        )
        released = [h for h in heads if h.lower() != "unreleased"]
        self.assertTrue(released, "the add-on changelog has no released version heading")
        self.assertEqual(released[0], self.version)

    def test_the_root_changelog_points_at_the_canonical_one(self):
        """The two used to be maintained by hand and had already drifted apart."""
        text = (ROOT / "CHANGELOG.md").read_text(encoding="utf-8")
        self.assertIn("siseli_bridge/CHANGELOG.md", text)
        self.assertNotRegex(text, r"^## \[[0-9]", "the root file must not carry its own history")

    def test_core_reports_the_single_source(self):
        from src.siseli_bridge import version as version_mod

        core_src = (ADDON / "src" / "siseli_bridge" / "core.py").read_text(encoding="utf-8")
        self.assertNotRegex(
            core_src,
            r'^VERSION\s*=\s*["\']',
            "core.py must import __version__, not re-declare a literal",
        )
        self.assertEqual(version_mod.__version__, self.version)


class TestOptionWiring(unittest.TestCase):
    """Every add-on option must exist in options, schema, translations, run.sh and
    config.py. A gap in any one of them is invisible until a user hits it."""

    def setUp(self):
        self.cfg = _load_yaml(ADDON / "config.yaml")
        self.translations = _load_yaml(ADDON / "translations" / "en.yaml")
        self.run_sh = (ADDON / "run.sh").read_text(encoding="utf-8")
        self.config_py = CONFIG_PY.read_text(encoding="utf-8")

    def test_options_and_schema_agree(self):
        self.assertEqual(set(self.cfg["options"]), set(self.cfg["schema"]))

    def test_every_option_is_documented(self):
        self.assertEqual(set(self.cfg["schema"]), set(self.translations["configuration"]))

    def test_every_option_is_exported_by_run_sh(self):
        for key in sorted(self.cfg["schema"]):
            with self.subTest(key=key):
                self.assertIn(f"bashio::config '{key}'", self.run_sh)

    def test_every_option_is_read_by_config_py(self):
        for key in sorted(self.cfg["schema"]):
            with self.subTest(key=key):
                self.assertIn(f'os.getenv("{key}"', self.config_py)


class TestSchemaValidatorParity(unittest.TestCase):
    """A value the options UI accepts must not make validate_config() sys.exit.

    Before this test, UPDATE_INTERVAL_SEC was declared int(0,) while the validator
    rejected anything below 1 -- so a UI-legal 0 put the add-on in a restart loop
    with the options page still showing the value as valid.
    """

    def setUp(self):
        self.schema = _load_yaml(ADDON / "config.yaml")["schema"]

    def test_update_interval_lower_bound_matches_validator(self):
        low = re.match(r"int\((\d+),", self.schema["UPDATE_INTERVAL_SEC"])
        self.assertIsNotNone(low, "UPDATE_INTERVAL_SEC must declare a lower bound")
        self.assertGreaterEqual(int(low.group(1)), 1)

    def test_no_ui_legal_value_is_rejected_by_the_validator(self):
        """Drive validate_config() with the minimum each bounded int option allows."""
        from tests.helpers import reload_config

        minima = {}
        for key, decl in self.schema.items():
            m = re.match(r"int\((\d+),", str(decl))
            if m:
                minima[key] = m.group(1)
        self.assertIn("UPDATE_INTERVAL_SEC", minima, "expected at least one bounded int option")

        cfg = reload_config(**minima)
        try:
            cfg.validate_config()
        except SystemExit as exc:  # pragma: no cover - only on regression
            self.fail(f"schema minima {minima} rejected by validate_config: {exc}")


class TestPackagingMetadata(unittest.TestCase):
    def test_build_backend_is_real(self):
        """`setuptools.backends.legacy:build` does not exist -- it made every
        `pip install .` fail at the PEP 517 hook."""
        text = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
        self.assertIn('build-backend = "setuptools.build_meta"', text)

    def test_packages_are_declared_explicitly(self):
        """siseli_bridge/ has no __init__.py, so auto-discovery finds nothing and
        would build an empty wheel."""
        text = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
        self.assertIn("[tool.setuptools]", text)
        self.assertIn('packages = ["src", "src.siseli_bridge"]', text)


class TestRemovedOptions(unittest.TestCase):
    """LISTEN_PORT was exported, validated and described in the UI as the port the
    add-on listens on. Nothing ever bound a socket -- its only consumer was a startup
    log line."""

    def setUp(self):
        self.cfg = _load_yaml(ADDON / "config.yaml")
        self.run_sh = (ADDON / "run.sh").read_text(encoding="utf-8")
        self.config_py = CONFIG_PY.read_text(encoding="utf-8")

    def test_listen_port_is_gone_everywhere(self):
        self.assertNotIn("LISTEN_PORT", self.cfg["schema"])
        self.assertNotIn("LISTEN_PORT", self.cfg["options"])
        self.assertNotIn("LISTEN_PORT", self.run_sh)
        self.assertNotIn("LISTEN_PORT", self.config_py)

    def test_nothing_claims_to_listen_on_a_socket(self):
        src_dir = ADDON / "src"
        for path in src_dir.rglob("*.py"):
            with self.subTest(path=path.name):
                text = path.read_text(encoding="utf-8")
                for token in ("socket.socket", ".bind(", ".listen("):
                    self.assertNotIn(token, text)


class TestDebugFlagWiring(unittest.TestCase):
    def setUp(self):
        self.cfg = _load_yaml(ADDON / "config.yaml")

    def test_every_declared_flag_is_offered_in_the_schema(self):
        from src.siseli_bridge.config import DEBUG_FLAG_NAMES

        declared = self.cfg["schema"]["DEBUG_FLAGS"][0]
        for flag in DEBUG_FLAG_NAMES:
            with self.subTest(flag=flag):
                self.assertIn(flag, declared)

    def test_verbose_logging_is_off_by_default(self):
        """It shipped as true, so a fresh install wrote a line per captured frame."""
        self.assertIs(self.cfg["options"]["LOG_VERBOSE"], False)
        self.assertEqual(self.cfg["options"]["DEBUG_FLAGS"], [])


if __name__ == "__main__":
    unittest.main()
