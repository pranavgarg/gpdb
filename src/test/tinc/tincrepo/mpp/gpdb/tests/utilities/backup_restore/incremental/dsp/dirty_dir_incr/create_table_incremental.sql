-- @gucs gp_create_table_random_default_distribution=off

Alter database dsp_db set gp_default_storage_options="appendonly=false";

\c dsp_db
show gp_default_storage_options;

SET gp_default_storage_options='appendonly=true,checksum=false, compresslevel=1, compresstype=quicklz'; 
show gp_default_storage_options;

Drop table if exists dsp_db_t4;
Create table dsp_db_t4 (i int, j int);
Insert into  dsp_db_t4 select i, i+1 from generate_series(1,10) i;
Select count(*) from  dsp_db_t4;

\d+ dsp_db_t4

select relstorage, reloptions,compresstype,columnstore,compresslevel,columnstore,checksum from pg_class c , pg_appendonly a where c.relfilenode=a.relid and c.relname='dsp_db_t4';

Drop table if exists dsp_db_t5;
Create table dsp_db_t5 (i int, j int) with(appendonly=false);
Insert into  dsp_db_t5 select i, i+1 from generate_series(1,10) i;
Select count(*) from  dsp_db_t5;

\d+ dsp_db_t5

select relname, relstorage, reloptions from pg_class where relname='dsp_db_t5';

Drop table if exists dsp_db_t6;
Create table dsp_db_t6 (i int, j int) with(appendonly=true, orientation=column, compresstype=rle_type, checksum=true);
Insert into  dsp_db_t6 select i, i+1 from generate_series(1,10) i;
Select count(*) from  dsp_db_t6;

\d+ dsp_db_t6

select relstorage, reloptions,compresstype,columnstore,compresslevel,columnstore,checksum from pg_class c , pg_appendonly a where c.relfilenode=a.relid and c.relname='dsp_db_t6';

 
SET gp_default_storage_options='appendonly=false';

show gp_default_storage_options;

Drop table if exists dsp_hp_t1;
Create table dsp_hp_t1 (i int, j int);
Insert into  dsp_hp_t1 select i, i+1 from generate_series(1,10) i;
Select count(*) from  dsp_hp_t1;

\d+ dsp_hp_t1

select relname, relstorage, reloptions from pg_class where relname='dsp_hp_t1';


