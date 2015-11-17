import os
from collections import Counter

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

        assert self.db["https://idp.example.com"] == [entry]

    def test_iterate_over_all_entries(self):
        entry = EntityCategoryTestResult(missing=["foo"], extra=["bar"])
        self.db["https://idp1.example.com"] = entry
        self.db["https://idp2.example.com"] = entry

        assert set(iter(self.db)) == set(["https://idp1.example.com", "https://idp2.example.com"])

    def test_store_results_for_different_tests(self):
        entry1 = EntityCategoryTestResult(missing=["foo"], extra=["bar"], test_id="test1")
        entry2 = EntityCategoryTestResult(missing=["bar"], extra=["foo"], test_id="test2")
        self.db["https://idp.example.com"] = entry1
        self.db["https://idp.example.com"] = entry2

        assert Counter(self.db["https://idp.example.com"]) == Counter([entry1, entry2])

    def test_update_with_new_result(self):
        entry1 = EntityCategoryTestResult(missing=["foo"], extra=["bar"], test_id="test")
        entry2 = EntityCategoryTestResult(missing=[], extra=[], test_id="test")

        self.db["https://idp.example.com"] = entry1
        assert self.db["https://idp.example.com"] == [entry1]

        self.db["https://idp.example.com"] = entry2
        assert self.db["https://idp.example.com"] == [entry2]
