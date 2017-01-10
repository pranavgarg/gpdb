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
from datetime import date
import unittest2 as unittest
import tinctest
from mpp.lib.PSQL import PSQL
from tinctest.models.scenario import ScenarioTestCase
from mpp.gpdb.tests.utilities.backup_restore.incremental import BackupTestCase, is_earlier_than
from tinctest.lib import local_path
from mpp.lib.gpdb_util import GPDBUtil

'''
@Incremental Backup
'''

gpdb_util = GPDBUtil()
version = gpdb_util.getGPDBVersion()

class test_backup_restore(BackupTestCase, ScenarioTestCase):
    """

    @description test cases for incremental backup
    @created 2013-01-24 10:10:10
    @modified 2013-03-08 17:10:15
    @tags backup restore gpcrondump gpdbrestore incremental
    @product_version gpdb: [4.2.5.x- main]
    @gucs gp_create_table_random_default_distribution=off
    """

    @classmethod
    def setUpClass(cls):
        bk = BackupTestCase('create_filespace')
        bk.create_filespace()
        bk.cleanup_backup_files()
        super(test_backup_restore, cls).setUpClass()

    def test_01_incremental_nooptions(self):
        tinctest.logger.info("Test1: gpcromndump --incremental with no options...")

        self.run_workload("backup_dir", 'bkdb1')

        self.run_full_backup(dbname = 'bkdb1')

        self.run_workload("dirty_dir_1", 'bkdb1')
        self.run_incr_backup("dirty_dir_1", dbname = 'bkdb1')

        self.run_workload("dirty_dir_2", 'bkdb1')
        self.run_incr_backup("dirty_dir_2", dbname = 'bkdb1')

        self.run_workload("dirty_dir_3", 'bkdb1')
        self.run_incr_backup("dirty_dir_3", dbname = 'bkdb1')

        self.run_workload("dirty_dir_4", 'bkdb1')
        self.get_data_to_file('bkdb1', 'backup1') #Create a copy of all the tables in database before the last backup
        self.run_incr_backup("dirty_dir_4", dbname = 'bkdb1')

        self.run_restore('bkdb1')
        self.validate_restore("restore_dir", 'bkdb1')
        self.compare_table_data('bkdb1')

        self.compare_ao_tuple_count('bkdb1')

    def test_02_incremental_option1(self):
        tinctest.logger.info("Test2: Test for verifying incremental backup  with options -b, -B, -d, -f, -j, -k ; Restore with -s")
        self.cleanup_backup_files()

        self.run_workload("backup_dir", 'bkdb2')
        self.run_full_backup(dbname = 'bkdb2')

        self.run_workload("dirty_dir_1", 'bkdb2')
        self.run_incr_backup("dirty_dir_1", dbname = 'bkdb2', option = "-b, -j, -k, -z")

        self.run_workload("dirty_dir_2", 'bkdb2')
        self.run_incr_backup("dirty_dir_2", dbname = 'bkdb2', option = "-B", value = "100")

        self.run_workload("dirty_dir_3", 'bkdb2')
        self.run_incr_backup("dirty_dir_3", dbname = 'bkdb2', option = "-d", value = "%s" % os.environ.get('MASTER_DATA_DIRECTORY'))

        self.run_workload("dirty_dir_4", 'bkdb2')
        self.get_data_to_file('bkdb2', 'backup1') #Create a copy of all the tables in database before the last backup
        self.run_incr_backup("dirty_dir_4", dbname = 'bkdb2')

        self.run_restore('bkdb2', option = '-s bkdb2 -e')
        self.validate_restore("restore_dir", 'bkdb2')
        self.compare_table_data('bkdb2')
        self.compare_ao_tuple_count('bkdb2')

    @unittest.skipIf((os.uname()[0] == 'SunOS'), 'Skipped on Solaris')
    def test_03_incremental_option2(self):

        tinctest.logger.info("Test3: incremental backup  with options -c, --resyncable, -l,--no-owner, --no-privileges, --inserts etc ...")
        self.cleanup_backup_files()

        self.run_workload("backup_dir", 'bkdb3')
        self.run_full_backup(dbname = 'bkdb3')

        self.run_workload("dirty_dir_1", 'bkdb3')
        self.run_incr_backup("dirty_dir_1", dbname = 'bkdb3', option = "--rsyncable, --no-privileges")

        self.run_workload("dirty_dir_2", 'bkdb3')
        self.run_incr_backup("dirty_dir_2", dbname = 'bkdb3', option = "-l", value = "new_log_file")

        self.run_workload("dirty_dir_3", 'bkdb3')
        self.run_incr_backup("dirty_dir_3", dbname = 'bkdb3', option = "--use-set-session-authorization")

        self.run_workload("dirty_dir_4", 'bkdb3')
        self.get_data_to_file('bkdb3', 'backup1') #Create a copy of all the tables in database before the last backup
        self.run_incr_backup("dirty_dir_4", dbname = 'bkdb3', option = " --no-owner ")

        self.run_restore('bkdb3', option = ' -l res_log -d %s -B 100 -e' % os.environ.get('MASTER_DATA_DIRECTORY'))
        self.validate_restore("restore_dir", 'bkdb3')
        self.compare_table_data('bkdb3')

        self.compare_ao_tuple_count('bkdb3')

    def test_04_incremental_with_backupdir(self):
        tinctest.logger.info("Test4: Test for verifying incremental backup to a location other than master_data_directory...")
        self.cleanup_backup_files(location = '/tmp') # Cleaning the previous backups under /tmp

        self.drop_create_database('bkdb4')
        self.run_full_backup(dbname = 'bkdb4')

        self.run_incr_backup("dirty_dir_1", dbname = 'bkdb4', option = "-u", value = '/tmp', expected_rc = 2)

        self.run_workload("backup_dir", 'bkdb4')
        self.run_full_backup(dbname = 'bkdb4', option = '-u', value = '/tmp/')

        self.run_workload("dirty_dir_1", 'bkdb4')
        self.run_incr_backup("dirty_dir_1", dbname = 'bkdb4', option = "-u", value = '/tmp')

        self.run_workload("dirty_dir_2", 'bkdb4')
        self.get_data_to_file('bkdb4', 'backup1') #Create a copy of all the tables in database before the last backup
        self.run_incr_backup("dirty_dir_2", dbname = 'bkdb4', option = "-u", value = '/tmp')

        self.run_restore('bkdb4', option = '-u /tmp -e')
        self.validate_restore("restore_dir2", 'bkdb4')
        self.compare_table_data('bkdb4')
        self.compare_ao_tuple_count('bkdb4')

    def test_05_incremental_config_global_objects(self):
        tinctest.logger.info("Test5: Test for verifying incremental backup with global objects and config")
        self.cleanup_backup_files()

        self.run_workload("backup_dir", 'bkdb5')
        self.run_full_backup(dbname = 'bkdb5')

        self.run_workload("dirty_dir_g1", 'bkdb5')
        self.run_incr_backup("dirty_dir_g1", dbname = 'bkdb5', option = "-g")

        self.run_workload("dirty_dir_g2", 'bkdb5')
        self.get_data_to_file('bkdb5', 'backup1') #Create a copy of all the tables in database before the last backup
        self.run_incr_backup("dirty_dir_g2", dbname = 'bkdb5', option = "-G")

        self.run_workload("dirty_dir_g3", 'bkdb5') # Drop global and dependent objects before restore
        self.run_restore('bkdb5', option = '-G -e')
        self.validate_restore("restore_dir_g", 'bkdb5')
        self.compare_table_data('bkdb5')
        self.compare_ao_tuple_count('bkdb5')

    @unittest.skipIf((os.uname()[0] == 'SunOS'), 'Skipped on Solaris')
    def test_06_incremental_with_full_backup_prev_day(self):
        tinctest.logger.info("Test6: Incremental backup against a full/incr that was created on previous day")
        self.cleanup_backup_files()

        self.run_workload("backup_dir", 'bkdb6')
        self.run_full_backup(dbname = 'bkdb6')

        self.copy_full_backup_to_prev_day()

        self.run_workload("dirty_dir_1", 'bkdb6')
        self.run_incr_backup("dirty_dir_1", dbname = 'bkdb6')

        self.copy_incr_backup_to_prev_day()

        self.run_workload("dirty_dir_2", 'bkdb6')
        self.get_data_to_file('bkdb6', 'backup1') #Create a copy of all the tables in database before the last backup
        self.run_incr_backup("dirty_dir_2", dbname = 'bkdb6')

        self.run_restore('bkdb6')
        self.validate_restore("restore_dir2", 'bkdb6')
        self.compare_table_data('bkdb6')
        self.compare_ao_tuple_count('bkdb6')

    def test_07_incremental_negative_options(self):
        tinctest.logger.info("Test7: Test for options that wont work with incremental")
        self.drop_create_database('bkdb7')
        self.drop_create_database('bkdb8')
        self.run_full_backup(dbname = 'bkdb7')
        self.run_full_backup(dbname = 'bkdb8')

        self.run_incr_backup("dirty_dir_1", dbname = 'bkdb7', option = "--ddboost", expected_rc = 2)
        self.run_incr_backup("dirty_dir_1", dbname = 'bkdb7', option = "-t", value = 'public.ao_table1', expected_rc = 2)
        self.run_incr_backup("dirty_dir_1", dbname = 'bkdb7', option = "-T", value = 'public.ao_table1', expected_rc = 2)
        self.run_incr_backup("dirty_dir_1", dbname = 'bkdb7', option = "--table-file", value = "file1",  expected_rc = 2)
        self.run_incr_backup("dirty_dir_1", dbname = 'bkdb7', option = "--exclude-table-file", value = "file1", expected_rc = 2)
        self.run_incr_backup("dirty_dir_1", dbname = 'bkdb7', option = "--oids",expected_rc = 2)
        self.run_incr_backup("dirty_dir_1", dbname = 'bkdb7', option = "--inserts",expected_rc = 2)
        self.run_incr_backup("dirty_dir_1", dbname = 'bkdb7', option = "--column-inserts",expected_rc = 2)
        self.run_incr_backup("dirty_dir_1", dbname = 'bkdb7', option = "-s", value = "new_coschema1", expected_rc = 2)
        self.run_incr_backup("dirty_dir_1", dbname = 'bkdb7', option = "-f", value = "15", expected_rc = 2)
        self.run_incr_backup("dirty_dir_1", dbname = 'bkdb7,bkdb8', expected_rc = 2)

    def test_08_incremental_with_option_L(self):
        tinctest.logger.info("Test8: Full and incremental restore with option L")
        self.cleanup_backup_files()

        self.run_workload("backup_dir", 'bkdb10')
        self.run_full_backup(dbname = 'bkdb10')

        self.run_restore('bkdb10', option = '-L')

        self.run_workload("dirty_dir_1", 'bkdb10')
        self.get_data_to_file('bkdb10', 'backup1') #Create a copy of all the tables in database before the last backup
        self.run_incr_backup("dirty_dir_1", dbname = 'bkdb10')

        self.run_restore('bkdb10', option = '-L')

    def test_09_incremental_with_option_L_and_u(self):
        tinctest.logger.info("Test9: Test for Full and incremental with -u and -L")

        self.run_workload("backup_dir", 'bkdb11')
        self.run_full_backup(dbname = 'bkdb11', option = '-u', value = '/tmp')

        self.run_restore('bkdb11', option = '-u /tmp -L')

        self.run_workload("dirty_dir_1", 'bkdb11')
        self.get_data_to_file('bkdb11', 'backup1') #Create a copy of all the tables in database before the last backup
        self.run_incr_backup("dirty_dir_1", dbname = 'bkdb11', option = '-u', value = '/tmp')

        self.run_restore('bkdb11', option = '-u /tmp -L')

    def test_10_full_with_backup_dir(self):
        tinctest.logger.info("Test10: Test with full restore and -u option")

        self.run_workload("backup_dir", 'bkdb12')
        self.run_full_backup(dbname = 'bkdb12', option = '-u', value = '/tmp')
        self.get_data_to_file('bkdb12', 'backup1') #Create a copy of all the tables in database before the last backup

        self.run_restore('bkdb12', option = '-u /tmp -e')
        self.compare_table_data('bkdb12')
        self.compare_ao_tuple_count('bkdb12')

    def test_11_incremental_with_restore_option_R(self):
        tinctest.logger.info("Test11: Incremental and full restore with -R option")

        self.cleanup_backup_files(location = '/tmp') # Cleaning the previous backups under /tmp
        self.run_workload("backup_dir", 'bkdb13')
        self.run_full_backup(dbname = 'bkdb13', option = '-u', value = '/tmp')
        self.copy_seg_files_to_master(location = '/tmp')

        self.run_restore('bkdb13', option = ' -R ', location = '/tmp')

        self.run_workload("dirty_dir_1", 'bkdb13')
        self.get_data_to_file('bkdb13', 'backup1') #Create a copy of all the tables in database before the last backup
        self.run_incr_backup("dirty_dir_restore", dbname = 'bkdb13', option = '-u', value = '/tmp')
        self.copy_seg_files_to_master(location = '/tmp')

        self.remove_full_dumps(location = '/tmp')
        self.run_restore('bkdb13', option = ' -R ', location = '/tmp', expected_rc = 2)

    @unittest.skipIf((os.uname()[0] == 'SunOS'), 'Skipped on Solaris')
    def test_12_incremental_with_restore_option_b(self):
        tinctest.logger.info("Test12: Incremental and Full restore with -b option")
        self.cleanup_backup_files()

        self.run_workload("backup_dir", 'bkdb14')
        self.run_full_backup(dbname = 'bkdb14')

        self.run_restore('bkdb14')

        self.run_workload("dirty_dir_1", 'bkdb14')
        self.get_data_to_file('bkdb14', 'backup1') #Create a copy of all the tables in database before the last backup
        self.run_incr_backup("dirty_dir_restore", dbname = 'bkdb14')

        self.run_restore('bkdb14', option = '-e -a -b ')
        self.compare_table_data('bkdb14')

        self.compare_ao_tuple_count('bkdb14')

    @unittest.skipIf((os.uname()[0] == 'SunOS'), 'Skipped on Solaris')
    def test_13_incremental_with_restore_option_b_and_u(self):
        tinctest.logger.info("Test13: Incremental and Full restore with -b option and a backup_dir")
        self.run_workload("backup_dir", 'bkdb15')
        self.run_full_backup(dbname = 'bkdb15', option = '-u', value = '/tmp')

        self.run_restore('bkdb15', option = '-e -a -u /tmp -b ', location = '/tmp')

        self.run_workload("dirty_dir_1", 'bkdb15')
        self.get_data_to_file('bkdb15', 'backup1') #Create a copy of all the tables in database before the last backup
        self.run_incr_backup("dirty_dir_restore", dbname = 'bkdb15', option = '-u', value = '/tmp')

        self.run_restore('bkdb15', option = '-e -a -u /tmp -b ', location = '/tmp')
        self.compare_table_data('bkdb15')
        self.compare_ao_tuple_count('bkdb15')

    """
    def test_14_incremental_restore_select_tables(self):
        tinctest.logger.info("Test14: Test to restore with selected tables ")
        self.cleanup_backup_files()

        self.run_workload("backup_dir", 'bkdb9')
        self.run_full_backup(dbname = 'bkdb9')

        self.run_workload("dirty_dir_1", 'bkdb9')
        self.get_data_to_file('bkdb9', 'backup1') #Create a copy of all the tables in database before the last backup
        self.run_incr_backup("dirty_dir_1", dbname = 'bkdb9')

        self.run_restore('bkdb9', option = '-T public.ao_table1,public.co_part01_1_prt_3_2_prt_sub1,public.heap_table3,public.mixed_part01', type = 'full')
        self.validate_restore("restore_full_T", 'bkdb9')

        self.run_restore('bkdb9', option = '-T public.ao_table1,new_coschema1.co_table3,public.co_part01_1_prt_3_2_prt_sub1,public.heap_table3,public.mixed_part01')
        self.validate_restore("restore_incr_T", 'bkdb9')

    def test_15_incremental_restore_select_tables_with_tablefile(self):
        tinctest.logger.info("Test15: Test to restore with selected tables from a tablefile ")
        self.cleanup_backup_files()

        self.run_workload("backup_dir", 'bkdb9')
        self.run_full_backup(dbname = 'bkdb9')

        self.run_workload("dirty_dir_1", 'bkdb9')
        self.get_data_to_file('bkdb9', 'backup1') #Create a copy of all the tables in database before the last backup
        self.run_incr_backup("dirty_dir_1", dbname = 'bkdb9')

        table_file = local_path('%s/table_file1' % ('restore_full_T'))
        self.run_restore('bkdb9', option = '--table-file=%s' % table_file, type = 'full')
        self.validate_restore("restore_full_T", 'bkdb9')

        table_file = local_path('%s/table_file1' % ('restore_incr_T'))
        self.run_restore('bkdb9', option = '--table-file=%s' % table_file)
        self.validate_restore("restore_incr_T", 'bkdb9')

    def test_16_incremental_restore_select_tables_with_dropdb(self):
        tinctest.logger.info("Test16: Test to restore with selected tables with -e, restore from old backup after changes to table")
        self.cleanup_backup_files()

        self.run_workload("backup_dir", 'bkdb9')
        self.run_full_backup(dbname = 'bkdb9')

        self.run_workload("dirty_dir_1", 'bkdb9')
        self.get_data_to_file('bkdb9', 'backup1') #Create a copy of all the tables in database before the last backup
        self.run_incr_backup("dirty_dir_1", dbname = 'bkdb9')

        self.run_workload("dirty_dir_tables", "bkdb9", verify = True)

        self.run_restore('bkdb9', option = '-T public.ao_table1,public.heap_table3,public.mixed_part01 -e', type = 'full')
        self.validate_restore("restore_full_T_with_e", 'bkdb9')

        self.run_restore('bkdb9', option = '-T public.ao_table1,public.heap_table3,public.mixed_part01 -e')
        self.validate_restore("restore_incr_T_with_e", 'bkdb9')

    def test_17_incremental_restore_select_tablefile_with_dropdb(self):
        tinctest.logger.info("Test17: Test to restore with selected tables in a file  with drop-recreatedb ")
        self.cleanup_backup_files()

        self.run_workload("backup_dir", 'bkdb9')
        self.run_full_backup(dbname = 'bkdb9')

        self.run_workload("dirty_dir_1", 'bkdb9')
        self.get_data_to_file('bkdb9', 'backup1') #Create a copy of all the tables in database before the last backup
        self.run_incr_backup("dirty_dir_1", dbname = 'bkdb9')

        table_file = local_path('%s/table_file1' % ('restore_full_T_with_e'))
        self.run_restore('bkdb9', option = '--table-file=%s -e' % table_file, type = 'full')
        self.validate_restore("restore_full_T_with_e", 'bkdb9')

        table_file = local_path('%s/table_file1' % ('restore_incr_T_with_e'))
        self.run_restore('bkdb9', option = '--table-file=%s -e' % table_file)
        self.validate_restore("restore_incr_T_with_e", 'bkdb9')

    def test_18_incremental_restore_select_tables_with_bakup_dir(self):
        tinctest.logger.info("Test18: Test to restore with selected tables from backup_dir")

        self.run_workload("backup_dir", 'bkdb9')
        self.run_full_backup(dbname = 'bkdb9', option = '-u', value = '/tmp')

        self.run_workload("dirty_dir_1", 'bkdb9')
        self.get_data_to_file('bkdb9', 'backup1') #Create a copy of all the tables in database before the last backup
        self.run_incr_backup("dirty_dir_1", dbname = 'bkdb9', option = '-u', value = '/tmp')

        self.run_restore('bkdb9', option = '-T public.ao_table1,public.heap_table3,public.mixed_part01 -u /tmp -e ', type = 'full')
        self.validate_restore("restore_full_T_with_e", 'bkdb9')

        self.run_restore('bkdb9', option = '-T public.ao_table1,public.heap_table3,public.mixed_part01 -u /tmp -e')
        self.validate_restore("restore_incr_T_with_e", 'bkdb9')

    def test_19_incremental_restore_select_tables_with_tablefile_with_backup_dir(self):
        tinctest.logger.info("Test19: Test to restore with selected tables from a tablefile from a backup_dir, restore from old backup after changes to table")

        self.run_workload("backup_dir", 'bkdb9')
        self.run_full_backup(dbname = 'bkdb9', option = '-u', value = '/tmp')

        self.run_workload("dirty_dir_1", 'bkdb9')
        self.get_data_to_file('bkdb9', 'backup1') #Create a copy of all the tables in database before the last backup
        self.run_incr_backup("dirty_dir_1", dbname = 'bkdb9', option = '-u', value = '/tmp')

        self.run_workload("dirty_dir_tables", "bkdb9", verify = True)

        table_file = local_path('%s/table_file1' % ('restore_full_T_with_e'))
        self.run_restore('bkdb9', option = '--table-file=%s -u /tmp -e' % table_file, type = 'full')
        self.validate_restore("restore_full_T_with_e", 'bkdb9')

        table_file = local_path('%s/table_file1' % ('restore_incr_T_with_e'))
        self.run_restore('bkdb9', option = '--table-file=%s -u /tmp -e ' % table_file)
        self.validate_restore("restore_incr_T_with_e", 'bkdb9')
    """

    def test_20_incremental_select_restore_with_b(self):
        tinctest.logger.info("Test20: Test to select restore with option b ")
        self.cleanup_backup_files()

        self.run_workload("backup_dir", 'bkdb9')
        self.run_full_backup(dbname = 'bkdb9')

        self.run_workload("dirty_dir_1", 'bkdb9')
        self.get_data_to_file('bkdb9', 'backup1') #Create a copy of all the tables in database before the last backup
        self.run_incr_backup("dirty_dir_1", dbname = 'bkdb9')

        self.run_restore('bkdb9', option = '-T public.ao_table1 -T public.heap_table3 -T public.mixed_part01 -a -e -b ')
        self.validate_restore("restore_incr_T_with_e", 'bkdb9')

    @unittest.skipIf((os.uname()[0] == 'SunOS'), 'Skipped on Solaris')
    def test_21_incremental_restore_select_tablefile_with_option_b(self):
        tinctest.logger.info("Test21: Test to restore with selected tables in a file  with option b ")
        self.cleanup_backup_files()

        self.run_workload("backup_dir", 'bkdb9')
        self.run_full_backup(dbname = 'bkdb9')

        self.run_workload("dirty_dir_1", 'bkdb9')
        self.get_data_to_file('bkdb9', 'backup1') #Create a copy of all the tables in database before the last backup
        self.run_incr_backup("dirty_dir_1", dbname = 'bkdb9')

        table_file = local_path('%s/table_file1' % ('restore_incr_T_with_e'))
        self.run_restore('bkdb9', option = '--table-file=%s -a -e -b ' % table_file)
        self.validate_restore("restore_incr_T_with_e", 'bkdb9')

    @unittest.skipIf((os.uname()[0] == 'SunOS'), 'Skipped on Solaris')
    def test_22_incremental_select_restore_with_b_and_u(self):
        tinctest.logger.info("Test22: Test to select restore with option b and u ")
        self.cleanup_backup_files(location = '/tmp') # Cleaning the previous backups under /tmp

        self.run_workload("backup_dir", 'bkdb9')
        self.run_full_backup(dbname = 'bkdb9', option = '-u', value = '/tmp')

        self.run_workload("dirty_dir_1", 'bkdb9')
        self.get_data_to_file('bkdb9', 'backup1') #Create a copy of all the tables in database before the last backup
        self.run_incr_backup("dirty_dir_1", dbname = 'bkdb9', option = '-u', value = '/tmp')

        self.run_restore('bkdb9', option = '-T public.ao_table1 -T public.heap_table3 -T public.mixed_part01 -u /tmp  -a -e -b ', location = '/tmp')
        self.validate_restore("restore_incr_T_with_e", 'bkdb9')

    @unittest.skipIf((os.uname()[0] == 'SunOS'), 'Skipped on Solaris')
    def test_23_incremental_restore_select_tablefile_with_b_and_u(self):
        tinctest.logger.info("Test23: Test to restore with selected tables in a file with option u and b ")

        self.run_workload("backup_dir", 'bkdb9')
        self.run_full_backup(dbname = 'bkdb9', option = '-u', value = '/tmp')

        self.run_workload("dirty_dir_1", 'bkdb9')
        self.get_data_to_file('bkdb9', 'backup1') #Create a copy of all the tables in database before the last backup
        self.run_incr_backup("dirty_dir_1", dbname = 'bkdb9', option = '-u', value = '/tmp')

        table_file = local_path('%s/table_file1' % ('restore_incr_T_with_e'))
        self.run_restore('bkdb9', option = '--table-file=%s -u /tmp -a -e -b ' % table_file, location = '/tmp')
        self.validate_restore("restore_incr_T_with_e", 'bkdb9')

    def test_24_incremental_restore_select_tables_with_s(self):
        tinctest.logger.info("Test24: Test to restore with selected tables with option s ")

        self.run_workload("backup_dir", 'bkdb9')
        self.run_full_backup(dbname = 'bkdb9')

        self.run_workload("dirty_dir_1", 'bkdb9')
        self.get_data_to_file('bkdb9', 'backup1') #Create a copy of all the tables in database before the last backup
        self.run_incr_backup("dirty_dir_1", dbname = 'bkdb9')

        self.run_restore('bkdb9', option = '-T public.ao_table1 -T public.heap_table3 -T public.mixed_part01 -e -s bkdb9')
        self.validate_restore("restore_incr_T_with_e", 'bkdb9')

    def test_25_incremental_restore_select_tablefile_with_option_s(self):
        tinctest.logger.info("Test25: Test to restore with selected tables in a file  with option s , drop and recreate db manualy before restore")

        self.run_workload("backup_dir", 'bkdb9')
        self.run_full_backup(dbname = 'bkdb9')

        self.run_workload("dirty_dir_1", 'bkdb9')
        self.get_data_to_file('bkdb9', 'backup1') #Create a copy of all the tables in database before the last backup
        self.run_incr_backup("dirty_dir_1", dbname = 'bkdb9')

        self.drop_create_database('bkdb9')

        table_file = local_path('%s/table_file1' % ('restore_incr_T_with_e'))
        self.run_restore('bkdb9', option = '--table-file=%s -e -s bkdb9' % table_file)
        self.validate_restore("restore_incr_T_with_e", 'bkdb9')

    def test_26_incremental_restore_select_tables_with_s_and_u(self):
        tinctest.logger.info("Test26: Test to restore with selected tables with option s and backup_dir , dropdb and -e should recreate the db")

        self.cleanup_backup_files(location = '/tmp') # Cleaning the previous backups under /tmp

        self.run_workload("backup_dir", 'bkdb9')
        self.run_full_backup(dbname = 'bkdb9', option = '-u', value = '/tmp')

        self.run_workload("dirty_dir_1", 'bkdb9')
        self.get_data_to_file('bkdb9', 'backup1') #Create a copy of all the tables in database before the last backup
        self.run_incr_backup("dirty_dir_1", dbname = 'bkdb9', option = '-u', value = '/tmp')

        self.drop_database('bkdb9')
        self.run_restore('bkdb9', option = '-T public.ao_table1 -T public.heap_table3 -T public.mixed_part01 -e -s bkdb9 -u /tmp ')
        self.validate_restore("restore_incr_T_with_e", 'bkdb9')

    def test_27_incremental_restore_select_tablefile_with_option_s_and_u(self):
        tinctest.logger.info("Test27: Test to restore with selected tables in a file  with option s and backup_dir ")

        self.run_workload("backup_dir", 'bkdb9')
        self.run_full_backup(dbname = 'bkdb9', option = '-u', value = '/tmp')

        self.run_workload("dirty_dir_1", 'bkdb9')
        self.get_data_to_file('bkdb9', 'backup1') #Create a copy of all the tables in database before the last backup
        self.run_incr_backup("dirty_dir_1", dbname = 'bkdb9', option = '-u', value = '/tmp')

        table_file = local_path('%s/table_file1' % ('restore_incr_T_with_e'))
        self.run_restore('bkdb9', option = '--table-file=%s -e -s bkdb9 -u /tmp ' % table_file)
        self.validate_restore("restore_incr_T_with_e", 'bkdb9')

    def test_28_restore_scenarios_1(self):
        tinctest.logger.info("Test28: Test restore scenarios : full,incre1, incre2, restore incre1, incre3, restore incre3")
        self.cleanup_backup_files()

        self.run_workload("backup_dir", 'bkdb17')
        self.run_full_backup(dbname = 'bkdb17')
        self.run_workload("dirty_dir_1", 'bkdb17')
        self.get_data_to_file('bkdb17', 'backup1') #Create a copy of all the tables in database before the last backup
        self.run_incr_backup("dirty_dir_1", dbname = 'bkdb17', incr_no = 1)
        self.run_workload("dirty_dir_2", 'bkdb17')
        self.run_incr_backup("dirty_dir_2", dbname = 'bkdb17', incr_no = 2)

        self.run_restore('bkdb17', option = ' -e ' , incr_no = 1)
        self.compare_table_data('bkdb17')

        self.run_workload("dirty_dir_3", 'bkdb17')
        self.get_data_to_file('bkdb17', 'backup1') #Create a copy of all the tables in database before the last backup
        self.run_incr_backup("dirty_dir_restore_1_and_3", dbname = 'bkdb17', incr_no = 3)

        self.run_restore('bkdb17', option = ' -e ', incr_no = 3)
        self.compare_table_data('bkdb17')
        self.compare_ao_tuple_count('bkdb17')

    def test_29_restore_scenarios_2(self):
        tinctest.logger.info("Test29: Test restore scenarios : full,incre1, incre2, restore full, incre3, restore incre2")
        self.cleanup_backup_files()

        self.run_workload("backup_dir", 'bkdb17')
        self.run_full_backup(dbname = 'bkdb17')

        self.run_workload("dirty_dir_1", 'bkdb17')
        self.run_incr_backup("dirty_dir_1", dbname = 'bkdb17', incr_no = 1)

        self.run_workload("dirty_dir_2", 'bkdb17')
        self.get_data_to_file('bkdb17', 'backup1') #Create a copy of all the tables in database before the last backup
        self.run_incr_backup("dirty_dir_2", dbname = 'bkdb17', incr_no = 2)

        self.run_restore('bkdb17', option = ' -e ' , type = 'full')

        self.run_workload("dirty_dir_3", 'bkdb17')
        self.get_data_to_file('bkdb17', 'backup2') #Create a copy of all the tables in database before the last backup
        self.run_incr_backup("dirty_dir_restore_full_and_3", dbname = 'bkdb17', incr_no = 3)

        self.run_restore('bkdb17', option = ' -e ' , incr_no = 2)
        self.compare_table_data('bkdb17')

        self.run_workload("backup_inserts" , 'bkdb17')
        self.run_full_backup(dbname = 'bkdb17')

        self.run_restore('bkdb17', option = ' -e ' , incr_no = 3)
        self.compare_table_data('bkdb17', restore_no = 2)
        self.compare_ao_tuple_count('bkdb17')

    def test_30_restore_scenarios_3(self):
        tinctest.logger.info("Test30: Test restore scenarios : full,incre1, incre2, restore full, incre3, full, restore incre3")
        self.cleanup_backup_files()

        self.run_workload("backup_dir", 'bkdb17')
        self.get_data_to_file('bkdb17', 'backup1') #Create a copy of all the tables in database before the last backup
        self.run_full_backup(dbname = 'bkdb17')

        self.run_workload("dirty_dir_1", 'bkdb17')
        self.run_incr_backup("dirty_dir_1", dbname = 'bkdb17', incr_no = 1)

        self.run_workload("dirty_dir_2", 'bkdb17')
        self.run_incr_backup("dirty_dir_2", dbname = 'bkdb17', incr_no = 2)

        self.run_restore('bkdb17', option = ' -e ' , type = 'full')
        self.compare_table_data('bkdb17')
        self.compare_ao_tuple_count('bkdb17')

        self.run_workload("dirty_dir_3", 'bkdb17')
        self.get_data_to_file('bkdb17', 'backup2') #Create a copy of all the tables in database before the last backup
        self.run_incr_backup("dirty_dir_restore_full_and_3", dbname = 'bkdb17', incr_no = 3)

        self.run_workload("backup_inserts" , 'bkdb17')
        self.run_full_backup(dbname = 'bkdb17')

        self.run_restore('bkdb17', option = ' -e ' , incr_no = 3)
        self.compare_table_data('bkdb17', restore_no = 2)
        self.compare_ao_tuple_count('bkdb17')

    def test_31_restore_scenarios_4(self):
        tinctest.logger.info("Test31: Test restore scenarios : full,incre1, incre2, incre3, incre4, restore full, restore incre2, restore incre3, restore incre4")
        self.cleanup_backup_files()

        self.run_workload("backup_dir", 'bkdb17')
        self.get_data_to_file('bkdb17', 'backup1')
        self.run_full_backup(dbname = 'bkdb17')

        self.run_workload("dirty_dir_1", 'bkdb17')
        self.get_data_to_file('bkdb17', 'backup2')
        self.run_incr_backup("dirty_dir_1", dbname = 'bkdb17', incr_no = 1)

        self.run_workload("dirty_dir_2", 'bkdb17')
        self.get_data_to_file('bkdb17', 'backup3')
        self.run_incr_backup("dirty_dir_2", dbname = 'bkdb17', incr_no = 2)

        self.run_workload("dirty_dir_3", 'bkdb17')
        self.get_data_to_file('bkdb17', 'backup4')
        self.run_incr_backup("dirty_dir_3", dbname = 'bkdb17', incr_no = 3)

        self.run_workload("dirty_dir_4", 'bkdb17')
        self.get_data_to_file('bkdb17', 'backup5')
        self.run_incr_backup("dirty_dir_4", dbname = 'bkdb17', incr_no = 4)

        self.run_restore('bkdb17', option = ' -e ' , type = 'full')
        self.compare_table_data('bkdb17')
        self.compare_ao_tuple_count('bkdb17')

        self.run_restore('bkdb17', option = ' -e ' , incr_no = 1)
        self.compare_table_data('bkdb17', restore_no = 2)
        self.compare_ao_tuple_count('bkdb17')

        self.run_restore('bkdb17', option = ' -e ' , incr_no = 2)
        self.compare_table_data('bkdb17', restore_no = 3)
        self.compare_ao_tuple_count('bkdb17')

        self.run_restore('bkdb17', option = ' -e ' , incr_no = 3)
        self.compare_table_data('bkdb17', restore_no = 4)
        self.compare_ao_tuple_count('bkdb17')

        self.run_restore('bkdb17', option = ' -e ' , incr_no = 4)
        self.compare_table_data('bkdb17', restore_no = 5)
        self.compare_ao_tuple_count('bkdb17')


    def test_32_large_dirty_list(self):
        tinctest.logger.info("Test32: gpcromndump --incremental with more than 1000 dirty tables...")
        self.cleanup_backup_files()

        self.run_workload("backup_dir", 'bkdb1')
        self.run_full_backup(dbname = 'bkdb1')

        self.run_workload("dirty_dir_1", 'bkdb1')
        self.run_incr_backup("dirty_dir_1", dbname = 'bkdb1')

        self.run_workload("dirty_dir_2", 'bkdb1')
        self.run_incr_backup("dirty_dir_2", dbname = 'bkdb1')

        self.run_workload("dirty_dir_3", 'bkdb1')
        self.run_incr_backup("dirty_dir_3", dbname = 'bkdb1')

        self.run_workload("dirty_dir_4", 'bkdb1')
        self.run_incr_backup("dirty_dir_4", dbname = 'bkdb1')

        self.run_workload("dirty_dir_5", 'bkdb1')
        self.get_data_to_file('bkdb1', 'backup1') #Create a copy of all the tables in database before the last backup
        self.run_incr_backup("dirty_dir_5", dbname = 'bkdb1')

        self.run_restore('bkdb1')
        self.validate_restore("restore_dir", 'bkdb1')
        self.compare_table_data('bkdb1')

    def test_33_full_backup_restore_prefix_option(self):
        tinctest.logger.info("Test33: Test for verifying full backup and restore with option --prefix")
        self.cleanup_backup_files()

        self.run_workload("backup_dir", 'bkdb2')
        self.run_full_backup(dbname = 'bkdb2', option = "--prefix=foo")
        self.check_filter_file_exists(expected=False, prefix='foo')

        self.get_data_to_file('bkdb2', 'backup1') #Create a copy of all the tables in database before the last backup

        self.run_restore('bkdb2', option = '-s bkdb2 -e --prefix foo')
        self.compare_table_data('bkdb2')
        self.compare_ao_tuple_count('bkdb2')

    def test_34_incremental_backup_restore_prefix_option(self):
        tinctest.logger.info("Test34: Test for verifying incremental backup and restore with option --prefix")
        self.cleanup_backup_files()

        self.run_workload("backup_dir_less_tables", 'bkdb34')
        self.run_full_backup(dbname = 'bkdb34', option = "--prefix=foo")
        self.check_filter_file_exists(expected=False, prefix='foo')

        self.run_workload("dirty_dir_1_less_tables", 'bkdb34')
        self.run_incr_backup("dirty_dir_1_less_tables", dbname = 'bkdb34',  option = "--prefix=foo")

        self.get_data_to_file('bkdb34', 'backup1') #Create a copy of all the tables in database before the last backup

        self.run_restore('bkdb34', option = '-s bkdb34 -e --prefix foo')
        self.compare_table_data('bkdb34')
        self.compare_ao_tuple_count('bkdb34')

    def test_35_full_backup_restore_filtering(self):
        tinctest.logger.info("Test35: Test for verifying full backup and restore with options --prefix and -t")
        self.cleanup_backup_files()

        self.run_workload("backup_dir_less_tables", 'bkdb35')
        self.run_full_backup(dbname = 'bkdb35', option = "--prefix=foo -t public.ao_table21")

        self.get_data_to_file('bkdb35', 'backup1') #Create a copy of all the tables in database before the last backup

        self.run_restore('bkdb35', option = '-s bkdb35 -e --prefix foo')
        self.compare_table_data('bkdb35')
        self.compare_ao_tuple_count('bkdb35')

    def test_36_incremental_backup_restore_filtering(self):
        tinctest.logger.info("Test36: Test for verifying incremental backup and restore for a full backup with options --prefix and -t")
        self.cleanup_backup_files()

        self.run_workload("backup_dir_less_tables", 'bkdb36')
        self.run_full_backup(dbname = 'bkdb36', option = "--prefix=foo -t public.ao_table21")

        self.run_workload("dirty_dir_1_filtering", 'bkdb36')
        self.run_incr_backup("dirty_dir_1_filtering", dbname = 'bkdb36',  option = "--prefix=foo")

        self.get_data_to_file('bkdb36', 'backup1') #Create a copy of all the tables in database before the last backup

        self.run_restore('bkdb36', option = '-s bkdb36 -e --prefix foo')
        self.compare_table_data('bkdb36')
        self.compare_ao_tuple_count('bkdb36')

    def test_37_multiple_prefixes_incr_filtering(self):
        tinctest.logger.info("Test37: Test for verifying multiple incremental backup and restore with filtering and different prefixes")
        self.cleanup_backup_files()

        self.run_workload("backup_dir_less_tables", 'bkdb37_1')
        self.run_full_backup(dbname = 'bkdb37_1', option = "--prefix=foo1 -t public.ao_table21")

        self.run_workload("backup_dir_less_tables", 'bkdb37_2')
        self.run_full_backup(dbname = 'bkdb37_2', option = "--prefix=foo2 -t public.ao_table20")

        self.run_workload("dirty_dir_1_filtering", 'bkdb37_1')
        self.run_incr_backup("dirty_dir_1_filtering", dbname = 'bkdb37_1',  option = "--prefix=foo1")

        self.run_workload("dirty_dir_2_filtering", 'bkdb37_2')
        self.run_incr_backup("dirty_dir_2_filtering", dbname = 'bkdb37_2',  option = "--prefix=foo2")

        self.get_data_to_file('bkdb37_1', 'backup1') #Create a copy of all the tables in database before the last backup
        self.get_data_to_file('bkdb37_2', 'backup2') #Create a copy of all the tables in database before the last backup

        self.run_restore('bkdb37_1', option = '-s bkdb37_1 -e --prefix foo1')
        self.run_restore('bkdb37_2', option = '-s bkdb37_2 -e --prefix foo2')
        self.compare_table_data('bkdb37_1')
        self.compare_ao_tuple_count('bkdb37_1')
        self.compare_table_data('bkdb37_2')
        self.compare_ao_tuple_count('bkdb37_2')

    def test_38_incremental_after_vacuum(self):
        tinctest.logger.info("Test 38: Negative: Full backup, Vacumm, incremental backup -should be an empty dirty_list")
        self.cleanup_backup_files()
        self.run_workload("backup_dir", 'bkdb38')
        self.run_full_backup(dbname = 'bkdb38')
        PSQL.run_sql_command('Vacuum;',dbname='bkdb38')
        self.run_incr_backup("dirty_dir_empty", dbname = 'bkdb38')

    def test_39_full_to_mdd(self):
        tinctest.logger.info("Test39:Full backup to gpdb data directories")

        self.run_workload("backup_dir", 'bkdb39')
        self.run_full_backup(dbname = 'bkdb39')
        self.get_data_to_file('bkdb39', 'backup1')
        self.run_restore('bkdb39')
        self.compare_table_data('bkdb39')
        self.compare_ao_tuple_count('bkdb39')

    def test_40_mpp11880(self):
	'''MPP-11880 - Dump and restore extremely long records '''
        # create a new database parttest_dump and partition table sales
        filesetup = local_path('sql/mpp11880_setup.sql')
        PSQL.run_sql_file(filesetup)

        # dump full database parttest_dump that only has partition table sales
        cmdDump = 'gpcrondump -x mpp11880 -a'
        output = self.run_gpcommand(cmdDump)

        # parse the output to get dump key
        dumpKey = self.get_timestamp(output)

        # truncate test_10m table before restore it from dump file
        cmdTrunc = 'psql -d mpp11880 -c "truncate table public.test_10m;"'
        self.run_command(cmdTrunc)

        # restore parttest_dump from backup
        cmdRestore = "gpdbrestore -t " + dumpKey + " -a -T public.test_10m"
        self.run_command(cmdRestore)

        sql_file = local_path('sql/mpp11880.sql')
        out_file = local_path('sql/mpp11880.out')

        # verify restored database is the same as original
        PSQL.run_sql_file(sql_file=sql_file, out_file=out_file)
        self.validate_sql_file(sql_file)


    def test_41_vanilla(self):
        ''' Full dump and restore with recreating database '''
        tinctest.logger.info("Test1: gpcromndump --full with no options...")
        self.run_workload("backup_dir_simple_db", 'bkdb1')

        # full database dump with default
        self.run_full_backup(dbname = 'bkdb1')

        # Need to drop database and restore
        self.drop_database('bkdb1')

        # recreate and restore database
        self.run_restore('bkdb1')
        self.validate_restore("restore_dir_simple_db", 'bkdb1')

        # drop database after test
        self.drop_database('bkdb1')

    def test_42_singletable(self):
        '''Include single table'''
        tinctest.logger.info("Test34: Test for single table, with option -t")
        self.cleanup_backup_files()

        self.run_workload("backup_dir_less_tables", 'bkdb42')
        self.run_full_backup(dbname = 'bkdb42', option = "-t public.ao_table21")

        self.get_data_to_file('bkdb42', 'backup1') #Create a copy of all the tables in database before the last backup

        #truncate heap_table2 table before restore it from dump file
        cmdTrunc = 'psql -d bkdb42 -c "truncate table public.ao_table21;"'
        self.run_command(cmdTrunc)

        #restore from backup
        self.run_restore('bkdb42', option = ' -s bkdb42 ')
        self.compare_table_data('bkdb42')
        self.drop_database('bkdb42')


    def test_43_multipletable(self):
        '''Include multiple table'''
        tinctest.logger.info("Test34: Test for multiple tables, ")
        self.cleanup_backup_files()

        self.run_workload("backup_dir_less_tables", 'bkdb43')
        self.run_full_backup(dbname = 'bkdb43', option = "-t public.ao_table21 -t public.ao_compr03 -t public.ao_compr02")

        self.get_data_to_file('bkdb43', 'backup1') #Create a copy of all the tables in database before the last backup

        #truncate heap_table2 table before restore it from dump file
        cmdTrunc = 'psql -d bkdb43 -c "truncate table public.ao_table21; truncate table public.ao_compr03; truncate table public.ao_compr02;"'
        self.run_command(cmdTrunc)

        #restore from backup
        self.run_restore('bkdb43', option = ' -s bkdb43 ')
        self.compare_table_data('bkdb43')
        self.drop_database('bkdb43')


    def test_44_exclude_singletable(self):
        '''exclude_singletable'''
        tinctest.logger.info("Test44: Test for exclude singletable ")
        self.cleanup_backup_files()

        self.run_workload("backup_dir_simple_db", 'bkdb44')
        self.run_full_backup(dbname = 'bkdb44', option = "-T public.ao_compr03")

        self.get_data_to_file('bkdb44', 'backup1') #Create a copy of all the tables in database before the last backup

        #truncate other table in the databse before restore it from dump file
        cmdTrunc = 'psql -d bkdb44 -c "truncate table public.ao_compr01; truncate table public.ao_compr02;\
                    truncate table public.ao_part01; truncate table public.ao_part02; truncate table public.heap_table1;"'
        self.run_command(cmdTrunc)

        #restore from backup
        self.run_restore('bkdb44', option = ' -s bkdb44 ')
        self.compare_table_data('bkdb44')
        self.drop_database('bkdb44')


    def test_45_exclude_multipletable(self):
        '''exclude multiple tables '''
        tinctest.logger.info("Test45: Test for exclude multiple tables ")
        self.cleanup_backup_files()

        self.run_workload("backup_dir_simple_db", 'bkdb45')
        self.run_full_backup(dbname = 'bkdb45', option = "-T public.ao_part01 -T public.ao_part02 -T public.ao_compr01")

        self.get_data_to_file('bkdb45', 'backup1') #Create a copy of all the tables in database before the last backup

        #truncate other table in the databse before restore it from dump file
        cmdTrunc = 'psql -d bkdb45 -c "truncate table public.ao_compr02; truncate table public.ao_compr03; truncate table public.heap_table1;"'
        self.run_command(cmdTrunc)

        #restore from backup
        self.run_restore('bkdb45', option = ' -s bkdb45')
        self.compare_table_data('bkdb45')
        self.drop_database('bkdb45')

    def test_46_crondump_opt_Gjv(self):
        ''' -G (dump global objects), -v (verbose), and -j (vacuum before dump) options '''
        tinctest.logger.info("Test46: Dump global objects ")

        # create a new database parttest_dump and partition table sales
        setup_sql = local_path('sql/query46_setup.sql')
        PSQL.run_sql_file(setup_sql)

        # dump full database parttest_dump that only has partition table sales
        self.run_full_backup(dbname = 'dumpglobaltest', option = ' -a -v -G -j')

        # drop role globaltest_role and schema globaltest_schema before restore it from dump file
        teardown_sql = local_path('sql/query46_teardown.sql')
        PSQL.run_sql_file(teardown_sql)

        self.run_restore('dumpglobaltest', option = ' -a -G')

        sql_file = local_path('sql/query46.sql')
        out_file = local_path('sql/query46.out')

        # verify restored database is the same as original
        PSQL.run_sql_file(sql_file=sql_file, out_file=out_file)
        self.validate_sql_file(sql_file)


    def test_47_single_table_restore(self):
        '''Dump multiple tables, restore a subset of those tables '''
        tinctest.logger.info("Test47: Dump multiple tables, restore a subset of those tables ")
        self.cleanup_backup_files()

        self.run_workload("backup_dir_simple_db", 'bkdb47')
        self.run_full_backup(dbname = 'bkdb47', option = "-t public.ao_part01 -t public.ao_compr01 -t public.heap_table1")

        self.get_data_to_file('bkdb47', 'backup1') #Create a copy of all the tables in database before the last backup

        #truncate the table in the databse before restore it from dump file
        cmdTrunc = 'psql -d bkdb47 -c "truncate table public.ao_part01;"'
        self.run_command(cmdTrunc)

        #restore from backup
        self.run_restore('bkdb47', option = ' -s bkdb47 -T public.ao_part01 ')
        self.compare_table_data('bkdb47')
        self.drop_database('bkdb47')


    def test_48_dbrestore_opt_L(self):
        '''GPDBRESTORE -L (list tablenames in backup set)'''
        tinctest.logger.info("Test48: GPDBRESTORE -L (list tablenames in backup set) ")
        self.cleanup_backup_files()

        self.run_workload("backup_dir_simple_db", 'bkdb48')
        self.run_full_backup(dbname = 'bkdb48')

        cmd = 'gpdbrestore -L -t '+ self.full_backup_timestamp
        (ok, out) = self.run_command(cmd)
        if ok:
            raise Exception('GPDBRESTORE Error: %s'%out)

        self.drop_database('bkdb48')

        # verify gpdbrestore -L output contains all tables
        if not (('Table public.ao_compr01' in out) and \
                ('Table public.ao_compr02' in out) and \
                ('Table public.ao_compr03' in out) and \
                ('Table public.ao_part01' in out) and \
                ('Table public.ao_part02' in out) and \
                ('Table public.heap_table1' in out)):
            raise Exception('GPDBRESTORE Error: option -L')



    def test_49_crondump_opt_o(self):
        """Test 49: -o (clear oldest dump directory only)"""
        #####################################################################
        ## The idea is to first create a dump directory of last year today
        ## on master and each segment, assuming this directory is the oldest,
        ## then call gpcrondump -o to remove this dump diretory and verify.
        ## The dump directory will be clean up via command before and after
        ## the test so to avoid any problem just in case test fails
        #####################################################################
        dumpDirOpLog = local_path('sql/dump_dir_OpLog.out')
        if os.path.isfile(dumpDirOpLog)	:
            os.remove(dumpDirOpLog)
        today = date.today()
        lastYear = date(today.year-1, today.month, today.day)

        #######################################################################
        # query to construct command to clear the one-year old dump directories
        sqlRemoveDumpDir = "SELECT 'ssh '||s.hostname||' rm -rf '||fe.fselocation||'/db_dumps/'||"\
                         + str(lastYear.strftime('%Y%m%d')) + " "\
                         + "FROM gp_segment_configuration s, pg_filespace f, pg_filespace_entry fe "\
                         + "WHERE s.dbid = fe.fsedbid and f.oid=fe.fsefsoid and s.role='p' and f.fsname='pg_system' "\
                         + "ORDER BY s.hostname;"
        fileRemove= local_path('sql/remove_dump_dir.sql')
        fp = open(fileRemove, 'w')
        fp.write(sqlRemoveDumpDir)
        fp.close()

        # execute remove query and output remove commands
        PSQL.run_sql_file(fileRemove)

        # execute commands to remove one-year old dump directories
        # before operation
        cmdfileRemove = local_path('sql/remove_dump_dir.out')
        cmdRemove = open(cmdfileRemove)
        self.execDumpDirCommand(cmdRemove,dumpDirOpLog)
        cmdRemove.close()
        #######################################################################
        # query to construct command to create the one-year old dump directories
        sqlMakeDumpDir = "SELECT 'ssh '||s.hostname||' mkdir -p '||fe.fselocation||'/db_dumps/'||"\
                         + str(lastYear.strftime('%Y%m%d')) + " "\
                         + "FROM gp_segment_configuration s, pg_filespace f, pg_filespace_entry fe "\
                         + "WHERE s.dbid = fe.fsedbid and f.oid=fe.fsefsoid and s.role='p' and f.fsname='pg_system' "\
                         + "ORDER BY s.hostname;"
        fileMake = local_path('sql/make_dump_dir.sql')
        fp = open(fileMake, 'w')
        fp.write(sqlMakeDumpDir)
        fp.close()

        # execute create query and output create commands
        PSQL.run_sql_file(fileMake)

        # execute commands to create one-year old dump directories
        cmdfileMake = local_path('sql/make_dump_dir.out')
        cmdMake = open(cmdfileMake)
        self.execDumpDirCommand(cmdMake,dumpDirOpLog)
        cmdMake.close()
        #######################################################################
        # query to construct command to check the one-year old dump directories
        sqlCheckDumpDir = "SELECT 'ssh '||s.hostname||' ls '||fe.fselocation||'/db_dumps/ | grep '||"\
                         + str(lastYear.strftime('%Y%m%d')) + "||' | wc' "\
                         + "FROM gp_segment_configuration s, pg_filespace f, pg_filespace_entry fe "\
                         + "WHERE s.dbid = fe.fsedbid and f.oid=fe.fsefsoid and s.role='p' and f.fsname='pg_system' "\
                         + "ORDER BY s.hostname;"
        fileCheck = local_path('sql/check_dump_dir.sql')
        fp = open(fileCheck,'w')
        fp.write(sqlCheckDumpDir)
        fp.close()

        # execute check query and output check commands
        PSQL.run_sql_file(fileCheck)

        # execute commands to check one-year old dump directories
        cmdfileCheck = local_path('sql/check_dump_dir.out')
        cmdCheck = open(cmdfileCheck)
        self.execDumpDirCommand(cmdCheck,dumpDirOpLog)
        cmdCheck.close()

        # check one-year old dump directories have been created successfuly
        afterDumpDirCreated = local_path('sql/dump_dir_OpLog.out')
        afterDumpDirCreatedAns= local_path('sql/after_dump_dir_created.ans')
        if not self.isFileEqual(afterDumpDirCreated, afterDumpDirCreatedAns):
            raise Exception('Create test dump directory error')

        # run gpcrondump -o option to clear the oldest one-year old dump directory
        cmd = 'gpcrondump -x gptest -o'
        (ok, out) = self.run_command(cmd)
        if ok:
            raise Exception('GPCRONDUMP Error:' + out)

        # check one-year old dump directories have been removed successfuly
        # via gpcrondump -o option
        # execute commands to check one-year old dump directories
        cmdCheck = open(cmdfileCheck)
        self.execDumpDirCommand(cmdCheck,dumpDirOpLog)
        cmdCheck.close()

        afterDumpDirRemoved = local_path('sql/dump_dir_OpLog.out')
        afterDumpDirRemovedAns= local_path('sql/after_dump_dir_removed.ans')
        if not self.isFileEqual(afterDumpDirCreated, afterDumpDirRemovedAns):
            raise Exception('GPCRONDUMP -o option error')

    @unittest.skipIf(is_earlier_than(version, '4.3.4.0') and version != '4.2.8.5', 'Skipped on version before 4.3.4.0 and not equal to 4.2.8.5')
    def test_50_empty_schema_restore(self):
        # create a new database
        new_db = 'psql -d template1 -c "create database testdb;"'
        self.run_command(new_db)

        # create new schema
        new_schema = 'psql -d testdb -c "create schema testschema;"'
        self.run_command(new_schema)

        # create new table under schema
        new_table = 'psql -d testdb -c "create table testschema.testtable(i int);"'
        self.run_command(new_table)

        # dump full database
        cmdDump = 'gpcrondump -x testdb -a'
        output = self.run_gpcommand(cmdDump)

        # parse the output to get dump key
        dumpKey = self.get_timestamp(output)

        # drop the table under schema to make it empty
        drop_table = 'psql -d testdb -c "drop table testschema.testtable;"'
        self.run_command(drop_table)

        # restore table from backup
        cmdRestore = "gpdbrestore -t " + dumpKey + " -a -T testschema.testtable"
        (rc, out) = self.run_command(cmdRestore)

        # verify no errors
        self.assertEqual(0, rc)
        self.assertNotIn('[ERROR]:', out)

        # cleanup, drop database
        drop_db = 'psql -d template1 -c "drop database testdb;"'
        self.run_command(drop_db)

    @unittest.skipIf(is_earlier_than(version, '4.3.6.2'), 'Skipped on version before 4.3.6.2')
    def test_master_not_hang_on_segment_crash(self):
        """
        MPP-25943: gpcrondump, backup fails on segment causes master hang and hold lock on pg_class.
        Test is to grab the procid of dump agent, wait for TASK_SET_SERIALIZABLE in dump_status file,
        crash the dump agent, and verify that the dump process on master will detect the fault.
        """
        list1 = []
        list1.append(('mpp.gpdb.tests.utilities.backup_restore.incremental.BackupTestCase.populate_tables',
                      {'db_name':'hang', 'num':2500}))
        self.test_case_scenario.append(list1)

        list2 = []
        list2.append(('mpp.gpdb.tests.utilities.backup_restore.incremental.BackupTestCase.run_gpcrondump',
                    {'dbname':'hang', 'sleeping':2, 'expected_rc':2}))
        list2.append(('mpp.gpdb.tests.utilities.backup_restore.incremental.BackupTestCase.wait_kill_and_verify_dump_agent_on_master',
                     {'datadir':os.environ['MASTER_DATA_DIRECTORY'],
                      'wait_log_msg':'TASK_SET_SERIALIZABLE',
                      'verify_log_msg':'Lost response from dump agent'}
                    ))
        self.test_case_scenario.append(list2)


    @unittest.skipIf(is_earlier_than(version, '4.3.7'), 'Skipped on version before 4.3.7')
    def test_gpcrondump_error_report(self):
        """
        gpcrondump sholuld report the errors from segment failures/errors
        """
        BFT_BACKUP_STATUS = 1
        drop_db = 'drop database if exists gpcrondump_err_db;'
        create_db = 'create database gpcrondump_err_db;'
        query = 'create table test(i int);'
        PSQL.run_sql_command(drop_db, dbname = 'template1')
        PSQL.run_sql_command(create_db, dbname = 'template1')
        PSQL.run_sql_command(query, dbname = 'gpcrondump_err_db')

        cmdDump = 'gpcrondump -x gpcrondump_err_db -a'
        output = self.run_gpcommand(cmdDump)
        dumpKey = self.get_timestamp(output)
        status_file = self.get_dump_status_file(os.environ['MASTER_DATA_DIRECTORY'], dumpKey)

        if not os.path.exists(status_file):
            status_file = self.get_dump_status_file(os.environ['MASTER_DATA_DIRECTORY'], dumpKey,
                                                   content_id_format=True)

        self.write_dirty_string(status_file, "ERROR: dump error")

        read_error_query = 'SELECT * FROM gp_read_backup_file(\'%s\', \'%s\', %s);' % (os.path.dirname(status_file), dumpKey, BFT_BACKUP_STATUS)
        output = PSQL.run_sql_command(read_error_query, dbname = 'gpcrondump_err_db', flags='-q')

        self.assertIn('ERROR', output)
        PSQL.run_sql_command(drop_db, dbname='template1')


    @unittest.skipIf(is_earlier_than(version, '4.3.7'), 'Skipped on version before 4.3.7')
    def test_gpdbrestore_error_report(self):
        """
        gpdbrestore should report the errors from segment failures/errors
        """
        drop_db = 'drop database if exists gpdbrestore_err_db;'
        create_db = 'create database gpdbrestore_err_db;'
        query = 'drop table if exists test; create table test(i int);'
        PSQL.run_sql_command(drop_db, dbname = 'template1')
        PSQL.run_sql_command(create_db, dbname = 'template1')
        PSQL.run_sql_command(query, dbname = 'gpdbrestore_err_db')

        cmdDump = 'gpcrondump -x gpdbrestore_err_db -a'
        output = self.run_gpcommand(cmdDump)

        # parse the output to get dump key
        dumpKey = self.get_timestamp(output)

        cmdRestore = 'gpdbrestore -t %s -a' % dumpKey
        self.run_gpcommand(cmdRestore, expected_rc=0)

        report_file = self.get_restore_report_file_path(os.environ.get('MASTER_DATA_DIRECTORY'), dumpKey)
        self.assertTrue(self.isStringInFile(report_file, 'ERROR:  relation "test" already exists'))
        PSQL.run_sql_command(drop_db, dbname='template1')

    @unittest.skipIf(is_earlier_than(version, '4.3.7'), 'Skipped on version before 4.3.7')
    def test_gpdbrestore_full_with_filter_error_report(self):
        """
        gpdbrestore -T should report errors
        """
        drop_db = 'drop database if exists gpdbrestore_err_db;'
        create_db = 'create database gpdbrestore_err_db;'
        query = 'drop table if exists test; create table test(i int);'
        PSQL.run_sql_command(drop_db, dbname = 'template1')
        PSQL.run_sql_command(create_db, dbname = 'template1')
        PSQL.run_sql_command(query, dbname = 'gpdbrestore_err_db')

        cmdDump = 'gpcrondump -x gpdbrestore_err_db -a'
        output = self.run_gpcommand(cmdDump)

        # parse the output to get dump key
        dumpKey = self.get_timestamp(output)

        cmdRestore = 'gpdbrestore -t %s -T public.test -a' % dumpKey
        self.run_gpcommand(cmdRestore, expected_rc=0)

        report_file = self.get_restore_report_file_path(os.environ.get('MASTER_DATA_DIRECTORY'), dumpKey)
        self.assertTrue(self.isStringInFile(report_file, 'ERROR:  relation "test" already exists'))
        PSQL.run_sql_command(drop_db, dbname='template1')

