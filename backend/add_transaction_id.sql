-- Add external transaction id column (unique id from statement)
ALTER TABLE transactions
ADD COLUMN IF NOT EXISTS transaction_id VARCHAR(100);

-- Enforce uniqueness only for non-null values
CREATE UNIQUE INDEX IF NOT EXISTS ix_transactions_transaction_id
ON transactions (transaction_id)
WHERE transaction_id IS NOT NULL;
