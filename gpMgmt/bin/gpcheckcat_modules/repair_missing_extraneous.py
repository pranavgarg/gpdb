#!/usr/bin/env python
from gppylib.gpcatalog import *


class IssueInfo: # TODO: Replace me later

    def __init__(self, catalog_name, primary_key, primary_key_value):
        self.catalog_name = catalog_name
        self.primary_key = primary_key
        self.primary_key_value = primary_key_value

    def get_delete_sql(self):
        return "delete from {0} where {1}={2};".format(self.catalog_name,
                                                       self.primary_key,
                                                       self.primary_key_value)


class RepairMissingExtraneous:

    def __init__(self, catalog_table_obj, db_name, repair_script_path, issues, pk_name, segmentinfo_map):
        self._catalog_table_obj = catalog_table_obj
        self._table_name = self._catalog_table_obj.getTableName()
        self._db_name = db_name
        self._repair_script_path = repair_script_path
        self._issues = issues
        if pk_name is None: # None is crazy
            pk_name = 'oid'
        self._pk_name = pk_name
        self._segmentinfo_map = segmentinfo_map

    def create_missing_repair_sql(self):
        return "repair script"

    def get_tentative_segments(self):
        # We assume that segmentid will always be the last one
        return {int(issue[-1].strip('{}')) for issue in self._issues if issue[0]}

    def get_issuesinfo(self):
        for segid in segmentids:
            myprint(GV.report_cfg[segid])
        return

    def get_extra_repair_sql_contents(self):

        if not self._issues:
            return

        # TODO: We need to create a sql file per segment
        oids_to_remove = {issue[0] for issue in self._issues if issue[0]}
        repair_sql_contents = ["set allow_system_table_mods='dml';"]
        repair_sql_contents += [self._delete_sql.format(self._catalog_table_obj.getTableName(),
                                                            self._pk_name, oid_to_remove)
                                   for oid_to_remove in oids_to_remove]

        return repair_sql_contents
