from core.models import SlideType
from core.parser import BlockClassifier, RawBlock, parse_blocks


def test_liturgy_detects_p_j_and_joint_speaker():
    deck = parse_blocks(
        [
            RawBlock("PERSIAPAN", "Heading 1", 0),
            RawBlock("P: Kasih karunia menyertai kamu.", "Normal", 1),
            RawBlock("J: Dan menyertai saudara juga.", "Normal", 2),
            RawBlock("P+J: Amin.", "Normal", 3),
        ]
    )

    liturgy = [slide for slide in deck.slides if slide.type == SlideType.LITURGY_DIALOG]
    speakers = [line.speaker for line in liturgy[0].speaker_lines]

    assert speakers == ["P", "J", "P+J"]


def test_liturgy_slide_has_no_empty_content():
    deck = parse_blocks(
        [
            RawBlock("PERSIAPAN", "Heading 1", 0),
            RawBlock("P: Marilah kita beribadah.", "Normal", 1),
        ]
    )

    assert all(slide.content.strip() for slide in deck.slides)


def test_liturgy_detects_speaker_without_colon_and_groups_until_next_heading():
    deck = parse_blocks(
        [
            RawBlock("TAHBISAN DAN SALAM", "Normal", 0, has_bold=True),
            RawBlock("P Tetapi TUHAN bersemayam untuk selama-lamanya.", "Normal", 1),
            RawBlock("J Amin", "Normal", 2),
            RawBlock("NAS PEMBIMBING", "Normal", 3, has_bold=True),
            RawBlock("Mazmur 9:8-9", "Normal", 4),
        ],
        max_lines_per_slide=1,
    )

    liturgy = [slide for slide in deck.slides if slide.type == SlideType.LITURGY_DIALOG]
    reading = [slide for slide in deck.slides if slide.type == SlideType.BIBLE_READING]

    assert len(liturgy) == 2
    assert [slide.speaker_lines[0].speaker for slide in liturgy] == ["P", "J"]
    assert "Tetapi TUHAN" in liturgy[0].speaker_lines[0].text
    assert reading


def test_liturgy_dialog_chunks_after_grouping_and_preserves_continuations():
    deck = parse_blocks(
        [
            RawBlock("TAHBISAN DAN SALAM", "Normal", 0, has_bold=True),
            RawBlock(
                "P: Saudara-saudara yang dikasihi Tuhan marilah kita menghadap Dia dengan hati yang bersyukur",
                "Normal",
                1,
            ),
            RawBlock("J: Amin", "Normal", 2),
        ],
        max_lines_per_slide=2,
    )

    liturgy = [slide for slide in deck.slides if slide.type == SlideType.LITURGY_DIALOG]

    assert len(liturgy) >= 2
    assert all(len(slide.content.splitlines()) <= 2 for slide in liturgy)
    assert liturgy[0].speaker_lines[0].speaker == "P"
    assert liturgy[0].speaker_lines[1].speaker == ""


def test_liturgy_blank_speaker_marker_applies_to_following_line():
    deck = parse_blocks(
        [
            RawBlock("TAHBISAN DAN SALAM", "Normal", 0, has_bold=True),
            RawBlock("P :", "Normal", 1),
            RawBlock(": Kasih karunia dan damai sejahtera menyertai kamu.", "Normal", 2),
            RawBlock("J : Amin", "Normal", 3),
        ],
        max_lines_per_slide=6,
    )

    liturgy = [slide for slide in deck.slides if slide.type == SlideType.LITURGY_DIALOG]

    assert liturgy[0].speaker_lines[0].speaker == "P"
    assert liturgy[0].speaker_lines[0].text == "Kasih karunia dan damai sejahtera menyertai kamu."
    assert not liturgy[0].speaker_lines[0].text.startswith(":")


def test_liturgy_continuation_chunk_starts_with_effective_speaker():
    deck = parse_blocks(
        [
            RawBlock("TAHBISAN DAN SALAM", "Normal", 0, has_bold=True),
            RawBlock(
                "P: Satu dua tiga empat lima enam tujuh delapan sembilan sepuluh sebelas dua belas tiga belas",
                "Normal",
                1,
            ),
        ],
        max_lines_per_slide=1,
    )

    liturgy = [slide for slide in deck.slides if slide.type == SlideType.LITURGY_DIALOG]

    assert len(liturgy) > 1
    assert all(slide.speaker_lines[0].speaker == "P" for slide in liturgy)


def test_speaker_regex_accepts_common_liturgy_variants():
    classifier = BlockClassifier()
    cases = {
        "P: Teks P": ("P", "Teks P"),
        "P : Teks P": ("P", "Teks P"),
        "P\tTeks P": ("P", "Teks P"),
        "P \tTeks P": ("P", "Teks P"),
        "P Teks P": ("P", "Teks P"),
        "P , Teks P": ("P", "Teks P"),
        "J: Amin": ("J", "Amin"),
        "J\tAmin": ("J", "Amin"),
        "J : Amin": ("J", "Amin"),
        "J Amin": ("J", "Amin"),
        "P+J: Amin": ("P+J", "Amin"),
        "P+J\tAmin": ("P+J", "Amin"),
        "P+J Amin": ("P+J", "Amin"),
        "PK: Pelayan khusus": ("PK", "Pelayan khusus"),
        "PK\tPelayan khusus": ("PK", "Pelayan khusus"),
        "PK Pelayan khusus": ("PK", "Pelayan khusus"),
        "p\tpetunjuk": ("p", "petunjuk"),
        "Calon : Ya, saya yakin.": ("Calon", "Ya, saya yakin."),
        "L: Liturgos": ("L", "Liturgos"),
        "S: Semua": ("S", "Semua"),
    }

    for text, expected in cases.items():
        classified = classifier.classify(RawBlock(text), has_cover=True)
        assert classified.kind == "speaker"
        assert (classified.speaker, classified.text) == expected
