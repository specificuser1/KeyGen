import discord
from discord.ext import commands
import os
from dotenv import load_dotenv
import motor.motor_asyncio
import json
from pathlib import Path

load_dotenv()

# Load config
with open('config.json', 'r') as f:
    config = json.load(f)

class KeysManagerBot(commands.Bot):
    def __init__(self):
        super().__init__(
            command_prefix=config['bot_prefix'],
            intents=discord.Intents.all(),
            help_command=None
        )
        self.config = config
        self.mongo_client = None
        self.db = None
        
    async def setup_hook(self):
        # Connect to MongoDB
        try:
            self.mongo_client = motor.motor_asyncio.AsyncIOMotorClient(os.getenv('MONGODB_URI'))
            self.db = self.mongo_client['keys_manager']
            print("✅ MongoDB Connected")
        except Exception as e:
            print(f"❌ MongoDB Connection Error: {e}")
            print("Bot will continue without MongoDB")
        
        # Load cogs
        try:
            await self.load_extension('cogs.key_commands')
            await self.load_extension('cogs.panel')
            await self.load_extension('cogs.events')
        except Exception as e:
            print(f"❌ Error loading cogs: {e}")
        
        # Sync commands
        try:
            await self.tree.sync()
            print("✅ Commands Synced")
        except Exception as e:
            print(f"❌ Error syncing commands: {e}")
        
        print(f"✅ Bot is ready! Logged in as {self.user}")
        

bot = KeysManagerBot()

if __name__ == "__main__":
    if not os.getenv('DISCORD_TOKEN'):
        print("❌ ERROR: DISCORD_TOKEN not found in .env file!")
        exit(1)
    bot.run(os.getenv('DISCORD_TOKEN'))
