# Portal do Suporte

Este repositório concentra o backend FastAPI, os frontends Angular e os artefatos de apoio usados para análise de logs, profiler e comparação de versões. A regra prática é simples: se o log está aprontando, este projeto tenta descobrir o motivo antes do café esfriar.

## Estrutura que realmente importa

- `backend/`: API principal em FastAPI e testes unitários focados em parsing, limpeza e comparação de versões.
- `frontend-angular/`: frontend Angular principal do portal.
- `frontend/`: servidor Express enxuto que publica o build gerado pelo Angular principal.
- `Centralizador-Log-main/`: variação do projeto com backend e frontend Angular próprios.

## Frontend ativo

O frontend principal deste projeto é o Angular em `frontend-angular/`.

O diretório `frontend/` nao contem uma aplicacao React ativa. Ele existe para servir o build pronto do Angular com `server.js`.

## Como rodar sem tropeçar

### Backend

Execute a API a partir de `backend/` na porta configurada pelo projeto.

### Frontend Angular principal

- Desenvolvimento: `npm start` ou `ng serve` em `frontend-angular/`
- Build: `npm run build` em `frontend-angular/`

### Publicacao local do frontend

Depois do build do Angular, execute `node frontend/server.js` para servir os arquivos gerados.

## Testes e observacoes

- Os testes unitarios mais confiaveis ficam em `backend/test_*.py`.
- Os testes de integracao em `backend/tests/` dependem de `BACKEND_URL` configurado para uma API real em execucao.
- Qualquer referencia antiga a React deve ser tratada como legado.

## Guia de manutencao rapida

- Alteracoes de interface devem ir para `frontend-angular/src/app`.
- Antes de mexer no Centralizador, valide tambem `Centralizador-Log-main/frontend-angular/`.
- Se algo parecer magico demais, provavelmente merece um teste ou um comentario melhor.
