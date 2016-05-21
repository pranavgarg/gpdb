#!/usr/bin/env python
from gppylib.gpcatalog import *

class RepairMissingExtraneous:

    def __init__(self):
        self.delete_sql = "delete from {0} where {1}={2};"

    def create_missing_repair_sql(self):
        return "repair script"

    def create_extra_repair_sql(self, catalog_table, entries, fkeylist):
        oids_to_remove = set()

        if entries:
            for entry in entries:
                oids_to_remove.add(entry[0])

        if fkeylist:
            for fkey in fkeylist:
                if fkey.getPkeyTableName() == "pg_class":
                    oid_column = fkey.getColumns()[0]

        repair_sql_contents = []

        for oid_to_remove in oids_to_remove:
            repair_sql_contents.append(self.delete_sql.format(catalog_table,
                                                              oid_column,
                                                              oid_to_remove))

        return repair_sql_contents



