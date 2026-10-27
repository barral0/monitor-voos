# Monitor de Voos

Monitor de tarifas aéreas de ida e volta, com busca flexível de datas e alertas no Telegram. Acompanha o preço de uma rota, avisa quando ele cai e descobre em que época a viagem sai mais barata. Inclui uma skill para agentes de IA (Antigravity, Hermes e compatíveis).

## O que faz

- Consulta o **Google Flights** (biblioteca `fast-flights`) e o **Kayak** e agências parceiras (leitura da página com Playwright).
- Limita as escalas conforme a configuração (`max_stops`, de 0 a 3). O limite vale para a consulta, para os links e para o texto das mensagens.
- Busca flexível: varre várias datas de partida mantendo a duração da viagem e monta um ranking.
- Telegram: avisa quando encontra voos, quando bate um novo menor preço (com a economia) ou quando atinge a meta de preço.
- Guarda o histórico de preços por rota, separado por origem, destino, datas, moeda e limite de escalas.

## Instalação

```bash
git clone https://github.com/barral0/monitor-voos.git
cd monitor-voos
pip install -r requirements.txt
python -m playwright install chromium
```

Requer Python 3.10 ou superior. O Playwright só é necessário para o Kayak; sem ele, o Google Flights continua funcionando.

## Configuração

1. Copie `config.example.json` para `config.json` e ajuste a rota, as datas e o limite de escalas.
2. Crie um bot no Telegram: converse com o `@BotFather`, envie `/newbot` e guarde o token. Descubra o seu ID com o `@userinfobot` e envie `/start` ao seu bot.
3. Informe as credenciais. O jeito recomendado é por variáveis de ambiente, que têm prioridade sobre o arquivo:

```bash
export TELEGRAM_BOT_TOKEN="seu-token"
export TELEGRAM_CHAT_ID="seu-id"
```

No Windows (PowerShell): `$env:TELEGRAM_BOT_TOKEN = "seu-token"`.

O `config.json` e o histórico (`price_history.json`) estão no `.gitignore` e não vão para o repositório. Nunca publique o token do bot.

### Opções do `config.json`

| Campo | Padrão | Descrição |
| --- | --- | --- |
| `flight.origin`, `flight.destination` | obrigatório | Códigos IATA de 3 letras. |
| `flight.departure_date`, `flight.return_date` | obrigatório | Formato `AAAA-MM-DD`; a volta deve ser posterior à ida. |
| `flight.max_stops` | `1` | Máximo de escalas, de 0 (só diretos) a 3. |
| `flight.currency` | `BRL` | Moeda da consulta. O Kayak só é usado com `BRL`. |
| `flight.seat_class` | `economy` | `economy`, `premium-economy`, `business` ou `first`. |
| `flight.target_price` | vazio | Avisa quando o menor preço ficar nesse valor ou abaixo. |
| `providers.google_flights`, `providers.kayak` | `true` | Liga ou desliga cada buscador. |
| `providers.kayak_min_price` | `3000` | Ignora valores menores no Kayak, que costumam ser taxas e não tarifas. Use `null` para desativar. |
| `telegram.enabled` | `true` | Liga ou desliga o envio. |
| `telegram.notify_always` | `true` | Envia a cada verificação, mesmo sem novidade. |
| `telegram.notify_when_found` | `true` | Avisa na primeira vez que encontra voos. |
| `telegram.notify_when_cheaper` | `true` | Avisa quando o menor preço histórico cai. |

## Uso

```bash
python -m monitor_voos monitorar
python -m monitor_voos flexivel --origin CNF --destination LAX --start 2027-01-01 --end 2027-06-30 --stay-days 30 --step-days 15 --telegram
python -m monitor_voos testar-telegram
```

| Comando | Função |
| --- | --- |
| `monitorar` | Verifica as datas fixas do `config.json`, compara com o histórico e avisa se houver novidade. |
| `flexivel` | Testa várias partidas com estadia fixa. Sem `config.json`, basta informar `--origin` e `--destination`. Com `--telegram`, envia os 5 melhores. |
| `testar-telegram` | Envia uma mensagem de teste para validar o token e o ID. |

Códigos de saída: `0` sucesso, `1` todos os buscadores falharam ou o envio falhou, `2` configuração ou argumentos inválidos.

No Windows, `run_monitor.bat` executa o comando `monitorar` com um clique. Para repetir a verificação, agende esse comando no Agendador de Tarefas ou no `cron`.

## Skill para agentes

A skill fica em `.agents/skills/monitor-voos/SKILL.md`. Ela não carrega código: apenas explica ao agente quando usar cada comando acima, como apresentar o resultado e as regras de segurança (não expor o token e confirmar antes de enviar mensagens). Para usar em outro agente, copie a pasta `monitor-voos` para o diretório de skills dele.

## Estrutura

```text
monitor_voos/          pacote com todo o código
  cli.py               comandos (monitorar, flexivel, testar-telegram)
  config.py            leitura e validação do config.json
  monitor.py           uma verificação completa
  busca_flexivel.py    varredura de datas
  alertas.py           regra pura de quando avisar
  historico.py         histórico de preços por rota
  mensagens.py         textos das notificações
  links.py             links de pesquisa nos buscadores
  telegram.py          envio de mensagens
  provedores/          Google Flights e Kayak
tests/                 testes unitários (sem rede)
.agents/skills/        skill para agentes de IA
config.example.json    modelo de configuração, sem credenciais
```

## Testes

```bash
python -m unittest discover -s tests -t .
```

Os testes não usam rede nem credenciais.

## Limitações

- O Google Flights é acessado por uma biblioteca não oficial; o Google pode alterar o formato e quebrar a consulta.
- A leitura do Kayak depende do HTML da página e pode parar de funcionar sem aviso. Ela só informa o que o texto do cartão diz (escalas e companhia) e não preenche conexões que a fonte não mostra.
- Os preços mudam a todo momento e são indicativos. Confira no link de reserva antes de comprar.
- Apenas viagens de ida e volta.
- Este projeto não compra passagens nem lida com pagamento.

## Origem

Refatoração do repositório [barral0/skill-monitor-voos](https://github.com/barral0/skill-monitor-voos), do mesmo autor. As mudanças principais: código reunido em um pacote único (antes havia cópias duplicadas dentro da skill), o limite de escalas e a classe do assento passam a valer de fato, histórico separado por rota, avisos sem o limite fixo de R$ 10.000, o Kayak deixa de inventar conexões, o token fica fora das mensagens de erro e há testes automatizados.

## Licença

MIT. Veja o arquivo `LICENSE`.
