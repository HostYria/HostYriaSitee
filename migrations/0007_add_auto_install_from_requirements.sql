
-- Add autoInstallFromRequirements column to repositories table
ALTER TABLE repositories ADD COLUMN IF NOT EXISTS auto_install_from_requirements BOOLEAN DEFAULT false;
