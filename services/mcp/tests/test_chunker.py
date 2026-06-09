from ingest.chunker import OVERLAP, TARGET_TOKENS, chunk_document, split_sections


def test_empty_text_yields_no_chunks():
    assert chunk_document("") == []
    assert chunk_document("   \n  \n") == []


def test_split_sections_markdown_headings():
    text = (
        "## Eligibility\n"
        "Adults aged 18 to 65.\n\n"
        "## Contraindications\n"
        "Known hypersensitivity.\n"
    )
    secs = dict(split_sections(text))
    assert "Eligibility" in secs
    assert "Contraindications" in secs
    assert "Adults aged 18 to 65." in secs["Eligibility"]


def test_split_sections_numbered_and_caps():
    text = (
        "4.3 Contraindications\n"
        "Do not use in pregnancy.\n\n"
        "DOSAGE AND ADMINISTRATION\n"
        "Take one tablet daily.\n"
    )
    names = [name for name, _ in split_sections(text)]
    assert "4.3 Contraindications" in names
    assert "DOSAGE AND ADMINISTRATION" in names


def test_text_before_first_heading_is_kept():
    text = "Intro paragraph here.\n\n## Methods\nWe did things.\n"
    secs = dict(split_sections(text))
    assert any("Intro paragraph" in body for body in secs.values())


def test_chunk_carries_section_label_and_sequential_ordinals():
    text = "## A\nalpha text\n\n## B\nbeta text\n"
    chunks = chunk_document(text)
    assert [c.ordinal for c in chunks] == list(range(len(chunks)))
    assert {"A", "B"} <= {c.section for c in chunks}


def test_token_count_matches_word_count():
    chunks = chunk_document("## S\none two three four five\n")
    assert chunks
    for c in chunks:
        assert c.token_count == len(c.text.split())


def test_long_section_is_windowed_with_overlap():
    body = " ".join(f"w{i}" for i in range(TARGET_TOKENS * 2 + 50))
    chunks = chunk_document("", sections=[("Big", body)])
    assert len(chunks) >= 2
    for c in chunks:
        assert c.token_count <= TARGET_TOKENS
        assert c.section == "Big"
    overlap = round(TARGET_TOKENS * OVERLAP)
    first_words = chunks[0].text.split()
    second_words = chunks[1].text.split()
    assert first_words[-overlap:] == second_words[:overlap]


def test_explicit_sections_bypass_detection():
    chunks = chunk_document("ignored ## Heading text", sections=[("Custom", "just a little text")])
    assert len(chunks) == 1
    assert chunks[0].section == "Custom"
    assert chunks[0].text == "just a little text"
