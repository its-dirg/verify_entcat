from collections import Counter

import pytest
from saml2.assertion import Policy
from saml2.entity_category.edugain import COCO
from saml2.entity_category.refeds import RESEARCH_AND_SCHOLARSHIP
from saml2.entity_category.swamid import NREN, RESEARCH_AND_EDUCATION, EU, HEI, SFS_1993_1153

from verify_entcat.ec_compare import EntityCategoryComparison, EntityCategoryTestStatusEnum


class TestEntityCategoryVerifier:
    @pytest.fixture(autouse=True)
    def create_comparer(self):
        attribute_release_policy = Policy({
            "default": {"entity_categories": ["swamid", "refeds", "edugain"]}
        })
        self.entity_category_comparer = EntityCategoryComparison(attribute_release_policy)

    @pytest.mark.parametrize("entity_categories,expected_attributes", [
        ([''], ['edupersontargetedid']),
        ([COCO], ['edupersontargetedid', 'edupersonprincipalname', 'edupersonscopedaffiliation',
                  'edupersonaffiliation', 'mail', 'displayname', 'cn',
                  'schachomeorganization', 'schachomeorganizationtype']),
        ([NREN], ['edupersontargetedid']),
        ([RESEARCH_AND_SCHOLARSHIP],
         ['edupersontargetedid', 'givenname', 'sn', 'displayname', 'edupersonscopedaffiliation',
          'edupersonprincipalname', 'mail']),
        ([RESEARCH_AND_EDUCATION, EU],
         ['c', 'givenname', 'sn', 'displayname', 'o', 'schachomeorganization', 'mail',
          'edupersontargetedid', 'edupersonscopedaffiliation', 'edupersonprincipalname', 'co',
          'noreduorgacronym']),
        ([RESEARCH_AND_EDUCATION, HEI],
         ['c', 'givenname', 'sn', 'displayname', 'o', 'schachomeorganization', 'mail',
          'edupersontargetedid', 'edupersonscopedaffiliation', 'edupersonprincipalname', 'co',
          'noreduorgacronym']),
        ([RESEARCH_AND_EDUCATION, NREN],
         ['c', 'givenname', 'sn', 'displayname', 'o', 'schachomeorganization', 'mail',
          'edupersontargetedid', 'edupersonscopedaffiliation', 'edupersonprincipalname', 'co',
          'noreduorgacronym']),
        ([RESEARCH_AND_EDUCATION, NREN, SFS_1993_1153],
         ['c', 'givenname', 'sn', 'displayname', 'o', 'schachomeorganization', 'co', 'mail',
          'edupersontargetedid', 'edupersonscopedaffiliation', 'edupersonprincipalname',
          'noredupersonnin', 'noreduorgacronym'])
    ])
    def test_correct_attributes_per_entity_categories(self, entity_categories, expected_attributes):
        diff = self.entity_category_comparer(entity_categories,
                                             {k: None for k in expected_attributes})
        assert len(diff) == 0
        assert diff.status.value == EntityCategoryTestStatusEnum.ok

    def test_missing_attributes_coco(self):
        diff = self.entity_category_comparer([COCO], {k: None for k in ['edupersonprincipalname',
                                                                        'edupersonscopedaffiliation',
                                                                        'edupersonaffiliation',
                                                                        'displayname', 'cn',
                                                                        'schachomeorganizationtype']})
        assert Counter(diff.missing_attributes) == Counter(
            ['edupersontargetedid', 'schachomeorganization', 'mail'])
        assert diff.status.value == EntityCategoryTestStatusEnum.too_few

    def test_extra_attributes_nren(self):
        diff = self.entity_category_comparer([NREN], {k: None for k in
                                                      ['edupersontargetedid', 'displayname',
                                                       'edupersonscopedaffiliation',
                                                       'edupersonprincipalname',
                                                       'schachomeorganization',
                                                       'mail']})
        assert Counter(diff.extra_attributes) == Counter(
            ['displayname', 'edupersonscopedaffiliation', 'edupersonprincipalname',
             'schachomeorganization', 'mail'])
        assert diff.status.value == EntityCategoryTestStatusEnum.too_many

    def test_missing_and_extra_attributes_coc(self):
        diff = self.entity_category_comparer([COCO], {k: None for k in ['edupersonprincipalname',
                                                                        'edupersonscopedaffiliation',
                                                                        'edupersonaffiliation',
                                                                        'displayname', 'cn',
                                                                        'schachomeorganizationtype',
                                                                        'sn', 'co', 'o']})
        assert Counter(diff.missing_attributes) == Counter(
            ['edupersontargetedid', 'schachomeorganization', 'mail'])
        assert Counter(diff.extra_attributes) == Counter(['sn', 'co', 'o'])
        assert diff.status.value == EntityCategoryTestStatusEnum.too_few_too_many

    def test_case_insensitive_compare_of_attribute_names(self):
        diff = self.entity_category_comparer([COCO], {k: None for k in
                                                      ['EDUPERSONTARGETEDID', 'displayName',
                                                       'eduPersonScopedAffiliation',
                                                       'edupErsonPrinciPalnAme',
                                                       'ScHaChoMEoRgAniZaTiOn', 'MAIL',
                                                       'schAchomeoRganizationtYpe',
                                                       'eduPersonAffiliation', 'cn']})

        assert len(diff) == 0
        assert diff.status.value == EntityCategoryTestStatusEnum.ok
