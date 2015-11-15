import json
from enum import IntEnum


class EntityCategoryTestStatus(IntEnum):
    ok = 1
    too_few = 2
    too_many = 3
    too_few_too_many = 4


class EntityCategoryTestResult:
    def __init__(self, missing, extra):
        self.missing_attributes = set(missing)
        self.extra_attributes = set(extra)

        if len(self) == 0:
            self.status = EntityCategoryTestStatus.ok
        elif len(missing) > 0 and len(extra) > 0:
            self.status = EntityCategoryTestStatus.too_few_too_many
        elif len(missing) > 0:
            self.status = EntityCategoryTestStatus.too_few
        elif len(extra) > 0:
            self.status = EntityCategoryTestStatus.too_many

    def to_dict(self):
        return {
            "missing_attributes": list(self.missing_attributes),
            "extra_attributes": list(self.extra_attributes),
            "status": self.status
        }

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
        expected_attributes = get_expected_attributes(self.policy, entity_categories)
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


def get_expected_attributes(attribute_release_policy, entity_categories):
    def expected_attributes_for_entity_categories(ec_maps, entity_categories, **kwargs):
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

    return attribute_release_policy.get("entity_categories", None,
                                        post_func=expected_attributes_for_entity_categories,
                                        entity_categories=entity_categories)
