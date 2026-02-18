# Bot Vagas Telegram

Bot em Python que escaneia todos os seus grupos do Telegram, filtra vagas por palavras-chave e encaminha as relevantes para um grupo específico.

## Como funciona

1. Conecta na sua conta do Telegram via Telethon
2. Lista todos os grupos/supergrupos que você participa
3. Escaneia as mensagens dos últimos X dias (configurável)
4. Filtra mensagens por palavras de inclusão e exclusão
5. Envia as vagas encontradas formatadas para o grupo destino

## Pré-requisitos

- Python 3.9+
- Conta no Telegram
- API ID e API Hash do Telegram

## Obtendo API ID e API Hash

1. Acesse [https://my.telegram.org/apps](https://my.telegram.org/apps)
2. Faça login com seu número de telefone
3. Clique em **"API development tools"**
4. Preencha o formulário (o nome do app pode ser qualquer coisa)
5. Copie o **API ID** (número) e o **API Hash** (string)

## Instalação

```bash
# Clone ou copie o projeto
cd bot-vagas

# Instale as dependências
pip install -r requirements.txt
```

## Configuração

Edite o arquivo `.env` com seus dados:

```env
API_ID=seu_api_id_aqui
API_HASH=seu_api_hash_aqui
PHONE=+5511999999999

TARGET_GROUP=Vagas
DAYS_BACK=30

KEYWORDS_INCLUDE=php,laravel,symfony,eloquent,backend php,dev php,desenvolvedor php,remoto
KEYWORDS_EXCLUDE=java,node,flutter,python,wordpress,estagio,hibrido
```

| Variável | Descrição |
|---|---|
| `API_ID` | ID da API do Telegram (número) |
| `API_HASH` | Hash da API do Telegram |
| `PHONE` | Seu número com DDI (ex: +5562999999999) |
| `TARGET_GROUP` | Nome exato do grupo destino (case-sensitive) |
| `DAYS_BACK` | Quantos dias para trás buscar |
| `KEYWORDS_INCLUDE` | Palavras que a vaga DEVE conter (pelo menos uma) |
| `KEYWORDS_EXCLUDE` | Palavras que a vaga NÃO pode conter (nenhuma) |

## Antes de rodar

Crie um grupo no Telegram com o nome exato configurado em `TARGET_GROUP` (padrão: **Vagas**).

## Executando

```bash
python bot.py
```

Na **primeira execução**, o Telethon vai pedir:
1. Seu número de telefone (digite com DDI: `+55...`)
2. O código de verificação enviado pelo Telegram (verifique no app do Telegram em "Mensagens Salvas" ou via SMS)

Após autenticar, o arquivo `session.session` é criado e as próximas execuções não pedem código novamente.

## Saída esperada

```
🤖 Conectado como: Seu Nome (5511999999999)

✅ Grupo destino encontrado: Vagas
📂 Grupos para escanear: 16
🔎 Palavras incluídas: php, laravel, symfony, ...
🚫 Palavras excluídas: java, node, flutter, ...
📅 Buscando mensagens dos últimos 30 dias (desde 19/01/2026)

══════════════════════════════════════════════════

[1/16] Escaneando: GrupoX... ✅ 3 vaga(s) encontrada(s)!
[2/16] Escaneando: GrupoY... —
...

══════════════════════════════════════════════════
📊 Resumo:
   Grupos escaneados: 16
   Vagas encontradas: 25
   Vagas enviadas:    25
   Destino:           Vagas
══════════════════════════════════════════════════
```

## Estrutura do projeto

```
bot-vagas/
├── bot.py              # Script principal
├── .env                # Configurações (não committar!)
├── requirements.txt    # Dependências Python
├── session.session     # Sessão do Telegram (gerado automaticamente)
└── README.md
```

## Observações

- O bot usa **sua conta pessoal** do Telegram (não é um bot do BotFather)
- Há um delay de 1.5s entre envios para evitar flood ban do Telegram
- Canais de broadcast são ignorados (só escaneia grupos e supergrupos)
- O grupo destino é removido automaticamente da lista de escaneamento
- O arquivo `session.session` contém sua sessão autenticada — não compartilhe
