-- Tutoria - Tutor de Trilhas de Estudo
-- Semana 1: criacao do banco de dados
-- Execute este arquivo antes do seed.sql

CREATE DATABASE IF NOT EXISTS tutor_trilhas
    CHARACTER SET utf8mb4
    COLLATE utf8mb4_unicode_ci;

USE tutor_trilhas;

CREATE TABLE alunos (
    id          INT AUTO_INCREMENT PRIMARY KEY,
    nome        VARCHAR(100) NOT NULL,
    matricula   VARCHAR(20)  NOT NULL UNIQUE,
    email       VARCHAR(100) UNIQUE,
    senha_hash  VARCHAR(255) NOT NULL,
    segmento    ENUM('FUNDAMENTAL_I','FUNDAMENTAL_II','MEDIO','TECNICO') NOT NULL,
    pontos_xp   INT NOT NULL DEFAULT 0,
    nivel       INT NOT NULL DEFAULT 1,
    criado_em   DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE responsaveis (
    id          INT AUTO_INCREMENT PRIMARY KEY,
    nome        VARCHAR(100) NOT NULL,
    email       VARCHAR(100) NOT NULL UNIQUE,
    senha_hash  VARCHAR(255) NOT NULL,
    telefone    VARCHAR(20),
    criado_em   DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE aluno_responsavel (
    aluno_id       INT NOT NULL,
    responsavel_id INT NOT NULL,
    PRIMARY KEY (aluno_id, responsavel_id),
    CONSTRAINT fk_ar_aluno       FOREIGN KEY (aluno_id)       REFERENCES alunos(id)       ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT fk_ar_responsavel FOREIGN KEY (responsavel_id) REFERENCES responsaveis(id) ON DELETE CASCADE ON UPDATE CASCADE
);

CREATE TABLE trilhas (
    id          INT AUTO_INCREMENT PRIMARY KEY,
    nome        VARCHAR(100) NOT NULL,
    descricao   TEXT,
    disciplina  VARCHAR(100) NOT NULL,
    segmento    ENUM('FUNDAMENTAL_I','FUNDAMENTAL_II','MEDIO','TECNICO') NOT NULL,
    criado_em   DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE sessoes (
    id               INT AUTO_INCREMENT PRIMARY KEY,
    aluno_id         INT          NOT NULL,
    trilha_id        INT          NULL,
    disciplina       VARCHAR(100) NOT NULL,
    pergunta         TEXT         NOT NULL,
    resposta_ia      TEXT,
    sugestao_pratica TEXT,
    avaliacao        TINYINT      NULL,
    xp_ganho         INT NOT NULL DEFAULT 10,
    criado_em        DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_sessao_aluno  FOREIGN KEY (aluno_id)  REFERENCES alunos(id)  ON DELETE CASCADE  ON UPDATE CASCADE,
    CONSTRAINT fk_sessao_trilha FOREIGN KEY (trilha_id) REFERENCES trilhas(id) ON DELETE SET NULL ON UPDATE CASCADE
);

CREATE TABLE conquistas (
    id          INT AUTO_INCREMENT PRIMARY KEY,
    nome        VARCHAR(100) NOT NULL,
    descricao   TEXT,
    icone       VARCHAR(50),
    xp_bonus    INT NOT NULL DEFAULT 0,
    criterio    VARCHAR(100)
);

CREATE TABLE aluno_conquistas (
    aluno_id        INT NOT NULL,
    conquista_id    INT NOT NULL,
    desbloqueado_em DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (aluno_id, conquista_id),
    CONSTRAINT fk_ac_aluno     FOREIGN KEY (aluno_id)     REFERENCES alunos(id)     ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT fk_ac_conquista FOREIGN KEY (conquista_id) REFERENCES conquistas(id) ON DELETE CASCADE ON UPDATE CASCADE
);

CREATE TABLE alertas_dificuldade (
    id              INT AUTO_INCREMENT PRIMARY KEY,
    aluno_id        INT          NOT NULL,
    assunto         VARCHAR(200) NOT NULL,
    total_perguntas INT NOT NULL DEFAULT 3,
    resolvido       BOOLEAN NOT NULL DEFAULT FALSE,
    criado_em       DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_alerta_aluno FOREIGN KEY (aluno_id) REFERENCES alunos(id) ON DELETE CASCADE ON UPDATE CASCADE
);
