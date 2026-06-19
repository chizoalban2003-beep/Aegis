import os
from pathlib import Path

import pytest

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


ESCAPE = "/tmp/aegis_pytest_breach.txt"


@pytest.mark.parametrize("body", [
    f"from pathlib import Path; Path({ESCAPE!r}).write_text('x')",
    f"import os; fd=os.open({ESCAPE!r}, os.O_CREAT|os.O_WRONLY); os.write(fd,b'x'); os.close(fd)",
    f"import os; os.system('echo x > {ESCAPE}')",
    f"import subprocess,sys; subprocess.run([sys.executable,'-c',\"open({ESCAPE!r},'w').write('x')\"])",
])
def test_headless_blocks_escape_vectors(tmp_path: Path, body: str):
    if os.path.exists(ESCAPE):
        os.remove(ESCAPE)
    runner = HeadlessRunner(tmp_path)
    res = runner.run_snippet(body, timeout=10)
    assert res.ok is False
    assert not os.path.exists(ESCAPE), f"sandbox escaped via: {body}"


def test_headless_allows_legit_write_vectors(tmp_path: Path):
    runner = HeadlessRunner(tmp_path)
    res = runner.run_snippet(
        "from pathlib import Path\n"
        "(AEGIS_ROOT/'a.txt').write_text('a')\n"
        "open('b.txt','w').write('b')\n"
        "import os\n"
        "fd=os.open('c.txt', os.O_CREAT|os.O_WRONLY); os.write(fd,b'c'); os.close(fd)\n"
    )
    assert res.ok, res.stderr
    assert {p.name for p in tmp_path.glob("*.txt")} >= {"a.txt", "b.txt", "c.txt"}
