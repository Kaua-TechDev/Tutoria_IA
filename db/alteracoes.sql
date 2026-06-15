ALTER TABLE alunos
    ADD COLUMN ativo ENUM('ativo', 'ausente') NOT NULL DEFAULT 'ativo';

ALTER TABLE trilhas
    ADD COLUMN ativo ENUM('ativo', 'ausente') NOT NULL DEFAULT 'ativo';

ALTER TABLE sessoes
    ADD COLUMN assunto VARCHAR(255) NULL;
