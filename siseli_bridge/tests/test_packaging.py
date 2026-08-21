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

    def test_run_sh_carries_no_version_literal(self):
        """run.sh printed a hardcoded banner that froze at 2.6.5 while the add-on
        shipped 2.6.7, so every log contradicted itself in its own header and a bug
        report quoted a release the user was not running. Forbidden outright rather
        than kept in sync: bumping it just moves the drift to the next release."""
        run_sh = (ADDON / "run.sh").read_text(encoding="utf-8")
        self.assertNotRegex(
            run_sh,
            r"Siseli Inverter Bridge\s+[0-9]",
            "run.sh must not print a version; core.log_startup_configuration() does",
        )

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

    def test_an_spdx_licence_carries_a_build_floor_that_understands_it(self):
        """PEP 639 metadata -- `license = "MIT"` as a bare string, plus `license-files`
        -- is a schema error on setuptools 61-76, raised inside the PEP 517 hook. It
        does not degrade: `pip install -e ".[dev]"` fails outright, before a single
        test runs, on every interpreter in the matrix. The two must move together."""
        text = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
        if not re.search(r"^license\s*=\s*\"", text, re.M):
            self.skipTest("no bare-string licence declared")
        self.assertRegex(text, r"setuptools>=(7[7-9]|[89]\d|\d{3,})")

    def test_the_licence_files_named_in_pyproject_exist(self):
        """`license-files` narrows setuptools' default glob rather than adding to it,
        so a typo here silently ships a wheel with no licence at all."""
        text = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
        named = re.search(r"^license-files\s*=\s*\[([^\]]*)\]", text, re.M)
        self.assertIsNotNone(named, "license-files is not declared")
        for name in re.findall(r'"([^"]+)"', named.group(1)):
            with self.subTest(licence_file=name):
                self.assertTrue((ROOT / name).is_file(), f"{name} is named but absent")


class TestDockerContext(unittest.TestCase):
    """Docker matches .dockerignore with filepath.Match semantics, where `*` does not
    cross `/`. A bare `__pycache__/` therefore matched only the context root, and
    src/__pycache__, src/siseli_bridge/__pycache__, .coverage and siseli_bridge.egg-info
    shipped in every locally built image -- changing the layer hash, so two developers
    building the same commit got different images.

    These assert the patterns rather than inspecting a built image on purpose. All four
    artefacts are in .gitignore, so a clean CI checkout never has them and a behavioural
    test would pass vacuously while proving nothing.
    """

    def setUp(self):
        self.lines = [
            line.strip()
            for line in (ADDON / ".dockerignore").read_text(encoding="utf-8").splitlines()
            if line.strip() and not line.lstrip().startswith("#")
        ]

    def test_residue_patterns_are_recursive(self):
        for pattern in (
            "**/__pycache__/",
            "**/*.pyc",
            "**/*.egg-info/",
            "**/.coverage",
            "**/.pytest_cache/",
            "**/.ruff_cache/",
        ):
            with self.subTest(pattern=pattern):
                self.assertIn(pattern, self.lines)

    def test_no_residue_pattern_is_root_only(self):
        """The regression is a pattern losing its `**/` prefix, not a pattern going
        missing -- the root-only form looks correct and silently covers one directory."""
        for bare in ("__pycache__/", "*.pyc", "*.egg-info/", ".coverage"):
            with self.subTest(pattern=bare):
                self.assertNotIn(bare, self.lines, f"{bare} matches only the context root")

    def test_the_changelog_is_re_included(self):
        """Supervisor renders the add-on's own CHANGELOG.md on the Changelog tab, so
        the blanket *.md exclusion has to make an exception for it."""
        self.assertIn("*.md", self.lines)
        self.assertIn("!CHANGELOG.md", self.lines)

    def test_no_build_yaml(self):
        """Supervisor logs `uses build.yaml which is deprecated`. Without one, the
        Dockerfile's ARG BUILD_FROM default wins -- and that default is a multi-arch
        manifest, which is what makes a local aarch64 build work at all."""
        self.assertFalse((ADDON / "build.yaml").exists())
        self.assertFalse((ADDON / "build.json").exists())


