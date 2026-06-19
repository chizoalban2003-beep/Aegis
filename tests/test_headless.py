from pathlib import Path

from aegis.headless.fallback import HeadlessRunner


def test_headless_writes_inside_sandbox(tmp_path: Path):
    runner = HeadlessRunner(tmp_path)
    res = runner.run_snippet(
        "with open(AEGIS_ROOT / 'out.txt', 'w') as f:\n    f.write('sovereign')\n",
    )
    assert res.ok, res.stderr
    assert (tmp_path / "out.txt").read_text() == "sovereign"


def test_headless_blocks_writes_outside_sandbox(tmp_path: Path):
    runner = HeadlessRunner(tmp_path)
    res = runner.run_snippet("open('/tmp/aegis_escape.txt', 'w').write('nope')\n")
    assert res.ok is False
    assert "sandbox" in res.stderr.lower() or "permissionerror" in res.stderr.lower()


def test_headless_timeout(tmp_path: Path):
    runner = HeadlessRunner(tmp_path)
    res = runner.run_snippet("import time\ntime.sleep(5)\n", timeout=0.5)
    assert res.ok is False
    assert "budget" in res.stderr.lower()
