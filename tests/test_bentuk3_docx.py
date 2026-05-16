from pathlib import Path

from core.models import SlideType
from core.parser import SlideBuilder, parse_docx_to_deck
from core.text_splitter import wrap_text_to_visual_lines


SAMPLE_DOCX = Path(__file__).resolve().parent.parent / "Bentuk 3.docx"


def _deck(max_lines: int = 6):
    return parse_docx_to_deck(str(SAMPLE_DOCX), max_lines_per_slide=max_lines)


def _speaker_lines(deck):
    return [
        line
        for slide in deck.slides
        for line in slide.speaker_lines
        if slide.type == SlideType.LITURGY_DIALOG
    ]


def test_bentuk3_detects_tab_speakers_and_calon():
    lines = _speaker_lines(_deck())
    speakers = [line.speaker for line in lines if line.speaker]

    assert "PK" in speakers
    assert "P" in speakers
    assert "J" in speakers
    assert "P+J" in speakers
    assert "p" in speakers
    assert "Calon" in speakers
    assert any(line.speaker == "Calon" and line.text.startswith("Ya, saya yakin") for line in lines)


def test_bentuk3_recognizes_nas_pembimbing_heading():
    deck = _deck()

    assert any(
        slide.type == SlideType.SECTION and "NAS PEMBIMBING" in slide.content
        for slide in deck.slides
    )


def test_bentuk3_pj_menyanyi_opens_song_lyrics():
    deck = _deck()
    song_titles = [slide for slide in deck.slides if slide.type == SlideType.SONG_TITLE]
    lyric_slides = [slide for slide in deck.slides if slide.type == SlideType.SONG_LYRICS]

    assert any("Bekerja Bersama-Sama" in slide.content for slide in song_titles)
    assert any("Bekerja bersama-sama" in slide.content for slide in lyric_slides)


def test_bentuk3_refr_and_indented_song_lines_stay_lyrics():
    deck = _deck()
    lyric_text = " ".join(
        "\n".join(slide.content for slide in deck.slides if slide.type == SlideType.SONG_LYRICS).split()
    )
    liturgy_text = "\n".join(slide.content for slide in deck.slides if slide.type == SlideType.LITURGY_DIALOG)

    assert "Refr Ringan semua di Kalvari" in lyric_text
    assert "Ringan semua di Kalvari, karn’a Yesus dekat." in lyric_text
    assert "Bagi Yesus kuserahkan hidupku seluruhnya;" in lyric_text
    assert "Refr Ringan semua di Kalvari" not in liturgy_text


def test_bentuk3_indented_dialog_lines_inherit_previous_speaker():
    effective_text_by_speaker = {}
    for slide in _deck(max_lines=20).slides:
        last_speaker = ""
        for line in slide.speaker_lines:
            if line.speaker:
                last_speaker = line.speaker
            speaker = line.speaker or last_speaker
            effective_text_by_speaker[speaker] = f"{effective_text_by_speaker.get(speaker, '')} {line.text}"

    assert "Demikianlah Firman TUHAN." in effective_text_by_speaker["P"]
    assert "Firman Allah menasehati" in effective_text_by_speaker["p"]


def test_bentuk3_applies_max_lines_after_final_chunking():
    deck = _deck(max_lines=6)
    builder = SlideBuilder()

    checked_types = {
        SlideType.SONG_LYRICS,
        SlideType.LITURGY_DIALOG,
        SlideType.PRAYER,
        SlideType.BIBLE_READING,
        SlideType.BLESSING,
        SlideType.CLOSING,
    }
    assert all(
        len(
            wrap_text_to_visual_lines(
                slide.content,
                builder._max_chars_for_slide(slide.type, deck.aspect_ratio),
            )
        ) <= 6
        for slide in deck.slides
        if slide.type in checked_types
    )


def test_bentuk3_long_dialog_and_lyrics_are_visual_line_limited():
    deck = _deck(max_lines=6)
    builder = SlideBuilder()
    targets = [
        slide
        for slide in deck.slides
        if "Saudara-saudara anggota jemaat" in slide.content
        or "Bekerja bersama-sama" in slide.content
    ]

    assert targets
    assert all(
        len(
            wrap_text_to_visual_lines(
                slide.content,
                builder._max_chars_for_slide(slide.type, deck.aspect_ratio),
            )
        ) <= 6
        for slide in targets
    )


def test_bentuk3_chunk_boundaries_do_not_cut_words():
    deck = _deck(max_lines=6)
    content = "\n".join(slide.content for slide in deck.slides)

    assert "Saudara-saudara" in content
    assert "bersama-sama" in content
    assert "Saudara-\nsaudara" not in content
    assert "bersama-\nsama" not in content
