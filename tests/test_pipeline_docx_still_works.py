from core.models import SlideType
from core.parser import parse_docx_to_deck


def test_pipeline_docx_still_works_with_service_document_path():
    deck = parse_docx_to_deck("test.docx", max_lines_per_slide=6)

    assert deck.slides
    assert deck.metadata.get("service_document")
    assert any(slide.type in {SlideType.COVER, SlideType.SECTION, SlideType.LITURGY_DIALOG} for slide in deck.slides)
