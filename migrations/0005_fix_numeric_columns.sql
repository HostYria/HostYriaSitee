
-- Fix balance column type
ALTER TABLE users ALTER COLUMN balance TYPE TEXT USING balance::TEXT;
ALTER TABLE users ALTER COLUMN balance SET DEFAULT '0';

-- Fix usd_rate column type
ALTER TABLE payment_methods ALTER COLUMN usd_rate TYPE TEXT USING usd_rate::TEXT;

-- Fix amount_sent column type
ALTER TABLE balance_requests ALTER COLUMN amount_sent TYPE TEXT USING amount_sent::TEXT;
