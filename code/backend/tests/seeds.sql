-- Academic Artifact Research Database Schema (PostgreSQL)
-- Test Data (INSERT Statements)

-- =================================================================================
-- 2. Test Data (INSERT Statements)
-- =================================================================================

-- 2.1 Sources
INSERT INTO sources (citation_text) VALUES 
('Smith, John. "Ancient Artifacts of Rome." Journal of Archaeology, 2023.'),
('Doe, Jane. "Digital Imaging in Archaeology." Tech & History, 2024.');

-- 2.2 Objects (Fuzzy Dates & Map Coordinates)
INSERT INTO objects (
    object_type, material, findspot, latitude, longitude, 
    inventory_number, date_display, date_start, date_end, 
    width, height, depth
) VALUES 
-- Object 1: Fuzzy Date (c. 4th Century)
('Amphora', 'Terracotta', 'Rome', 41.9028, 12.4964, 
 'INV-2024-001', 'c. 4th Century AD', 301, 400, 
 30.5, 60.0, 30.5),

-- Object 2: Distinct Map Coordinates (Athens)
('Coin', 'Silver', 'Athens', 37.9838, 23.7275, 
 'INV-2024-002', 'c. 450 BC', -450, -440, 
 2.5, 0.2, 2.5);

-- 2.3 Images
INSERT INTO images (object_id, source_id, image_type, view_type, file_url) VALUES 
(1, 1, 'Photograph', 'Front', 'https://s3.amazonaws.com/bucket/obj1_front.jpg'),
(1, 2, 'Drawing', 'Profile', 'https://s3.amazonaws.com/bucket/obj1_profile.png'),
(2, 1, 'Photograph', 'Obverse', 'https://s3.amazonaws.com/bucket/obj2_obverse.jpg');

-- 2.4 Tags & Junctions
INSERT INTO tags (tag_name) VALUES ('Sawing'), ('Skilled Worker'), ('Pottery'), ('Numismatics');

INSERT INTO image_tags (image_id, tag_id) VALUES 
(1, 1), -- Image 1 tagged 'Sawing'
(1, 2), -- Image 1 tagged 'Skilled Worker'
(2, 2); -- Image 2 tagged 'Skilled Worker'
