-- =========================================
-- TEMPORARY: Create the "Speakly Demo" organization
-- for MVP self-signup testing.
--
-- Run this ONCE in your PostgreSQL database (psql or Supabase SQL editor).
-- Copy the returned UUID and paste it into .env as DEMO_ORG_ID.
--
-- To remove later: DELETE FROM organizations WHERE name = 'Speakly Demo';
-- =========================================

INSERT INTO organizations 
  (name, plan, max_seats, seats_used, is_active)
VALUES 
  ('Speakly Demo', 'academy', 200, 0, TRUE)
RETURNING id;
