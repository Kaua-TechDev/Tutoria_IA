-- =============================================================
--  TÚTORA — Tutor de Trilhas de Estudo com IA
--  Disciplina: Introdução à Inteligência Artificial
--  Curso Técnico em Informática — Colégio Castelo
-- =============================================================
--  SCRIPT 1: schema.sql  (DDL — criação do banco e das tabelas)
--  Execute este arquivo ANTES do seed.sql
-- =============================================================

-- ------------------------------------------------------------
-- 1. BANCO DE DADOS
-- ------------------------------------------------------------
CREATE DATABASE IF NOT EXISTS tutor_trilhas
    CHARACTER SET utf8mb4
    COLLATE utf8mb4_unicode_ci;

USE tutor_trilhas;

-- ------------------------------------------------------------
-- 2. TABELAS  (ordem respeita as dependências de FK)
-- ------------------------------------------------------------

-- 2.1 ALUNOS
CREATE TABLE alunos (
    id            INT AUTO_INCREMENT PRIMARY KEY,
    nome          VARCHAR(100)  NOT NULL,
    matricula     VARCHAR(20)   NOT NULL UNIQUE,
    email         VARCHAR(100)  UNIQUE,
    senha_hash    VARCHAR(255)  NOT NULL,
    segmento      ENUM('FUNDAMENTAL_I','FUNDAMENTAL_II','MEDIO','TECNICO') NOT NULL,
    pontos_xp     INT           NOT NULL DEFAULT 0,
    nivel         INT           NOT NULL DEFAULT 1,
    criado_em     DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- 2.2 RESPONSAVEIS
CREATE TABLE responsaveis (
    id            INT AUTO_INCREMENT PRIMARY KEY,
    nome          VARCHAR(100)  NOT NULL,
    email         VARCHAR(100)  NOT NULL UNIQUE,
    senha_hash    VARCHAR(255)  NOT NULL,
    telefone      VARCHAR(20),
    criado_em     DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- 2.3 ALUNO_RESPONSAVEL  (relacionamento N:N)
CREATE TABLE aluno_responsavel (
    aluno_id        INT NOT NULL,
    responsavel_id  INT NOT NULL,
    PRIMARY KEY (aluno_id, responsavel_id),
    CONSTRAINT fk_ar_aluno       FOREIGN KEY (aluno_id)
        REFERENCES alunos(id)       ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT fk_ar_responsavel FOREIGN KEY (responsavel_id)
        REFERENCES responsaveis(id) ON DELETE CASCADE ON UPDATE CASCADE
);

-- 2.4 TRILHAS
CREATE TABLE trilhas (
    id          INT AUTO_INCREMENT PRIMARY KEY,
    nome        VARCHAR(100)  NOT NULL,
    descricao   TEXT,
    disciplina  VARCHAR(100)  NOT NULL,
    segmento    ENUM('FUNDAMENTAL_I','FUNDAMENTAL_II','MEDIO','TECNICO') NOT NULL,
    criado_em   DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- 2.5 SESSOES
CREATE TABLE sessoes (
    id               INT AUTO_INCREMENT PRIMARY KEY,
    aluno_id         INT           NOT NULL,
    trilha_id        INT           NULL,
    disciplina       VARCHAR(100)  NOT NULL,
    pergunta         TEXT          NOT NULL,
    resposta_ia      TEXT,
    sugestao_pratica TEXT,
    avaliacao        TINYINT       NULL COMMENT '1 a 5 estrelas',
    xp_ganho         INT           NOT NULL DEFAULT 10,
    criado_em        DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_sessao_aluno  FOREIGN KEY (aluno_id)
        REFERENCES alunos(id)  ON DELETE CASCADE  ON UPDATE CASCADE,
    CONSTRAINT fk_sessao_trilha FOREIGN KEY (trilha_id)
        REFERENCES trilhas(id) ON DELETE SET NULL ON UPDATE CASCADE
);

-- 2.6 CONQUISTAS
CREATE TABLE conquistas (
    id          INT AUTO_INCREMENT PRIMARY KEY,
    nome        VARCHAR(100)  NOT NULL,
    descricao   TEXT,
    icone       VARCHAR(50),
    xp_bonus    INT           NOT NULL DEFAULT 0,
    criterio    VARCHAR(100)  COMMENT 'Identificador interno usado pelo gamificacao_service'
);

-- 2.7 ALUNO_CONQUISTAS  (relacionamento N:N com data de desbloqueio)
CREATE TABLE aluno_conquistas (
    aluno_id       INT      NOT NULL,
    conquista_id   INT      NOT NULL,
    desbloqueado_em DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (aluno_id, conquista_id),
    CONSTRAINT fk_ac_aluno     FOREIGN KEY (aluno_id)
        REFERENCES alunos(id)      ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT fk_ac_conquista FOREIGN KEY (conquista_id)
        REFERENCES conquistas(id)  ON DELETE CASCADE ON UPDATE CASCADE
);

-- 2.8 ALERTAS_DIFICULDADE
CREATE TABLE alertas_dificuldade (
    id              INT AUTO_INCREMENT PRIMARY KEY,
    aluno_id        INT           NOT NULL,
    assunto         VARCHAR(200)  NOT NULL,
    total_perguntas INT           NOT NULL DEFAULT 3,
    resolvido       BOOLEAN       NOT NULL DEFAULT FALSE,
    criado_em       DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_alerta_aluno FOREIGN KEY (aluno_id)
        REFERENCES alunos(id) ON DELETE CASCADE ON UPDATE CASCADE
);

-- ------------------------------------------------------------
-- 3. VERIFICAÇÃO RÁPIDA
-- ------------------------------------------------------------
-- Execute para confirmar as 8 tabelas criadas:
-- SHOW TABLES;
-- DESCRIBE alunos;
