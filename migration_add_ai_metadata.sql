-- Добавление полей для хранения информации о промптах и моделях AI

-- Добавляем поля в таблицу letter_generations
ALTER TABLE letter_generations 
ADD COLUMN IF NOT EXISTS prompt_filename VARCHAR,
ADD COLUMN IF NOT EXISTS ai_model VARCHAR;

-- Добавляем поля в таблицу applications
ALTER TABLE applications 
ADD COLUMN IF NOT EXISTS prompt_filename VARCHAR,
ADD COLUMN IF NOT EXISTS ai_model VARCHAR;

-- Опционально: индексы для аналитики
CREATE INDEX IF NOT EXISTS idx_letter_generations_prompt ON letter_generations(prompt_filename);
CREATE INDEX IF NOT EXISTS idx_letter_generations_model ON letter_generations(ai_model);
CREATE INDEX IF NOT EXISTS idx_applications_prompt ON applications(prompt_filename);
CREATE INDEX IF NOT EXISTS idx_applications_model ON applications(ai_model);