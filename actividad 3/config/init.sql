CREATE TABLE IF NOT EXISTS inventory(id integer PRIMARY KEY, name text NOT NULL, quantity integer CHECK(quantity >= 0));
INSERT INTO inventory VALUES (1, 'OTel Collector', 3), (2, 'Observable service', 3) ON CONFLICT DO NOTHING;
