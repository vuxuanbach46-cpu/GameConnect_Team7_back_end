-- Run once for existing databases; fresh databases get this column from the model.
ALTER TABLE users
    ADD COLUMN locked_reason VARCHAR(500) NULL AFTER locked_until;
