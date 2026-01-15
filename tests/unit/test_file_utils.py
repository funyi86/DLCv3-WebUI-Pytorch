import os
import pytest

from src.core.utils.file_utils import sanitize_filename, safe_join


def test_sanitize_filename_basename():
    assert sanitize_filename("foo/bar.mp4") == "bar.mp4"
    assert sanitize_filename("bar.mp4") == "bar.mp4"


@pytest.mark.parametrize("name", ["", ".", ".."])
def test_sanitize_filename_invalid(name):
    with pytest.raises(ValueError):
        sanitize_filename(name)


def test_safe_join_within_root(tmp_path):
    root = tmp_path / "root"
    root.mkdir()
    result = safe_join(str(root), "child", "file.txt")
    assert result.startswith(str(root) + os.sep)


def test_safe_join_rejects_traversal(tmp_path):
    root = tmp_path / "root"
    root.mkdir()
    with pytest.raises(ValueError):
        safe_join(str(root), "..", "outside.txt")
