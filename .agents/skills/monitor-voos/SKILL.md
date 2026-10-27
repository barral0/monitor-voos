---
name: monitor-voos
description: >-
  Monitora tarifas de passagens aereas de ida e volta e procura as datas mais baratas, com aviso no Telegram.
  Use quando o usuario pedir para acompanhar o preco de um voo, comparar datas de partida mantendo a duracao da
  viagem, ou testar o bot de alertas. Limita o numero de escalas e consulta Google Flights e Kayak.
---

# Monitor de voos

Skill do repositorio `monitor-voos`. Todo o codigo fica no pacote `monitor_voos/`; esta skill so orienta o uso da linha de comando.

## Preparacao (uma vez)

1. `pip install -r requirements.txt` e `python -m playwright install chromium`.
2. Copiar `config.example.json` para `config.json` e preencher a rota, as datas e o limite de escalas (`max_stops`).
3. Credenciais do Telegram: preferir as variaveis de ambiente `TELEGRAM_BOT_TOKEN` e `TELEGRAM_CHAT_ID`. O `config.json` nunca vai para o Git.

## Comandos

Rodar sempre na raiz do repositorio.

| Pedido do usuario | Comando |
| --- | --- |
| Verificar o preco das datas fixas do `config.json` | `python -m monitor_voos monitorar` |
| Achar a melhor epoca para viajar | `python -m monitor_voos flexivel --origin CNF --destination LAX --start 2027-01-01 --end 2027-06-30 --stay-days 30 --step-days 15` |
| Mandar o ranking ao Telegram | acrescentar `--telegram` ao comando `flexivel` |
| Validar a conexao com o bot | `python -m monitor_voos testar-telegram` |

Codigos de saida: `0` sucesso, `1` todos os buscadores falharam ou o envio falhou, `2` configuracao ou argumentos invalidos.

## Como apresentar o resultado

- Mostrar os menores precos em ordem, com companhia, escalas e datas, e os links de reserva.
- Informar quando um buscador falhou: falha de consulta e diferente de "nenhum voo encontrado".
- O Kayak e lido pela pagina e pode quebrar; as escalas dele so aparecem quando o proprio site informa. Nao completar o que a fonte nao disse.
- Precos de buscadores mudam a todo momento. Tratar como indicativo e conferir no link antes de comprar.

## Regras de seguranca

- Nunca pedir, exibir nem registrar o token do bot. Usar [REDACTED] se precisar citar.
- O envio ao Telegram e uma acao externa: confirmar com o usuario antes de usar `--telegram` ou `testar-telegram` pela primeira vez.
- Nao comprar nem preencher dados de pagamento. O fluxo termina nos links de pesquisa.
- Respeitar os intervalos entre consultas; nao disparar varreduras em laco apertado.

## Testes

`python -m unittest discover -s tests -t .` (nao usa rede nem credenciais).
