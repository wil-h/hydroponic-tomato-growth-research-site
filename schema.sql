CREATE TABLE IF NOT EXISTS LI (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    created TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PN TEXT,
    EC TEXT,
    height TEXT,
    leafSize TEXT,
    deficiencies TEXT
);

CREATE TABLE IF NOT EXISTS PH (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    created TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PN TEXT,
    EC TEXT,
    height TEXT,
    leafSize TEXT,
    deficiencies TEXT
);

CREATE TABLE IF NOT EXISTS CalMag (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    created TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PN TEXT,
    EC TEXT,
    height TEXT,
    leafSize TEXT,
    deficiencies TEXT
);

CREATE TABLE IF NOT EXISTS Control (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    created TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PN TEXT,
    EC TEXT,
    height TEXT,
    leafSize TEXT,
    deficiencies TEXT
);
