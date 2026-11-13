# assets/

Recursos embutidos no painel. O painel final é **100% offline**: nada aqui é carregado por rede
em tempo de execução — os arquivos são lidos pelo `run.py --stage build` e escritos dentro do HTML.

## echarts.min.js

- Projeto: Apache ECharts
- Versão: 5.5.1
- Origem: https://cdn.jsdelivr.net/npm/echarts@5.5.1/dist/echarts.min.js
- Licença: Apache License 2.0 (https://www.apache.org/licenses/LICENSE-2.0)
- Tamanho: ~1,0 MB
- Uso: biblioteca de gráficos, embutida em `<script>` no `output/painel_decisao.html`.

Se o arquivo for removido, o estágio `build` falha com mensagem explícita e o painel não é gerado
(não há fallback silencioso para CDN).
