import pytest


@pytest.fixture
def tmp_output_dir(tmp_path):
    return tmp_path


@pytest.fixture
def mock_gcs_write(mocker):
    return mocker.patch("shared.gcs.write_file")
