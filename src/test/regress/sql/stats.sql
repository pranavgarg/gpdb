--
-- Test Statistics Collector
--
-- Must be run after tenk2 has been created (by create_table),
-- populated (by create_misc) and indexed (by create_index).
--

-- conditio sine qua non
SHOW stats_start_collector;  -- must be on

-- wait to let any prior tests finish dumping out stats;
-- else our messages might get lost due to contention
SELECT pg_sleep(2.0);

-- save counters
CREATE TEMP TABLE prevstats AS
SELECT t.seq_scan, t.seq_tup_read, t.idx_scan, t.idx_tup_fetch,
       (b.heap_blks_read + b.heap_blks_hit) AS heap_blks,
       (b.idx_blks_read + b.idx_blks_hit) AS idx_blks
  FROM pg_catalog.pg_stat_user_tables AS t,
       pg_catalog.pg_statio_user_tables AS b
 WHERE t.relname='tenk2' AND b.relname='tenk2';

-- enable statistics
SET stats_block_level = on;
SET stats_row_level = on;

-- do a seqscan
SELECT count(*) FROM tenk2;
-- do an indexscan
SELECT count(*) FROM tenk2 WHERE unique1 = 1;

-- All of the thrashing here is to wait for the stats collector to update,
-- without waiting too long (in fact, we'd like to try to measure how long
-- we wait).  Watching for change in the stats themselves wouldn't work
-- because the backend only reads them once per transaction.  The stats file
-- mod timestamp isn't too helpful because it may have resolution of only one
-- second, or even worse.  So, we touch a new table and then watch for change
-- in the size of the stats file.  Ugh.

-- save current stats-file size
CREATE TEMP TABLE prevfilesize AS
  SELECT size FROM pg_stat_file('global/pgstat.stat');

-- make and touch a previously nonexistent table
CREATE TABLE stats_hack (f1 int);
SELECT * FROM stats_hack;

-- wait for stats collector to update
create function wait_for_stats() returns void as $$
declare
  start_time timestamptz := clock_timestamp();
  oldsize bigint;
  newsize bigint;
begin
  -- fetch previous stats-file size
  select size into oldsize from prevfilesize;

  -- we don't want to wait forever; loop will exit after 30 seconds
  for i in 1 .. 300 loop

    -- look for update of stats file
    select size into newsize from pg_stat_file('global/pgstat.stat');

    exit when newsize != oldsize;

    -- wait a little
    perform pg_sleep(0.1);

  end loop;

  -- report time waited in postmaster log (where it won't change test output)
  raise log 'wait_for_stats delayed % seconds',
    extract(epoch from clock_timestamp() - start_time);
end
$$ language plpgsql;

SELECT wait_for_stats();

DROP TABLE stats_hack;

-- check effects
SELECT st.seq_scan >= pr.seq_scan + 1,
       st.seq_tup_read >= pr.seq_tup_read + cl.reltuples,
       st.idx_scan >= pr.idx_scan + 1,
       st.idx_tup_fetch >= pr.idx_tup_fetch + 1
  FROM pg_stat_user_tables AS st, pg_class AS cl, prevstats AS pr
 WHERE st.relname='tenk2' AND cl.relname='tenk2';
SELECT st.heap_blks_read + st.heap_blks_hit >= pr.heap_blks + cl.relpages,
       st.idx_blks_read + st.idx_blks_hit >= pr.idx_blks + 1
  FROM pg_statio_user_tables AS st, pg_class AS cl, prevstats AS pr
 WHERE st.relname='tenk2' AND cl.relname='tenk2';

-- End of Stats Test
