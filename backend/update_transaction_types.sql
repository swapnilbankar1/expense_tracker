-- Update NULL transaction_type values to DEBIT
UPDATE transactions 
SET transaction_type = 'DEBIT' 
WHERE transaction_type IS NULL;

-- Check the results
SELECT transaction_type, COUNT(*) as count 
FROM transactions 
GROUP BY transaction_type;
