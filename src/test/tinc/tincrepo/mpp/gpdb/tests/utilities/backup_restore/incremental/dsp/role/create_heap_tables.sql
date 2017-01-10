-- @gucs gp_create_table_random_default_distribution=off

Alter database dsp_db set gp_default_storage_options='appendonly=false';
Alter role dsp_role set gp_default_storage_options='appendonly=false';

\c dsp_db dsp_role
show gp_default_storage_options;

Drop table if exists dsp_hp_t1;
Create table dsp_hp_t1 (i int, j int);
Insert into  dsp_hp_t1 select i, i+1 from generate_series(1,10) i;
Select count(*) from  dsp_hp_t1;

\d+ dsp_hp_t1

select relname, relstorage, reloptions from pg_class where relname='dsp_hp_t1';

 
