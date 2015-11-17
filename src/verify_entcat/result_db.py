import pickle
import shelve


class ResultDB:
    def __init__(self, db_path):
        self.db_path = db_path
        self.db_params = dict(protocol=pickle.HIGHEST_PROTOCOL)

    def __setitem__(self, idp_entity_id, test_result):
        with shelve.open(self.db_path, **self.db_params) as db:
            db[idp_entity_id] = test_result

    def __getitem__(self, idp_entity_id):
        with shelve.open(self.db_path, **self.db_params) as db:
            return db[idp_entity_id]
