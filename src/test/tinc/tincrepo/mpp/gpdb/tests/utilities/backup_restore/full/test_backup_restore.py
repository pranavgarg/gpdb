#!/usr/bin/env python

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
import pexpect
from datetime import date
import unittest2 as unittest
import tinctest
from mpp.lib.PSQL import PSQL
from mpp.gpdb.tests.utilities.backup_restore.full import BackupTestCase, is_earlier_than
from tinctest.lib import local_path
from mpp.lib.gpdb_util import GPDBUtil

'''
@Full Backup
'''
gpdb_util = GPDBUtil()
version = gpdb_util.getGPDBVersion()

# storage unit TEMP must exist already on DD server for test, please make sure created it (currently manually)
alternative_storage_unit = 'TEMP'

class test_backup_restore(BackupTestCase):
    """
    @description test cases for full backup
    @tags backup restore gpcrondump gpdbrestore full ddboost and NFS
    @gucs gp_create_table_random_default_distribution=off
    """

    def __init__(self, methodName):
        super(test_backup_restore, self).__init__(methodName)
        ddboost_path_yml = os.path.join(os.getenv('MASTER_DATA_DIRECTORY'),
                                        'ddboost_config.yml')
        tinctest.logger.info("reading ddboost config yml")
        ddboost_config = self._read_config_yaml(ddboost_path_yml)
        self.HOST = ddboost_config['DDBOOST_HOST']
        self.USER = ddboost_config['DDBOOST_USER']
        self.PASSWORD = ddboost_config['DDBOOST_PASSWORD']

        self.BACKUPDIR = "MFR_TINC"
        self.NFSBACKUPDIR = "/backup/DCA-35"
        self.create_filespace()

    def cleanup(self):
        self.cleanup_backup_files(location = self.BACKUPDIR)
        path = '%s/%s/' % (os.environ.get('MASTER_DATA_DIRECTORY'), self.BACKUPDIR)
        self.cleanup_backup_files(location = path)

    def ddboost_config_setup(self, backup_dir=None, storage_unit=None):
        cmd_remove_config = "gpcrondump --ddboost-config-remove"
        (err, out) = self.run_command(cmd_remove_config)
        if err:
            msg = "Failed to remove previous DD configuration\n"
            raise Exception('Error: %s\n%s'% (msg,out))

        cmd_config = "gpcrondump --ddboost-host %s --ddboost-user %s" % (self.HOST, self.USER)
        cmd_config += " --ddboost-backupdir %s" % (self.BACKUPDIR if backup_dir is None else backup_dir)

        if storage_unit:
            cmd_config += " --ddboost-storage-unit %s" % storage_unit

        cmd_config
        local = pexpect.spawn(cmd_config)
        local.expect('Password: ')
        local.sendline(self.PASSWORD)
        local.expect(pexpect.EOF)
        local.close()

    def test_01_ddboost_config_without_storage_unit(self):
        self.ddboost_config_setup(self.BACKUPDIR)

    @unittest.skipIf(is_earlier_than(version, '4.3.9'), 'Skipped on version before 4.3.9')
    def test_01_ddboost_config_with_storage_unit(self):
        self.ddboost_config_setup(self.BACKUPDIR, storage_unit="GPDB2")

    def test_ddboost_02_full_with_no_history_table(self):
        tinctest.logger.info("Test-ddboost-2: Test for gpcromndump -H option with ddboost; Restore with -e")
        self.drop_create_database('historydb')
        self.run_full_backup(dbname = 'historydb', option = ' --ddboost -H')
        # dumping second time as history table gets generated after dump is done
        self.run_full_backup(dbname = 'historydb', option = ' --ddboost -H')

        self.cleanup()
        self.run_restore('historydb', option = '-e --ddboost')
        if self.history_table_exists('historydb'):
            raise Exception('gpcrondump_history table should not exists')

    def test_ddboost_02_full_with_history_table(self):
        tinctest.logger.info("Test-ddboost-2: Test for gpcromndump with ddboost; Restore with -e")
        self.drop_create_database('historydb')
        self.run_full_backup(dbname = 'historydb', option = ' --ddboost')
        # dumping second time as history table gets generated after dump is done
        self.run_full_backup(dbname = 'historydb', option = ' --ddboost')

        self.cleanup()
        self.run_restore('historydb', option = '-e --ddboost')

        if not self.history_table_exists('historydb'):
            raise Exception('gpcrondump_history table should exists')

    def test_ddboost_02_full(self):
        tinctest.logger.info("Test-ddboost-1: Test for gpcromndump with ddboost; Restore with -e")

        self.run_workload("backup_dir", 'bkdb1')
        self.run_full_backup(dbname = 'bkdb1', option = '--ddboost')

        self.get_data_to_file('bkdb1', 'backup1') #Create a copy of all the tables in database before the last backup

        self.cleanup()
        self.run_restore('bkdb1', option = '-e --ddboost')
        self.validate_restore("restore_dir", 'bkdb1')
        self.compare_table_data('bkdb1')

        self.compare_ao_co_tuple_count('bkdb1')

    def test_ddboost_03_full_options1(self):
        tinctest.logger.info("Test-ddboost-2: Test for gpcromndump with ddboost with option -b -d -j -k -z -B; Restore with -e -s")

        self.run_full_backup(dbname = 'bkdb1', option = '-b -j -k -z -B 100 -d %s --ddboost' % os.environ.get('MASTER_DATA_DIRECTORY'))

        self.get_data_to_file('bkdb1', 'backup1') #Create a copy of all the tables in database before the last backup

        self.cleanup()
        self.run_restore('bkdb1', option = '-s bkdb1 -e --ddboost')
        self.validate_restore("restore_dir", 'bkdb1')
        self.compare_table_data('bkdb1')

        self.compare_ao_co_tuple_count('bkdb1')

    @unittest.skipIf((os.uname()[0] == 'SunOS'), 'Skipped on Solaris')
    def test_ddboost_04_full_options2(self):

        tinctest.logger.info("Test-ddboost-3: Test for gpcrondump with options -c, --resyncable, -l,--no-owner, --no-privileges; Restore with -l -d -e")

        self.run_full_backup(dbname = 'bkdb1', option = '-c --rsyncable --no-privileges --no-owner -l -d %s --ddboost' % os.environ.get('MASTER_DATA_DIRECTORY'), value = "/tmp/log")

        self.get_data_to_file('bkdb1', 'backup1') #Create a copy of all the tables in database before the last backup

        self.cleanup()
        self.run_restore('bkdb1', option = ' -l /tmp/res_log -d %s -e --ddboost' % os.environ.get('MASTER_DATA_DIRECTORY'))
        self.validate_restore("restore_dir", 'bkdb1')
        self.compare_table_data('bkdb1')

        self.compare_ao_co_tuple_count('bkdb1')

    def test_ddboost_05_full_config_global_objects(self):
        tinctest.logger.info("Test-ddboost-4: Test for gpcrondump backup with global objects and config")

        self.run_workload("backup_dir", 'bkdb2')
        self.run_workload("dirty_dir_g1", 'bkdb2')
        self.run_full_backup(dbname = 'bkdb2', option = '-g -G --ddboost')

        self.get_data_to_file('bkdb2', 'backup1') #Create a copy of all the tables in database before the last backup

        self.run_workload("dirty_dir_g2", 'bkdb2') # Drop global and dependent objects before restore
        self.cleanup()
        self.run_restore('bkdb2', option = '-G -e --ddboost')
        self.validate_restore("restore_dir_g", 'bkdb2')
        self.compare_table_data('bkdb2')
        self.compare_ao_co_tuple_count('bkdb2')

    def test_ddboost_06_full_restore_with_option_T(self):
        tinctest.logger.info("Test-ddboost-5: Test for gpcrondump; Restore with option -T")

        self.run_workload("backup_dir", 'bkdb3')
        self.run_full_backup(dbname = 'bkdb3', option = '--ddboost')

        self.get_data_to_file('bkdb3', 'backup1') #Create a copy of all the tables in database before the last backup

        self.cleanup()
        self.run_restore('bkdb3', option = '-T public.ao_table1 -T public.heap_table3 -T public.mixed_part01 -a -e --ddboost')
        self.validate_restore("restore_T_with_e", 'bkdb3')

    def test_ddboost_07_full_restore_with_tablefile(self):
        tinctest.logger.info("Test-ddboost-6: Test to restore with selected tables in a file with ddboost")

        self.run_workload("backup_dir", 'bkdb4')
        self.run_full_backup(dbname = 'bkdb4', option = '--ddboost')

        self.get_data_to_file('bkdb4', 'backup1') #Create a copy of all the tables in database before the last backup

        table_file = local_path('%s/table_file1' % ('restore_T_with_e'))
        self.cleanup()
        self.run_restore('bkdb4', option = '--table-file=%s -a -e --ddboost' % table_file)
        self.validate_restore("restore_T_with_e", 'bkdb4')

    def test_ddboost_08_full_multiple_db(self):
        tinctest.logger.info("Test-ddboost-7: Test for multiple databases backup and restore")

        self.run_workload("backup_dir_small_1", 'bkdb5')
        self.run_workload("backup_dir_small_2", 'bkdb6')

        self.run_full_backup(dbname = 'bkdb5,bkdb6', option = '--ddboost')

        self.get_data_to_file('bkdb5', 'backup1') #Create a copy of all the tables in database before the last backup
        self.get_data_to_file('bkdb6', 'backup2') #Create a copy of all the tables in database before the last backup

        self.cleanup()
        self.run_restore('bkdb5,bkdb6', option = '-e --ddboost')

        self.validate_restore("restore_dir_small_1", 'bkdb5')
        self.validate_restore("restore_dir_small_2", 'bkdb6')

        self.compare_table_data('bkdb5')
        self.compare_table_data('bkdb6', restore_no = 2)

        self.compare_ao_co_tuple_count('bkdb5')
        #self.compare_ao_co_tuple_count('bkdb6')

    @unittest.skipIf((os.uname()[0] == 'SunOS'), 'Skipped on Solaris')
    def test_ddboost_09_full_with_restore_option_b(self):
        tinctest.logger.info("Test-ddboost-8: Full restore with -b option")

        self.drop_create_database('bkdb1')
        self.run_workload("backup_dir", 'bkdb1')
        self.run_full_backup(dbname = 'bkdb1', option = '--ddboost')

        self.get_data_to_file('bkdb1', 'backup1') #Create a copy of all the tables in database before the last backup

        self.cleanup()
        self.run_restore('bkdb1', option = '-e -a --ddboost -b ', location = self.BACKUPDIR)
        self.compare_table_data('bkdb1')
        self.compare_ao_co_tuple_count('bkdb1')

    @unittest.skipIf((os.uname()[0] == 'SunOS'), 'Skipped on Solaris')
    def test_ddboost_10_full_select_restore_with_b(self):
        tinctest.logger.info("Test-ddboost-9: Test to select restore with option b")

        self.run_workload("backup_dir", 'bkdb7')
        self.run_full_backup(dbname = 'bkdb7', option = '--ddboost')

        self.get_data_to_file('bkdb7', 'backup1') #Create a copy of all the tables in database before the last backup

        self.cleanup()
        self.run_restore('bkdb7', option = '-T public.ao_table1 -T public.heap_table3 -T public.mixed_part01 -a -e --ddboost -b ', location = self.BACKUPDIR)
        self.validate_restore("restore_T_with_e", 'bkdb7')

    @unittest.skipIf((os.uname()[0] == 'SunOS'), 'Skipped on Solaris')
    def test_ddboost_11_full_restore_with_tablefile_with_b(self):
        tinctest.logger.info("Test-ddboost-10: Test to restore with selected tables in a file with option b using ddboost")

        self.run_workload("backup_dir", 'bkdb8')
        self.run_full_backup(dbname = 'bkdb8', option = '--ddboost')

        self.get_data_to_file('bkdb8', 'backup1') #Create a copy of all the tables in database before the last backup

        table_file = local_path('%s/table_file1' % ('restore_T_with_e'))
        self.cleanup()
        self.run_restore('bkdb8', option = '--table-file=%s -a -e --ddboost -b ' % table_file, location = self.BACKUPDIR)
        self.validate_restore("restore_T_with_e", 'bkdb8')

    def test_ddboost_12_full_select_restore_with_T_and_s(self):
        tinctest.logger.info("Test-ddboost-11: Test to select restore with option T and s")

        self.run_workload("backup_dir", 'bkdb9')
        self.run_full_backup(dbname = 'bkdb9', option = ' --ddboost ')

        self.get_data_to_file('bkdb9', 'backup1') #Create a copy of all the tables in database before the last backup

        self.cleanup()
        self.run_restore('bkdb9', option = '-T public.ao_table1 -T public.heap_table3 -T public.mixed_part01 -s bkdb9 -a -e --ddboost')
        self.validate_restore("restore_T_with_e", 'bkdb9')

    def test_ddboost_13_full_select_restore_with_table_file_and_s(self):
        tinctest.logger.info("Test-ddboost-12: Test to select restore with option table-file and s")

        self.run_workload("backup_dir", 'bkdb10')
        self.run_full_backup(dbname = 'bkdb10', option = ' --ddboost ')

        self.get_data_to_file('bkdb10', 'backup1') #Create a copy of all the tables in database before the last backup

        table_file = local_path('%s/table_file1' % ('restore_T_with_e'))
        self.cleanup()
        self.run_restore('bkdb10', option = '--table-file=%s -s bkdb10 -a -e --ddboost' % table_file)
        self.validate_restore("restore_T_with_e", 'bkdb10')

    def test_ddboost_14_full_with_option_L(self):
        tinctest.logger.info("Test-ddboost-13: GPDBRESTORE -L (list tablenames in backup set) ")

        self.run_workload("backup_dir_simple_db", 'bkdb6')
        self.run_full_backup(dbname = 'bkdb6', option = '--ddboost')

        cmd = 'gpdbrestore -L -t '+ self.full_backup_timestamp + ' --ddboost'
        (ok, out) = self.run_command(cmd)
        if ok:
            raise Exception('GPDBRESTORE Error: %s'%out)

        self.drop_database('bkdb6')

        # verify gpdbrestore -L output contains all tables
        if not (('Table public.ao_compr01' in out) and \
                ('Table public.ao_compr02' in out) and \
                ('Table public.ao_compr03' in out) and \
                ('Table public.ao_part01' in out) and \
                ('Table public.ao_part02' in out) and \
                ('Table public.heap_table1' in out)):
            raise Exception('GPDBRESTORE Error: option -L')

    def test_ddboost_15_full_backup_restore_with_recreating_db(self):
        ''' Full dump and restore with recreating database '''
        tinctest.logger.info("Test-ddboost-14: gpcromndump  with options ddboost and recreating database")
        self.run_workload("backup_dir_simple_db", 'bkdbbb')

        # full database dump with default
        self.run_full_backup(dbname = 'bkdbbb', option = '--ddboost')

        # Need to drop database and restore
        self.drop_create_database('bkdbbb')

        # recreate and restore database
        self.cleanup()
        self.run_restore('bkdbbb', option = '--ddboost')
        self.validate_restore("restore_dir_simple_db", 'bkdbbb')

        # drop database after test
        self.drop_database('bkdbbb')

    def test_ddboost_16_full_ddboost_singletable(self):
        '''Include single table'''
        tinctest.logger.info("Test-ddboost-15: Test for single table, with option -t")

        self.run_workload("backup_dir_less_tables", 'bkdbbb')
        self.run_full_backup(dbname = 'bkdbbb', option = "-t public.ao_table21 --ddboost")

        self.get_data_to_file('bkdbbb', 'backup1') #Create a copy of all the tables in database before the last backup

        #truncate heap_table2 table before restore it from dump file
        cmdTrunc = 'psql -d bkdbbb -c "truncate table public.ao_table21;"'
        self.run_command(cmdTrunc)

        #restore from backup
        self.cleanup()
        self.run_restore('bkdbbb', option = ' -s bkdbbb --ddboost ')
        self.compare_table_data('bkdbbb')
        self.drop_database('bkdbbb')

    def test_ddboost_17_full_ddboost_multipletable(self):
        '''Include multiple table'''
        tinctest.logger.info("Test-ddboost-16: Test for multiple tables, with option -t")

        self.run_workload("backup_dir_less_tables", 'bkdbbb')
        self.run_full_backup(dbname = 'bkdbbb', option = "-t public.ao_table21 -t public.ao_compr03 -t public.ao_compr02 --ddboost")

        self.get_data_to_file('bkdbbb', 'backup1') #Create a copy of all the tables in database before the last backup

        #truncate heap_table2 table before restore it from dump file
        cmdTrunc = 'psql -d bkdbbb -c "truncate table public.ao_table21; truncate table public.ao_compr03; truncate table public.ao_compr02;"'
        self.run_command(cmdTrunc)

        #restore from backup
        self.cleanup()
        self.run_restore('bkdbbb', option = ' -s bkdbbb --ddboost ')
        self.compare_table_data('bkdbbb')
        self.drop_database('bkdbbb')

    def test_ddboost_18_full_exclude_singletable(self):
        '''exclude_singletable'''
        tinctest.logger.info("Test-ddboost-17: Test for exclude singletable with --ddboost")

        self.run_workload("backup_dir_simple_db", 'bkdbbb')
        self.run_full_backup(dbname = 'bkdbbb', option = "-T public.ao_compr03 --ddboost")

        self.get_data_to_file('bkdbbb', 'backup1') #Create a copy of all the tables in database before the last backup

        #truncate other table in the databse before restore it from dump file
        cmdTrunc = 'psql -d bkdbbb -c "truncate table public.ao_compr01; truncate table public.ao_compr02; truncate table schema_ao.ao_table1;\
                    truncate table public.ao_part01; truncate table public.ao_part02; truncate table public.heap_table1;"'
        self.run_command(cmdTrunc)

        #restore from backup
        self.cleanup()
        self.run_restore('bkdbbb', option = ' -s bkdbbb --ddboost ')
        self.compare_table_data('bkdbbb')
        self.drop_database('bkdbbb')

    def test_ddboost_19_full_exclude_multipletable(self):
        '''exclude multiple tables '''
        tinctest.logger.info("Test-ddboost-18: Test for exclude multiple tables with --ddboost")

        self.run_workload("backup_dir_simple_db", 'bkdbbb')
        self.run_full_backup(dbname = 'bkdbbb', option = "-T public.ao_part01 -T public.ao_part02 -T public.ao_compr01 --ddboost")

        self.get_data_to_file('bkdbbb', 'backup1') #Create a copy of all the tables in database before the last backup

        #truncate other table in the databse before restore it from dump file
        cmdTrunc = 'psql -d bkdbbb -c "truncate table public.ao_compr02; truncate table public.ao_compr03; truncate table public.heap_table1; truncate table schema_ao.ao_table1;"'
        self.run_command(cmdTrunc)

        #restore from backup
        self.cleanup()
        self.run_restore('bkdbbb', option = ' -s bkdbbb --ddboost')
        self.compare_table_data('bkdbbb')
        self.drop_database('bkdbbb')

    def test_ddboost_20_full_include_schema(self):
        '''include multiple tables '''
        tinctest.logger.info("Test-ddboost-20: Test for exclude multiple tables with --ddboost")

        self.run_workload("backup_dir_simple_db", 'bkdbbb')
        self.run_full_backup(dbname = 'bkdbbb', option = "-s schema_ao --ddboost")

        self.get_data_to_file('bkdbbb', 'backup1') #Create a copy of all the tables in database before the last backup

        #truncate other table in the databse before restore it from dump file
        cmdTrunc = 'psql -d bkdbbb -c "truncate table schema_ao.ao_table1;"'
        self.run_command(cmdTrunc)

        #restore from backup
        self.cleanup()
        self.run_restore('bkdbbb', option = ' -s bkdbbb --ddboost')
        self.compare_table_data('bkdbbb')
        self.drop_database('bkdbbb')

    @unittest.skipIf(is_earlier_than(version, '4.3.4'), 'Skipped on version before 4.3.4')
    def test_ddboost_21_full_exclude_schema(self):
        '''exclude multiple tables '''
        tinctest.logger.info("Test-ddboost-20: Test for exclude multiple tables with --ddboost")

        self.run_workload("backup_dir_simple_db", 'bkdbbb')
        self.run_full_backup(dbname = 'bkdbbb', option = "-S public --ddboost")

        self.get_data_to_file('bkdbbb', 'backup1') #Create a copy of all the tables in database before the last backup

        #truncate other table in the databse before restore it from dump file
        cmdTrunc = 'psql -d bkdbbb -c "truncate table schema_ao.ao_table1;"'
        self.run_command(cmdTrunc)

        #restore from backup
        self.cleanup()
        self.run_restore('bkdbbb', option = ' -s bkdbbb --ddboost')
        self.compare_table_data('bkdbbb')
        self.drop_database('bkdbbb')

    def test_ddboost_22_full_include_schema_file(self):
        '''include multiple tables '''
        tinctest.logger.info("Test-ddboost-20: Test for exclude multiple tables with --ddboost")

        self.run_workload("backup_dir_simple_db", 'bkdbbb')
        schema_file = local_path('%s/schema_file' % ('filter_file'))
        self.run_full_backup(dbname = 'bkdbbb', option = "schema-file %s --ddboost" % schema_file)
        self.run_full_backup(dbname = 'bkdbbb', option = "-s schema_ao --ddboost")

        self.get_data_to_file('bkdbbb', 'backup1') #Create a copy of all the tables in database before the last backup

        #truncate other table in the databse before restore it from dump file
        cmdTrunc = 'psql -d bkdbbb -c "truncate table schema_ao.ao_table1;"'
        self.run_command(cmdTrunc)

        #restore from backup
        self.cleanup()
        self.run_restore('bkdbbb', option = ' -s bkdbbb --ddboost')
        self.compare_table_data('bkdbbb')
        self.drop_database('bkdbbb')

    @unittest.skipIf(is_earlier_than(version, '4.3.4'), 'Skipped on version before 4.3.4')
    def test_ddboost_23_full_exclude_schema_file(self):
        '''exclude multiple tables '''
        tinctest.logger.info("Test-ddboost-20: Test for exclude multiple tables with --ddboost")

        self.run_workload("backup_dir_simple_db", 'bkdbbb')
        exclude_schema_file = local_path('%s/exclude_schema_file' % ('filter_file'))
        self.run_full_backup(dbname = 'bkdbbb', option = "--exclude-schema-file %s --ddboost" % exclude_schema_file)

        self.get_data_to_file('bkdbbb', 'backup1') #Create a copy of all the tables in database before the last backup

        #truncate other table in the databse before restore it from dump file
        cmdTrunc = 'psql -d bkdbbb -c "truncate table schema_ao.ao_table1;"'
        self.run_command(cmdTrunc)

        #restore from backup
        self.cleanup()
        self.run_restore('bkdbbb', option = ' -s bkdbbb --ddboost')
        self.compare_table_data('bkdbbb')
        self.drop_database('bkdbbb')

    def test_ddboost_25_full_gpdbrestore_negative_options(self):
        tinctest.logger.info("Test-ddboost-20: Test for options that wont work with ddboost")
        self.drop_create_database('ddbkdb')
        self.run_full_backup(dbname = 'ddbkdb', option = '--ddboost')
        cmd1 = 'gpdbrestore -s -R %s --ddboost' % self.BACKUPDIR
        (rc, out) = self.run_command(cmd1)
        if rc == 0:
            raise Exception('Error: %s'%out)

    @unittest.skipIf(is_earlier_than(version, '4.3.4'), 'Skipped on version before 4.3.4')
    def test_ddboost_26_full_restore_with_option_T_truncate(self):
        tinctest.logger.info("Test-ddboost-5: Test for gpcrondump; Restore with option -T")

        self.run_workload("backup_dir", 'bkdb3')
        self.run_full_backup(dbname = 'bkdb3', option = '--ddboost')

        self.get_data_to_file('bkdb3', 'backup1') #Create a copy of all the tables in database before the last backup

        self.cleanup()
        self.run_restore('bkdb3', option = '-T public.ao_table1 -T public.heap_table3 -T public.mixed_part01 -a  --truncate --ddboost')
        self.validate_restore("restore_T_with_e", 'bkdb3')

    @unittest.skipIf(version >= '4.3' or is_earlier_than(version, '4.2.8.4'), 'Skipped on version after 4.3 or before 4.2.8.4')
    def test_ddboost_28_check_sequence_value(self):
        tinctest.logger.info("Test-ddboost-28: Test gpdbrestore with --ddboost option to restore sequence values")
        self.drop_database('bkdbseq')
        self.run_workload("check_seq_val", 'bkdbseq')
        self.run_full_backup(dbname = 'bkdbseq', option = '--ddboost')

        self.cleanup()

        #Increase sequence value twice
        cmdSql = 'psql -d bkdbseq -c "SELECT nextval(\'serial\')"'
        self.run_command(cmdSql) #1
        self.run_command(cmdSql) #2

        #Drop tables before restoring it from dump file
        cmdTrunc = 'psql -d bkdbseq -c "drop table public.company"'
        self.run_command(cmdTrunc)

        self.run_restore('bkdbseq', option = '-T public.company -a --ddboost')
        self.validate_restore("check_seq_val_ans", 'bkdbseq')
        self.drop_database('bkdbseq')

    def test_ddboost_29_remove_backup_dir(self):
        cmd_del_dir = "gpddboost --del-dir=%s" % self.BACKUPDIR
        (err, out) = self.run_command(cmd_del_dir)
        if err:
            msg = "Failed to delete backup directory\n" % self.BACKUPDIR
            raise Exception('Error: %s\n%s'% (msg,out))

    @unittest.skipIf(is_earlier_than(version, '4.3.5.4'), 'Skipped on version before 4.3.5.4')
    def test_ddboost_30_restore_should_not_restore_sequence(self):
        """
        MPP-25744, restoring single table should not restore any sequence with ddboost
        """
        tinctest.logger.info("Restoring a single table should not restore sequence from other tables")

        if not self.check_db_exists('gptest'):
            self.create_database('gptest')

        PSQL.run_sql_command('''DROP SCHEMA IF EXISTS mfec_test CASCADE;
                                CREATE SCHEMA mfec_test;
                                CREATE TABLE mfec_test.kantest_restore (id int,name varchar(10));
                                INSERT INTO mfec_test.kantest_restore values (10,'kan');
                                CREATE TABLE mfec_test.test_case_restore (id serial,name varchar(10),adds varchar(10));
                                INSERT INTO mfec_test.test_case_restore (name ,adds) values ('peter','LA');
                                ''', dbname = 'gptest');

        self.run_gpcrondump(dbname='gptest', option = '-s mfec_test --ddboost')

        PSQL.run_sql_command('''DROP TABLE mfec_test.kantest_restore;
                                CREATE TABLE mfec_test.kantest_restore (id int,name varchar(10));
                                INSERT INTO mfec_test.test_case_restore (name ,adds) values ('peter','LA');
                                ''', dbname = 'gptest');

        cmd = 'gpdbrestore -t '+ self.full_backup_timestamp + ' -T mfec_test.kantest_restore --ddboost -a'
        self.run_command(cmd)
        sql = 'select last_value from mfec_test.test_case_restore_id_seq;'
        last_val = self.run_SQLQuery(sql, 'gptest')[0][0]

        # sequence number should not be restored back to 1
        self.assertEquals(last_val, 2)

    @unittest.skipIf(is_earlier_than(version, '4.3.6.2'), 'Skipped on version before 4.3.6.2')
    def test_ddboost_31_restore_without_compression(self):
        """
        MPP-25620: gpdbrestore is failing for ddboost if compression program is
        not specified.
        """

        status_file_prefix = 'gp_restore_status_-1_1_'

        PSQL.run_sql_command('''DROP TABLE  IF EXISTS t1 CASCADE;
                                CREATE TABLE t1 (id int);
                                INSERT INTO t1 select generate_series(1, 10);
                                CREATE UNIQUE INDEX t1_idx on t1(id);
                                ALTER TABLE t1 ADD CONSTRAINT verify CHECK (id > 0);
                                ''', dbname = 'gptest');

        self.run_gpcrondump(dbname='gptest', option = '-x gptest -z --ddboost')

        cmd = 'gpdbrestore -t '+ self.full_backup_timestamp + ' -T public.t1 --ddboost -a'
        rc, stdout = self.run_command(cmd)
        self.assertEquals(0, rc)
        self.assertNotIn("Error executing query", stdout)
        self.assertNotIn("Type 2 could not be be found", stdout)

        status_file = self.get_restore_status_file_on_master()
        with open(status_file, 'r') as fd:
            lines = fd.readlines()
            self.assertNotIn('psql finished abnormally with return code 1', lines)

    @unittest.skipIf(is_earlier_than(version, '4.3.9'), 'Skipped on version before 4.3.9')
    def test_ddboost_32_dynamic_storage_unit(self):
        """
        Note: storage unit TEMP is assumed to already exist on DD server.
        """

        default_dbname = 'gptest'

        if not self.check_db_exists('gptest'):
            self.create_database('gptest')

        # create some table with data for test
        self.cleanup_simple_tables(default_dbname)
        self.populate_simple_tables(default_dbname)
        self.populate_simple_tables_data(default_dbname)

        # run full dump using the alternative_storage_unit: TEMP
        dump_to_dd_storage_unit_option = '--ddboost --ddboost-storage-unit %s' % alternative_storage_unit
        self.run_gpcrondump(dbname='gptest', option = dump_to_dd_storage_unit_option)

        # get list of dumped files on DD server
        list_dumped_files= "gpddboost --ls '/%s/%s/' --ddboost-storage-unit=%s" % (self.BACKUPDIR, self.full_backup_timestamp[:8], alternative_storage_unit)
        _, stdout = self.run_command(list_dumped_files)
        dumped_files = self.get_list_of_ddboost_files(stdout, self.full_backup_timestamp)
        self.assertTrue(len(dumped_files) > 0)

        # drop all tables and run restore
        self.cleanup_simple_tables(default_dbname)
        self.run_restore(default_dbname, option = ' --ddboost --ddboost-storage-unit %s ' % alternative_storage_unit)

        # verify row count matches
        self.verifying_simple_tables(default_dbname, {'ao':1, 'co':1, 'heap':1})

        # cleanup the dumped files on DD server
        self.delete_ddboost_files(os.path.join(self.BACKUPDIR, self.full_backup_timestamp[:8]), dumped_files, alternative_storage_unit)

    @unittest.skipIf(is_earlier_than(version, '4.3.9'), 'Skipped on version before 4.3.9')
    def test_ddboost_33_dynamic_storage_unit_on_specific_objects(self):
        """
        Note: storage unit TEMP is assumed to already exist on DD server.
        """

        default_dbname = 'gptest'

        if not self.check_db_exists('gptest'):
            self.create_database('gptest')

        # run full dump using the alternative_storage_unit: TEMP
        dump_to_dd_storage_unit_option = '-G -g --dump-stats --ddboost --ddboost-storage-unit %s' % alternative_storage_unit
        self.run_gpcrondump(dbname='gptest', option = dump_to_dd_storage_unit_option)

        # get list of dumped files on DD server
        list_dumped_files= "gpddboost --ls '/%s/%s/' --ddboost-storage-unit=%s" % (self.BACKUPDIR, self.full_backup_timestamp[:8], alternative_storage_unit)
        _, stdout = self.run_command(list_dumped_files)
        dumped_files = self.get_list_of_ddboost_files(stdout, self.full_backup_timestamp)

        cdatabase_file_new = 'gp_cdatabase_-1_1_' + self.full_backup_timestamp
        cdatabase_file_old = 'gp_cdatabase_1_1_' + self.full_backup_timestamp
        if cdatabase_file_new in dumped_files:
            use_old = False
        elif cdatabase_file_old in dumped_files:
            use_old = True
        else:
            raise Exception("Neither %s nor %s found in %s" % (cdatabase_file_new, cdatabase_file_old, dumped_files))

        global_dump_file = 'gp_global_%d_1_' % (1 if use_old else -1) + self.full_backup_timestamp
        self.assertIn(global_dump_file, dumped_files)

        dump_stats_file = 'gp_statistics_%d_1_' % (1 if use_old else -1) + self.full_backup_timestamp
        self.assertIn(dump_stats_file, dumped_files)

        config_file = 'gp_master_config_files_' + self.full_backup_timestamp + '.tar'
        self.assertIn(config_file, dumped_files)

        # cleanup the dumped files on DD server
        self.delete_ddboost_files(os.path.join(self.BACKUPDIR, self.full_backup_timestamp[:8]), dumped_files, alternative_storage_unit)

