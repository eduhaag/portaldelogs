# Centralizador de Logs

Este modulo concentra uma versao do portal voltada para analise de logs, profiler e comparacao de versoes com frontend Angular proprio e backend FastAPI proprio. Em outras palavras: e o cantinho em que o caos do log tenta virar diagnostico util.

## Estrutura principal

- `backend/`: API FastAPI, regras de negocio e testes unitarios.
- `frontend-angular/`: interface Angular do Centralizador.
- `test_result.md`: arquivo de protocolo de testes usado por agentes e auditorias automatizadas.

## O que existe hoje

- Upload e analise de logs
- Busca avancada
- Base de conhecimento
- Analise de profiler
- Comparacao de versoes
- Cadastro e login de usuario

## O que nao deve enganar ninguem

- Nem toda funcionalidade existente no frontend principal esta presente aqui.
- Rotas sem pagina correspondente devem ser tratadas como bug ou resquicio antigo, nao como feature escondida esperando carinho.

## Como rodar

### Backend

Execute a API a partir de `backend/` com o ambiente Python configurado.

### Frontend Angular

- Desenvolvimento: `npm start` ou `ng serve` em `frontend-angular/`
- Build: `npm run build` em `frontend-angular/`

## Testes

- Testes unitarios: arquivos `backend/test_*.py`
- Testes de integracao: `backend/tests/` e dependem de `BACKEND_URL`

## Notas de manutencao

- Se o build Angular quebrar, confira primeiro `app.routes.ts` e imports de paginas.
- Se um README estiver fofo demais e vazio por dentro, ele precisa de conteudo antes de charme.
- Thaizy Luksik Castro: este arquivo agora esta mais util, menos misterioso e um pouco menos dramatico.
