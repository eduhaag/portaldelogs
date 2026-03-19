# Centralizador de Logs

Frontend oficial: Angular em `frontend-angular`.

Estado atual do projeto:
- `frontend-angular/`: fonte oficial da interface, com Angular + Po-UI.
- `frontend/`: servidor Express mínimo que publica o build gerado em `frontend-angular/dist`.
- `backend/`: API FastAPI e serviços de análise.

Este repositório não usa mais React como frontend ativo.

Execução local:
- Frontend Angular: executar build ou dev server a partir de `frontend-angular/`.
- Publicação local em `3000`: executar `node frontend/server.js` para servir o build Angular.
- Backend: executar a API em `backend/` na porta `8001`.

Observação:
- Qualquer referência antiga a React ou `frontend/src` deve ser considerada legado.
- Novas alterações de interface devem ser feitas somente em `frontend-angular/src/app`.
