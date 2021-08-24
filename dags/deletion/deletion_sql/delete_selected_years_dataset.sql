--------------------------------------
-- SQL to Delete datasets from product in year (Y1, Y2)
--------------------------------------
SET search_path = 'agdc';
-----------------------------------
-- test
-----------------------------------
select * from agdc.dataset;

-------------------------------------
-- Matching dataset location and delete
-------------------------------------
-- SELECT Count(*)
-- FROM   dataset_location dl
-- WHERE  dl.dataset_ref in
--        (
--             SELECT ds.id
--             FROM   dataset ds
--             WHERE  ds.dataset_type_ref = (SELECT id
--                                         FROM   dataset_type dt
--                                         WHERE  dt.NAME = 'ls5_fc_albers')
--             AND ( ds.metadata -> 'extent' ->> 'center_dt' LIKE '1986%'
--                     OR ds.metadata -> 'extent' ->> 'center_dt' LIKE '1995%'
--                     OR ds.metadata -> 'extent' ->> 'center_dt' LIKE '1997%'
--                     OR ds.metadata -> 'extent' ->> 'center_dt' LIKE '1999%' )
--         );

-- DELETE
-- FROM   dataset_location dl
-- WHERE  dl.dataset_ref in
--        (
--             SELECT ds.id
--             FROM   dataset ds
--             WHERE  ds.dataset_type_ref = (SELECT id
--                                         FROM   dataset_type dt
--                                         WHERE  dt.NAME = 'ls5_fc_albers')
--             AND ( ds.metadata -> 'extent' ->> 'center_dt' LIKE '1986%'
--                     OR ds.metadata -> 'extent' ->> 'center_dt' LIKE '1995%'
--                     OR ds.metadata -> 'extent' ->> 'center_dt' LIKE '1997%'
--                     OR ds.metadata -> 'extent' ->> 'center_dt' LIKE '1999%' )
--         );


-- -- -------------------------------------
-- -- -- Check and delete lineage
-- -- -------------------------------------
-- SELECT Count(*)
-- FROM   dataset_source ds_source
-- WHERE  ds_source.source_dataset_ref in
--        (
--             SELECT ds.id
--             FROM   dataset ds
--             WHERE  ds.dataset_type_ref = (SELECT id
--                                         FROM   dataset_type dt
--                                         WHERE  dt.NAME = 'ls5_fc_albers')
--             AND ( ds.metadata -> 'extent' ->> 'center_dt' LIKE '1986%'
--                     OR ds.metadata -> 'extent' ->> 'center_dt' LIKE '1995%'
--                     OR ds.metadata -> 'extent' ->> 'center_dt' LIKE '1997%'
--                     OR ds.metadata -> 'extent' ->> 'center_dt' LIKE '1999%' )
--                 );

-- DELETE
-- FROM   dataset_source ds_source
-- WHERE  ds_source.source_dataset_ref in
--        (
--             SELECT ds.id
--             FROM   dataset ds
--             WHERE  ds.dataset_type_ref = (SELECT id
--                                         FROM   dataset_type dt
--                                         WHERE  dt.NAME = 'ls5_fc_albers')
--             AND ( ds.metadata -> 'extent' ->> 'center_dt' LIKE '1986%'
--                     OR ds.metadata -> 'extent' ->> 'center_dt' LIKE '1995%'
--                     OR ds.metadata -> 'extent' ->> 'center_dt' LIKE '1997%'
--                     OR ds.metadata -> 'extent' ->> 'center_dt' LIKE '1999%' )
--                 );
-- -------------------------------------
-- -- finally delete datasets
-- -------------------------------------
-- SELECT
--    count(*)
-- FROM
--    dataset ds
-- WHERE
--    ds.dataset_type_ref =
--    ( -- limit to the product name
--       SELECT
--          id
--       FROM
--          dataset_type dt
--       WHERE
--          dt.NAME = 'ls5_fc_albers'
--    )
--    AND
--    ( -- limit to the years for bad datasets
-- (ds.metadata -> 'extent' ->> 'center_dt' LIKE '1986%'
--       AND ds.metadata -> 'extent' ->> 'from_dt' LIKE '1986%'
--       AND ds.metadata -> 'extent' ->> 'to_dt' LIKE '1986%')
--       OR
--       (
--          ds.metadata -> 'extent' ->> 'center_dt' LIKE '1995%'
--          AND ds.metadata -> 'extent' ->> 'from_dt' LIKE '1995%'
--          AND ds.metadata -> 'extent' ->> 'to_dt' LIKE '1995%'
--       )
--       OR
--       (
--          ds.metadata -> 'extent' ->> 'center_dt' LIKE '1997%'
--          AND ds.metadata -> 'extent' ->> 'from_dt' LIKE '1997%'
--          AND ds.metadata -> 'extent' ->> 'to_dt' LIKE '1997%'
--       )
--       OR
--       (
--          ds.metadata -> 'extent' ->> 'center_dt' LIKE '1999%'
--          AND ds.metadata -> 'extent' ->> 'from_dt' LIKE '1999%'
--          AND ds.metadata -> 'extent' ->> 'to_dt' LIKE '1999%'
--       )
--    )
-- ;

