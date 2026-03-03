-- Add transaction_type column to transactions table
ALTER TABLE transactions 
ADD COLUMN IF NOT EXISTS transaction_type VARCHAR(10) DEFAULT 'DEBIT';

-- Update existing records to have DEBIT as default
UPDATE transactions 
SET transaction_type = 'DEBIT' 
WHERE transaction_type IS NULL;
