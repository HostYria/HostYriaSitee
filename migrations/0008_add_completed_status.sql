
-- Add 'completed' status to repository_status enum
ALTER TYPE repository_status ADD VALUE IF NOT EXISTS 'completed';
