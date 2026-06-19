from aegis.tier2_core.dna.store import CrystalRecord, DNAStore, XorCipher


def test_xor_cipher_roundtrip():
    c = XorCipher("governor-key")
    blob = c.encrypt("private memory")
    assert blob != b"private memory"
    assert c.decrypt(blob) == "private memory"


def test_dna_remember_and_search():
    store = DNAStore(":memory:", cipher=XorCipher("k"))
    store.remember(CrystalRecord(kind="trade", description="export the quarterly sales report to csv"))
    store.remember(CrystalRecord(kind="trade", description="organise the screenshots folder"))
    assert store.count() == 2
    hits = store.search("export sales report")
    assert hits
    assert "export" in hits[0].description
    store.close()


def test_dna_search_filters_by_kind():
    store = DNAStore(":memory:")
    store.remember(CrystalRecord(kind="trade", description="open the browser"))
    store.remember(CrystalRecord(kind="ui_nav", description="open the browser"))
    assert len(store.search("open browser", kind="ui_nav")) == 1
    store.close()


def test_dna_persists_to_disk_and_reopens(tmp_path):
    path = tmp_path / "dna.sqlite3"
    s = DNAStore(path, cipher=XorCipher("k"))
    s.remember(CrystalRecord(kind="trade", description="export sales report quarterly"))
    s.close()

    s2 = DNAStore(path, cipher=XorCipher("k"))
    assert s2.count() == 1
    assert s2.search("sales report")[0].description.startswith("export")
    s2.close()


def test_dna_wrong_key_does_not_crash_retrieval(tmp_path):
    path = tmp_path / "dna.sqlite3"
    s = DNAStore(path, cipher=XorCipher("right"))
    s.remember(CrystalRecord(kind="trade", description="secret memory"))
    s.close()

    # A wrong key must not crash search; the undecryptable row is skipped.
    s2 = DNAStore(path, cipher=XorCipher("wrong"))
    assert s2.search("secret") == []
    assert s2.count() == 1  # the row still exists on disk
    s2.close()
