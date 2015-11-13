import json


class EntityCategoryTestResult:
    def __init__(self, missing, extra):
        self.missing_attributes = set(missing)
        self.extra_attributes = set(extra)

    def to_json(self):
        return json.dumps({"missing_attributes": list(self.missing_attributes),
                           "extra_attributes": list(self.extra_attributes)})

    def __eq__(self, other):
        return self.missing_attributes == other.missing_attributes and self.extra_attributes == other.extra_attributes

    def __len__(self):
        return len(self.missing_attributes) + len(self.extra_attributes)

    def __repr__(self):
        return "{}(missing={}, extra={})".format(type(self).__name__, self.missing_attributes,
                                                 self.extra_attributes)


class EntityCategoryComparison:
    def __init__(self, attribute_release_policy):
        self.policy = attribute_release_policy

    def __call__(self, entity_categories, attributes):
        expected_attributes = self.policy.get("entity_categories", None,
                                              post_func=self.expected_attributes_for_entity_categories,
                                              entity_categories=entity_categories)
        lowercase_attribute_names = [k.lower() for k in attributes.keys()]

        missing = []
        for key in expected_attributes:
            if key.lower() not in lowercase_attribute_names:
                missing.append(key)

        extra = []
        for key in lowercase_attribute_names:
            if key not in expected_attributes:
                extra.append(key)
        return EntityCategoryTestResult(missing, extra)

    def expected_attributes_for_entity_categories(self, ec_maps, entity_categories, **kwargs):
        entity_categories_set = set(entity_categories)
        expected_attributes = set()
        for ec_map in ec_maps:
            for ec, released_attributes in ec_map.items():
                always_released = ec == ""
                covers_ec_combo = isinstance(ec, tuple) and entity_categories_set.issuperset(
                    ec)  # specified entity categories includes at least the release policies entity categories
                if ec in entity_categories or always_released or covers_ec_combo:
                    expected_attributes.update(released_attributes)

        return expected_attributes
