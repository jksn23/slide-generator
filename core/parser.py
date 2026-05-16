import re
from core.models import SlideType, SlideItem

def split_long_text(text: str, max_chars_per_line: int = 90) -> list:
    """Split a long text block into list of lines, respecting punctuation."""
    lines = text.split('\n')
    result = []
    for line in lines:
        line = line.strip()
        if not line:
            continue
        if len(line) <= max_chars_per_line:
            result.append(line)
        else:
            # Try to split on sentence boundaries first
            sentences = re.split(r'(?<=[.;?])\s+', line)
            current_line = ""
            for sentence in sentences:
                if not current_line:
                    if len(sentence) > max_chars_per_line:
                        # Split on commas
                        sub_parts = re.split(r'(?<=,)\s+', sentence)
                        sub_line = ""
                        for part in sub_parts:
                            if len(sub_line) + len(part) <= max_chars_per_line:
                                sub_line += (" " if sub_line else "") + part
                            else:
                                if sub_line:
                                    result.append(sub_line)
                                sub_line = part
                        if sub_line:
                            current_line = sub_line
                    else:
                        current_line = sentence
                else:
                    if len(current_line) + len(sentence) + 1 <= max_chars_per_line:
                        current_line += " " + sentence
                    else:
                        result.append(current_line)
                        if len(sentence) > max_chars_per_line:
                            sub_parts = re.split(r'(?<=,)\s+', sentence)
                            sub_line = ""
                            for part in sub_parts:
                                if len(sub_line) + len(part) <= max_chars_per_line:
                                    sub_line += (" " if sub_line else "") + part
                                else:
                                    if sub_line:
                                        result.append(sub_line)
                                    sub_line = part
                            if sub_line:
                                current_line = sub_line
                        else:
                            current_line = sentence
            if current_line:
                result.append(current_line)
    return result


def parse_docx(file_path: str, max_lines_per_slide: int = 6) -> list:
    try:
        import docx
    except ImportError:
        return [SlideItem(slide_type=SlideType.COVER, content="Error: python-docx not installed.")]

    doc = docx.Document(file_path)
    slides = []

    current_type = SlideType.COVER
    current_title = ""
    buffer_lines = []
    current_speaker = None

    # --- Nyanyian mode flag ---
    # True when we're inside a lagu/nyanyian section, so liturgi is center-aligned
    nyanyian_mode = False

    def flush_buffer():
        nonlocal buffer_lines, slides, current_speaker, current_type, nyanyian_mode
        if not buffer_lines:
            return

        # Split buffer into multiple slides if it exceeds max_lines
        chunks = [buffer_lines[i:i + max_lines_per_slide]
                  for i in range(0, len(buffer_lines), max_lines_per_slide)]

        for chunk in chunks:
            content = "\n".join(chunk)
            slide = SlideItem(
                slide_type=current_type,
                content=content,
                speaker=current_speaker,
                title=current_title,
                is_nyanyian=nyanyian_mode and current_type == SlideType.LITURGI
            )
            slides.append(slide)
        buffer_lines = []

    # Regex to catch song-title lines regardless of Word paragraph style or case.
    # Matches lines starting with: Menyanyi, Nyanyian, KJ, NKB, PKJ, PKJ2, Mazmur
    # optionally followed by a number and/or song name.
    _LAGU_RE = re.compile(
        r'^(Menyanyi|Nyanyian|KJ|NKB|PKJ2?|Mazmur|Hymne|Kidung)\b', re.IGNORECASE
    )

    for p in doc.paragraphs:
        text = p.text.strip()
        if not text:
            continue

        text_lower = text.lower()

        # --- Detect speaker tags (P:, J:, P+J:) ---
        speaker_match = re.match(r'^(P\+J|P\s*\+\s*J|P|J|L|S)\s*[:]\s*(.*)', text, re.IGNORECASE)
        if speaker_match:
            flush_buffer()
            current_type = SlideType.LITURGI
            speaker_tag = speaker_match.group(1).upper().replace(" ", "")
            content_after_tag = speaker_match.group(2)
            current_speaker = speaker_tag
            if content_after_tag:
                buffer_lines.extend(split_long_text(content_after_tag))
            continue

        # --- Detect song titles (any paragraph style / any case) ---
        # e.g. "Menyanyi NKB No. 3 "Terpujilah Allah""
        if _LAGU_RE.match(text):
            flush_buffer()
            current_speaker = None
            nyanyian_mode = True
            current_type = SlideType.JUDUL_LAGU
            current_title = text
            slides.append(SlideItem(
                slide_type=SlideType.JUDUL_LAGU, content=text, title=text, is_nyanyian=True
            ))
            current_type = SlideType.LIRIK_LAGU
            continue

        # --- Detect headings / section titles ---
        if p.style.name.startswith('Heading') or text.isupper():
            flush_buffer()
            current_speaker = None

            is_lagu = any(kw in text.upper() for kw in ["LAGU", "MENYANYI", "KJ ", "NKB ", "PKJ ", "NYANYIAN"])
            is_bacaan = any(kw in text.upper() for kw in ["BACAAN", "ALKITAB"])
            is_penutup = any(kw in text.upper() for kw in ["BERKAT", "PENUTUP"]) or text.upper() == "AMIN"
            is_doa = any(kw in text.upper() for kw in ["PERSIAPAN", "DOA", "PANGGILAN", "VOTUM", "SALAM"])

            if is_lagu:
                nyanyian_mode = True
                current_type = SlideType.JUDUL_LAGU
                current_title = text
                slides.append(SlideItem(slide_type=current_type, content=text, title=text, is_nyanyian=True))
                current_type = SlideType.LIRIK_LAGU  # subsequent text is lyrics

            elif is_bacaan:
                nyanyian_mode = False
                current_type = SlideType.BAGIAN
                slides.append(SlideItem(slide_type=current_type, content=text, title=text))
                current_type = SlideType.BACAAN

            elif is_penutup:
                nyanyian_mode = False
                current_type = SlideType.BAGIAN
                if text.upper() != "AMIN":
                    slides.append(SlideItem(slide_type=current_type, content=text, title=text))
                current_type = SlideType.PENUTUP

            elif is_doa:
                nyanyian_mode = False
                current_type = SlideType.BAGIAN
                slides.append(SlideItem(slide_type=current_type, content=text, title=text))
                current_type = SlideType.LITURGI

            else:
                if not slides:
                    current_type = SlideType.COVER
                    buffer_lines.extend(split_long_text(text))
                else:
                    nyanyian_mode = False
                    current_type = SlideType.BAGIAN
                    slides.append(SlideItem(slide_type=current_type, content=text, title=text))
                    current_type = SlideType.LITURGI
            continue

        # --- Detect instruction slides ---
        if "dimohon untuk" in text_lower or "mulai ibadah" in text_lower or text.startswith(("(", "[", "*")):
            flush_buffer()
            current_type = SlideType.INSTRUKSI
            slides.append(SlideItem(slide_type=current_type, content=text))
            continue

        # Normal text → add to buffer
        buffer_lines.extend(split_long_text(text))

    flush_buffer()

    # Assign sequential slide numbers
    for i, slide in enumerate(slides):
        slide.slide_number = i + 1

    if not slides:
        slides.append(SlideItem(
            slide_type=SlideType.COVER,
            content="Tidak ada teks ditemukan.",
            slide_number=1
        ))

    return slides
