-- @gucs gp_create_table_random_default_distribution=off

Alter database dsp_db set gp_default_storage_options='appendonly=true, orientation=column, blocksize=65536, checksum=true, compresslevel=4, compresstype=rle_type';

\c dsp_db
show gp_default_storage_options;

Drop table if exists dsp_db_t1;
Create table dsp_db_t1 (i int, j int);
Insert into  dsp_db_t1 select i, i+1 from generate_series(1,10) i;
Select count(*) from  dsp_db_t1;

\d+ dsp_db_t1

select relstorage, reloptions,compresstype,columnstore,compresslevel,columnstore,checksum from pg_class c , pg_appendonly a where c.relfilenode=a.relid and c.relname='dsp_db_t1';

Drop table if exists dsp_db_t2;
Create table dsp_db_t2 (i int, j int) with(appendonly=false);
Insert into  dsp_db_t2 select i, i+1 from generate_series(1,10) i;
Select count(*) from  dsp_db_t2;

\d+ dsp_db_t2

select relname, relstorage, reloptions from pg_class where relname='dsp_db_t2';

Drop table if exists dsp_db_t3;
Create table dsp_db_t3 (i int, j int) with(appendonly=true, orientation=row, compresstype=zlib);
Insert into  dsp_db_t3 select i, i+1 from generate_series(1,10) i;
Select count(*) from  dsp_db_t3;

\d+ dsp_db_t3

select relstorage, reloptions,compresstype,columnstore,compresslevel,columnstore,checksum from pg_class c , pg_appendonly a where c.relfilenode=a.relid and c.relname='dsp_db_t3';

 
