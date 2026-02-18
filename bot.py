import asyncio
import os
from datetime import datetime, timedelta, timezone
from dotenv import load_dotenv
from telethon import TelegramClient
from telethon.tl.types import Channel, Chat, Message

load_dotenv()

# ── Configurações ──────────────────────────────────────────────
API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
PHONE = os.getenv("PHONE")

KEYWORDS_INCLUDE = [kw.strip().lower() for kw in os.getenv("KEYWORDS_INCLUDE", "").split(",") if kw.strip()]
KEYWORDS_EXCLUDE = [kw.strip().lower() for kw in os.getenv("KEYWORDS_EXCLUDE", "").split(",") if kw.strip()]

TARGET_GROUP = os.getenv("TARGET_GROUP", "Vagas")
DAYS_BACK = int(os.getenv("DAYS_BACK", "30"))

# ── Cliente ────────────────────────────────────────────────────
client = TelegramClient("session", API_ID, API_HASH)


def matches_filter(text: str) -> bool:
    """Verifica se o texto passa no filtro de include/exclude."""
    if not text:
        return False
    text_lower = text.lower()
    has_include = any(kw in text_lower for kw in KEYWORDS_INCLUDE)
    has_exclude = any(kw in text_lower for kw in KEYWORDS_EXCLUDE)
    return has_include and not has_exclude


def format_message(msg: Message, group_name: str) -> str:
    """Formata a mensagem para envio no grupo Vagas."""
    date_str = msg.date.strftime("%d/%m/%Y %H:%M")
    separator = "━" * 40
    return (
        f"📌 **Vaga encontrada!**\n"
        f"{separator}\n"
        f"📂 **Grupo:** {group_name}\n"
        f"📅 **Data:** {date_str}\n"
        f"{separator}\n\n"
        f"{msg.text}\n\n"
        f"{separator}"
    )


async def find_target_group(client: TelegramClient):
    """Encontra o grupo de destino pelo nome."""
    async for dialog in client.iter_dialogs():
        if dialog.name == TARGET_GROUP and dialog.is_group:
            return dialog.entity
    return None


async def get_all_groups(client: TelegramClient) -> list:
    """Retorna todos os grupos/supergrupos que o usuário participa."""
    groups = []
    async for dialog in client.iter_dialogs():
        if dialog.is_group or dialog.is_channel:
            entity = dialog.entity
            # Pula canais de broadcast (só pega grupos e supergrupos)
            if isinstance(entity, Channel) and entity.broadcast:
                continue
            groups.append(dialog)
    return groups


async def scan_group(client: TelegramClient, dialog, since: datetime) -> list:
    """Escaneia um grupo e retorna mensagens que passam no filtro."""
    matched = []
    try:
        async for msg in client.iter_messages(dialog.entity, offset_date=datetime.now(timezone.utc), reverse=False):
            if msg.date.replace(tzinfo=timezone.utc) < since:
                break
            if msg.text and matches_filter(msg.text):
                matched.append(msg)
    except Exception as e:
        print(f"  ⚠️  Erro ao escanear '{dialog.name}': {e}")
    return matched


async def main():
    async with client:
        await client.start(phone=PHONE)
        me = await client.get_me()
        print(f"\n🤖 Conectado como: {me.first_name} ({me.phone})\n")

        # ── Encontrar grupo destino ────────────────────────────────
        target = await find_target_group(client)
        if not target:
            print(f"❌ Grupo '{TARGET_GROUP}' não encontrado!")
            print("   Crie um grupo com esse nome no Telegram e tente novamente.")
            return

        print(f"✅ Grupo destino encontrado: {TARGET_GROUP}")

        # ── Listar grupos ──────────────────────────────────────────
        groups = await get_all_groups(client)
        # Remove o grupo destino da lista de busca
        groups = [g for g in groups if g.entity.id != target.id]

        print(f"📂 Grupos para escanear: {len(groups)}")
        print(f"🔎 Palavras incluídas: {', '.join(KEYWORDS_INCLUDE)}")
        print(f"🚫 Palavras excluídas: {', '.join(KEYWORDS_EXCLUDE)}")

        since = datetime.now(timezone.utc) - timedelta(days=DAYS_BACK)
        print(f"📅 Buscando mensagens dos últimos {DAYS_BACK} dias (desde {since.strftime('%d/%m/%Y')})")
        print(f"\n{'═' * 50}\n")

        total_found = 0
        total_sent = 0

        for i, dialog in enumerate(groups, 1):
            print(f"[{i}/{len(groups)}] Escaneando: {dialog.name}...", end=" ", flush=True)

            matched = await scan_group(client, dialog, since)

            if matched:
                print(f"✅ {len(matched)} vaga(s) encontrada(s)!")
                total_found += len(matched)

                for msg in matched:
                    try:
                        formatted = format_message(msg, dialog.name)
                        await client.send_message(target, formatted)
                        total_sent += 1
                        # Delay pra não tomar flood do Telegram
                        await asyncio.sleep(1.5)
                    except Exception as e:
                        print(f"  ⚠️  Erro ao enviar mensagem: {e}")
            else:
                print("—")

        # ── Resumo ─────────────────────────────────────────────────
        print(f"\n{'═' * 50}")
        print(f"📊 Resumo:")
        print(f"   Grupos escaneados: {len(groups)}")
        print(f"   Vagas encontradas: {total_found}")
        print(f"   Vagas enviadas:    {total_sent}")
        print(f"   Destino:           {TARGET_GROUP}")
        print(f"{'═' * 50}\n")


if __name__ == "__main__":
    asyncio.run(main())