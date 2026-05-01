import discord
from discord.ext import commands
from discord import app_commands
import os
from datetime import datetime

class Panel(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        
    def has_permission():
        async def predicate(interaction: discord.Interaction):
            if interaction.user.id in interaction.client.config['owner_ids']:
                return True
            user_roles = [role.id for role in interaction.user.roles]
            if any(role_id in user_roles for role_id in interaction.client.config['allowed_role_ids']):
                return True
            return False
        return app_commands.check(predicate)
    
    def count_keys(self):
        stock = {"BP": {}, "HK": {}}
        for category in ["BP", "HK"]:
            folder_path = f"./{category}"
            if os.path.exists(folder_path):
                for file in os.listdir(folder_path):
                    if file.endswith('.txt'):
                        duration = file.replace('.txt', '')
                        with open(os.path.join(folder_path, file), 'r') as f:
                            keys = [line.strip() for line in f if line.strip()]
                        stock[category][duration] = len(keys)
        return stock
    
    @app_commands.command(name="panel", description="Open the key manager panel")
    @has_permission()
    async def panel(self, interaction: discord.Interaction):
        embed = discord.Embed(
            title=self.bot.config['panel_settings']['title'],
            description=self.bot.config['panel_settings']['description'],
            color=discord.Color.from_str(self.bot.config['embed_color']),
            timestamp=datetime.now()
        )
        
        if self.bot.config['panel_settings']['thumbnail_url']:
            embed.set_thumbnail(url=self.bot.config['panel_settings']['thumbnail_url'])
        
        # Bot Status
        embed.add_field(
            name="Bot Status",
            value=f"```\nOnline \nLatency: {round(self.bot.latency * 1000)}ms\nServers: {len(self.bot.guilds)}\n```",
            inline=False
        )
        
        # Key Stock Summary
        stock = self.count_keys()
        stock_text = ""
        for category, durations in stock.items():
            stock_text += f"**{category}:**\n"
            for duration, count in durations.items():
                duration_name = self.bot.config['duration_names'].get(duration, duration)
                stock_text += f"  {duration_name}: {count} keys\n"
        
        embed.add_field(
            name="Key Stock",
            value=stock_text or "Keys Nahi Ha",
            inline=False
        )
        
        embed.set_footer(text=self.bot.config['panel_settings']['footer_text'])
        
        view = PanelView(self.bot)
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)

class PanelView(discord.ui.View):
    def __init__(self, bot):
        super().__init__(timeout=None)
        self.bot = bot
        
    @discord.ui.select(
        placeholder="Select an action...",
        options=[
            discord.SelectOption(label="Key Stocks", value="stocks", description="View detailed key stock information"),
            discord.SelectOption(label="Bot Status", value="status", description="View bot status information"),
            discord.SelectOption(label="Add Keys", value="addkeys", description="Add keys to storage"),
            discord.SelectOption(label="Change Role", value="changerole", description="Change allowed role ID"),
        ]
    )
    async def panel_select(self, interaction: discord.Interaction, select: discord.ui.Select):
        if select.values[0] == "stocks":
            await self.show_stocks(interaction)
        elif select.values[0] == "status":
            await self.show_status(interaction)
        elif select.values[0] == "addkeys":
            await self.add_keys_menu(interaction)
        elif select.values[0] == "changerole":
            await self.change_role(interaction)
    
    async def show_stocks(self, interaction: discord.Interaction):
        embed = discord.Embed(
            title="Detailed Key Stock",
            color=discord.Color.from_str(self.bot.config['embed_color']),
            timestamp=datetime.now()
        )
        
        for category in ["BP", "HK"]:
            category_text = ""
            folder_path = f"./{category}"
            if os.path.exists(folder_path):
                for file in os.listdir(folder_path):
                    if file.endswith('.txt'):
                        duration = file.replace('.txt', '')
                        duration_name = self.bot.config['duration_names'].get(duration, duration)
                        with open(os.path.join(folder_path, file), 'r') as f:
                            keys = [line.strip() for line in f if line.strip()]
                        category_text += f"**{duration_name}:** {len(keys)} keys\n"
            
            if category_text:
                embed.add_field(
                    name=f"{self.bot.config['category_names'][category]}",
                    value=category_text,
                    inline=True
                )
        
        # Redeemed keys count
        with open('./redeem.txt', 'r') as f:
            redeemed = len([line for line in f if line.strip()])
        embed.add_field(
            name="Generated Keys",
            value=f"Total: {redeemed} keys",
            inline=False
        )
        
        embed.set_footer(text=f"Powered by {self.bot.config['powered_by']} | Dev: {self.bot.config['dev_name']}")
        await interaction.response.edit_message(embed=embed, view=self)
    
    async def show_status(self, interaction: discord.Interaction):
        embed = discord.Embed(
            title="Bot Status",
            color=discord.Color.from_str(self.bot.config['embed_color']),
            timestamp=datetime.now()
        )
        
        embed.add_field(
            name="Latency",
            value=f"```{round(self.bot.latency * 1000)}ms```",
            inline=True
        )
        embed.add_field(
            name="Servers",
            value=f"```{len(self.bot.guilds)}```",
            inline=True
        )
        embed.add_field(
            name="Users",
            value=f"```{len(self.bot.users)}```",
            inline=True
        )
        embed.add_field(
            name="Memory",
            value=f"```Working```",
            inline=True
        )
        embed.add_field(
            name="MangoBD Database",
            value=f"```Connected```",
            inline=True
        )
        
        embed.set_footer(text=f"Powered by {self.bot.config['powered_by']} | Dev: {self.bot.config['dev_name']}")
        await interaction.response.edit_message(embed=embed, view=self)
    
    async def add_keys_menu(self, interaction: discord.Interaction):
        view = AddKeysView(self.bot, self)
        embed = discord.Embed(
            title="Add Keys",
            description="Select the category where you want to add keys:",
            color=discord.Color.from_str(self.bot.config['embed_color'])
        )
        embed.set_footer(text=f"Powered by {self.bot.config['powered_by']} | Dev: {self.bot.config['dev_name']}")
        await interaction.response.edit_message(embed=embed, view=view)
    
    async def change_role(self, interaction: discord.Interaction):
        modal = ChangeRoleModal(self.bot)
        await interaction.response.send_modal(modal)

