from mock import *

from gp_unittest import *
from gpcheckcat_modules.repair_missing_extraneous import RepairMissingExtraneous

class RepairMissingExtraneousTestCase(GpTestCase):
    def setUp(self):
        self.subject = RepairMissingExtraneous()

    def test_create_repair_sql_returns_sql(self):
        entries = [(49401, 'cmax', 49401, '{2}'),
                   (49401, 'cmin', 49401, '{2}'),
                   (49401, 'ctid', 49401, '{2}'),
                   (49401, 'gp_segment_id', 49401, '{2}'),
                   (49401, 'tableoid', 49401, '{2}'),
                   (49401, 'xmax', 49401, '{2}'),
                   (49401, 'xmin', 49401, '{2}')]

        catalog_table_mock = Mock(spec=['getTableName'])
        catalog_table_mock.getTableName.return_value = "pg_attribute"
        repair_sql_contents = self.subject.create_extra_repair_sql(catalog_table_mock,
                                                                   entries,
                                                                   "attrelid")


        self.assertEqual(len(repair_sql_contents), 1)
        self.assertEqual(repair_sql_contents[0], "delete from pg_attribute "
                                                 "where attrelid=49401;")

if __name__ == '__main__':
    run_tests()