class TestPinsAgree(unittest.TestCase):
    """Every pin in this project is written down twice, and nothing used to check that
    the copies agreed. Dependabot raises one PR per location, so a half-landed bump is
    the realistic failure -- and in both cases below it is the *second* copy that ships."""

    def test_python_dependencies_match(self):
        """requirements.txt is installed into the image; pyproject.toml is what CI
        installs. A drift between them means CI tests a pin set no user runs."""
        declared = re.search(
            r"^dependencies\s*=\s*\[(.*?)\]", (ROOT / "pyproject.toml").read_text(encoding="utf-8"), re.S | re.M
        )
        self.assertIsNotNone(declared, "pyproject.toml declares no [project] dependencies")
        project = sorted(re.findall(r'"([^"]+)"', declared.group(1)))

        runtime = sorted(
            line.strip()
            for line in (ADDON / "requirements.txt").read_text(encoding="utf-8").splitlines()
            if line.strip() and not line.lstrip().startswith("#")
        )
        self.assertEqual(project, runtime)

    def test_the_base_image_pin_matches(self):
        """Dependabot's docker ecosystem bumps the Dockerfile and cannot see the shell
        script, so the smoke test would keep building against the superseded base --
        testing an image no user would get."""
        dockerfile = re.search(
            r"^ARG BUILD_FROM=(\S+)", (ADDON / "Dockerfile").read_text(encoding="utf-8"), re.M
        )
        smoke = re.search(
            r'^BUILD_FROM="\$\{BUILD_FROM:-(\S+?)\}"',
            (ROOT / "scripts" / "smoke-test.sh").read_text(encoding="utf-8"),
            re.M,
        )
        self.assertIsNotNone(dockerfile, "Dockerfile declares no ARG BUILD_FROM default")
        self.assertIsNotNone(smoke, "smoke-test.sh declares no BUILD_FROM default")
        self.assertEqual(dockerfile.group(1), smoke.group(1))


class TestDeprecatedOptions(unittest.TestCase):
    """LISTEN_PORT was exported, validated and described in the UI as the port the
    add-on listens on. Nothing ever bound a socket -- its only consumer was a startup
    log line.

    It is nevertheless kept in the schema. Supervisor validates the *stored* options
    before installing an update, so deleting a key that existing installations still
    have on disk blocks the upgrade for all of them. It is removed in 2.7.0, by which
    point stored copies have been rewritten.
    """

    def setUp(self):
        self.cfg = _load_yaml(ADDON / "config.yaml")
        self.config_py = CONFIG_PY.read_text(encoding="utf-8")

    def test_listen_port_is_retained_but_optional(self):
        self.assertTrue(str(self.cfg["schema"]["LISTEN_PORT"]).endswith("?"))

    def test_listen_port_is_read_only_to_warn(self):
        self.assertIn("LISTEN_PORT_DEPRECATED", self.config_py)
        self.assertNotIn("LISTEN_PORT,", self.config_py)  # not in the port-range checks

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


def _validates(value, declaration):
    """Approximate Home Assistant's add-on option validation.

    Only the declaration forms this add-on uses are handled. The rule that matters and
    is easy to get wrong: a trailing `?` means the option may be *absent*, not that an
    empty string is acceptable. An empty string is a present value and must satisfy the
    declaration on its own.
    """
    if isinstance(declaration, list):
        if not isinstance(value, list):
            return False
        inner = re.match(r"list\((.+)\)$", declaration[0])
        allowed = set(inner.group(1).split("|")) if inner else set()
        return all(item in allowed for item in value)

    declaration = str(declaration)
    if declaration.endswith("?"):
        declaration = declaration[:-1]
        if value is None:
            return True

    if declaration == "bool":
        return isinstance(value, bool)
    if declaration == "str" or declaration == "password":
        return isinstance(value, str)
    if declaration.startswith("list("):
        allowed = set(declaration[len("list(") : -1].split("|"))
        return value in allowed
    if declaration.startswith("match("):
        pattern = declaration[len("match(") : -1]
        return isinstance(value, str) and re.match(pattern, value) is not None
    if declaration.startswith("float"):
        return isinstance(value, (int, float))
    if declaration.startswith("int"):
        if isinstance(value, bool) or not isinstance(value, int):
            return False
        bounds = re.match(r"int\((-?\d*),(-?\d*)\)$", declaration)
        if bounds:
            low, high = bounds.groups()
            if low and value < int(low):
                return False
            if high and value > int(high):
                return False
        return True
    raise AssertionError(f"unhandled schema declaration: {declaration!r}")


