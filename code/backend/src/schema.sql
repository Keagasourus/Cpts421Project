-- Academic Artifact Research Database Schema (PostgreSQL)
-- Table Definitions and DDL

-- =================================================================================
-- 1. Table Definitions
-- =================================================================================

-- 1.1 SOURCES
-- Represents bibliographic references or origins of data/images.
CREATE TABLE sources (
    id SERIAL PRIMARY KEY,
    citation_text TEXT NOT NULL -- Full citation in Chicago style
);

-- 1.2 OBJECTS
-- Represents physical artifacts.
-- Includes core attributes, fuzzy dating logic, and map coordinates.
CREATE TABLE objects (
    id SERIAL PRIMARY KEY,
    object_type VARCHAR(255) NOT NULL, -- e.g., 'Vase', 'Coin'
    material VARCHAR(255),             -- e.g., 'Gold', 'Clay'
    findspot VARCHAR(255),             -- Original location of discovery
    latitude DECIMAL(9, 6),            -- For Map UI: -90.0 to 90.0
    longitude DECIMAL(9, 6),           -- For Map UI: -180.0 to 180.0
    date_discovered DATE,              -- Precise date of discovery (if known)
    inventory_number VARCHAR(100) UNIQUE, -- Museum/Collection ID
    
    -- Fuzzy Dates System (3-Column Approach)
    date_display VARCHAR(255) NOT NULL,-- Display string (e.g., "c. 350-400 AD")
    date_start INTEGER NOT NULL,       -- Start year (Inclusive)
    date_end INTEGER NOT NULL,         -- End year (Inclusive)
    
    -- Dimensions
    width DECIMAL(10, 2),
    height DECIMAL(10, 2),
    depth DECIMAL(10, 2),
    unit VARCHAR(20) DEFAULT 'cm'
);

-- Indexes for performance on common filters
CREATE INDEX idx_objects_date_start ON objects(date_start);
CREATE INDEX idx_objects_date_end ON objects(date_end);
CREATE INDEX idx_objects_type ON objects(object_type);

-- 1.3 IMAGES
-- Represents digital files linked to objects.
-- Note: Files are stored externally (e.g., S3), only URLs are stored here.
CREATE TABLE images (
    id SERIAL PRIMARY KEY,
    object_id INTEGER REFERENCES objects(id) ON DELETE CASCADE,
    source_id INTEGER REFERENCES sources(id) ON DELETE SET NULL,
    image_type VARCHAR(50),  -- e.g., 'Photograph', 'Drawing', 'Scan'
    view_type VARCHAR(50),   -- e.g., 'Front', 'Back', 'Detail'
    file_url TEXT NOT NULL   -- Link to external storage (S3)
);

-- 1.4 TAGS
-- A controlled vocabulary for categorizing images/objects.
CREATE TABLE tags (
    id SERIAL PRIMARY KEY,
    tag_name VARCHAR(100) UNIQUE NOT NULL
);

-- 1.5 IMAGE_TAGS
-- Many-to-Many relationship between Images and Tags.
CREATE TABLE image_tags (
    image_id INTEGER REFERENCES images(id) ON DELETE CASCADE,
    tag_id INTEGER REFERENCES tags(id) ON DELETE CASCADE,
    PRIMARY KEY (image_id, tag_id)
);

CREATE INDEX idx_image_tags_tag_id ON image_tags(tag_id);
