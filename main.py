import sys
print("=" * 50)
print("🔥 PYTHON SCRIPT STARTED!")
print(f"Python version: {sys.version}")
print("=" * 50)

import os
TOKEN = os.environ.get("BOT_TOKEN")
print(f"Token loaded: {TOKEN[:20] if TOKEN else 'NOT FOUND'}...")

print("\nTrying to import aiogram...")
from aiogram import Bot
print("✅ Aiogram imported successfully!")

print("\nStarting bot...")
import asyncio

async def main():
    print("🤖 Bot main() started")
    bot = Bot(token=TOKEN)
    me = await bot.get_me()
    print(f"✅ Bot connected! Username: @{me.username}")
    await bot.close()

if __name__ == "__main__":
    asyncio.run(main())
    print("✅ Script finished successfully!")
