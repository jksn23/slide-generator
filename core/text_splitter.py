import re


DEFAULT_MAX_CHARS_PER_LINE = 58


def normalize_content_line(line: str) -> str:
    """Normalize user-facing text without deleting words."""
    return re.sub(r"\s+", " ", (line or "").strip()).lstrip(":").strip()


def split_text_to_lines(text: str, max_chars_per_line: int = DEFAULT_MAX_CHARS_PER_LINE) -> list[str]:
    """Split text into visual lines without cutting words."""
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


def split_text_to_slides(
    text: str,
    max_lines: int,
    max_chars_per_line: int = DEFAULT_MAX_CHARS_PER_LINE,
) -> list[str]:
    """Split text into slide-safe chunks based on visual content lines."""
    limit = max(1, int(max_lines or 1))
    lines = split_text_to_lines(text, max_chars_per_line=max_chars_per_line)
    if not lines:
        return [""]
    return ["\n".join(lines[index:index + limit]) for index in range(0, len(lines), limit)]
