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

