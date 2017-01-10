-- @gucs gp_create_table_random_default_distribution=off
-- Validate the roleconfig after restore

select rolname, rolconfig from pg_roles where rolname='dsp_role';

-- validate the tables's state after restore

\c dsp_db dsp_role

show gp_default_storage_options;

\d+ dsp_db_t1

select relstorage, reloptions,compresstype,columnstore,compresslevel,columnstore,checksum from pg_class c , pg_appendonly a where c.relfilenode=a.relid and c.relname='dsp_db_t1';

\d+ dsp_db_t2

select relname, relstorage, reloptions from pg_class where relname='dsp_db_t2';

\d+ dsp_db_t3

select relstorage, reloptions,compresstype,columnstore,compresslevel,columnstore,checksum from pg_class c , pg_appendonly a where c.relfilenode=a.relid and c.relname='dsp_db_t3';

\d+ dsp_db_t4

select relstorage, reloptions,compresstype,columnstore,compresslevel,columnstore,checksum from pg_class c , pg_appendonly a where c.relfilenode=a.relid and c.relname='dsp_db_t4';

