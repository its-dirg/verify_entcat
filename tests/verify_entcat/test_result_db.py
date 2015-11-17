import os

import pytest

from verify_entcat.ec_compare import EntityCategoryTestResult
from verify_entcat.result_db import ResultDB


class TestResultDB:
    @pytest.fixture(autouse=True)
    def create_db(self, tmpdir):
        db_path = os.path.join(tmpdir.strpath, "result_db")
        self.db = ResultDB(db_path)

    def test_store_result(self):
        entry = EntityCategoryTestResult(missing=["foo"], extra=["bar"])
        self.db["https://idp.example.com"] = entry

        assert self.db["https://idp.example.com"] == entry

    def test_iterate_over_all_entries(self):
        entry = EntityCategoryTestResult(missing=["foo"], extra=["bar"])
        self.db["https://idp1.example.com"] = entry
        self.db["https://idp2.example.com"] = entry

        assert set(iter(self.db)) == set(["https://idp1.example.com", "https://idp2.example.com"])