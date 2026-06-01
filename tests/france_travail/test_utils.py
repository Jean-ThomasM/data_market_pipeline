import json
import pytest


@pytest.fixture
def config():
    from config import Config

    return Config(
        project_id="p",
        storage="local",
        ft_client_id="id",
        ft_client_key="key",
        scope="s",
        gcs_bucket_name="",
        token_url="",
        offres_base_url="",
        referentiels_base_url="",
        local_save_dir_offres="/tmp",
        local_save_dir_refs="/tmp",
        search_params=[],
    )


class TestSaveTextContent:
    def test_local(self, config, tmp_output_dir):
        from shared.storage import save_text_content

        cfg = config
        cfg.local_save_dir_offres = tmp_output_dir
        save_text_content(
            cfg,
            "hello",
            "test.txt",
            gcs_prefix="raw_offres",
            local_directory=tmp_output_dir,
        )

        assert (tmp_output_dir / "test.txt").read_text(encoding="utf-8") == "hello"

    def test_gcs(self, config, mock_gcs_write):
        from shared.storage import save_text_content

        cfg = config
        cfg.storage = "gcs"
        cfg.gcs_bucket_name = "bucket"
        save_text_content(
            cfg, "data", "f.ndjson", gcs_prefix="raw_offres", local_directory=None
        )

        mock_gcs_write.assert_called_once_with("bucket", "raw_offres/f.ndjson", b"data")


class TestSaveJsonPayload:
    def test_local(self, config, tmp_output_dir):
        from shared.storage import save_json_payload

        config.local_save_dir_refs = tmp_output_dir
        payload = [{"code": "M1811"}]
        save_json_payload(
            config,
            payload,
            "ref.json",
            gcs_prefix="raw_referentiels",
            local_directory=tmp_output_dir,
        )

        result = json.loads((tmp_output_dir / "ref.json").read_text(encoding="utf-8"))
        assert result == payload


class TestSaveNdjsonRecords:
    def test_local(self, config, tmp_output_dir):
        from shared.storage import save_ndjson_records

        config.local_save_dir_offres = tmp_output_dir
        records = [{"id": "1"}, {"id": "2"}]
        save_ndjson_records(
            config,
            records,
            "out.ndjson",
            gcs_prefix="raw_offres",
            local_directory=tmp_output_dir,
        )

        lines = (
            (tmp_output_dir / "out.ndjson")
            .read_text(encoding="utf-8")
            .strip()
            .split("\n")
        )
        assert len(lines) == 2
        assert json.loads(lines[0]) == {"id": "1"}
