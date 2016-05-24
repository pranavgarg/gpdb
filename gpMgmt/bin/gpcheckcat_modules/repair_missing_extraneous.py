#!/usr/bin/env python
from gppylib.gpcatalog import *

class RepairMissingExtraneous:

    def __init__(self, catalog_table_obj, db_name, repair_script_path, issues, pk_name):
        self._delete_sql = "delete from {0} where {1}={2};"
        self._catalog_table_obj = catalog_table_obj
        self._table_name = self._catalog_table_obj.getTableName()
        self._db_name = db_name
        self._repair_script_path = repair_script_path
        self._issues = issues
        self._pk_name = pk_name

    def create_missing_repair_sql(self):
        return "repair script"

    def get_extra_repair_sql_contents(self):

        if not self._issues:
            return

        oids_to_remove = {issue[0] for issue in self._issues if issue[0]}
        repair_sql_contents = [self._delete_sql.format(self._catalog_table_obj.getTableName(),
                                                       self._pk_name, oid_to_remove)
                               for oid_to_remove in oids_to_remove]

        return repair_sql_contents

    def create_repair_sql(self,  repair_type_prefix, timestamp):

        contents = self.get_extra_repair_sql_contents()
        sql_file_name = '{0}.{1}_{2}.{3}.sql'.format(self.db_name, repair_type_prefix,
                                                     self._table_name,timestamp)
        repair_script_path = '{0}/{1}'.format(self._repair_script_path, sql_file_name)

        sql_file_obj = None
        try:
            sql_file_obj = open(repair_script_path, 'w')
            sql_file_obj.writelines(contents)
        except Exception, e:
            logger.fatal('Unable to create file "%s": %s' % (repair_script_path, str(e)))
            sys.exit(1)
        finally:
            if sql_file_obj:
                sql_file_obj.close()

        description = '\necho "something extra"\n'
        return description, sql_file_name

