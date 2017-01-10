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
