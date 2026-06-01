import json


class TestSaveTextContent:
    def test_local(self, config, tmp_output_dir):
        from utils import save_text_content

        config.local_save_dir_offres = tmp_output_dir
        save_text_content(
            config,
            "hello",
            "test.txt",
            gcs_prefix="raw_offres_adzuna",
            local_directory=tmp_output_dir,
        )

        assert (tmp_output_dir / "test.txt").read_text(encoding="utf-8") == "hello"

    def test_gcs(self, config, mock_gcs_write):
        from utils import save_text_content

        config.storage = "gcs"
        config.gcs_bucket_name = "bucket"
        save_text_content(
            config,
            "data",
            "f.ndjson",
            gcs_prefix="raw_offres_adzuna",
            local_directory=None,
        )

        mock_gcs_write.assert_called_once_with(
            "bucket", "raw_offres_adzuna/f.ndjson", b"data"
        )


class TestSaveNdjsonRecords:
    def test_local(self, config, tmp_output_dir):
        from utils import save_ndjson_records

        config.local_save_dir_offres = tmp_output_dir
        records = [{"id": "1"}, {"id": "2"}]
        save_ndjson_records(
            config,
            records,
            "out.ndjson",
            gcs_prefix="raw_offres_adzuna",
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
