-- Academic Artifact Research Database Schema (PostgreSQL)
-- Test Cases (Verification Queries)

-- =================================================================================
-- 3. Test Cases (Verification Queries)
-- =================================================================================

-- 3.1 Map Query: Select Object Name, Lat, Long for the map UI
SELECT object_type, inventory_number, latitude, longitude 
FROM objects 
WHERE latitude IS NOT NULL AND longitude IS NOT NULL;

-- 3.2 Timeline Query: Find objects existing between year 300 and 400
SELECT * 
FROM objects 
WHERE date_start <= 400 AND date_end >= 300;

-- 3.3 Complex Filter: Find images tagged with "Sawing" OR "Skilled Worker"
SELECT DISTINCT i.file_url, o.object_type, t.tag_name
FROM images i
JOIN objects o ON i.object_id = o.id
JOIN image_tags it ON i.id = it.image_id
JOIN tags t ON it.tag_id = t.id
WHERE t.tag_name IN ('Sawing', 'Skilled Worker');