class TestShippedDefaultsSatisfyTheSchema(unittest.TestCase):
    """Home Assistant validates the *stored* options against the schema before it will
    install an update. A default that its own schema rejects therefore blocks the
    upgrade for every existing installation, with an error that names the schema rather
    than the option -- which is exactly what happened when a MAC address pattern was
    added to two options that both default to an empty string.
    """

    def setUp(self):
        self.cfg = _load_yaml(ADDON / "config.yaml")

    def test_every_default_satisfies_its_own_declaration(self):
        for key, declaration in sorted(self.cfg["schema"].items()):
            with self.subTest(option=key):
                self.assertIn(key, self.cfg["options"], "option has a schema but no default")
                value = self.cfg["options"][key]
                self.assertTrue(
                    _validates(value, declaration),
                    f"the shipped default {value!r} does not satisfy {declaration!r}",
                )

    def test_an_optional_pattern_still_accepts_an_empty_string(self):
        """`?` marks the option optional; it does not exempt an empty string from the
        pattern. Any pattern on an option that can be left blank has to allow it."""
        for key in ("INVERTER_MAC", "ROUTER_MAC"):
            with self.subTest(option=key):
                declaration = self.cfg["schema"][key]
                self.assertTrue(_validates("", declaration), "a blank value must be accepted")
                self.assertTrue(_validates("74-E9-D8-A3-41-2A", declaration))
                self.assertTrue(_validates("aa:bb:cc:dd:ee:ff", declaration))
                self.assertFalse(_validates("not-a-mac", declaration))

    def test_a_previously_valid_stored_configuration_still_installs(self):
        """A real configuration from a running installation, as Supervisor would
        present it on upgrade. Every key it carries must still validate."""
        stored = {
            "MQTT_HOST": "192.168.0.134",
            "MQTT_PORT": 1883,
            "MQTT_USER": "frigate",
            "MQTT_PASSWORD": "frigate",
            "TARGET_HOST": "8.212.18.157",
            "TARGET_PORT": 1883,
            "LISTEN_PORT": 18899,
            "INVERTER_IP": "192.168.0.152",
            "ROUTER_IP": "192.168.0.1",
            "INVERTER_MAC": "74-E9-D8-A3-41-2A",
            "ROUTER_MAC": "",
            "AUTO_INTERCEPT": True,
            "MQTT_DISCOVERY_PREFIX": "homeassistant",
            "DEVICE_ID": "siseli_inverter_1",
            "DEVICE_NAME": "Siseli Inverter 1",
            "MODEL_NAME": "Siseli Inverter 1",
            "MANUFACTURER": "Siseli Compatible",
            "ENTITY_PREFIX": "Siseli",
            "INVERTER_COUNT": 2,
            "BATTERY_COUNT": 2,
            "BATTERY_CAPACITY_PER_BATTERY_AH": 300.0,
            "STATE_TOPIC": "siseli/siseli_inverter_1/state",
            "AVAILABILITY_TOPIC": "siseli/siseli_inverter_1/availability",
            "SNIFF_IFACE": "",
            "LOG_VERBOSE": True,
            "LOG_LEVEL": "info",
            "UPDATE_INTERVAL_SEC": 10,
            "MQTT_RETAIN": True,
        }
        schema = self.cfg["schema"]
        for key, value in sorted(stored.items()):
            with self.subTest(option=key):
                self.assertIn(key, schema, "a stored option lost its schema entry")
                self.assertTrue(
                    _validates(value, schema[key]),
                    f"stored value {value!r} rejected by {schema[key]!r}",
                )


class TestTestEnvironmentMatchesShippedDefaults(unittest.TestCase):
    """tests/helpers.py BASE_ENV stands in for the options Supervisor supplies. When
    it drifts from config.yaml, any test that reloads config silently runs against a
    value nobody ships -- which made a genuine availability-flapping bug look fixed
    depending on test order."""

    def test_base_env_matches_config_yaml(self):
        from tests.helpers import BASE_ENV

        options = _load_yaml(ADDON / "config.yaml")["options"]
        for key, shipped in sorted(options.items()):
            if key not in BASE_ENV:
                continue  # list-valued options are represented differently
            with self.subTest(option=key):
                expected = shipped
                if isinstance(shipped, bool):
                    expected = str(shipped).lower()
                elif isinstance(shipped, list):
                    continue
                self.assertEqual(
                    BASE_ENV[key],
                    str(expected),
                    f"BASE_ENV has {BASE_ENV[key]!r} but the add-on ships {shipped!r}",
                )

    def test_every_shipped_option_is_represented(self):
        from tests.helpers import BASE_ENV

        options = set(_load_yaml(ADDON / "config.yaml")["options"])
        self.assertEqual(
            options - set(BASE_ENV), set(), "an option the add-on ships is missing from BASE_ENV"
        )


if __name__ == "__main__":
    unittest.main()