#======================================================================================================================#
    def test_nfs_01_config(self):
        cmd_remove_config = "gpcrondump --ddboost-config-remove"
        (err, out) = self.run_command(cmd_remove_config)
        if err:
            msg = "Failed to remove previous DD configuration\n"
            raise Exception('Error: %s\n%s'% (msg,out))

        cmd_config = "gpcrondump --ddboost-host %s --ddboost-user %s --ddboost-backupdir %s" % (self.HOST, self.USER, self.NFSBACKUPDIR)
        local = pexpect.spawn(cmd_config)
        local.expect('Password: ')
        local.sendline(self.PASSWORD)
        local.expect(pexpect.EOF)
        local.close()

    # TODO: RUN THIS WITH THE NEW CODE
    def cluster_in_change_tracking(self, fault_injector_object):
        '''
        Put Cluster into change_tracking
        '''
        import time
        def invoke_fault(object, fault_name, type, role='mirror', port=None, occurence=None, sleeptime=None, seg_id=None):
            ''' Reset the fault and then issue the fault with the given type'''
            object.inject_fault(f=fault_name, y='reset', r=role, p=port , o=occurence, sleeptime=sleeptime, seg_id=seg_id)
            object.inject_fault(f=fault_name, y=type, r=role, p=port , o=occurence, sleeptime=sleeptime, seg_id=seg_id)
            tinctest.logger.info('Successfully injected fault_name : %s fault_type : %s  occurence : %s ' % (fault_name, type, occurence))
            time.sleep(30)

        invoke_fault(fault_injector_object, 'postmaster', 'panic', role='primary')
        fault_injector_object.wait_till_change_tracking_transition()
        tinctest.logger.info('Change_tracking transition complete')


    def test_nfs_02_full_with_backupdir(self):
        tinctest.logger.info("Test-nfs-1: Test for verifying full backup to a location other than master_data_directory...; gpcrondump and restore with -u option")
        self.cleanup_backup_files(location = self.NFSBACKUPDIR) # Cleaning the previous backups

        self.drop_create_database('bkdb1')
        self.run_full_backup(dbname = 'bkdb1')

        self.run_workload("backup_dir", 'bkdb1')
        self.run_full_backup(dbname = 'bkdb1', option = '-u', value = self.NFSBACKUPDIR)

        self.get_data_to_file('bkdb1', 'backup1') #Create a copy of all the tables in database before the last backup

        self.run_restore('bkdb1', option = '-u %s -e' % self.NFSBACKUPDIR)
        self.validate_restore("restore_dir2", 'bkdb1')
        self.compare_table_data('bkdb1')
        self.compare_ao_co_tuple_count('bkdb1')

    def test_nfs_03_full_with_backupdir_with_restore_option_R(self):
        tinctest.logger.info("Test-nfs-2: Test for verifying full backup to a location other than master_data_directory; gpcrondump with -u optionl restore with -R option")
        self.cleanup_backup_files(location = self.NFSBACKUPDIR) # Cleaning the previous backups

        self.drop_create_database('bkdb1')

        self.run_workload("backup_dir", 'bkdb1')
        self.run_full_backup(dbname = 'bkdb1', option = '-u', value = self.NFSBACKUPDIR)
        self.validate_backup_files_on_mounted_backedup_dir(self.NFSBACKUPDIR)

        self.get_data_to_file('bkdb1', 'backup1') #Create a copy of all the tables in database before the last backup

        self.run_restore('bkdb1', option = '-a -e -R ', location = self.NFSBACKUPDIR)
        self.validate_restore("restore_dir2", 'bkdb1')
        self.compare_table_data('bkdb1')
        self.compare_ao_co_tuple_count('bkdb1')

    @unittest.skipIf((os.uname()[0] == 'SunOS'), 'Skipped on Solaris')
    def test_nfs_04_full_restore_with_option_b_and_u(self):
        tinctest.logger.info("Test-nfs-3: Full restore with -b option and a backup_dir")
        self.drop_create_database('bkdb1')
        self.run_workload("backup_dir", 'bkdb1')
        self.run_full_backup(dbname = 'bkdb1', option = '-u', value = self.NFSBACKUPDIR)

        self.get_data_to_file('bkdb1', 'backup1') #Create a copy of all the tables in database before the last backup

        self.run_restore('bkdb1', option = '-a -e -u %s -b ' % (self.NFSBACKUPDIR), location = self.NFSBACKUPDIR)
        self.compare_table_data('bkdb1')
        self.compare_ao_co_tuple_count('bkdb1')

    def test_nfs_05_full_select_restore_with_T(self):
        tinctest.logger.info("Test-nfs-4: Test to select restore with nfs backup_dir")
        self.run_workload("backup_dir", 'bkdbnfs1')
        self.run_full_backup(dbname = 'bkdbnfs1', option = '-u', value = self.NFSBACKUPDIR)

        self.get_data_to_file('bkdbnfs1', 'backup1') #Create a copy of all the tables in database before the last backup

        self.run_restore('bkdbnfs1', option = '-T public.ao_table1 -T public.heap_table3 -T public.mixed_part01 -a -e -u %s ' % self.NFSBACKUPDIR)
        self.validate_restore("restore_T_with_e", 'bkdbnfs1')

    def test_nfs_06_full_select_restore_with_table_file(self):
        tinctest.logger.info("Test-nfs-5: Test to select restore with option table-file and nfs backup_dir")
        self.run_workload("backup_dir", 'bkdbnfs2')
        self.run_full_backup(dbname = 'bkdbnfs2', option = '-u', value = self.NFSBACKUPDIR)

        self.get_data_to_file('bkdbnfs2', 'backup1') #Create a copy of all the tables in database before the last backup

        table_file = local_path('%s/table_file1' % ('restore_T_with_e'))
        self.run_restore('bkdbnfs2', option = '--table-file=%s -a -e -u %s '  % (table_file, self.NFSBACKUPDIR))
        self.validate_restore("restore_T_with_e", 'bkdbnfs2')

    @unittest.skipIf((os.uname()[0] == 'SunOS'), 'Skipped on Solaris')
    def test_nfs_07_full_select_restore_with_option_b_and_u(self):
        tinctest.logger.info("Test-nfs-6: Test to select restore with option b and nfs backup_dir")
        self.run_workload("backup_dir", 'bkdbnfs3')
        self.run_full_backup(dbname = 'bkdbnfs3', option = '-u', value = self.NFSBACKUPDIR)

        self.get_data_to_file('bkdbnfs3', 'backup1') #Create a copy of all the tables in database before the last backup

        self.run_restore('bkdbnfs3', option = '-T public.ao_table1 -T public.heap_table3 -T public.mixed_part01 -a -e -u %s -b ' % (self.NFSBACKUPDIR), location = self.NFSBACKUPDIR)
        self.validate_restore("restore_T_with_e", 'bkdbnfs3')

    def test_nfs_08_full_select_restore_with_table_file_and_b(self):
        tinctest.logger.info("Test-nfs-7: Test to select restore with option table-file and nfs backup_dir")
        self.run_workload("backup_dir", 'bkdbnfs4')
        self.run_full_backup(dbname = 'bkdbnfs4', option = '-u', value = self.NFSBACKUPDIR)

        self.get_data_to_file('bkdbnfs4', 'backup1') #Create a copy of all the tables in database before the last backup

        table_file = local_path('%s/table_file1' % ('restore_T_with_e'))
        self.run_restore('bkdbnfs4', option = '--table-file=%s -a -e -u %s -b '  % (table_file, self.NFSBACKUPDIR), location = self.NFSBACKUPDIR)
        self.validate_restore("restore_T_with_e", 'bkdbnfs4')

    def test_nfs_09_full_select_restore_with_T_and_s(self):
        tinctest.logger.info("Test-nfs-8: Test to select restore with option T, s and nfs backup_dir")

        self.run_workload("backup_dir", 'bkdbnfs5')
        self.run_full_backup(dbname = 'bkdbnfs5', option = '-u', value = self.NFSBACKUPDIR)

        self.get_data_to_file('bkdbnfs5', 'backup1') #Create a copy of all the tables in database before the last backup

        self.run_restore('bkdbnfs5', option = '-T public.ao_table1 -T public.heap_table3 -T public.mixed_part01 -a -e -s bkdbnfs5 -u %s' % self.NFSBACKUPDIR)
        self.validate_restore("restore_T_with_e", 'bkdbnfs5')

    def test_nfs_10_full_select_restore_with_table_file_and_s(self):
        tinctest.logger.info("Test-nfs-9: Test to select restore with option table-file, s and nfs backup_dir")

        self.run_workload("backup_dir", 'bkdbnfs6')
        self.run_full_backup(dbname = 'bkdbnfs6', option = '-u', value = self.NFSBACKUPDIR)

        self.get_data_to_file('bkdbnfs6', 'backup1') #Create a copy of all the tables in database before the last backup

        table_file = local_path('%s/table_file1' % ('restore_T_with_e'))
        self.run_restore('bkdbnfs6', option = '--table-file=%s -s bkdbnfs6 -a -e -u %s' % (table_file, self.NFSBACKUPDIR))
        self.validate_restore("restore_T_with_e", 'bkdbnfs6')

    def test_nfs_11_full_with_option_L_u(self):
        tinctest.logger.info("Test-nfs-10: GPDBRESTORE -L (list tablenames in backup set) ")

        self.run_workload("backup_dir_simple_db", 'bkdbnfs')
        self.run_full_backup(dbname = 'bkdbnfs', option = '-u %s' % self.NFSBACKUPDIR)

        cmd = 'gpdbrestore -L -t '+ self.full_backup_timestamp + ' -u %s' % self.NFSBACKUPDIR
        (ok, out) = self.run_command(cmd)
        if ok:
            raise Exception('GPDBRESTORE Error: %s'%out)

        self.drop_database('bkdbnfs')

        # verify gpdbrestore -L output contains all tables
        if not (('Table public.ao_compr01' in out) and \
                ('Table public.ao_compr02' in out) and \
                ('Table public.ao_compr03' in out) and \
                ('Table public.ao_part01' in out) and \
                ('Table public.ao_part02' in out) and \
                ('Table public.heap_table1' in out)):
            raise Exception('GPDBRESTORE Error: option -L')

    def test_nfs_12_full_backup_restore_with_prefix_option(self):
        tinctest.logger.info("Test-nfs-11: Test for verifying full backup and restore with option --prefix and -u")

        self.run_workload("backup_dir", 'bkdbnfs6')
        self.run_full_backup(dbname = 'bkdbnfs6', option = '--prefix=foo -u %s' % self.NFSBACKUPDIR)
        self.check_filter_file_exists(expected=False, prefix='foo', location=self.NFSBACKUPDIR)

        self.get_data_to_file('bkdbnfs6', 'backup1') #Create a copy of all the tables in database before the last backup

        self.run_restore('bkdbnfs6', option = '-s bkdbnfs6 -e --prefix foo -u %s' % self.NFSBACKUPDIR)
        self.compare_table_data('bkdbnfs6')
        self.compare_ao_co_tuple_count('bkdbnfs6')

    def test_nfs_13_full_backup_restore_filtering_with_prefix_option(self):
        tinctest.logger.info("Test-nfs-12: Test for verifying full backup and restore filtering with option --prefix and -u")

        self.run_workload("backup_dir", 'bkdbnfs7')
        self.run_full_backup(dbname = 'bkdbnfs7', option = '-t public.ao_table21 --prefix=foo -u %s' % self.NFSBACKUPDIR)

        self.get_data_to_file('bkdbnfs7', 'backup1') #Create a copy of all the tables in database before the last backup

        self.run_restore('bkdbnfs7', option = '-s bkdbnfs7 -e --prefix foo -u %s' % self.NFSBACKUPDIR)
        self.compare_table_data('bkdbnfs7')
        self.compare_ao_co_tuple_count('bkdbnfs7')

    def test_nfs_14_full_backup_restore_with_recreating_db(self):
        ''' Full dump and restore with recreating database '''
        tinctest.logger.info("Test-nfs-13: gpcromndump --full for nfs backup_dir with recreating database")
        self.run_workload("backup_dir_simple_db", 'bkdbnfs')

        # full database dump with default
        self.run_full_backup(dbname = 'bkdbnfs', option = '-u', value = self.NFSBACKUPDIR)

        # Need to drop database and restore
        self.drop_create_database('bkdbnfs')

        # recreate and restore database
        self.run_restore('bkdbnfs', option = '-u %s' % self.NFSBACKUPDIR)
        self.validate_restore("restore_dir_simple_db", 'bkdbnfs')

        # drop database after test
        self.drop_database('bkdbnfs')

    def test_nfs_15_full_singletable(self):
        '''Include single table'''
        tinctest.logger.info("Test-nfs-14: Test for single table, with option -t")

        self.run_workload("backup_dir_less_tables", 'bkdbnfs')
        self.run_full_backup(dbname = 'bkdbnfs', option = "-t public.ao_table21 -u %s" % self.NFSBACKUPDIR)

        self.get_data_to_file('bkdbnfs', 'backup1') #Create a copy of all the tables in database before the last backup

        #truncate heap_table2 table before restore it from dump file
        cmdTrunc = 'psql -d bkdbnfs -c "truncate table public.ao_table21;"'
        self.run_command(cmdTrunc)

        #restore from backup
        self.run_restore('bkdbnfs', option = ' -s bkdbnfs -u %s ' % self.NFSBACKUPDIR)
        self.compare_table_data('bkdbnfs')
        self.drop_database('bkdbnfs')

    def test_nfs_16_full_multipletable(self):
        '''Include multiple table'''
        tinctest.logger.info("Test-nfs-15: Test for multiple tables, with option -t")

        self.run_workload("backup_dir_less_tables", 'bkdbnfs')
        self.run_full_backup(dbname = 'bkdbnfs', option = "-t public.ao_table21 -t public.ao_compr03 -t public.ao_compr02 -u %s" % self.NFSBACKUPDIR)

        self.get_data_to_file('bkdbnfs', 'backup1') #Create a copy of all the tables in database before the last backup

        #truncate heap_table2 table before restore it from dump file
        cmdTrunc = 'psql -d bkdbnfs -c "truncate table public.ao_table21; truncate table public.ao_compr03; truncate table public.ao_compr02;"'
        self.run_command(cmdTrunc)

        #restore from backup
        self.run_restore('bkdbnfs', option = ' -s bkdbnfs -u %s ' % self.NFSBACKUPDIR)
        self.compare_table_data('bkdbnfs')
        self.drop_database('bkdbnfs')

    def test_nfs_17_full_exclude_singletable(self):
        '''exclude_singletable'''
        tinctest.logger.info("Test-nfs-16: Test for exclude singletable with -u")

        self.run_workload("backup_dir_simple_db", 'bkdbnfs')
        self.run_full_backup(dbname = 'bkdbnfs', option = "-T public.ao_compr03 -u %s" % self.NFSBACKUPDIR)

        self.get_data_to_file('bkdbnfs', 'backup1') #Create a copy of all the tables in database before the last backup

        #truncate other table in the databse before restore it from dump file
        cmdTrunc = 'psql -d bkdbnfs -c "truncate table public.ao_compr01; truncate table public.ao_compr02; truncate table schema_ao.ao_table1;\
                    truncate table public.ao_part01; truncate table public.ao_part02; truncate table public.heap_table1;"'
        self.run_command(cmdTrunc)

        #restore from backup
        self.run_restore('bkdbnfs', option = ' -s bkdbnfs -u %s ' % self.NFSBACKUPDIR)
        self.compare_table_data('bkdbnfs')
        self.drop_database('bkdbnfs')

    def test_nfs_18_full_exclude_multipletable(self):
        '''exclude multiple tables '''
        tinctest.logger.info("Test-nfs-17: Test for exclude multiple tables with -u")

        self.run_workload("backup_dir_simple_db", 'bkdbnfs')
        self.run_full_backup(dbname = 'bkdbnfs', option = "-T public.ao_part01 -T public.ao_part02 -T public.ao_compr01 -u %s" % self.NFSBACKUPDIR)

        self.get_data_to_file('bkdbnfs', 'backup1') #Create a copy of all the tables in database before the last backup

        #truncate other table in the databse before restore it from dump file
        cmdTrunc = 'psql -d bkdbnfs -c "truncate table public.ao_compr02; truncate table public.ao_compr03; truncate table public.heap_table1; truncate table schema_ao.ao_table1;"'
        self.run_command(cmdTrunc)

        #restore from backup
        self.run_restore('bkdbnfs', option = ' -s bkdbnfs -u %s' % self.NFSBACKUPDIR)
        self.compare_table_data('bkdbnfs')
        self.drop_database('bkdbnfs')

    def test_nfs_19_full_options1(self):
        tinctest.logger.info("Test-nfs-18: Test for gpcromndump with option -b -d -j -k -z -B and -u; Restore with -e -s")

        self.run_full_backup(dbname = 'bkdb1', option = '-b -j -k -z -B 100 -d %s -u %s' % (os.environ.get('MASTER_DATA_DIRECTORY'), self.NFSBACKUPDIR))

        self.get_data_to_file('bkdb1', 'backup1') #Create a copy of all the tables in database before the last backup

        self.run_restore('bkdb1', option = '-s bkdb1 -e -u %s' % self.NFSBACKUPDIR)
        self.validate_restore("restore_dir", 'bkdb1')
        self.compare_table_data('bkdb1')

        self.compare_ao_co_tuple_count('bkdb1')

    @unittest.skipIf((os.uname()[0] == 'SunOS'), 'Skipped on Solaris')
    def test_nfs_20_full_options2(self):

        tinctest.logger.info("Test-nfs-19: Test for gpcrondump with options -c, --resyncable, -l,--no-owner, --no-privileges; Restore with -l -d -e")

        self.run_full_backup(dbname = 'bkdb1', option = '-c --rsyncable --no-privileges --no-owner -l -d %s -u %s' % (os.environ.get('MASTER_DATA_DIRECTORY'), self.NFSBACKUPDIR))

        self.get_data_to_file('bkdb1', 'backup1') #Create a copy of all the tables in database before the last backup

        self.run_restore('bkdb1', option = ' -l /tmp/res_log -d %s -e -u %s' % (os.environ.get('MASTER_DATA_DIRECTORY'), self.NFSBACKUPDIR))
        self.validate_restore("restore_dir", 'bkdb1')
        self.compare_table_data('bkdb1')

        self.compare_ao_co_tuple_count('bkdb1')

    def test_nfs_21_full_config_global_objects(self):
        tinctest.logger.info("Test-nfs-20: Test for gpcrondump backup with global objects and config")

        self.run_workload("backup_dir", 'bkdbnfs8')
        self.run_workload("dirty_dir_g1", 'bkdbnfs8')
        self.run_full_backup(dbname = 'bkdbnfs8', option = '-g -G -u %s' % self.NFSBACKUPDIR)

        self.get_data_to_file('bkdbnfs8', 'backup1') #Create a copy of all the tables in database before the last backup

        self.run_workload("dirty_dir_g2", 'bkdbnfs8') # Drop global and dependent objects before restore
        self.run_restore('bkdbnfs8', option = '-G -e -u %s' % self.NFSBACKUPDIR)
        self.validate_restore("restore_dir_g", 'bkdbnfs8')
        self.compare_table_data('bkdbnfs8')
        self.compare_ao_co_tuple_count('bkdbnfs8')

    def test_nfs_22_full_include_multiple_schema(self):
        '''include multiple tables '''
        tinctest.logger.info("Test-nfs-22: Test for exclude multiple tables with -u")

        self.run_workload("backup_dir_simple_db", 'bkdbbb')
        self.run_full_backup(dbname = 'bkdbbb', option = "-s schema_ao -u %s" % self.NFSBACKUPDIR)

        self.get_data_to_file('bkdbbb', 'backup1') #Create a copy of all the tables in database before the last backup

        #truncate other table in the databse before restore it from dump file
        cmdTrunc = 'psql -d bkdbbb -c "truncate table schema_ao.ao_table1;"'
        self.run_command(cmdTrunc)

        #restore from backup
        self.cleanup()
        self.run_restore('bkdbbb', option = ' -s bkdbbb -u %s' % self.NFSBACKUPDIR)
        self.compare_table_data('bkdbbb')
        self.drop_database('bkdbbb')

    @unittest.skipIf(is_earlier_than(version, '4.3.4'), 'Skipped on version before 4.3.4')
    def test_nfs_23_full_exclude_multiple_schema(self):
        '''exclude multiple tables '''
        tinctest.logger.info("Test-nfs-20: Test for exclude multiple tables with -u")

        self.run_workload("backup_dir_simple_db", 'bkdbbb')
        self.run_full_backup(dbname = 'bkdbbb', option = "-S public -u %s" % self.NFSBACKUPDIR)

        self.get_data_to_file('bkdbbb', 'backup1') #Create a copy of all the tables in database before the last backup

        #truncate other table in the databse before restore it from dump file
        cmdTrunc = 'psql -d bkdbbb -c "truncate table schema_ao.ao_table1;"'
        self.run_command(cmdTrunc)

        #restore from backup
        self.cleanup()
        self.run_restore('bkdbbb', option = ' -s bkdbbb -u %s' % self.NFSBACKUPDIR)
        self.compare_table_data('bkdbbb')
        self.drop_database('bkdbbb')

    @unittest.skipIf(is_earlier_than(version, '4.3.4'), 'Skipped on version before 4.3.4')
    def test_nfs_24_full_include_schema_file(self):
        '''include multiple tables '''
        tinctest.logger.info("Test-nfs-20: Test for exclude multiple tables with --nfs")

        self.run_workload("backup_dir_simple_db", 'bkdbbb')
        schema_file = local_path('%s/schema_file' % ('filter_file'))
        self.run_full_backup(dbname = 'bkdbbb', option = "--schema-file %s -u %s" % (schema_file, self.NFSBACKUPDIR))

        self.get_data_to_file('bkdbbb', 'backup1') #Create a copy of all the tables in database before the last backup

        #truncate other table in the databse before restore it from dump file
        cmdTrunc = 'psql -d bkdbbb -c "truncate table schema_ao.ao_table1;"'
        self.run_command(cmdTrunc)

        #restore from backup
        self.cleanup()
        self.run_restore('bkdbbb', option = ' -s bkdbbb -u %s' % (self.NFSBACKUPDIR))
        self.compare_table_data('bkdbbb')
        self.drop_database('bkdbbb')

    @unittest.skipIf(is_earlier_than(version, '4.3.4'), 'Skipped on version before 4.3.4')
    def test_nfs_25_full_exclude_schema_file(self):
        '''exclude multiple tables '''
        tinctest.logger.info("Test-nfs-20: Test for exclude multiple tables with -u")

        self.run_workload("backup_dir_simple_db", 'bkdbbb')
        exclude_schema_file = local_path('%s/exclude_schema_file' % ('filter_file'))
        self.run_full_backup(dbname = 'bkdbbb', option = "--exclude-schema-file %s -u %s" % (exclude_schema_file, self.NFSBACKUPDIR))

        self.get_data_to_file('bkdbbb', 'backup1') #Create a copy of all the tables in database before the last backup

        #truncate other table in the databse before restore it from dump file
        cmdTrunc = 'psql -d bkdbbb -c "truncate table schema_ao.ao_table1;"'
        self.run_command(cmdTrunc)

        #restore from backup
        self.cleanup()
        self.run_restore('bkdbbb', option = ' -s bkdbbb -u %s' % self.NFSBACKUPDIR)
        self.compare_table_data('bkdbbb')
        self.drop_database('bkdbbb')

    @unittest.skipIf(is_earlier_than(version, '4.3.4'), 'Skipped on version before 4.3.4')
    def test_nfs_26_full_select_restore_with_T(self):
        tinctest.logger.info("Test-nfs-4: Test to select restore with nfs backup_dir")
        self.run_workload("backup_dir", 'bkdbnfs1')
        self.run_full_backup(dbname = 'bkdbnfs1', option = '-u', value = self.NFSBACKUPDIR)

        self.get_data_to_file('bkdbnfs1', 'backup1') #Create a copy of all the tables in database before the last backup

        self.run_restore('bkdbnfs1', option = '-T public.ao_table1 -T public.heap_table3 -T public.mixed_part01 -a --truncate -u %s ' % self.NFSBACKUPDIR)
        self.validate_restore("restore_T_with_e", 'bkdbnfs1')

    @unittest.skipIf(is_earlier_than(version, '4.3.6.0'), 'Skipped on version before 4.3.6.0')
    def test_schema_level_restore(self):
        """
        MPP-25845: Test the -T option with schema_name.* to verify all tables under schema_name was restored.
        """

        PSQL.run_sql_command('''DROP SCHEMA IF EXISTS schema_test CASCADE;
                                CREATE SCHEMA schema_test;
                                CREATE TABLE schema_test.t1 (id int);
                                CREATE TABLE schema_test.t2 (id int);
                                INSERT INTO schema_test.t1 select generate_series(1, 10);
                                INSERT INTO schema_test.t2 select generate_series(11, 20);
                                CREATE UNIQUE INDEX t1_idx on schema_test.t1(id);
                                ALTER TABLE schema_test.t1 ADD CONSTRAINT verify CHECK (id > 0);
                                ''', dbname = 'gptest');

        self.run_gpcrondump(dbname='gptest', option = '-x gptest')

        cmd = 'gpdbrestore -t '+ self.full_backup_timestamp + ' -T schema_test.* -a --truncate'
        self.run_command(cmd)

        # total rows will be 10 with truncating
        sql = 'select count(*) from schema_test.t1;'
        total_rows = self.run_SQLQuery(sql, 'gptest')[0][0]
        self.assertEquals(total_rows, 10)

        sql = 'select count(*) from schema_test.t2;'
        total_rows = self.run_SQLQuery(sql, 'gptest')[0][0]
        self.assertEquals(total_rows, 10)

        sql = 'select count(*) from pg_tables where (tablename = \'t1\' or tablename = \'t2\') and schemaname=\'schema_test\';'
        total_tables = self.run_SQLQuery(sql, 'gptest')[0][0]
        self.assertEquals(total_tables, 2)

        sql = 'select count(*) from pg_constraint c, pg_class g where c.conname = \'verify\' and c.conrelid = g.oid and g.relnamespace in (select oid from pg_namespace where nspname = \'schema_test\');'
        found_constraint = self.run_SQLQuery(sql, 'gptest')[0][0]
        self.assertEquals(found_constraint, 1)

        # index restore is currently not supported by -T options
        #sql = 'select count(*) from pg_class c, pg_index i where c.oid = i.indexrelid and c.relname = \'t1_idx\' and c.relnamespace in (select oid from pg_namespace where nspname = \'schema_test\');'
        #found_index = self.run_SQLQuery(sql, 'gptest')[0][0]
        #self.assertEquals(found_index, 1)

    @unittest.skipIf(is_earlier_than(version, '4.3.6.0'), 'Skipped on version before 4.3.6.0')
    def test_exclude_SET_clause_in_function_ddl(self):
        """
        MPP-25781: gpdbrestore fails due to gprestore_filter.py not able to distinguish
        independent SET clause and a SET clause within a function ddl
        Don't change the function definition and indentation below
        """

        status_file_prefix = 'gp_restore_status_-1_1_'
        drop_table = 'DROP TABLE IF EXISTS test_set CASCADE;'
        create_table = 'CREATE TABLE test_set (i int);'
        create_or_replace_function = '''
CREATE OR REPLACE FUNCTION fun_set() RETURNS VOID
AS $$
BEGIN
SET optimizer = 0;
EXECUTE 'INSERT into test_set values (1);';
END;
$$
LANGUAGE plpgsql NO SQL;'''

        PSQL.run_sql_command('%s %s' % (drop_table, create_table), dbname = 'gptest')
        PSQL.run_sql_command(create_or_replace_function, dbname = 'gptest')

        self.run_gpcrondump(dbname='gptest', option = '-x gptest')

        PSQL.run_sql_command(drop_table, dbname = 'gptest')

        cmd = 'gpdbrestore -t '+ self.full_backup_timestamp + ' -T public.test_set -a'
        rc, stdout = self.run_command(cmd)
        self.assertEquals(0, rc)
        self.assertNotIn("[CRITICAL]:-gpdbrestore failed", stdout)

        status_file = self.get_restore_status_file_on_master()
        with open(status_file, 'r') as fd:
            lines = fd.readlines()
            self.assertNotIn('syntax error at or near', lines)

    @unittest.skipIf(is_earlier_than(version, '4.3.6.2'), 'Skipped on version before 4.3.6.2')
    def test_alter_set_schema_for_subpartition(self):
        """
        MPP-25549: gpcrondump should determine if required to set the schema of
        subpartition tables

        This test fails if subpartition tables not being created by restore
        """

        drop_schema = 'DROP SCHEMA IF EXISTS testschema1 CASCADE; DROP SCHEMA IF EXISTS testschema2 CASCADE;'
        create_schema = 'CREATE SCHEMA testschema1; CREATE SCHEMA testschema2;'
        create_partition_table = '''
                                 CREATE TABLE testschema1.parttest(i int, j int) distributed by (i)
                                 partition by range (j)
                                 (start (1) end (5) every (1), default partition extra);
                                 '''
        insert_data = 'INSERT INTO testschema1.parttest SELECT i, i FROM generate_series(1, 15) i;'
        alter_partition = 'ALTER TABLE testschema1.parttest SET SCHEMA testschema2;'
        validate_count = 'SELECT * FROM testschema2.parttest;'
        PSQL.run_sql_command('%s %s' % (drop_schema, create_schema), dbname = 'gptest')
        PSQL.run_sql_command(create_partition_table, dbname = 'gptest')
        PSQL.run_sql_command(insert_data, dbname = 'gptest')
        PSQL.run_sql_command(alter_partition, dbname = 'gptest')

        self.run_gpcrondump(dbname='gptest', option = '-x gptest')

        PSQL.run_sql_command(drop_schema, dbname = 'gptest')

        cmd = 'gpdbrestore -t '+ self.full_backup_timestamp + ' -a'
        rc, stdout = self.run_command(cmd)
        self.assertEquals(0, rc)

        rows = len(self.run_SQLQuery(validate_count, 'gptest'))
        self.assertEquals(rows, 15)

