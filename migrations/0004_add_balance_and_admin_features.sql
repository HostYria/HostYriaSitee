
-- Add balance and isAdmin to users table
ALTER TABLE users ADD COLUMN balance INTEGER DEFAULT 0 NOT NULL;
ALTER TABLE users ADD COLUMN is_admin BOOLEAN DEFAULT false NOT NULL;

-- Create payment_methods table
CREATE TABLE payment_methods (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  name TEXT NOT NULL,
  image_url TEXT NOT NULL,
  instructions TEXT NOT NULL,
  currency TEXT NOT NULL,
  usd_rate INTEGER NOT NULL,
  is_active BOOLEAN DEFAULT true NOT NULL,
  created_at TIMESTAMP DEFAULT now() NOT NULL
);

-- Create balance_requests table
CREATE TABLE balance_requests (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  payment_method_id UUID NOT NULL REFERENCES payment_methods(id),
  amount_sent INTEGER NOT NULL,
  transaction_id TEXT NOT NULL,
  screenshot_url TEXT NOT NULL,
  status TEXT DEFAULT 'pending' NOT NULL,
  created_at TIMESTAMP DEFAULT now() NOT NULL
);

-- Create support_messages table
CREATE TABLE support_messages (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  message TEXT NOT NULL,
  is_from_user BOOLEAN DEFAULT true NOT NULL,
  created_at TIMESTAMP DEFAULT now() NOT NULL
);

-- Set admin user
UPDATE users SET is_admin = true WHERE email = 'abojafar1327@gmail.com';