class AddKeysView(discord.ui.View):
    def __init__(self, bot, previous_view):
        super().__init__(timeout=120)
        self.bot = bot
        self.previous_view = previous_view
        
    @discord.ui.select(
        placeholder="Select category...",
        options=[
            discord.SelectOption(label="BP Keys", value="BP", description="Add BP keys", emoji="🔵"),
            discord.SelectOption(label="HK Keys", value="HK", description="Add HK keys", emoji="🟢"),
        ]
    )
    async def category_select(self, interaction: discord.Interaction, select: discord.ui.Select):
        self.category = select.values[0]
        view = DurationSelectView(self.bot, self.category, self.previous_view)
        embed = discord.Embed(
            title="➕ Add Keys",
            description=f"Selected category: **{self.bot.config['category_names'][self.category]}**\nNow select the duration:",
            color=discord.Color.from_str(self.bot.config['embed_color'])
        )
        embed.set_footer(text=f"Powered by {self.bot.config['powered_by']} | Dev: {self.bot.config['dev_name']}")
        await interaction.response.edit_message(embed=embed, view=view)

class DurationSelectView(discord.ui.View):
    def __init__(self, bot, category, previous_view):
        super().__init__(timeout=120)
        self.bot = bot
        self.category = category
        self.previous_view = previous_view
        
        options = []
        for duration, name in bot.config['duration_names'].items():
            options.append(
                discord.SelectOption(
                    label=name,
                    value=duration,
                    description=f"Add {name} keys"
                )
            )
        
        self.select_menu = discord.ui.Select(
            placeholder="Select duration...",
            options=options
        )
        self.select_menu.callback = self.duration_callback
        self.add_item(self.select_menu)
    
    async def duration_callback(self, interaction: discord.Interaction):
        self.duration = self.select_menu.values[0]
        modal = AddKeysModal(self.bot, self.category, self.duration)
        await interaction.response.send_modal(modal)

class AddKeysModal(discord.ui.Modal, title="Add Keys"):
    def __init__(self, bot, category, duration):
        super().__init__()
        self.bot = bot
        self.category = category
        self.duration = duration
        
        self.keys_input = discord.ui.TextInput(
            label="Keys (one per line)",
            placeholder="Enter keys here, each on a new line...",
            style=discord.TextStyle.paragraph,
            required=True,
            max_length=4000
        )
        self.add_item(self.keys_input)
    
    async def on_submit(self, interaction: discord.Interaction):
        keys = [key.strip() for key in self.keys_input.value.split('\n') if key.strip()]
        
        file_path = f"./{self.category}/{self.duration}.txt"
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        
        with open(file_path, 'a') as f:
            for key in keys:
                f.write(f"{key}\n")
        
        embed = discord.Embed(
            title="✅ Keys Added Successfully",
            description=f"Added **{len(keys)}** keys to **{self.bot.config['category_names'][self.category]} - {self.bot.config['duration_names'][self.duration]}**",
            color=discord.Color.green()
        )
        embed.set_footer(text=f"Powered by {self.bot.config['powered_by']} | Dev: {self.bot.config['dev_name']}")
        await interaction.response.send_message(embed=embed, ephemeral=True)

class ChangeRoleModal(discord.ui.Modal, title="Change Allowed Role ID"):
    def __init__(self, bot):
        super().__init__()
        self.bot = bot
        
        self.role_id = discord.ui.TextInput(
            label="New Role ID",
            placeholder="Enter the new role ID...",
            required=True,
            min_length=17,
            max_length=20
        )
        self.add_item(self.role_id)
    
    async def on_submit(self, interaction: discord.Interaction):
        try:
            role_id = int(self.role_id.value)
            import json
            
            with open('config.json', 'r') as f:
                config = json.load(f)
            
            config['allowed_role_ids'] = [str(role_id)]
            
            with open('config.json', 'w') as f:
                json.dump(config, f, indent=4)
            
            self.bot.config = config
            
            embed = discord.Embed(
                title="✅ Role Updated",
                description=f"Allowed role ID changed to: **{role_id}**",
                color=discord.Color.green()
            )
            embed.set_footer(text=f"Powered by {self.bot.config['powered_by']} | Dev: {self.bot.config['dev_name']}")
            await interaction.response.send_message(embed=embed, ephemeral=True)
            
        except ValueError:
            embed = discord.Embed(
                title="❌ Error",
                description="Invalid role ID! Please enter a valid numeric ID.",
                color=discord.Color.red()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)

async def setup(bot):
    await bot.add_cog(Panel(bot))
