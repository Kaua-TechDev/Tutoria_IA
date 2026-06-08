-- Tutoria - Tutor de Trilhas de Estudo
-- Semana 1: insercao de dados iniciais e registros de teste
-- Execute este arquivo depois do schema.sql

USE tutor_trilhas;

-- Conquistas (criterio de aceite: 8 registros)
INSERT INTO conquistas (nome, descricao, icone, xp_bonus, criterio) VALUES
('Primeira Pergunta',    'Voce fez sua primeira pergunta. A jornada comecou!',                    'alvo',    20,  'PRIMEIRA_PERGUNTA'),
('Maratonista',          'Realizou 10 sessoes de estudo.',                                         'corrida', 50,  'SESSOES_10'),
('Explorador',           'Estudou em 5 trilhas diferentes.',                                       'mapa',    40,  'TRILHAS_5'),
('Avaliador',            'Avaliou 5 respostas. Seu feedback melhora o sistema.',                   'estrela', 15,  'AVALIACOES_5'),
('Persistente',          'Estudou em 3 dias consecutivos.',                                        'fogo',    30,  'DIAS_CONSECUTIVOS_3'),
('Dedicado',             'Acumulou 500 pontos de XP.',                                             'musculo', 60,  'XP_500'),
('Mestre do Conhecimento','Acumulou 1000 pontos de XP.',                                           'coroa',   100, 'XP_1000'),
('Trilheiro',            'Completou uma trilha de estudos do inicio ao fim.',                      'medalha', 45,  'TRILHA_COMPLETA');

-- Trilhas (criterio de aceite: 8 registros)
INSERT INTO trilhas (nome, descricao, disciplina, segmento) VALUES
('Logica de Programacao do Zero', 'Variaveis, condicionais, lacos e funcoes.',                                  'Programacao',  'TECNICO'),
('Banco de Dados na Pratica',     'Modelagem relacional, SQL, JOINs e normalizacao com exemplos reais.',        'Banco de Dados','TECNICO'),
('Python para Iniciantes',        'Sintaxe basica, estruturas de dados e boas praticas.',                       'Programacao',  'TECNICO'),
('Redacao Nota 1000',             'Estrutura dissertativa, argumentacao e proposta de intervencao ENEM.',       'Portugues',    'MEDIO'),
('Geometria e Algebra',           'Funcoes, trigonometria, geometria plana e espacial.',                        'Matematica',   'MEDIO'),
('Interpretacao de Texto',        'Estrategias de leitura, generos textuais e compreensao critica.',            'Portugues',    'FUNDAMENTAL_II'),
('Ciencias da Natureza',          'Biologia, Fisica e Quimica integradas: corpo humano, energia e materia.',   'Ciencias',     'FUNDAMENTAL_II'),
('Matematica Basica',             'Numeros, operacoes, fracoes e problemas do cotidiano.',                      'Matematica',   'FUNDAMENTAL_I');

-- Alunos de teste
-- senha_hash abaixo sao placeholders; o hash real e gerado pelo Flask via set_senha()
INSERT INTO alunos (nome, matricula, email, senha_hash, segmento, pontos_xp, nivel) VALUES
('Ana Lima',     '2026001', 'ana.lima@escola.edu.br',     '$2b$12$PLACEHOLDER_ANA',   'TECNICO',       120, 1),
('Bruno Souza',  '2026002', 'bruno.souza@escola.edu.br',  '$2b$12$PLACEHOLDER_BRUNO', 'MEDIO',          80, 1),
('Carla Mendes', '2026003', 'carla.mendes@escola.edu.br', '$2b$12$PLACEHOLDER_CARLA', 'FUNDAMENTAL_II', 30, 1),
('Diego Alves',  '2026004', 'diego.alves@escola.edu.br',  '$2b$12$PLACEHOLDER_DIEGO', 'TECNICO',       500, 2);

-- Responsaveis de teste
INSERT INTO responsaveis (nome, email, senha_hash, telefone) VALUES
('Maria Lima', 'maria.lima@email.com', '$2b$12$PLACEHOLDER_MARIA', '(22) 99001-0001'),
('Joao Souza', 'joao.souza@email.com', '$2b$12$PLACEHOLDER_JOAO',  '(22) 99001-0002');

-- Vinculo aluno-responsavel
INSERT INTO aluno_responsavel (aluno_id, responsavel_id) VALUES
(1, 1),
(2, 2),
(3, 1);

-- Sessoes de teste
INSERT INTO sessoes (aluno_id, trilha_id, disciplina, pergunta, resposta_ia, sugestao_pratica, avaliacao, xp_ganho) VALUES
(1, 1, 'Programacao',
 'O que e uma variavel em programacao?',
 'Uma variavel e um espaco na memoria que armazena um valor que pode mudar durante a execucao do programa.',
 'Crie um programa em Python que declare tres variaveis (nome, idade, nota) e as exiba no console.',
 5, 10),

(1, 2, 'Banco de Dados',
 'Qual a diferenca entre PRIMARY KEY e FOREIGN KEY?',
 'PRIMARY KEY identifica de forma unica cada linha de uma tabela. FOREIGN KEY aponta para a PRIMARY KEY de outra tabela, criando o vinculo entre elas.',
 'Crie duas tabelas (clientes e pedidos) e escreva um INSERT que gere erro de FK.',
 4, 10),

(2, 4, 'Portugues',
 'Como estruturar uma redacao dissertativa?',
 'A redacao dissertativa tem tres partes: introducao, desenvolvimento e conclusao. A introducao apresenta o tema e a tese; o desenvolvimento traz os argumentos; a conclusao retoma a tese e propoe uma intervencao.',
 'Escreva um paragrafo de introducao sobre o impacto das redes sociais na saude mental.',
 5, 10);

-- Conquistas desbloqueadas (registros de teste)
INSERT INTO aluno_conquistas (aluno_id, conquista_id) VALUES
(1, 1),
(4, 1),
(4, 6);

-- Alerta de dificuldade (registro de teste)
INSERT INTO alertas_dificuldade (aluno_id, assunto, total_perguntas, resolvido) VALUES
(1, 'Chaves estrangeiras (FK)', 3, FALSE);

-- Para verificar apos rodar:
-- SELECT COUNT(*) FROM conquistas;  -- 8
-- SELECT COUNT(*) FROM trilhas;     -- 8
--
-- Teste de FK (deve gerar ERROR 1452):
-- INSERT INTO sessoes (aluno_id, disciplina, pergunta) VALUES (9999, 'Teste', 'Erro esperado');