-- DELETE
-- FROM
--    dataset ds
-- WHERE
--    ds.dataset_type_ref =
--    ( -- limit to the product name
--       SELECT
--          id
--       FROM
--          dataset_type dt
--       WHERE
--          dt.NAME = 'ls5_fc_albers'
--    )
--    AND
--    ( -- limit to the years for bad datasets
-- (ds.metadata -> 'extent' ->> 'center_dt' LIKE '1986%'
--       AND ds.metadata -> 'extent' ->> 'from_dt' LIKE '1986%'
--       AND ds.metadata -> 'extent' ->> 'to_dt' LIKE '1986%')
--       OR
--       (
--          ds.metadata -> 'extent' ->> 'center_dt' LIKE '1995%'
--          AND ds.metadata -> 'extent' ->> 'from_dt' LIKE '1995%'
--          AND ds.metadata -> 'extent' ->> 'to_dt' LIKE '1995%'
--       )
--       OR
--       (
--          ds.metadata -> 'extent' ->> 'center_dt' LIKE '1997%'
--          AND ds.metadata -> 'extent' ->> 'from_dt' LIKE '1997%'
--          AND ds.metadata -> 'extent' ->> 'to_dt' LIKE '1997%'
--       )
--       OR
--       (
--          ds.metadata -> 'extent' ->> 'center_dt' LIKE '1999%'
--          AND ds.metadata -> 'extent' ->> 'from_dt' LIKE '1999%'
--          AND ds.metadata -> 'extent' ->> 'to_dt' LIKE '1999%'
--       )
--    )
-- ;

-- -------------------------------------
-- -- Check and delete lineage
-- -------------------------------------
-- SELECT *
-- FROM   dataset_source ds_source
-- WHERE  ds_source.dataset_ref not in (
--     select ds.id
--     from dataset ds
-- )
-- limit 1;

-- SELECT *
-- FROM   dataset_source ds_source
-- WHERE  ds_source.source_dataset_ref not in (
--     select ds.id
--     from dataset ds
-- )
-- limit 1;

-- DELETE
-- FROM   dataset_source ds_source
-- WHERE  ds_source.source_dataset_ref in
--        (
--             SELECT ds.id
--             FROM   dataset ds
--             WHERE  ds.dataset_type_ref = (SELECT id
--                                         FROM   dataset_type dt
--                                         WHERE  dt.NAME = 'ls5_fc_albers')
--             AND ( ds.metadata -> 'extent' ->> 'center_dt' LIKE '1986%'
--                     OR ds.metadata -> 'extent' ->> 'center_dt' LIKE '1995%'
--                     OR ds.metadata -> 'extent' ->> 'center_dt' LIKE '1997%'
--                     OR ds.metadata -> 'extent' ->> 'center_dt' LIKE '1999%' )
--                 );