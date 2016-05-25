create table tbl1_mpp_11257 (
  id            bigint,
 partition_key timestamp,
 distribution_key bigint not null,
 constraint pk_tbl1_mpp_11257 primary key (distribution_key, partition_key, id)
 )
 distributed by (distribution_key)
 partition by range (partition_key)
 (
 default partition default_partition,
 partition d_2010_09_28 start (date '2010-09-28') end (date '2010-09-29')
 );

select localoid, relname, attrnums as distribution_attributes from gp_distribution_policy p, pg_class c where p.localoid = c.oid and relname like 'tbl1_mpp_11257%' order by p.localoid;

alter table tbl1_mpp_11257 split default partition
start (date '2010-09-27' )
end (date '2010-09-28')
into (partition d_2010_09_27, partition default_partition);
select localoid, relname, attrnums as distribution_attributes from gp_distribution_policy p, pg_class c where p.localoid = c.oid and relname like 'tbl1_mpp_11257%' order by p.localoid;

