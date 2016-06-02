#!/usr/bin/env python
from gppylib.gpcatalog import *

class RepairMissingExtraneous:

    def __init__(self, catalog_table_obj,  issues, pk_name):
        self._table_name = catalog_table_obj.getTableName()
        self._issues = issues
        if pk_name is None: # None is crazy
            pk_name = 'oid'
        self._pk_name = pk_name

    def get_delete_sql(self, primary_key_value):
        # TODO: add begin and commit
        return "set allow_system_table_mods='dml';"\
                "delete from {0} where {1}={2};".format(self._table_name,
                                                       self._pk_name,
                                                       primary_key_value)

    def get_extra_or_missing_oids_in_segments(self):
        if not self._issues:
            return

        oids_to_segment_mapping = {}
        for issue in self._issues:
            seg_ids = issue[-1].strip('{}').split(',')
            if not oids_to_segment_mapping.has_key(issue[0]):
                oids_to_segment_mapping[issue[0]] = set()
            oids_to_segment_mapping[issue[0]].update(int(seg_id) for seg_id in seg_ids)

        return oids_to_segment_mapping

