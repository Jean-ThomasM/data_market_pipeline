import json
import pytest


class TestSaveTextContent:
    def test_local(self, tmp_output_dir):
        from config import Config
        from shared.storage import save_text_content

        cfg = Config(
            storage="local",
            project_id=None,
            gcs_bucket_name="",
            local_save_directory=tmp_output_dir,
        )
        save_text_content(
            cfg,
            "hello",
            "test.txt",
            gcs_prefix="raw_geo",
            local_directory=tmp_output_dir,
        )

        path = tmp_output_dir / "test.txt"
        assert path.read_text(encoding="utf-8") == "hello"

    def test_gcs_no_bucket(self):
        from config import Config
        from shared.storage import save_text_content

        cfg = Config(
            storage="gcs",
            project_id="p",
            gcs_bucket_name=None,
            local_save_directory=None,
        )
        with pytest.raises(ValueError, match="GCS_BUCKET_NAME"):
            save_text_content(
                cfg, "data", "f.txt", gcs_prefix="raw_geo", local_directory=None
            )

    def test_gcs_calls_write_file(self, mock_gcs_write):
        from config import Config
        from shared.storage import save_text_content

        cfg = Config(
            storage="gcs",
            project_id="p",
            gcs_bucket_name="bucket",
            local_save_directory=None,
        )
        save_text_content(
            cfg, "content123", "dest.ndjson", gcs_prefix="raw_geo", local_directory=None
        )

        mock_gcs_write.assert_called_once_with(
            "bucket", "raw_geo/dest.ndjson", b"content123"
        )

    def test_local_missing_dir(self):
        from config import Config
        from shared.storage import save_text_content

        cfg = Config(
            storage="local",
            project_id=None,
            gcs_bucket_name="",
            local_save_directory=None,
        )
        with pytest.raises(ValueError, match="local output directory"):
            save_text_content(
                cfg, "data", "f.txt", gcs_prefix="raw_geo", local_directory=None
            )


class TestSaveJsonPayload:
    def test_local(self, tmp_output_dir):
        from config import Config
        from shared.storage import save_json_payload

        cfg = Config(
            storage="local",
            project_id=None,
            gcs_bucket_name="",
            local_save_directory=tmp_output_dir,
        )
        payload = {"key": "value", "num": 42}
        save_json_payload(
            cfg,
            payload,
            "data.json",
            gcs_prefix="raw_geo",
            local_directory=tmp_output_dir,
        )

        result = json.loads((tmp_output_dir / "data.json").read_text(encoding="utf-8"))
        assert result == payload


class TestSaveNdjsonRecords:
    def test_local(self, tmp_output_dir):
        from config import Config
        from shared.storage import save_ndjson_records

        cfg = Config(
            storage="local",
            project_id=None,
            gcs_bucket_name="",
            local_save_directory=tmp_output_dir,
        )
        records = [{"id": 1}, {"id": 2}]
        save_ndjson_records(
            cfg,
            records,
            "out.ndjson",
            gcs_prefix="raw_geo",
            local_directory=tmp_output_dir,
        )

        lines = (
            (tmp_output_dir / "out.ndjson")
            .read_text(encoding="utf-8")
            .strip()
            .split("\n")
        )
        assert len(lines) == 2
        assert json.loads(lines[0]) == {"id": 1}
        assert json.loads(lines[1]) == {"id": 2}
