# -*- coding: UTF-8 -*-

INSERT_QUERY = """
PRAGMA TablePathPrefix("{table_prefix}");

DECLARE $seriesId AS Uint64;
DECLARE $title AS Utf8;
DECLARE $seriesInfo AS Utf8;
DECLARE $releaseDate AS Uint32;
DECLARE $views AS Uint64;

-- Simulate a DESC index by inverting views using max(uint64)-views
$maxUint64 = 0xffffffffffffffff;
$revViews = $maxUint64 - $views;

INSERT INTO series (series_id, title, series_info, release_date, views)
VALUES ($seriesId, $title, $seriesInfo, $releaseDate, $views);

-- Insert above already verified series_id is unique, so it is safe to use upsert
UPSERT INTO series_rev_views (rev_views, series_id)
VALUES ($revViews, $seriesId);
"""

DELETE_QUERY = """
PRAGMA TablePathPrefix("{table_prefix}");

DECLARE $seriesId AS Uint64;

$maxUint64 = 0xffffffffffffffff;

$data = (
    SELECT series_id, ($maxUint64 - views) AS rev_views
    FROM [series]
    WHERE series_id = $seriesId
);

DELETE FROM series
ON SELECT series_id FROM $data;

DELETE FROM series_rev_views
ON SELECT rev_views, series_id FROM $data;

SELECT COUNT(*) AS cnt FROM $data;
"""

UPDATE_VIEWS_QUERY = """
PRAGMA TablePathPrefix("{table_prefix}");

DECLARE $seriesId AS Uint64;
DECLARE $newViews AS Uint64;

$maxUint64 = 0xffffffffffffffff;
$newRevViews = $maxUint64 - $newViews;

$data = (
    SELECT series_id, ($maxUint64 - views) AS old_rev_views
    FROM series
    WHERE series_id = $seriesId
);

UPSERT INTO series
SELECT series_id, $newViews AS views FROM $data;

DELETE FROM series_rev_views
ON SELECT old_rev_views AS rev_views, series_id FROM $data;

UPSERT INTO series_rev_views
SELECT $newRevViews AS rev_views, series_id FROM $data;

SELECT COUNT(*) AS cnt FROM $data;
"""

FIND_BY_ID_QUERY = """
PRAGMA TablePathPrefix("{table_prefix}");

DECLARE $seriesId AS Uint64;

SELECT series_id, title, series_info, release_date, views
FROM series
WHERE series_id = $seriesId;
"""

FIND_ALL_QUERY = """
PRAGMA TablePathPrefix("{table_prefix}");

DECLARE $limit AS Uint64;

SELECT series_id, title, series_info, release_date, views
FROM series
ORDER BY series_id
LIMIT $limit;
"""

FIND_ALL_NEXT_QUERY = """
PRAGMA TablePathPrefix("{table_prefix}");

DECLARE $limit AS Uint64;
DECLARE $lastSeriesId AS Uint64;

SELECT series_id, title, series_info, release_date, views
FROM series
WHERE series_id > $lastSeriesId
ORDER BY series_id
LIMIT $limit;
"""

FIND_MOST_VIEWED_QUERY = """
PRAGMA TablePathPrefix("{table_prefix}");

DECLARE $limit AS Uint64;

$filter = (
    SELECT rev_views, series_id
    FROM series_rev_views
    ORDER BY rev_views, series_id
    LIMIT $limit
);

SELECT t2.series_id AS series_id, title, series_info, release_date, views
FROM $filter AS t1
INNER JOIN series AS t2 USING (series_id)
ORDER BY views DESC, series_id ASC;
"""

FIND_MOST_VIEWED_NEXT_QUERY = """
PRAGMA TablePathPrefix("{table_prefix}");

DECLARE $limit AS Uint64;
DECLARE $lastSeriesId AS Uint64;
DECLARE $lastViews AS Uint64;

$maxUint64 = 0xffffffffffffffff;
$lastRevViews = $maxUint64 - $lastViews;

$filterRaw = (
    SELECT rev_views, series_id
    FROM series_rev_views
    WHERE rev_views = $lastRevViews AND series_id > $lastSeriesId
    ORDER BY rev_views, series_id
    LIMIT $limit
    UNION ALL
    SELECT rev_views, series_id
    FROM series_rev_views
    WHERE rev_views > $lastRevViews
    ORDER BY rev_views, series_id
    LIMIT $limit
);

-- $filterRaw may have more than $limit rows
$filter = (
    SELECT rev_views, series_id
    FROM $filterRaw
    ORDER BY rev_views, series_id
    LIMIT $limit
);

SELECT t2.series_id AS series_id, title, series_info, release_date, views
FROM $filter AS t1
INNER JOIN series AS t2 USING (series_id)
ORDER BY views DESC, series_id ASC;
"""
