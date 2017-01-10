-- @gucs gp_create_table_random_default_distribution=off
-- validate the sqls's state after restore

\c dsp_db

show gp_default_storage_options;

\d+ dsp_db_t1

select relstorage, reloptions,compresstype,columnstore,compresslevel,columnstore,checksum from pg_class c , pg_appendonly a where c.relfilenode=a.relid and c.relname='dsp_db_t1';

\d+ dsp_db_t2

select relname, relstorage, reloptions from pg_class where relname='dsp_db_t2';

\d+ dsp_db_t3

select relstorage, reloptions,compresstype,columnstore,compresslevel,columnstore,checksum from pg_class c , pg_appendonly a where c.relfilenode=a.relid and c.relname='dsp_db_t3';

\d+ dsp_db_t4

select relstorage, reloptions,compresstype,columnstore,compresslevel,columnstore,checksum from pg_class c , pg_appendonly a where c.relfilenode=a.relid and c.relname='dsp_db_t4';

\d+ dsp_db_t5

select relname, relstorage, reloptions from pg_class where relname='dsp_db_t5';

\d+ dsp_db_t6

select relstorage, reloptions,compresstype,columnstore,compresslevel,columnstore,checksum from pg_class c , pg_appendonly a where c.relfilenode=a.relid and c.relname='dsp_db_t6';

\d+ dsp_hp_t1

select relname, relstorage, reloptions from pg_class where relname='dsp_hp_t1';

select count(*) from dsp_db_t1;
select count(*) from dsp_db_t2;
select count(*) from dsp_db_t3;
select count(*) from dsp_db_t4;
select count(*) from dsp_db_t5;
select count(*) from dsp_db_t6;
select count(*) from dsp_hp_t1;
