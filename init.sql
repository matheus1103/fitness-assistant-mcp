-- init.sql
-- Configuração inicial do banco de dados

-- Extensões úteis
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_stat_statements";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- Configurações de performance
ALTER SYSTEM SET shared_preload_libraries = 'pg_stat_statements';
ALTER SYSTEM SET pg_stat_statements.track = 'all';
ALTER SYSTEM SET max_connections = '200';
ALTER SYSTEM SET shared_buffers = '256MB';

-- Timezone
ALTER DATABASE fitness_assistant SET timezone TO 'UTC';

-- Schema para testes
CREATE SCHEMA IF NOT EXISTS test_data;
GRANT ALL PRIVILEGES ON SCHEMA test_data TO fitness_user;

-- Usuário para aplicação (caso não exista)
DO $$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'fitness_app') THEN
        CREATE ROLE fitness_app WITH LOGIN PASSWORD 'app_password_2024';
        GRANT CONNECT ON DATABASE fitness_assistant TO fitness_app;
        GRANT USAGE ON SCHEMA public TO fitness_app;
        GRANT CREATE ON SCHEMA public TO fitness_app;
    END IF;
END
$$;

-- Função de limpeza automática (executa via cron job)
CREATE OR REPLACE FUNCTION cleanup_old_data()
RETURNS void AS $function$
BEGIN
    -- Remove dados de FC muito antigos (mais de 2 anos)
    DELETE FROM heart_rate_data 
    WHERE created_at < NOW() - INTERVAL '2 years';
    
    -- Remove sessões de treino muito antigas (mais de 5 anos)
    DELETE FROM workout_sessions 
    WHERE session_date < NOW() - INTERVAL '5 years';
    
    -- Log da limpeza
    RAISE NOTICE 'Limpeza de dados antigos executada em %', NOW();
END;
$function$ LANGUAGE plpgsql;

-- Função para calcular estatísticas de usuário
CREATE OR REPLACE FUNCTION calculate_user_stats(user_uuid UUID)
RETURNS JSON AS $function$
DECLARE
    result JSON;
BEGIN
    SELECT json_build_object(
        'total_sessions', COUNT(ws.id),
        'total_duration_minutes', SUM(ws.duration_minutes),
        'avg_heart_rate', AVG(ws.avg_heart_rate),
        'last_session', MAX(ws.session_date),
        'total_calories', SUM(ws.calories_estimated)
    ) INTO result
    FROM workout_sessions ws
    WHERE ws.user_profile_id = user_uuid
    AND ws.session_date > NOW() - INTERVAL '1 year';
    
    RETURN result;
END;
$function$ LANGUAGE plpgsql;

-- Índices para performance
-- (Serão criados automaticamente pelo SQLAlchemy, mas listados aqui para referência)
-- CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_users_user_id ON user_profiles(user_id);
-- CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_sessions_user_date ON workout_sessions(user_profile_id, session_date);
-- CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_heart_rate_user_date ON heart_rate_data(user_profile_id, timestamp);

-- View para estatísticas rápidas
CREATE OR REPLACE VIEW user_statistics AS
SELECT 
    up.user_id,
    up.age,
    up.fitness_level,
    COUNT(ws.id) as total_sessions,
    AVG(ws.duration_minutes) as avg_duration,
    AVG(ws.avg_heart_rate) as avg_heart_rate,
    MAX(ws.session_date) as last_session,
    SUM(ws.calories_estimated) as total_calories
FROM user_profiles up
LEFT JOIN workout_sessions ws ON up.id = ws.user_profile_id
WHERE ws.session_date > NOW() - INTERVAL '90 days'
GROUP BY up.id, up.user_id, up.age, up.fitness_level;

-- Trigger para atualizar timestamp automaticamente
CREATE OR REPLACE FUNCTION update_modified_column()
RETURNS TRIGGER AS $function$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$function$ LANGUAGE plpgsql;

-- Mensagem de sucesso
DO $$
BEGIN
    RAISE NOTICE '✅ Banco fitness_assistant configurado com sucesso!';
    RAISE NOTICE '📊 Database: fitness_assistant';
    RAISE NOTICE '👤 Usuário: fitness_user';
    RAISE NOTICE '🔗 Conexão: postgresql://fitness_user:fitness_dev_2024@localhost:5432/fitness_assistant';
END
$$;