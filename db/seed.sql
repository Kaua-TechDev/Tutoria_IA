-- =============================================================
--  TÚTORA — Tutor de Trilhas de Estudo com IA
--  Disciplina: Introdução à Inteligência Artificial
--  Curso Técnico em Informática — Colégio Castelo
-- =============================================================
--  SCRIPT 2: seed.sql  (DML — dados iniciais + registros de teste)
--  Execute este arquivo DEPOIS do schema.sql
-- =============================================================

USE tutor_trilhas;

-- ============================================================
-- BLOCO A — DADOS OBRIGATÓRIOS (critério de aceite da Semana 1)
-- ============================================================

-- ------------------------------------------------------------
-- A.1  8 CONQUISTAS
-- (SELECT COUNT(*) FROM conquistas  deve retornar 8)
-- ------------------------------------------------------------
INSERT INTO conquistas (nome, descricao, icone, xp_bonus, criterio) VALUES
('Primeira Pergunta',
 'Você fez sua primeira pergunta à Tútora. A jornada começou!',
 '🎯', 20, 'PRIMEIRA_PERGUNTA'),

('Maratonista',
 'Realizou 10 sessões de estudo. Dedicação é tudo!',
 '🏃', 50, 'SESSOES_10'),

('Explorador',
 'Estudou em 5 trilhas diferentes. Conhecimento sem fronteiras!',
 '🗺️', 40, 'TRILHAS_5'),

('Avaliador',
 'Avaliou 5 respostas da IA. Seu feedback melhora o sistema!',
 '⭐', 15, 'AVALIACOES_5'),

('Persistente',
 'Estudou em 3 dias consecutivos. A constância faz a diferença!',
 '🔥', 30, 'DIAS_CONSECUTIVOS_3'),

('Dedicado',
 'Acumulou 500 pontos de XP. Você está avançando muito!',
 '💪', 60, 'XP_500'),

('Mestre do Conhecimento',
 'Acumulou 1.000 pontos de XP. Nível máximo desbloqueado!',
 '👑', 100, 'XP_1000'),

('Trilheiro',
 'Completou sua primeira trilha de estudos do início ao fim.',
 '🏅', 45, 'TRILHA_COMPLETA');

-- ------------------------------------------------------------
-- A.2  8 TRILHAS
-- (SELECT COUNT(*) FROM trilhas  deve retornar 8)
-- ------------------------------------------------------------
INSERT INTO trilhas (nome, descricao, disciplina, segmento) VALUES
('Lógica de Programação do Zero',
 'Aprenda os fundamentos da lógica: variáveis, condicionais, laços e funções.',
 'Programação', 'TECNICO'),

('Banco de Dados na Prática',
 'Modelagem relacional, SQL, JOINs e normalização com exemplos reais.',
 'Banco de Dados', 'TECNICO'),

('Python para Iniciantes',
 'Sintaxe básica, estruturas de dados, orientação a objetos e boas práticas.',
 'Programação', 'TECNICO'),

('Redação Nota 1000',
 'Estrutura dissertativa, argumentação, coesão e proposta de intervenção ENEM.',
 'Português', 'MEDIO'),

('Geometria e Álgebra',
 'Funções, trigonometria, geometria plana e espacial para o Ensino Médio.',
 'Matemática', 'MEDIO'),

('Interpretação de Texto',
 'Estratégias de leitura, gêneros textuais e compreensão crítica.',
 'Português', 'FUNDAMENTAL_II'),

('Ciências da Natureza',
 'Biologia, Física e Química integradas: corpo humano, energia e matéria.',
 'Ciências', 'FUNDAMENTAL_II'),

('Matemática Básica',
 'Números, operações, frações e problemas do cotidiano.',
 'Matemática', 'FUNDAMENTAL_I');

-- ============================================================
-- BLOCO B — REGISTROS DE TESTE
-- (Para validar FKs, rotas e comportamento do sistema)
-- ============================================================

-- ------------------------------------------------------------
-- B.1  ALUNOS DE TESTE
-- Senhas armazenadas aqui são bcrypt apenas para teste visual.
-- O Flask vai gerar o hash real via set_senha().
-- senha_hash abaixo = bcrypt de "senha123"
-- ------------------------------------------------------------
INSERT INTO alunos (nome, matricula, email, senha_hash, segmento, pontos_xp, nivel) VALUES
('Ana Lima',       '2026001', 'ana.lima@escola.edu.br',
 '$2b$12$TESTE_HASH_ANA_PLACEHOLDER_BCRYPT_AQ', 'TECNICO',      120, 1),

