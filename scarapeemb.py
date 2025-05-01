from telethon import TelegramClient, events, errors
from telethon.sessions.string import _STRUCT_PREFORMAT, CURRENT_VERSION, StringSession
from telethon.tl.types import Channel, Chat

import asyncio
import base64
import ipaddress
import struct
import random
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s: %(message)s',
    datefmt='%H:%M:%S'
)


# Configuration
api_id = 11573285
api_hash = 'f2cc3fdc32197c8fbaae9d0bf69d2033'
#Aim
session_input = 'BQFYX_AAbZnjF8c7btbpraYFUvol58dj9S-BYFPYhsDY3NVBZuYd800uFHoNQv3UjkS2YUMZ9lNyWfR4h0D3hO-H2bLfil8IyqOzceDR74X7b8AdKymTOVhvFfBRs5KIWZcdnGOSB4F3qOHSyxt-0v5akXZnmKxb49NRKTYWWb7EIRT4m0uy5iox0SDCr2-dOspjDrie3ifHFneGPRRqLImya6Z2pPt7oos30QLgEk3Ptayf3pD47omjiwrK-eWpF9-iAvPGgk8djd27P6JoSaIm2l6hcBxOjqXV1kTUTa3Fn63DO0MSsiyjaYmxnse-5ocV6i04QcN7_a-JUtgbMxHn6dN6fgAAAAG3JYn-AA'
target_group_id = "https://t.me/+drtjD3_QVhY5M2Vl"
destination_channel_id = -1002515286715

def convert_pyrogram_session(session):
    pyro_format = {
        351: ">B?256sI?",
        356: ">B?256sQ?",
        362: ">BI?256sQ?",
    }
    ipv4_dc = {
        1: "149.154.175.53",
        2: "149.154.167.51",
        3: "149.154.175.100",
        4: "149.154.167.91",
        5: "91.108.56.130",
    }
    if len(session) in pyro_format:
        if len(session) in [351, 356]:
            dc_id, _, auth_key, _, _ = struct.unpack(
                pyro_format[len(session)],
                base64.urlsafe_b64decode(session + "=" * (-len(session) % 4)),
            )
        else:
            dc_id, _, _, auth_key, _, _ = struct.unpack(
                pyro_format[len(session)],
                base64.urlsafe_b64decode(session + "=" * (-len(session) % 4)),
            )
        new_session = CURRENT_VERSION + StringSession.encode(
            struct.pack(
                _STRUCT_PREFORMAT.format(4),
                dc_id,
                ipaddress.ip_address(ipv4_dc[dc_id]).packed,
                443,
                auth_key,
            )
        )
        return new_session
    return session
    
  
async def get_chat_entity(client, group_link_or_id):
    try:
        if isinstance(group_link_or_id, int) or group_link_or_id.lstrip('-').isdigit():
            if str(group_link_or_id).startswith("-100"):
                return await client.get_entity(int(group_link_or_id))
            else:
                return await client.get_entity(int(f"-100{group_link_or_id}"))
        else:
            return await client.get_entity(group_link_or_id)
    except Exception as e:
        logging.error(f"Error fetching chat entity: {e}")
        return None

async def scrape_members_and_send(client):
    entity = await get_chat_entity(client, target_group_id)
    if entity is None:
        logging.error("Failed to fetch target group entity.")
        return

    logging.info(f"Scraping members from group {entity.title}...")

    members = []
    async for user in client.iter_participants(entity):
        username = f"@{user.username}" if user.username else "NoUsername"
        members.append(f"{user.id}: {username}")

    # Write to file
    filename = "members.txt"
    with open(filename, "w", encoding="utf-8") as f:
        f.write("\n".join(members))

    logging.info(f"Scraped {len(members)} members. Sending file to destination channel...")
    await client.send_file(destination_channel_id, filename, caption="Here is the member list.")
    logging.info("File sent successfully!")

async def scrape_unhide_and_send(client):
    entity = await get_chat_entity(client, target_group_id)
    if entity is None:
        logging.error("Failed to fetch target group entity.")
        return

    logging.info(f"Scraping unhidden members from group {entity.title} via messages...")

    members = []
    async for message in client.iter_messages(entity, limit=1000):
        if message.sender_id:
            try:
                user = await client.get_entity(message.sender_id)
                username = f"@{user.username}" if user.username else "NoUsername"
                members.append(f"{user.id}: {username}")
            except Exception as e:
                logging.warning(f"Failed to fetch user {message.sender_id}: {e}")

    # Write to file
    filename = "members.txt"
    with open(filename, "w", encoding="utf-8") as f:
        f.write("\n".join(set(members)))  # Set to remove duplicates

    logging.info(f"Scraped {len(members)} unique members. Sending file to destination channel...")
    await client.send_file(destination_channel_id, filename, caption="Here is the member list (Unhidden Members).")
    logging.info("File sent successfully!")
    
# Main logic
async def main():
    session_string = convert_pyrogram_session(session_input)

    client = TelegramClient(
        session=StringSession(session_string),
        api_id=api_id,
        api_hash=api_hash,
    )

    await client.start()
    # await scrape_members_and_send(client)
    await scrape_unhide_and_send(client)
    logging.info("Bot started successfully.")

# Run the bot
logging.info("Launching bot...")
asyncio.run(main())