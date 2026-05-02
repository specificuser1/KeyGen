import discord
from discord.ext import commands
import os
from dotenv import load_dotenv
import motor.motor_asyncio
import json

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

        # Bot Activity
   # async def on_ready(self):
       # print(f'🌟 {self.user} has connected to Discord!')
      #  await self.change_presence(
         #   activity=discord.Activity(
          #      type=discord.ActivityType.watching,
        #        name=f"Keys | Dev: {config['dev_name']}"
   #         )
   #     )
        
        # Restore panels from database
        await self.restore_panels()
    
    async def restore_panels(self):
        """Restore panel views on all channels where they were previously loaded"""
        if self.db is None:
            print("⚠️ MongoDB not available, skipping panel restoration")
            return
        
        try:
            panels = await self.db.panels.find({}).to_list(length=None)
            restored_count = 0
            
            for panel_data in panels:
                try:
                    channel_id = panel_data.get('channel_id')
                    message_id = panel_data.get('message_id')
                    
                    if not channel_id or not message_id:
                        continue
                    
                    channel = self.get_channel(int(channel_id))
                    if not channel:
                        continue
                    
                    try:
                        message = await channel.fetch_message(int(message_id))
                        
                        # Create fresh view and embed
                        from cogs.panel import PersistentPanelView
                        view = PersistentPanelView(self)
                        panel_cog = self.get_cog('Panel')
                        if panel_cog:
                            embed = panel_cog.create_main_panel_embed()
                            await message.edit(embed=embed, view=view)
                            restored_count += 1
                    except discord.NotFound:
                        await self.db.panels.delete_one({"_id": panel_data["_id"]})
                    except Exception as e:
                        print(f"Error restoring panel {message_id}: {e}")
                        
                except Exception as e:
                    print(f"Error processing panel data: {e}")
            
            if restored_count > 0:
                print(f"✅ Restored {restored_count} panel(s)")
                
        except Exception as e:
            print(f"Error restoring panels: {e}")

bot = KeysManagerBot()

if __name__ == "__main__":
    if not os.getenv('DISCORD_TOKEN'):
        print("❌ ERROR: DISCORD_TOKEN not found in .env file!")
        exit(1)
    bot.run(os.getenv('DISCORD_TOKEN'))
