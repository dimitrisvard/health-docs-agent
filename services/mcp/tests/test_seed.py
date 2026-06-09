import pytest

from ingest.seed import (
    discover,
    ensure_schema,
    infer_kind,
    ingest_file,
    ingest_text,
    load_text,
    title_from,
)


class FakeCursor:
    def __init__(self, store: dict) -> None:
        self.store = store
        self._last: tuple | None = None

    def __enter__(self) -> "FakeCursor":
        return self

    def __exit__(self, *exc: object) -> bool:
        return False

    def execute(self, sql: str, params: tuple | None = None) -> None:
        self.store["execute"].append((sql, params))
        self._last = (42,) if "RETURNING id" in sql else None

    def executemany(self, sql: str, seq: object) -> None:
        self.store["executemany"].append((sql, list(seq)))  # type: ignore[arg-type]

    def fetchone(self) -> tuple | None:
        return self._last


class FakeConn:
    def __init__(self) -> None:
        self.store: dict = {"execute": [], "executemany": [], "commits": 0}

    def cursor(self) -> FakeCursor:
        return FakeCursor(self.store)

    def commit(self) -> None:
        self.store["commits"] += 1


def test_infer_kind():
    assert infer_kind("NCT12345_protocol.txt") == "trial"
    assert infer_kind("aspirin_smpc.pdf") == "drug_label"
    assert infer_kind("nice_guideline_hypertension.md") == "guideline"


def test_title_from():
    assert title_from("aspirin_smpc.pdf") == "aspirin smpc"


def test_discover_only_supported_files(tmp_path):
    (tmp_path / "a.md").write_text("x", encoding="utf-8")
    (tmp_path / "b.txt").write_text("x", encoding="utf-8")
    (tmp_path / "ignore.png").write_bytes(b"x")
    (tmp_path / "README.md").write_text("x", encoding="utf-8")
    found = {p.name for p in discover(tmp_path)}
    assert found == {"a.md", "b.txt"}


def test_load_text_reads_plaintext(tmp_path):
    p = tmp_path / "note.txt"
    p.write_text("hello world", encoding="utf-8")
    assert load_text(p) == "hello world"


def test_load_text_rejects_unsupported(tmp_path):
    p = tmp_path / "x.csv"
    p.write_text("a,b", encoding="utf-8")
    with pytest.raises(ValueError):
        load_text(p)


def test_ingest_file_is_idempotent_and_inserts_chunks(tmp_path):
    doc = tmp_path / "trial_acme.md"
    doc.write_text("## Eligibility\nAdults 18 to 65.\n\n## Endpoints\nOverall survival.\n", encoding="utf-8")
    conn = FakeConn()
    seen: dict = {}

    def fake_embed(texts: list[str]) -> list[list[float]]:
        seen["texts"] = texts
        return [[0.1] * 768 for _ in texts]

    n = ingest_file(conn, doc, embed=fake_embed)

    assert n >= 2
    execs = conn.store["execute"]
    # idempotency: delete the prior document by title before inserting
    assert any(sql.startswith("DELETE FROM documents") for sql, _ in execs)
    inserts = [(sql, p) for sql, p in execs if sql.startswith("INSERT INTO documents")]
    assert inserts and inserts[0][1][0] == "trial"  # inferred kind
    assert inserts[0][1][1] == "trial acme"  # derived title
    # all chunks written in one batch, one embedding per chunk
    assert len(conn.store["executemany"]) == 1
    assert len(conn.store["executemany"][0][1]) == n
    assert len(seen["texts"]) == n
    assert conn.store["commits"] >= 1


def test_ensure_schema_executes_committed_ddl():
    conn = FakeConn()
    ensure_schema(conn)
    executed = " ".join(sql for sql, _ in conn.store["execute"])
    assert "CREATE TABLE" in executed
    assert "chunks" in executed


def test_ingest_text_returns_document_id_and_chunk_count():
    conn = FakeConn()

    def fake_embed(texts: list[str]) -> list[list[float]]:
        return [[0.0] * 768 for _ in texts]

    doc_id, n = ingest_text(
        conn,
        "Aspirin SmPC",
        "drug_label",
        "## Contraindications\nPregnancy.\n\n## Posology\nOne daily.\n",
        embed=fake_embed,
    )

    assert doc_id == 42
    assert n >= 2
    execs = conn.store["execute"]
    assert any(sql.startswith("DELETE FROM documents") for sql, _ in execs)
    inserts = [(sql, p) for sql, p in execs if sql.startswith("INSERT INTO documents")]
    assert inserts[0][1][:2] == ("drug_label", "Aspirin SmPC")
