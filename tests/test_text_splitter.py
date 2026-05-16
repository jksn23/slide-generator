from core.text_splitter import split_text_to_slides, split_visual_lines_to_chunks, wrap_text_to_visual_lines


def test_split_text_to_slides_respects_max_lines_and_words():
    text = (
        "Aku percaya kepada satu Allah Bapa Yang Mahakuasa Pencipta langit dan bumi "
        "segala yang kelihatan dan yang tidak kelihatan serta kepada satu Tuhan Yesus Kristus"
    )

    chunks = split_text_to_slides(text, max_lines=6, max_chars_per_line=24)

    assert all(len(chunk.splitlines()) <= 6 for chunk in chunks)
    assert "\n".join(chunks).split() == text.split()
    assert all(word in "\n".join(chunks) for word in ["Mahakuasa", "Pencipta", "Kristus"])


def test_split_text_to_slides_creates_continuation_chunks_for_long_lyrics():
    lyrics = "\n".join(
        [
            "Hai mari sembah Raja yang mulia",
            "Nyanyikan kasih dan rahmat-Nya",
            "Puji nama-Nya selama-lamanya",
            "Bersyukur dengan segenap hati",
            "Angkat suara memuliakan Tuhan",
            "Kasih-Nya tetap untuk selamanya",
            "Amin haleluya pujilah Dia",
        ]
    )

    chunks = split_text_to_slides(lyrics, max_lines=3, max_chars_per_line=80)

    assert len(chunks) == 3
    assert chunks[0].splitlines() == [
        "Hai mari sembah Raja yang mulia",
        "Nyanyikan kasih dan rahmat-Nya",
        "Puji nama-Nya selama-lamanya",
    ]


def test_wrap_text_to_visual_lines_preserves_words_and_paragraphs():
    text = "Saudara-saudara anggota jemaat Yesus Kristus\nBekerja bersama-sama jalan berdekat-dekat"

    lines = wrap_text_to_visual_lines(text, max_chars_per_line=24)

    assert "\n".join(lines).split() == text.split()
    assert all(len(line) <= 24 or len(line.split()) == 1 for line in lines)
    assert any(line.startswith("Saudara-saudara") for line in lines)
    assert "bersama-sama" in "\n".join(lines)


def test_split_visual_lines_to_chunks_limits_visual_lines_and_keeps_words():
    text = (
        "Saudara-saudara anggota jemaat Yesus Kristus sambutlah saudara-saudara yang dilantik "
        "menjadi Panitia Pemilihan Pelayan Khusus\n"
        "Bekerja bersama-sama jalan berdekat-dekat hidup dan beramah-ramah bersehati sefakat"
    )

    chunks = split_visual_lines_to_chunks(text, max_lines=3, max_chars_per_line=30)

    assert len(chunks) > 1
    assert all(len(chunk.splitlines()) <= 3 for chunk in chunks)
    assert "\n".join(chunks).split() == text.split()
    assert "Saudara-\nsaudara" not in "\n".join(chunks)
    assert "bersama-\nsama" not in "\n".join(chunks)
