-- Add state_code column to properties table
ALTER TABLE properties ADD COLUMN IF NOT EXISTS state_code VARCHAR(10);

-- Add holiday-related columns to defrag_moves table  
ALTER TABLE defrag_moves ADD COLUMN IF NOT EXISTS is_holiday_move BOOLEAN DEFAULT FALSE;
ALTER TABLE defrag_moves ADD COLUMN IF NOT EXISTS holiday_period_name VARCHAR(255);
ALTER TABLE defrag_moves ADD COLUMN IF NOT EXISTS holiday_type VARCHAR(50);
ALTER TABLE defrag_moves ADD COLUMN IF NOT EXISTS holiday_importance VARCHAR(20);

-- Add indexes for performance
CREATE INDEX IF NOT EXISTS idx_properties_state_code ON properties(state_code);
CREATE INDEX IF NOT EXISTS idx_defrag_moves_holiday ON defrag_moves(is_holiday_move);