('Bruno Souza',    '2026002', 'bruno.souza@escola.edu.br',
 '$2b$12$TESTE_HASH_BRUNO_PLACEHOLDER_BCRYPT', 'MEDIO',         80,  1),

('Carla Mendes',   '2026003', 'carla.mendes@escola.edu.br',
 '$2b$12$TESTE_HASH_CARLA_PLACEHOLDER_BCRYPT', 'FUNDAMENTAL_II', 30,  1),

('Diego Alves',    '2026004', 'diego.alves@escola.edu.br',
 '$2b$12$TESTE_HASH_DIEGO_PLACEHOLDER_BCRYPT', 'TECNICO',       500, 2);

-- Observação: ao rodar o Flask (Semana 2), substitua os hashes acima
-- pelos gerados via:  aluno.set_senha("senha123")

-- ------------------------------------------------------------
-- B.2  RESPONSAVEIS DE TESTE
-- ------------------------------------------------------------
INSERT INTO responsaveis (nome, email, senha_hash, telefone) VALUES
('Maria Lima',     'maria.lima@email.com',
 '$2b$12$TESTE_HASH_MARIA_PLACEHOLDER_BCRYPT', '(22) 99001-0001'),

('João Souza',     'joao.souza@email.com',
 '$2b$12$TESTE_HASH_JOAO_PLACEHOLDER_BCRYPT',  '(22) 99001-0002');

-- ------------------------------------------------------------
-- B.3  VINCULO ALUNO–RESPONSAVEL
-- ------------------------------------------------------------
INSERT INTO aluno_responsavel (aluno_id, responsavel_id) VALUES
(1, 1),   -- Ana Lima  → Maria Lima
(2, 2),   -- Bruno     → João Souza
(3, 1);   -- Carla     → Maria Lima (mesma responsável)

-- ------------------------------------------------------------
-- B.4  SESSOES DE TESTE
-- ------------------------------------------------------------
INSERT INTO sessoes (aluno_id, trilha_id, disciplina, pergunta,
                     resposta_ia, sugestao_pratica, avaliacao, xp_ganho) VALUES
(1, 1, 'Programação',
 'O que é uma variável em programação?',
 'Uma variável é um espaço na memória que armazena um valor que pode mudar durante a execução do programa.',
 'Crie um programa em Python que declare três variáveis (nome, idade, nota) e as exiba no console.',
 5, 10),

(1, 2, 'Banco de Dados',
 'Qual a diferença entre PRIMARY KEY e FOREIGN KEY?',
 'PRIMARY KEY identifica de forma única cada linha de uma tabela. FOREIGN KEY aponta para a PRIMARY KEY de outra tabela, criando o vínculo entre elas.',
 'Crie duas tabelas (clientes e pedidos) e escreva um INSERT que gere erro de FK.',
 4, 10),

(2, 4, 'Português',
 'Como estruturar uma redação dissertativa?',
 'A redação dissertativa tem três partes: introdução (apresenta o tema e tese), desenvolvimento (argumentos com evidências) e conclusão (retoma a tese e propõe intervenção).',
 'Escreva um parágrafo de introdução sobre o tema: impacto das redes sociais na saúde mental.',
 5, 10);

-- ------------------------------------------------------------
-- B.5  CONQUISTA DESBLOQUEADA (registro de teste)
-- ------------------------------------------------------------
INSERT INTO aluno_conquistas (aluno_id, conquista_id) VALUES
(1, 1),  -- Ana desbloqueou "Primeira Pergunta"
(4, 1),  -- Diego desbloqueou "Primeira Pergunta"
(4, 6);  -- Diego desbloqueou "Dedicado" (≥ 500 XP)

-- ------------------------------------------------------------
-- B.6  ALERTA DE DIFICULDADE (registro de teste)
-- ------------------------------------------------------------
INSERT INTO alertas_dificuldade (aluno_id, assunto, total_perguntas, resolvido) VALUES
(1, 'Chaves estrangeiras (FK)', 3, FALSE);

-- ============================================================
-- BLOCO C — VERIFICAÇÕES (rode após o seed para confirmar)
-- ============================================================
-- SELECT COUNT(*) AS total_conquistas FROM conquistas;   -- deve retornar 8
-- SELECT COUNT(*) AS total_trilhas    FROM trilhas;      -- deve retornar 8
-- SELECT * FROM conquistas;
-- SELECT * FROM trilhas;
--
-- Teste de FK — deve gerar ERROR 1452:
-- INSERT INTO sessoes (aluno_id, disciplina, pergunta)
-- VALUES (9999, 'Teste', 'Isso deve falhar por FK inválida');
