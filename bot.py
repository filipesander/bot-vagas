import asyncio
import hashlib
import os
from datetime import datetime, timedelta, timezone
from dotenv import load_dotenv
from telethon import TelegramClient
from telethon.tl.types import Channel, Message

load_dotenv()

API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
PHONE = os.getenv("PHONE")

KEYWORDS_INCLUDE = [kw.strip().lower() for kw in os.getenv("KEYWORDS_INCLUDE", "").split(",") if kw.strip()]
KEYWORDS_EXCLUDE = [kw.strip().lower() for kw in os.getenv("KEYWORDS_EXCLUDE", "").split(",") if kw.strip()]
KEYWORDS_JOB = [kw.strip().lower() for kw in os.getenv("KEYWORDS_JOB", "").split(",") if kw.strip()]

TARGET_GROUP = os.getenv("TARGET_GROUP", "Vagas")
DAYS_BACK = int(os.getenv("DAYS_BACK", "30"))

client = TelegramClient("session", API_ID, API_HASH)


def matches_filter(text: str) -> bool:
    """Verifica se o texto é uma vaga e passa no filtro de include/exclude."""
    if not text:
        return False
    text_lower = text.lower()

    is_job = any(kw in text_lower for kw in KEYWORDS_JOB)
    if not is_job:
        return False

    has_include = any(kw in text_lower for kw in KEYWORDS_INCLUDE)

    has_exclude = any(kw in text_lower for kw in KEYWORDS_EXCLUDE)

    return has_include and not has_exclude


def get_text_hash(text: str) -> str:
    """Gera um hash do texto normalizado para detectar duplicatas."""
    normalized = " ".join(text.lower().split())
    return hashlib.md5(normalized.encode()).hexdigest()


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
            if isinstance(entity, Channel) and entity.broadcast:
                continue
            groups.append(dialog)
    return groups


async def scan_group(client: TelegramClient, dialog, since: datetime) -> list:
    """Escaneia um grupo e retorna mensagens que passam no filtro."""
    matched = []
    try:
        async for msg in client.iter_messages(dialog.entity):
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

        target = await find_target_group(client)
        if not target:
            print(f"❌ Grupo '{TARGET_GROUP}' não encontrado!")
            print("   Crie um grupo com esse nome no Telegram e tente novamente.")
            return

        print(f"✅ Grupo destino encontrado: {TARGET_GROUP}")

        groups = await get_all_groups(client)
        groups = [g for g in groups if g.entity.id != target.id]

        print(f"📂 Grupos para escanear: {len(groups)}")
        print(f"💼 Palavras de vaga:    {', '.join(KEYWORDS_JOB)}")
        print(f"🔎 Palavras incluídas: {', '.join(KEYWORDS_INCLUDE)}")
        print(f"🚫 Palavras excluídas: {', '.join(KEYWORDS_EXCLUDE)}")

        since = datetime.now(timezone.utc) - timedelta(days=DAYS_BACK)
        print(f"📅 Buscando mensagens dos últimos {DAYS_BACK} dias (desde {since.strftime('%d/%m/%Y')})")
        print(f"\n{'═' * 50}\n")

        all_jobs = []  
        total_found = 0

        for i, dialog in enumerate(groups, 1):
            print(f"[{i}/{len(groups)}] Escaneando: {dialog.name}...", end=" ", flush=True)

            matched = await scan_group(client, dialog, since)

            if matched:
                print(f"✅ {len(matched)} vaga(s)")
                total_found += len(matched)
                for msg in matched:
                    all_jobs.append((msg, dialog.name))
            else:
                print("—")

        seen_hashes = set()
        unique_jobs = []

        for msg, group_name in all_jobs:
            msg_hash = get_text_hash(msg.text)
            if msg_hash not in seen_hashes:
                seen_hashes.add(msg_hash)
                unique_jobs.append((msg, group_name))

        total_duplicates = total_found - len(unique_jobs)

        unique_jobs.sort(key=lambda x: x[0].date, reverse=True)

        print(f"\n{'═' * 50}")
        print(f"📋 {len(unique_jobs)} vagas únicas | 🔄 {total_duplicates} duplicadas removidas")
        print(f"📤 Enviando para {TARGET_GROUP} (mais recentes primeiro)...")
        print(f"{'═' * 50}\n")

        total_sent = 0

        for msg, group_name in unique_jobs:
            try:
                formatted = format_message(msg, group_name)
                await client.send_message(target, formatted)
                total_sent += 1
                date_str = msg.date.strftime("%d/%m/%Y")
                print(f"  [{total_sent}/{len(unique_jobs)}] ✅ {date_str} — {group_name}")
                await asyncio.sleep(1.5)
            except Exception as e:
                print(f"  ⚠️  Erro ao enviar mensagem: {e}")

        end_date = datetime.now(timezone.utc)
        print(f"\n{'═' * 50}")
        print(f"📊 Resumo:")
        print(f"   📅 Período:          {since.strftime('%d/%m/%Y')} até {end_date.strftime('%d/%m/%Y')}")
        print(f"   📂 Grupos escaneados: {len(groups)}")
        print(f"   🔍 Vagas encontradas: {total_found}")
        print(f"   🔄 Duplicadas puladas: {total_duplicates}")
        print(f"   ✅ Vagas enviadas:    {total_sent}")
        print(f"   📬 Destino:           {TARGET_GROUP}")
        print(f"{'═' * 50}\n")


if __name__ == "__main__":
    asyncio.run(main())