-- init.sql - настройка полнотекстового поиска для русского языка
CREATE EXTENSION IF NOT EXISTS pg_trgm;
CREATE EXTENSION IF NOT EXISTS unaccent;

-- Настройка русской конфигурации полнотекстового поиска
CREATE TEXT SEARCH CONFIGURATION russian (COPY = russian);

-- Обновление конфигурации для базы знаний
ALTER TABLE knowledge_base ADD COLUMN IF NOT EXISTS search_vector tsvector;
CREATE INDEX IF NOT EXISTS idx_kb_search ON knowledge_base USING GIN(search_vector);

-- Функция обновления поискового вектора
CREATE OR REPLACE FUNCTION kb_search_update() RETURNS trigger AS $$
BEGIN
  NEW.search_vector := to_tsvector('russian', COALESCE(NEW.text, ''));
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Триггер для автоматического обновления
DROP TRIGGER IF EXISTS kb_search_trigger ON knowledge_base;
CREATE TRIGGER kb_search_trigger
  BEFORE INSERT OR UPDATE ON knowledge_base
  FOR EACH ROW
  EXECUTE FUNCTION kb_search_update();