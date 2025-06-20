SELECT * FROM prediction_data.predictions;
ALTER TABLE predictions ADD COLUMN email VARCHAR(255) NOT NULL;
