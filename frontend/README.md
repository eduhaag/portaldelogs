# Servidor de Publicacao do Frontend

Esta pasta nao abriga um app React vivo, escondido ou em coma induzido. Ela existe para servir o build do Angular principal por meio de `server.js`.

## O que fica aqui

- `server.js`: servidor HTTP simples para publicar o build gerado

## Dependencia real

As fontes da interface ficam em `../frontend-angular/`.

O build esperado para publicacao fica em `../frontend-angular/dist/frontend-angular/browser`.

## Uso local

1. Gere o build em `../frontend-angular` com `npm run build`.
2. Execute `npm start` nesta pasta para publicar o build na porta `3000`.

## Dica honesta

Se voce estiver procurando componentes, telas ou estilo aqui, pode voltar tranquila: a festa acontece no Angular, nao neste corredor tecnico.