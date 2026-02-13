-- Migration: Ajouter colonne trial_reminder_sent_at
-- Date: 2026-02-13
-- Description: Garde-fou pour ne pas envoyer le rappel J-3 plusieurs fois

ALTER TABLE users ADD COLUMN trial_reminder_sent_at TIMESTAMPTZ;
