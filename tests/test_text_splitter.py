from core.text_splitter import split_text_to_slides


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
