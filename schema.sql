-- RainFall Predict AI — MySQL schema
-- Run:  mysql -u root -p < schema.sql

CREATE DATABASE IF NOT EXISTS rainfall_db
    CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

USE rainfall_db;

CREATE TABLE IF NOT EXISTS predictions (
    id                  INT AUTO_INCREMENT PRIMARY KEY,
    created_at          DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,

    -- raw meteorological inputs
    day                 SMALLINT NOT NULL,
    pressure            FLOAT NOT NULL,
    maxtemp             FLOAT NOT NULL,
    temparature         FLOAT NOT NULL,
    mintemp             FLOAT NOT NULL,
    dewpoint            FLOAT NOT NULL,
    humidity            FLOAT NOT NULL,
    cloud               FLOAT NOT NULL,
    sunshine            FLOAT NOT NULL,
    winddirection       FLOAT NOT NULL,
    windspeed           FLOAT NOT NULL,

    -- model output
    prediction_label    VARCHAR(16) NOT NULL,      -- 'Rain' or 'No Rain'
    rain_probability    FLOAT NOT NULL,             -- 0..1

    -- bookkeeping
    client_ip           VARCHAR(64)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE INDEX idx_predictions_created_at ON predictions (created_at);
