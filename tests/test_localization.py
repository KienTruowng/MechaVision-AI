"""Kiểm tra Unicode và hợp đồng dòng lệnh sau khi Việt hóa."""
import numpy as np
import pytest
from mechavision.cli import main
from mechavision.i18n import put_text


@pytest.mark.parametrize('argv', [[], ['live', '--detector', 'invalid'],
                                   ['simulate', '--fps', 'abc']])
def test_cli_errors_are_vietnamese(argv, capsys):
    with pytest.raises(SystemExit) as exc:
        main(argv)
    assert exc.value.code == 2
    text = capsys.readouterr().err
    assert 'Cách dùng:' in text
    assert 'lỗi:' in text
    assert 'error:' not in text


def test_cli_help_keeps_flags_and_choices(capsys):
    with pytest.raises(SystemExit) as exc:
        main(['live', '--help'])
    assert exc.value.code == 0
    text = capsys.readouterr().out
    assert '--detector {color,aruco,yolo}' in text
    assert '--geometry' in text
    assert 'Tệp JSON hình học đã hiệu chuẩn' in text
    assert 'Hiển thị trợ giúp và thoát' in text


def test_unicode_overlay_is_in_place_bgr_and_fits():
    image = np.zeros((70, 220, 3), dtype=np.uint8)
    result = put_text(image, 'Mất dấu — Không đủ độ tin cậy', (8, 42),
                      fontScale=.6, color=(0, 0, 255), thickness=2)
    assert result is image
    assert image[:, :, 2].any()
    assert not image[:, :, :2].any()
    assert not image[:8].any()
    assert not image[:, :8].any()
    assert image.shape == (70, 220, 3)


def test_unicode_diacritics_are_not_question_marks():
    vietnamese = np.zeros((70, 220, 3), dtype=np.uint8)
    fallback = vietnamese.copy()
    put_text(vietnamese, 'Độ bất định', (0, 40), fontScale=.6)
    put_text(fallback, '?? b?t ??nh', (0, 40), fontScale=.6)
    assert not np.array_equal(vietnamese, fallback)
