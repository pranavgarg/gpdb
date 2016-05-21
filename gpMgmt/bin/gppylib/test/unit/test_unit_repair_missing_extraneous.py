from mock import *

from gp_unittest import *
from gpcheckcat_modules.repair_missing_extraneous import RepairMissingExtraneous
from gppylib.gpcatalog import GPCatalogTableForeignKey

class RepairMissingExtraneousTestCase(GpTestCase):
    def setUp(self):
        self.subject = RepairMissingExtraneous()

    def test_create_repair_sql_returns_sql(self):
        entries =\
        [(49401, 'cmax', 49401, '{2}'), (49401, 'cmin', 49401, '{2}'), (49401, 'ctid', 49401, '{2}'), (49401, 'gp_segment_id', 49401, '{2}'), (49401, 'tableoid', 49401, '{2}'), (49401, 'xmax', 49401, '{2}'), (49401, 'xmin', 49401, '{2}')]

        """"[GPCatalogTableForeignKey: pg_attribute; col: [u'attrelid']; , o
            GPCatalogTableForeignKey: pg_attribute; col: [u'atttypid']; ]"""
        fkObj1 = GPCatalogTableForeignKey(tname="pg_attribute",cols=["attrelid"],
                                         pktablename="pg_class",pkey="oid")
        fkObj2 = GPCatalogTableForeignKey(tname="pg_attribute",cols=["atttypid"],
                                         pktablename="pg_type",pkey="oid")
        fklist = [fkObj1, fkObj2]
        repair_sql_contents = self.subject.create_extra_repair_sql("pg_attribute",
                                                                   entries,
                                                                   fklist)


        self.assertEqual(len(repair_sql_contents), 1)
        self.assertEqual(repair_sql_contents[0], "delete from pg_attribute "
                                                 "where attrelid=49401;")

if __name__ == '__main__':
    run_tests()
