import importlib
import pytest

MODULES = [
    "shared",
    "shared.gcs",
    "shared.secrets",
]


def test_shared_imports():
    for mod_name in MODULES:
        importlib.import_module(mod_name)


class TestGeoImports:
    module_names = ["config", "scraper", "utils"]

    @pytest.fixture(autouse=True)
    def setup_path(self):
        import sys
        import os

        sys.path.insert(
            0, os.path.join(os.path.dirname(__file__), "..", "02_extract", "geo")
        )

    def test_all_modules_import(self):
        for mod_name in self.module_names:
            importlib.reload(importlib.import_module(mod_name))


class TestFranceTravailImports:
    module_names = ["config", "scraper", "utils", "auth"]

    @pytest.fixture(autouse=True)
    def setup_path(self):
        import sys
        import os

        sys.path.insert(
            0,
            os.path.join(
                os.path.dirname(__file__), "..", "02_extract", "france_travail"
            ),
        )

    def test_all_modules_import(self):
        for mod_name in self.module_names:
            importlib.reload(importlib.import_module(mod_name))


class TestAdzunaImports:
    module_names = ["config", "scraper", "utils"]

    @pytest.fixture(autouse=True)
    def setup_path(self):
        import sys
        import os

        sys.path.insert(
            0, os.path.join(os.path.dirname(__file__), "..", "02_extract", "adzuna")
        )

    def test_all_modules_import(self):
        for mod_name in self.module_names:
            importlib.reload(importlib.import_module(mod_name))
