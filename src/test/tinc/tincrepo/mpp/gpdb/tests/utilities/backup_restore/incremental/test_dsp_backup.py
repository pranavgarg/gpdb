"""
Copyright (C) 2004-2015 Pivotal Software, Inc. All rights reserved.

This program and the accompanying materials are made available under
the terms of the under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""

import os
import unittest2 as unittest
import tinctest
from tinctest.lib import local_path, run_shell_command
from mpp.lib.PSQL import PSQL
from mpp.lib.gpstop import GpStop
from mpp.gpdb.tests.utilities.backup_restore.incremental import BackupTestCase

'''
Backup and Restore with default storage parameters (DSP)
'''

class DspBackupRestore(BackupTestCase):
    """

    @description test cases for bk/rstr with Default Storage Parameters (DSP)
    @tags backup restore dsp
    @product_version gpdb: [4.3.4.0-]
    @gucs gp_create_table_random_default_distribution=off
    """

    os.environ['PGPASSWORD'] = 'dsprolepwd'

    @classmethod
    def setUpClass(cls):
        bk = BackupTestCase('cleanup_backup_files')
        bk.cleanup_backup_files()
        PSQL.run_sql_file(local_path('dsp/setup.sql'), dbname='postgres')
        super(DspBackupRestore, cls).setUpClass()

    def test_backup_restore_with_role_level_guc(self):
        tinctest.logger.info("Backup-Restore with GUC value set at role level")

        self.add_user('dsp_role', 'password')
        self.run_workload("dsp/role", 'dsp_db')

        self.get_data_to_file('dsp_db', 'backup1') #Create a copy of all the tables in database before the last backup
        self.run_full_backup(dbname = 'dsp_db')

        self.run_restore('dsp_db')
        self.validate_restore("dsp/restore", 'dsp_db')
        self.compare_table_data('dsp_db')

        self.compare_ao_tuple_count('dsp_db')
        self.remove_user('dsp_role')

    def test_backup_restore_with_session_level_guc(self):
        tinctest.logger.info("Backup-Restore with GUC value set at session level")

        self.run_workload("dsp/session", 'dsp_db')

        self.get_data_to_file('dsp_db', 'backup1') #Create a copy of all the tables in database before the last backup
        self.run_full_backup(dbname = 'dsp_db')

        self.run_restore('dsp_db')
        self.validate_restore("dsp/restore", 'dsp_db')
        self.compare_table_data('dsp_db')

        self.compare_ao_tuple_count('dsp_db')


    def test_backup_restore_with_system_level_guc(self):
        tinctest.logger.info("Backup-Restore with GUC value set at system level")
        command = "gpconfig -c gp_default_storage_options -v \"\'appendonly=true, orientation=column, blocksize=65536, checksum=true, compresslevel=4, compresstype=rle_type\'\" --skipvalidation"
        rc = run_shell_command(command)
        if not rc:
            raise Exception('Unable to set the configuration parameter')
        gpstop = GpStop()
        gpstop.run_gpstop_cmd(restart=True)

        self.run_workload("dsp/system", 'dsp_db')

        self.get_data_to_file('dsp_db', 'backup1') #Create a copy of all the tables in database before the last backup
        self.run_full_backup(dbname = 'dsp_db')

        self.run_restore('dsp_db')
        self.validate_restore("dsp/restore_system", 'dsp_db')
        self.compare_table_data('dsp_db')

        self.compare_ao_tuple_count('dsp_db')

        rc = run_shell_command("gpconfig -r gp_default_storage_options")
        if not rc:
            raise Exception('Unable to reset guc')
        gpstop.run_gpstop_cmd(restart=True)

    def test_restore_after_role_level_guc(self):

        tinctest.logger.info("Backup, SET role level guc to new values, restore")

        self.add_user('dsp_role', 'password')
        self.run_workload("dsp/role", 'dsp_db')

        self.get_data_to_file('dsp_db', 'backup1') #Create a copy of all the tables in database before the last backup
        self.run_full_backup(dbname = 'dsp_db')

        PSQL.run_sql_command("Alter role dsp_role set gp_default_storage_options='appendonly=true,checksum=true'", dbname='postgres')

        self.run_restore('dsp_db')
        self.validate_restore("dsp/restore", 'dsp_db')
        self.compare_table_data('dsp_db')

        self.compare_ao_tuple_count('dsp_db')
        self.remove_user('dsp_role')


    def test_restore_no_drop_db(self):
        tinctest.logger.info("Backup, Restore the db without dropiing it first, use option -s")

        self.cleanup_backup_files()
        self.run_workload("dsp/session", 'dsp_db')

        self.run_full_backup(dbname = 'dsp_db')

        self.run_restore('dsp_db',option = '-s dsp_db')
        self.validate_restore("dsp/restore_nodrop", 'dsp_db')

    def test_restore_global_objects(self):
        tinctest.logger.info("Backup, Restore the database and role options, The new tables created after restore with these should use the options set")

        self.add_user('dsp_role', 'password')
        self.run_workload("dsp/global", 'dsp_db')

        self.run_full_backup(dbname = 'dsp_db', option = ' -G ')

        self.run_restore('dsp_db', option = ' -G ')
        self.validate_restore("dsp/restore_global", 'dsp_db')

        self.remove_user('dsp_role')

    def test_single_table_backup_full_restore(self):
        tinctest.logger.info("Single table backup and Restore")
        self.run_workload("dsp/session", 'dsp_db')

        self.get_data_to_file('dsp_db', 'backup1') #Create a copy of all the tables in database before the last backup
        self.run_full_backup(dbname = 'dsp_db', option = "-t public.dsp_db_t1")

        self.run_restore('dsp_db')
        self.validate_restore("dsp/restore_single", 'dsp_db')
        self.compare_table_data('dsp_db')

        self.compare_ao_tuple_count('dsp_db')


    def test_full_backup_single_table_restore(self):

        tinctest.logger.info("Full backup ,Single table restore")
        self.run_workload("dsp/session", 'dsp_db')

        self.get_data_to_file('dsp_db', 'backup1') #Create a copy of all the tables in database before the last backup
        self.run_full_backup(dbname = 'dsp_db')

        self.run_restore('dsp_db', option = '-e  -T public.dsp_db_t1')
        self.validate_restore("dsp/restore_single", 'dsp_db')

        self.compare_ao_tuple_count('dsp_db')


    def test_full_and_incremental_backup(self):
        tinctest.logger.info('Table created with guc in incremental backup')

        self.add_user('dsp_role', 'password')
        self.run_workload("dsp/global", 'dsp_db')

        self.run_full_backup(dbname = 'dsp_db')

        self.run_workload("dsp/dirty_dir_incr", 'dsp_db')
        self.get_data_to_file('dsp_db', 'backup1') #Create a copy of all the tables in database before the last backup
        self.run_incr_backup("dsp/dirty_dir_incr", dbname = 'dsp_db')

        self.run_restore('dsp_db')
        self.validate_restore("dsp/restore", 'dsp_db')

        self.compare_table_data('dsp_db')

        self.compare_ao_tuple_count('dsp_db')

        self.remove_user('dsp_role')
