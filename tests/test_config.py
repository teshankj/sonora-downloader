from sonora.config import default_output_dir


def test_default_output_dir_is_under_music():
    assert default_output_dir().name == "SONORA"
    assert default_output_dir().parent.name == "Music"
