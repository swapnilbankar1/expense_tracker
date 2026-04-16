# PhonePe PDF Extraction Rules

Use these rules to reliably parse PhonePe transaction statements (especially when merchant names wrap to the next line).

## 1) Detect transaction header row
A transaction starts on a line matching:

- `MMM DD, YYYY <details> <DEBIT|CREDIT> ₹<amount>`
- Regex:
  - `^([A-Za-z]{3}\s+\d{1,2},\s+\d{4})\s+(.+?)\s+(DEBIT|CREDIT)\s+₹([\d,]+(?:\.\d+)?)$`

This line provides:
- `date`
- initial `details`
- `transaction_type`
- `amount`
- transaction id from metadata lines (`Transaction ID ...`)

## 2) Build a transaction block
After header row, consume following lines until one of these stop conditions:
- next transaction header date line (`MMM DD, YYYY ...`)
- `Transaction ID ...`
- page footer line (`Page X of Y`)

## 3) Ignore metadata lines in block
Skip these lines while building merchant details:
- `UTR No. ...`
- `Paid by ...`
- `Credited to ...`
- `Date Transaction Details Type Amount`
- `This is a system generated statement...`

## 4) Handle wrapped merchant details
If a continuation line starts with time (`HH:MM am/pm`), remove only the time prefix and keep the remaining text as merchant detail continuation.

Examples:
- `09:50 am SIRVI BANDHU MITHAIWALE AND FOOD MALL`
- `07:44 pm Mr DADASAHEB VAIJNATHRAO SHINDE`

Also append additional non-metadata continuation lines (e.g., line breaks after `AND`) until stop condition.

## 5) Normalize final description
After joining header details + continuation details:
- collapse multiple spaces
- remove leading intent prefixes:
  - `Paid to `
  - `Received from `

If description becomes empty after cleanup, set fallback to `Unknown`.

## 6) Preserve amount and type faithfully
- Keep `DEBIT`/`CREDIT` exactly from the header line.
- Parse amount with commas and optional decimals.

## 7) Output schema
For each transaction emit:
- `transaction_id` (unique id from statement; use this for dedup)
- `id` (same as `transaction_id` for parser-level compatibility)
- `date` (e.g., `Apr 16, 2026`)
- `description` (merchant/entity)
- `amount` (numeric string from PDF)
- `type` (`DEBIT`/`CREDIT`)
- `source` (`phonepe`)

## 8) Validation checks
After extraction, verify:
- no `description` should be exactly `Paid to` or `Received from`
- counts for header rows and extracted transactions should match
- random samples with wrapped merchants resolve correctly
- no duplicate `transaction_id` values within the same statement
