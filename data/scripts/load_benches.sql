-- Create table for City of Melbourne public benches and picnic settings
CREATE TABLE IF NOT EXISTS public_benches (
    id          SERIAL PRIMARY KEY,
    description TEXT,
    type        VARCHAR(50),       -- 'Seat' or 'Picnic Setting'
    model       VARCHAR(255),
    location    TEXT,
    condition   NUMERIC(4,2),      -- 1.0 (poor) to 5.0 (excellent)
    latitude    DOUBLE PRECISION NOT NULL,
    longitude   DOUBLE PRECISION NOT NULL
);

-- Spatial index for fast nearby queries
CREATE INDEX IF NOT EXISTS idx_benches_lat_lon
    ON public_benches (latitude, longitude);

-- Optional: PostGIS geography column for proper distance queries
-- (requires PostGIS extension)
-- ALTER TABLE public_benches ADD COLUMN geom GEOGRAPHY(POINT, 4326);
-- UPDATE public_benches SET geom = ST_SetSRID(ST_MakePoint(longitude, latitude), 4326);
-- CREATE INDEX idx_benches_geom ON public_benches USING GIST(geom);
