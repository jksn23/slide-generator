from core.models import SlideItem, SlideType
from ui.fullscreen_preview import FullscreenPreviewDialog
from ui.main_window import transition_value_from_label
from ui.components import PreviewSlideItemWidget, VisualSlidePreviewWidget


def test_visual_preview_contract_defaults_to_square():
    assert VisualSlidePreviewWidget.DEFAULT_SIZE == 280


def test_visual_preview_dimensions_follow_aspect_ratio():
    assert VisualSlidePreviewWidget.preview_dimensions(360, "square") == (360, 360)
    assert VisualSlidePreviewWidget.preview_dimensions(360, "standard_4_3") == (360, 270)
    assert VisualSlidePreviewWidget.preview_dimensions(360, "landscape_16_9") == (360, 202)


def test_preview_uses_slide_type_labels_and_template_contract():
    slide = SlideItem(type=SlideType.SONG_LYRICS, content="Haleluya")

    assert slide.type.label == "Lirik Lagu"
    assert PreviewSlideItemWidget.selected is not None


def test_preview_uses_same_speaker_color_contract_as_template():
    style = {"color": "#FFFFFF", "speaker_colors": {"P": "#FFFFFF", "J": "#F2C94C", "P+J": "#F2C94C", "S": "#FFFFFF"}}

    assert VisualSlidePreviewWidget.speaker_color("P", style) == "#FFFFFF"
    assert VisualSlidePreviewWidget.speaker_color("J", style) == "#F2C94C"
    assert VisualSlidePreviewWidget.speaker_color("P+J", style) == "#F2C94C"
    assert VisualSlidePreviewWidget.speaker_color("S", style) == "#FFFFFF"


def test_transition_mapping_supports_morph():
    assert transition_value_from_label("Morph") == "morph"
    assert transition_value_from_label("Tanpa Transisi") is None


def test_fullscreen_preview_dialog_import_contract():
    assert FullscreenPreviewDialog.__name__ == "FullscreenPreviewDialog"
