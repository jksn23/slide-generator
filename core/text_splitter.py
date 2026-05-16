import re


DEFAULT_MAX_CHARS_PER_LINE = 58
DEFAULT_SQUARE_MAX_CHARS_PER_LINE = 42
REFERENCE_FONT_SIZE = 42


def normalize_content_line(line: str) -> str:
    """Normalize user-facing text without deleting words."""
    return re.sub(r"\s+", " ", (line or "").strip()).lstrip(":").strip()


def wrap_text_to_visual_lines(text: str, max_chars_per_line: int = DEFAULT_MAX_CHARS_PER_LINE) -> list[str]:
    """Wrap text into visual lines without cutting words."""
    max_chars = max(1, int(max_chars_per_line or DEFAULT_MAX_CHARS_PER_LINE))
    lines: list[str] = []

    for raw_paragraph in (text or "").splitlines():
        paragraph = normalize_content_line(raw_paragraph)
        if not paragraph:
            continue

        current = ""
        for word in paragraph.split():
            if not current:
                current = word
            elif len(current) + 1 + len(word) <= max_chars:
                current = f"{current} {word}"
            else:
                lines.append(current)
                current = word
        if current:
            lines.append(current)

    return lines


def split_visual_lines_to_chunks(
    text: str,
    max_lines: int,
    max_chars_per_line: int = DEFAULT_MAX_CHARS_PER_LINE,
) -> list[str]:
    """Split text into slide-safe chunks based on visual content lines."""
    limit = max(1, int(max_lines or 1))
    lines = wrap_text_to_visual_lines(text, max_chars_per_line=max_chars_per_line)
    if not lines:
        return [""]
    return ["\n".join(lines[index:index + limit]) for index in range(0, len(lines), limit)]


def max_chars_for_style(
    font_size: int | float | None = None,
    aspect_ratio: str = "square",
    base_chars: int = DEFAULT_SQUARE_MAX_CHARS_PER_LINE,
) -> int:
    """Estimate visual line capacity for the slide shape and font size."""
    ratio_factor = {
        "square": 1.0,
        "standard_4_3": 1.12,
        "landscape_16_9": 1.35,
    }.get(aspect_ratio, 1.0)
    size = float(font_size or REFERENCE_FONT_SIZE)
    size_factor = REFERENCE_FONT_SIZE / max(size, 1.0)
    return max(18, int(round(base_chars * ratio_factor * size_factor)))


def split_text_to_lines(text: str, max_chars_per_line: int = DEFAULT_MAX_CHARS_PER_LINE) -> list[str]:
    """Compatibility wrapper for older imports."""
    return wrap_text_to_visual_lines(text, max_chars_per_line=max_chars_per_line)


def split_text_to_slides(
    text: str,
    max_lines: int,
    max_chars_per_line: int = DEFAULT_MAX_CHARS_PER_LINE,
) -> list[str]:
    """Compatibility wrapper for older imports."""
    return split_visual_lines_to_chunks(
        text,
        max_lines=max_lines,
        max_chars_per_line=max_chars_per_line,
    )
