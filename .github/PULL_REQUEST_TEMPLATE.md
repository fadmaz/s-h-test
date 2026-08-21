## What this changes, and why

<!-- What was wrong or missing. If it fixes a defect, what the defect actually did. -->

## How you know it works

<!-- What you ran, and what it showed. A debug log from a real installation beats any
     amount of local reasoning -- every deployment-shaped bug in this project's history
     was found by running it, not by reading it. -->

## Checklist

- [ ] `pytest siseli_bridge/tests -q` passes
- [ ] `ruff check .` passes
- [ ] `bash scripts/smoke-test.sh` passes — **required** if this touches the Dockerfile,
      `run.sh`, `requirements.txt`, or anything in the startup path. Tests passing and
      the image building have both been true of a release that crash-looped on start.
- [ ] If this is a release: `version.py`, `siseli_bridge/config.yaml`, the README badge
      and the `siseli_bridge/CHANGELOG.md` heading all updated **in the same commit**.
      `test_packaging.py` fails until they agree.
- [ ] If this adds a configuration option: wired through `config.yaml` schema *and*
      defaults, `translations/en.yaml`, `run.sh`, `config.py`, and documented in
      `siseli_bridge/DOCS.md`. Tests assert all five.
- [ ] If a test asserting `CURRENT BEHAVIOUR` changed, said so above and why.
- [ ] If a sensor was removed from the parser, added its key to `UNDECODED_SENSOR_KEYS`
      so `/data/state.json` does not restore it onto users' dashboards.
