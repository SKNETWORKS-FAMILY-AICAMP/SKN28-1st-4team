CREATE TABLE IF NOT EXISTS connectivity_check (
    id INT NOT NULL AUTO_INCREMENT,
    label VARCHAR(64) NOT NULL,
    PRIMARY KEY (id)
);

INSERT INTO connectivity_check (label)
VALUES ('test_db_docker');
