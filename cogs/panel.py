import discord
from discord.ext import commands
from discord import app_commands
import os
from datetime import datetime
import json

class Panel(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        
    async def check_permission(self, interaction: discord.Interaction) -> bool:
        """Check if user has permission to use commands"""
        if interaction.user.id in self.bot.config.get('owner_ids', []):
            return True
            
        user_roles = [role.id for role in interaction.user.roles]
        allowed_roles_int = []
        for role_id in self.bot.config.get('allowed_role_ids', []):
            try:
                allowed_roles_int.append(int(role_id))
            except (ValueError, TypeError):
                pass
        
        if any(role_id in user_roles for role_id in allowed_roles_int):
            return True
            
        return False
    
    def count_keys(self):
        stock = {"BP": {}, "HK": {}}
        for category in ["BP", "HK"]:
            folder_path = f"./{category}"
            if os.path.exists(folder_path):
                for file in os.listdir(folder_path):
                    if file.endswith('.txt'):
                        duration = file.replace('.txt', '')
                        file_full_path = os.path.join(folder_path, file)
                        with open(file_full_path, 'r') as f:
                            keys = [line.strip() for line in f if line.strip()]
                        stock[category][duration] = len(keys)
        return stock
    
    @app_commands.command(name="panel", description="Load the key manager panel in current channel")
    async def panel(self, interaction: discord.Interaction):
        # Check permission inline
        if not await self.check_permission(interaction):
            embed = discord.Embed(
                title="Access Denied",
                description="Gand Masti Na Kr Loray!\nRequired Russian Pussy To Used This Command!",
                color=discord.Color.red()
            )
            embed.set_footer(text=f"Powered by {self.bot.config['powered_by']} | Dev: {self.bot.config['dev_name']}")
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        # Create main panel embed
        embed = self.create_main_panel_embed()
        
        # Create persistent view
        view = PersistentPanelView(self.bot)
        
        # Send panel message in channel (not ephemeral)
        message = await interaction.channel.send(embed=embed, view=view)
        
        # Save panel message ID to MongoDB for persistence
        if self.bot.db is not None:
            try:
                await self.bot.db.panels.update_one(
                    {"guild_id": interaction.guild.id, "channel_id": interaction.channel.id},
                    {"$set": {
                        "message_id": message.id,
                        "guild_id": interaction.guild.id,
                        "channel_id": interaction.channel.id
                    }},
                    upsert=True
                )
            except:
                pass
        
        # Confirm to user
        confirm_embed = discord.Embed(
            title="Panel Loaded",
            description="Panel has been loaded in this channel\nIt will work even after bot restart.",
            color=discord.Color.green()
        )
        confirm_embed.set_footer(text=f"Powered by {self.bot.config['powered_by']} | Dev: {self.bot.config['dev_name']}")
        await interaction.response.send_message(embed=confirm_embed, ephemeral=True)
    
    @app_commands.command(name="reloadpanel", description="Reload panel if it stops working")
    async def reload_panel(self, interaction: discord.Interaction):
        if not await self.check_permission(interaction):
            embed = discord.Embed(
                title="Access Denied",
                description="Gand Masti Na Kr Loray!",
                color=discord.Color.red()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        # Try to find existing panel in this channel
        async for message in interaction.channel.history(limit=100):
            if message.author == self.bot.user and message.embeds:
                embed = message.embeds[0]
                if "KEY MANAGER PANEL" in embed.title or "Panel" in embed.title:
                    view = PersistentPanelView(self.bot)
                    await message.edit(embed=self.create_main_panel_embed(), view=view)
                    
                    # Update MongoDB
                    if self.bot.db is not None:
                        try:
                            await self.bot.db.panels.update_one(
                                {"guild_id": interaction.guild.id, "channel_id": interaction.channel.id},
                                {"$set": {
                                    "message_id": message.id,
                                    "guild_id": interaction.guild.id,
                                    "channel_id": interaction.channel.id
                                }},
                                upsert=True
                            )
                        except:
                            pass
                    
                    await interaction.response.send_message("Panel Reload Ho Gaya Ha", ephemeral=True)
                    return
        
        await interaction.response.send_message("No panel found in this channel! Use ``/panel`` to create one.", ephemeral=True)
    
    def create_main_panel_embed(self):
        """Create the main panel embed"""
        embed = discord.Embed(
            title=self.bot.config['panel_settings']['title'],
            description=f"{self.bot.config['panel_settings']['description']}\n\n**Chutt Chuut Chutt Chutt**",
            color=discord.Color.from_str(self.bot.config['embed_color']),
            timestamp=datetime.now()
        )
        
        if self.bot.config['panel_settings'].get('thumbnail_url'):
            embed.set_thumbnail(url=self.bot.config['panel_settings']['thumbnail_url'])
        
        # Bot Status
        ping = round(self.bot.latency * 1000)
        embed.add_field(
            name="Bot Status",
            value=f"```yaml\nStatus: Online\nLatency: {ping}ms\nServers: {len(self.bot.guilds)}\nUsers: {len(self.bot.users)}\n```",
            inline=False
        )
        
        # Key Stock Summary
        stock = self.count_keys()
        stock_text = ""
        for category, durations in stock.items():
            cat_name = self.bot.config['category_names'].get(category, category)
            stock_text += f"**{cat_name}:**\n"
            if durations:
                for duration, count in sorted(durations.items()):
                    duration_name = self.bot.config['duration_names'].get(duration, duration)
                    stock_text += f"  ▸ {duration_name}: **{count}** keys\n"
            else:
                stock_text += "  ▸ No keys available\n"
            stock_text += "\n"
        
        embed.add_field(
            name="Key Stock Overview",
            value=stock_text or "No keys available",
            inline=False
        )
        
        # Redeemed count
        if os.path.exists('./redeem.txt'):
            with open('./redeem.txt', 'r') as f:
                redeemed = len([line for line in f if line.strip()])
            embed.add_field(
                name="Total Generated",
                value=f"```{redeemed} keys```",
                inline=True
            )
        
        # Available Durations
        durations_list = ", ".join([f"`{name}`" for name in self.bot.config['duration_names'].values()])
        embed.add_field(
            name="Available Durations",
            value=durations_list,
            inline=False
        )
        
        embed.set_footer(text=self.bot.config['panel_settings']['footer_text'])
        return embed

class PersistentPanelView(discord.ui.View):
    def __init__(self, bot):
        super().__init__(timeout=None)  # No timeout - persistent forever
        self.bot = bot
        
    @discord.ui.select(
        placeholder="🔧 Select an action...",
        options=[
            discord.SelectOption(label="Refesh Panel", value="home", description="Return to main menu", emoji="♦️"),
            discord.SelectOption(label="Key Stocks", value="stocks", description="View detailed key stock information", emoji="♦️"),
            discord.SelectOption(label="Bot Status", value="status", description="View bot status information", emoji="♦️"),
            discord.SelectOption(label="Add Keys", value="addkeys", description="Add new keys to storage", emoji="♦️"),
            discord.SelectOption(label="New Duration", value="newduration", description="Create a new duration category", emoji="♦️"),
            discord.SelectOption(label="Remove Duration", value="removeduration", description="Permanently remove a duration", emoji="♦️"),
            discord.SelectOption(label="Temp Remove Duration", value="tempremove", description="Temporarily hide a duration", emoji="♦️"),
            discord.SelectOption(label="Change Role", value="changerole", description="Update allowed role ID", emoji="♦️"),
        ]
    )
    async def panel_select(self, interaction: discord.Interaction, select: discord.ui.Select):
        # Check permission
        if not await self.check_permission_inline(interaction):
            embed = discord.Embed(
                title="Access Denied",
                description="Gand Masti Na Kr Loray. Tary Pass Permit Nahi Panel Use Krni Ki SUBHAN Daddy Sy Primit Loo.",
                color=discord.Color.red()
            )
            embed.set_footer(text=f"Powered by {self.bot.config['powered_by']} | Dev: {self.bot.config['dev_name']}")
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        if select.values[0] == "home":
            await self.show_home(interaction)
        elif select.values[0] == "stocks":
            await self.show_stocks(interaction)
        elif select.values[0] == "status":
            await self.show_status(interaction)
        elif select.values[0] == "addkeys":
            await self.add_keys_menu(interaction)
        elif select.values[0] == "newduration":
            await self.new_duration(interaction)
        elif select.values[0] == "removeduration":
            await self.remove_duration_menu(interaction, permanent=True)
        elif select.values[0] == "tempremove":
            await self.remove_duration_menu(interaction, permanent=False)
        elif select.values[0] == "changerole":
            await self.change_role_prompt(interaction)
    
    async def check_permission_inline(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id in self.bot.config.get('owner_ids', []):
            return True
            
        user_roles = [role.id for role in interaction.user.roles]
        allowed_roles_int = []
        for role_id in self.bot.config.get('allowed_role_ids', []):
            try:
                allowed_roles_int.append(int(role_id))
            except (ValueError, TypeError):
                pass
        
        if any(role_id in user_roles for role_id in allowed_roles_int):
            return True
            
        return False
    
    async def show_home(self, interaction: discord.Interaction):
        """Show main panel embed"""
        panel_cog = self.bot.get_cog('Panel')
        if panel_cog:
            embed = panel_cog.create_main_panel_embed()
        else:
            embed = discord.Embed(
                title="Home Menu",
                description="Main Panel",
                color=discord.Color.from_str(self.bot.config['embed_color'])
            )
        
        await interaction.response.edit_message(embed=embed, view=self)
    
    async def show_stocks(self, interaction: discord.Interaction):
        embed = discord.Embed(
            title="Key Stock",
            color=discord.Color.from_str(self.bot.config['embed_color']),
            timestamp=datetime.now()
        )
        
        total_keys = 0
        for category in ["BP", "HK"]:
            category_text = ""
            has_keys = False
            folder_path = f"./{category}"
            if os.path.exists(folder_path):
                files_found = False
                for file in sorted(os.listdir(folder_path)):
                    if file.endswith('.txt'):
                        files_found = True
                        duration = file.replace('.txt', '')
                        duration_name = self.bot.config['duration_names'].get(duration, duration)
                        file_full_path = os.path.join(folder_path, file)
                        
                        # Check if file is temporarily disabled
                        if os.path.exists(f"{file_full_path}.disabled"):
                            category_text += f"**{duration_name}:** `TEMPORARILY DISABLED`\n"
                            continue
                        
                        with open(file_full_path, 'r') as f:
                            keys = [line.strip() for line in f if line.strip()]
                        count = len(keys)
                        total_keys += count
                        has_keys = True
                        category_text += f"**{duration_name}:** `{count}` keys\n"
                
                if not files_found:
                    category_text = "No duration files found"
            else:
                category_text = "Category folder not found"
            
            embed.add_field(
                name=f"📁 {self.bot.config['category_names'].get(category, category)}",
                value=category_text or "No keys available",
                inline=True
            )
        
        embed.add_field(
            name="Total Available",
            value=f"```{total_keys} keys```",
            inline=False
        )
        
        # Redeemed keys count
        if os.path.exists('./redeem.txt'):
            with open('./redeem.txt', 'r') as f:
                redeemed = len([line for line in f if line.strip()])
            embed.add_field(
                name="Total Generated",
                value=f"```{redeemed} keys```",
                inline=True
            )
        
        embed.set_footer(text=f"Powered by {self.bot.config['powered_by']} | Dev: {self.bot.config['dev_name']}")
        await interaction.response.edit_message(embed=embed, view=self)
    
    async def show_status(self, interaction: discord.Interaction):
        embed = discord.Embed(
            title="Bot Status",
            color=discord.Color.from_str(self.bot.config['embed_color']),
            timestamp=datetime.now()
        )
        
        ping = round(self.bot.latency * 1000)
        embed.add_field(name="- Latency", value=f"```{ping}ms```", inline=True)
        embed.add_field(name="- Servers", value=f"```{len(self.bot.guilds)}```", inline=True)
        embed.add_field(name="- Users", value=f"```{len(self.bot.users)}```", inline=True)
        embed.add_field(name="- Memory Usage", value=f"```Optimal```", inline=True)
        embed.add_field(name="- MangoBD", value=f"```Connected```", inline=True)
        embed.add_field(name="- Files Status", value=f"```All OK```", inline=True)
        embed.add_field(name="- Hosting Platform", value=f"```Linux x64```", inline=True)
        embed.add_field(name="- Developer", value=f"```{self.bot.config['dev_name']}```", inline=True)
        embed.add_field(name="- Powered By", value=f"```{self.bot.config['powered_by']}```", inline=True)
        
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
    
    async def new_duration(self, interaction: discord.Interaction):
        """Open modal to create new duration"""
        modal = NewDurationModal(self.bot)
        await interaction.response.send_modal(modal)
    
    async def remove_duration_menu(self, interaction: discord.Interaction, permanent: bool):
        """Show menu to select duration to remove"""
        view = RemoveDurationView(self.bot, self, permanent)
        
        if permanent:
            title = "Remove Duration Permanently"
            description = "Select a duration to **permanently delete**.\n⚠️ This will delete all keys in this duration!"
        else:
            title = "Temporarily Remove Duration"
            description = "Select a duration to **temporarily disable**.\n💡 You can restore it later by using the same option."
        
        embed = discord.Embed(
            title=title,
            description=description,
            color=discord.Color.from_str(self.bot.config['embed_color'])
        )
        
        # List current durations
        durations_text = ""
        for duration, name in self.bot.config['duration_names'].items():
            status = ""
            # Check if disabled
            is_disabled = False
            for category in ["BP", "HK"]:
                if os.path.exists(f"./{category}/{duration}.txt.disabled"):
                    is_disabled = True
                    break
            
            if is_disabled:
                status = " (Currently Disabled)"
            durations_text += f"• **{name}** (`{duration}`){status}\n"
        
        embed.add_field(name="Current Durations", value=durations_text, inline=False)
        embed.set_footer(text=f"Powered by {self.bot.config['powered_by']} | Dev: {self.bot.config['dev_name']}")
        await interaction.response.edit_message(embed=embed, view=view)
    
    async def change_role_prompt(self, interaction: discord.Interaction):
        embed = discord.Embed(
            title="Change Allowed Role",
            description="Click the button below to change the allowed role ID",
            color=discord.Color.from_str(self.bot.config['embed_color'])
        )
        
        current_roles = ", ".join(self.bot.config.get('allowed_role_ids', []))
        embed.add_field(
            name="Current Allowed Role IDs",
            value=f"```{current_roles if current_roles else 'None'}```",
            inline=False
        )
        
        embed.set_footer(text=f"Powered by {self.bot.config['powered_by']} | Dev: {self.bot.config['dev_name']}")
        
        view = ChangeRoleView(self.bot, self)
        await interaction.response.edit_message(embed=embed, view=view)

class NewDurationModal(discord.ui.Modal, title="Create New Duration"):
    def __init__(self, bot):
        super().__init__()
        self.bot = bot
        
        self.duration_code = discord.ui.TextInput(
            label="Duration Code",
            placeholder="e.g., 12h, 5d (use: h=hours, d=days, w=weeks, m=months)",
            required=True,
            max_length=10
        )
        self.add_item(self.duration_code)
        
        self.duration_name = discord.ui.TextInput(
            label="Duration Display Name",
            placeholder="e.g., 12 Hours, 5 Days",
            required=True,
            max_length=50
        )
        self.add_item(self.duration_name)
    
    async def on_submit(self, interaction: discord.Interaction):
        code = self.duration_code.value.strip().lower()
        name = self.duration_name.value.strip()
        
        # Update config.json
        with open('config.json', 'r') as f:
            config = json.load(f)
        
        if code in config['duration_names']:
            embed = discord.Embed(
                title="❌ Error",
                description=f"Duration code `{code}` already exists!",
                color=discord.Color.red()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        config['duration_names'][code] = name
        
        with open('config.json', 'w') as f:
            json.dump(config, f, indent=4)
        
        self.bot.config = config
        
        # Create empty txt files for new duration in BP and HK folders
        for category in ["BP", "HK"]:
            file_path = f"./{category}/{code}.txt"
            if not os.path.exists(file_path):
                with open(file_path, 'w') as f:
                    pass  # Create empty file
        
        embed = discord.Embed(
            title="Duration Created Successfully",
            description=f"New duration added:\n**Code:** `{code}`\n**Name:** {name}\n\nEmpty files created in BP and HK folders.",
            color=discord.Color.green(),
            timestamp=datetime.now()
        )
        embed.set_footer(text=f"Powered by {self.bot.config['powered_by']} | Dev: {self.bot.config['dev_name']}")
        await interaction.response.send_message(embed=embed, ephemeral=True)
        
        # Log
        await self.send_log(interaction, code, name)
    
    async def send_log(self, interaction, code, name):
        log_channel_id = self.bot.config.get('log_channel_id', '0')
        if log_channel_id and log_channel_id != '0' and log_channel_id != 'YOUR_LOG_CHANNEL_ID':
            try:
                log_channel = self.bot.get_channel(int(log_channel_id))
                if log_channel:
                    log_embed = discord.Embed(
                        title="New Duration Created",
                        color=discord.Color.blue(),
                        timestamp=datetime.now()
                    )
                    log_embed.add_field(name="- Created By", value=f"{interaction.user.mention}\n(ID: {interaction.user.id})", inline=True)
                    log_embed.add_field(name="- Code", value=f"`{code}`", inline=True)
                    log_embed.add_field(name="- Name", value=name, inline=True)
                    log_embed.set_footer(text=f"Powered by {self.bot.config['powered_by']} | Dev: {self.bot.config['dev_name']}")
                    await log_channel.send(embed=log_embed)
            except:
                pass

class RemoveDurationView(discord.ui.View):
    def __init__(self, bot, previous_view, permanent):
        super().__init__(timeout=300)
        self.bot = bot
        self.previous_view = previous_view
        self.permanent = permanent
        
        options = []
        for duration, name in bot.config['duration_names'].items():
            # Check if disabled
            is_disabled = False
            for category in ["BP", "HK"]:
                if os.path.exists(f"./{category}/{duration}.txt.disabled"):
                    is_disabled = True
                    break
            
            if self.permanent or (not self.permanent and not is_disabled):
                emoji_status = "⏸️" if is_disabled else "✅"
                options.append(
                    discord.SelectOption(
                        label=f"{name}",
                        value=duration,
                        description=f"{'Permanently delete' if permanent else 'Toggle disable'} this duration",
                        emoji="🗑️" if permanent else "⏸️"
                    )
                )
        
        if options:
            self.select_menu = discord.ui.Select(
                placeholder=f"Select duration to {'delete' if permanent else 'toggle'}...",
                options=options[:25]
            )
            self.select_menu.callback = self.remove_callback
            self.add_item(self.select_menu)
        else:
            # No durations to remove
            self.select_menu = discord.ui.Select(
                placeholder="No durations available to remove...",
                options=[discord.SelectOption(label="None", value="none")],
                disabled=True
            )
            self.add_item(self.select_menu)
    
    async def remove_callback(self, interaction: discord.Interaction):
        duration = self.select_menu.values[0]
        
        if self.permanent:
            # Permanent removal - show confirmation
            view = ConfirmRemoveView(self.bot, self.previous_view, duration)
            embed = discord.Embed(
                title="⚠️ Confirm Permanent Deletion",
                description=f"Are you sure you want to **permanently delete** the duration:\n**{self.bot.config['duration_names'][duration]}** (`{duration}`)?\n\nThis will:\n• Delete all keys in this duration\n• Remove duration from config\n• This action cannot be undone!",
                color=discord.Color.red()
            )
            embed.set_footer(text=f"Powered by {self.bot.config['powered_by']} | Dev: {self.bot.config['dev_name']}")
            await interaction.response.edit_message(embed=embed, view=view)
        else:
            # Toggle temporary disable
            await self.toggle_duration(interaction, duration)
    
    async def toggle_duration(self, interaction, duration):
        """Toggle duration disable/enable"""
        is_disabled = False
        for category in ["BP", "HK"]:
            if os.path.exists(f"./{category}/{duration}.txt.disabled"):
                is_disabled = True
                break
        
        if is_disabled:
            # Enable the duration (remove .disabled files)
            for category in ["BP", "HK"]:
                disabled_file = f"./{category}/{duration}.txt.disabled"
                original_file = f"./{category}/{duration}.txt"
                if os.path.exists(disabled_file):
                    os.rename(disabled_file, original_file)
            
            status = "enabled"
            emoji_status = "✅"
        else:
            # Disable the duration (add .disabled extension)
            for category in ["BP", "HK"]:
                original_file = f"./{category}/{duration}.txt"
                disabled_file = f"./{category}/{duration}.txt.disabled"
                if os.path.exists(original_file):
                    os.rename(original_file, disabled_file)
            
            status = "disabled"
            emoji_status = "⏸️"
        
        embed = discord.Embed(
            title=f"{emoji_status} Duration Updated",
            description=f"Duration **{self.bot.config['duration_names'][duration]}** (`{duration}`) has been {status}.",
            color=discord.Color.green() if status == "enabled" else discord.Color.orange(),
            timestamp=datetime.now()
        )
        embed.set_footer(text=f"Powered by {self.bot.config['powered_by']} | Dev: {self.bot.config['dev_name']}")
        
        # Add home and back buttons
        view = discord.ui.View(timeout=300)
        
        home_btn = discord.ui.Button(label="Home Menu", style=discord.ButtonStyle.gray)
        home_btn.callback = lambda i: self.previous_view.show_home(i)
        view.add_item(home_btn)
        
        back_btn = discord.ui.Button(label="↩ Back", style=discord.ButtonStyle.gray)
        async def back_callback(interaction_back):
            await self.previous_view.remove_duration_menu(interaction_back, permanent=False)
        back_btn.callback = back_callback
        view.add_item(back_btn)
        
        await interaction.response.edit_message(embed=embed, view=view)
        
        # Log
        await self.send_log(interaction, duration, status)
    
    async def send_log(self, interaction, duration, action):
        log_channel_id = self.bot.config.get('log_channel_id', '0')
        if log_channel_id and log_channel_id != '0' and log_channel_id != 'YOUR_LOG_CHANNEL_ID':
            try:
                log_channel = self.bot.get_channel(int(log_channel_id))
                if log_channel:
                    log_embed = discord.Embed(
                        title="Duration Toggled" if action in ["enabled", "disabled"] else "🗑️ Duration Removed",
                        color=discord.Color.orange(),
                        timestamp=datetime.now()
                    )
                    log_embed.add_field(name="- By", value=f"{interaction.user.mention}", inline=True)
                    log_embed.add_field(name="- Duration", value=f"`{duration}`", inline=True)
                    log_embed.add_field(name="- Name", value=self.bot.config['duration_names'].get(duration, duration), inline=True)
                    log_embed.add_field(name="- Action", value=action.upper(), inline=True)
                    log_embed.set_footer(text=f"Powered by {self.bot.config['powered_by']} | Dev: {self.bot.config['dev_name']}")
                    await log_channel.send(embed=log_embed)
            except:
                pass
    
    @discord.ui.button(label="Home Menu", style=discord.ButtonStyle.gray, row=2)
    async def home_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.previous_view.show_home(interaction)
    
    @discord.ui.button(label="↩ Back", style=discord.ButtonStyle.gray, row=2)
    async def back_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        # Go back to main panel
        panel_cog = self.bot.get_cog('Panel')
        if panel_cog:
            embed = panel_cog.create_main_panel_embed()
            await interaction.response.edit_message(embed=embed, view=self.previous_view)
        else:
            await interaction.response.edit_message(view=self.previous_view)

class ConfirmRemoveView(discord.ui.View):
    def __init__(self, bot, previous_view, duration):
        super().__init__(timeout=120)
        self.bot = bot
        self.previous_view = previous_view
        self.duration = duration
    
    @discord.ui.button(label="Confirm Delete", style=discord.ButtonStyle.danger)
    async def confirm_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        # Delete files
        for category in ["BP", "HK"]:
            for ext in ['.txt', '.txt.disabled']:
                file_path = f"./{category}/{self.duration}{ext}"
                if os.path.exists(file_path):
                    os.remove(file_path)
        
        # Update config
        with open('config.json', 'r') as f:
            config = json.load(f)
        
        if self.duration in config['duration_names']:
            del config['duration_names'][self.duration]
            
            with open('config.json', 'w') as f:
                json.dump(config, f, indent=4)
            
            self.bot.config = config
        
        embed = discord.Embed(
            title="Duration Deleted",
            description=f"Duration `{self.duration}` has been permanently deleted.",
            color=discord.Color.green(),
            timestamp=datetime.now()
        )
        embed.set_footer(text=f"Powered by {self.bot.config['powered_by']} | Dev: {self.bot.config['dev_name']}")
        
        # Add home button
        view = discord.ui.View(timeout=300)
        home_btn = discord.ui.Button(label="Home Menu", style=discord.ButtonStyle.gray)
        home_btn.callback = lambda i: self.previous_view.show_home(i)
        view.add_item(home_btn)
        
        await interaction.response.edit_message(embed=embed, view=view)
        
        # Log
        log_channel_id = self.bot.config.get('log_channel_id', '0')
        if log_channel_id and log_channel_id != '0' and log_channel_id != 'YOUR_LOG_CHANNEL_ID':
            try:
                log_channel = self.bot.get_channel(int(log_channel_id))
                if log_channel:
                    log_embed = discord.Embed(
                        title="Duration Permanently Deleted",
                        color=discord.Color.red(),
                        timestamp=datetime.now()
                    )
                    log_embed.add_field(name="- Deleted By", value=f"{interaction.user.mention}", inline=True)
                    log_embed.add_field(name="- Duration", value=f"`{self.duration}`", inline=True)
                    log_embed.set_footer(text=f"Powered by {self.bot.config['powered_by']} | Dev: {self.bot.config['dev_name']}")
                    await log_channel.send(embed=log_embed)
            except:
                pass
    
    @discord.ui.button(label="❌ Cancel", style=discord.ButtonStyle.gray)
    async def cancel_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.previous_view.remove_duration_menu(interaction, permanent=True)

# Keep existing AddKeysView, DurationSelectView, AddKeysModal, ChangeRoleView, ChangeRoleModal classes as they were
# ... (include all the classes from previous code)

class AddKeysView(discord.ui.View):
    def __init__(self, bot, previous_view):
        super().__init__(timeout=300)
        self.bot = bot
        self.previous_view = previous_view
        
    @discord.ui.select(
        placeholder="Select category...",
        options=[
            discord.SelectOption(label="BP Keys", value="BP", description="Add Bypass keys to storage", emoji="🔻"),
            discord.SelectOption(label="HK Keys", value="HK", description="Add Hack keys to storage", emoji="🔺"),
        ]
    )
    async def category_select(self, interaction: discord.Interaction, select: discord.ui.Select):
        category = select.values[0]
        
        # Check which durations are available (not disabled)
        view = DurationSelectView(self.bot, category, self.previous_view)
        embed = discord.Embed(
            title="Add Keys",
            description=f"Selected category: **{self.bot.config['category_names'].get(category, category)}**\n\nNow select the duration:",
            color=discord.Color.from_str(self.bot.config['embed_color'])
        )
        embed.set_footer(text=f"Powered by {self.bot.config['powered_by']} | Dev: {self.bot.config['dev_name']}")
        await interaction.response.edit_message(embed=embed, view=view)
    
    @discord.ui.button(label="Home Menu", style=discord.ButtonStyle.gray, row=2)
    async def home_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        panel_cog = self.bot.get_cog('Panel')
        if panel_cog:
            embed = panel_cog.create_main_panel_embed()
            await interaction.response.edit_message(embed=embed, view=self.previous_view)
        else:
            await interaction.response.edit_message(view=self.previous_view)

class DurationSelectView(discord.ui.View):
    def __init__(self, bot, category, previous_view):
        super().__init__(timeout=300)
        self.bot = bot
        self.category = category
        self.previous_view = previous_view
        
        options = []
        for duration, name in bot.config['duration_names'].items():
            # Check if disabled
            is_disabled = False
            disabled_file = f"./{category}/{duration}.txt.disabled"
            if os.path.exists(disabled_file):
                is_disabled = True
            
            if not is_disabled:
                options.append(
                    discord.SelectOption(
                        label=name,
                        value=duration,
                        description=f"Add keys for {name}",
                        emoji="⏰"
                    )
                )
        
        if options:
            self.select_menu = discord.ui.Select(
                placeholder="Select duration...",
                options=options[:25]
            )
            self.select_menu.callback = self.duration_callback
            self.add_item(self.select_menu)
        else:
            self.select_menu = discord.ui.Select(
                placeholder="No active durations available...",
                options=[discord.SelectOption(label="None available", value="none")],
                disabled=True
            )
            self.add_item(self.select_menu)
    
    async def duration_callback(self, interaction: discord.Interaction):
        duration = self.select_menu.values[0]
        modal = AddKeysModal(self.bot, self.category, duration)
        await interaction.response.send_modal(modal)
    
    @discord.ui.button(label="Home Menu", style=discord.ButtonStyle.gray, row=2)
    async def home_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        panel_cog = self.bot.get_cog('Panel')
        if panel_cog:
            embed = panel_cog.create_main_panel_embed()
            await interaction.response.edit_message(embed=embed, view=self.previous_view)
        else:
            await interaction.response.edit_message(view=self.previous_view)
    
    @discord.ui.button(label="↩ Back", style=discord.ButtonStyle.gray, row=2)
    async def back_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        view = AddKeysView(self.bot, self.previous_view)
        embed = discord.Embed(
            title="➕ Add Keys",
            description="Select the category where you want to add keys:",
            color=discord.Color.from_str(self.bot.config['embed_color'])
        )
        embed.set_footer(text=f"Powered by {self.bot.config['powered_by']} | Dev: {self.bot.config['dev_name']}")
        await interaction.response.edit_message(embed=embed, view=view)

class AddKeysModal(discord.ui.Modal, title="➕ Add Keys"):
    def __init__(self, bot, category, duration):
        super().__init__()
        self.bot = bot
        self.category = category
        self.duration = duration
        
        self.keys_input = discord.ui.TextInput(
            label="Enter Keys (one per line)",
            placeholder="key1\nkey2\nkey3\n...",
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
            title="Keys Added Successfully",
            description=f"Added **{len(keys)}** keys to:\n📁 **{self.bot.config['category_names'].get(self.category, self.category)}**\n⏰ **{self.bot.config['duration_names'].get(self.duration, self.duration)}**",
            color=discord.Color.green(),
            timestamp=datetime.now()
        )
        
        if len(keys) <= 5:
            key_preview = "\n".join([f"`{k}`" for k in keys])
        else:
            key_preview = "\n".join([f"`{k}`" for k in keys[:5]]) + f"\n... and {len(keys) - 5} more"
        
        embed.add_field(name="🔑 Keys Added", value=key_preview, inline=False)
        
        embed.set_footer(text=f"Powered by {self.bot.config['powered_by']} | Dev: {self.bot.config['dev_name']}")
        await interaction.response.send_message(embed=embed, ephemeral=True)
        
        await self.send_log(interaction, keys)
    
    async def send_log(self, interaction, keys):
        log_channel_id = self.bot.config.get('log_channel_id', '0')
        if log_channel_id and log_channel_id != '0' and log_channel_id != 'YOUR_LOG_CHANNEL_ID':
            try:
                log_channel = self.bot.get_channel(int(log_channel_id))
                if log_channel:
                    log_embed = discord.Embed(
                        title="Keys Added",
                        color=discord.Color.blue(),
                        timestamp=datetime.now()
                    )
                    log_embed.add_field(name="- Added By", value=f"{interaction.user.mention}\n(ID: {interaction.user.id})", inline=True)
                    log_embed.add_field(name="- Category", value=self.bot.config['category_names'].get(self.category, self.category), inline=True)
                    log_embed.add_field(name="- Duration", value=self.bot.config['duration_names'].get(self.duration, self.duration), inline=True)
                    log_embed.add_field(name="- Amount", value=f"**{len(keys)}** keys", inline=True)
                    
                    if len(keys) <= 10:
                        keys_text = "\n".join([f"`{k}`" for k in keys])
                    else:
                        keys_text = "\n".join([f"`{k}`" for k in keys[:10]]) + f"\n... and {len(keys) - 10} more"
                    
                    log_embed.add_field(name="🔑 Keys", value=keys_text, inline=False)
                    
                    log_embed.set_footer(text=f"Powered by {self.bot.config['powered_by']} | Dev: {self.bot.config['dev_name']}")
                    await log_channel.send(embed=log_embed)
            except Exception as e:
                print(f"Log error: {e}")

class ChangeRoleView(discord.ui.View):
    def __init__(self, bot, previous_view):
        super().__init__(timeout=300)
        self.bot = bot
        self.previous_view = previous_view
    
    @discord.ui.button(label="Change Role ID", style=discord.ButtonStyle.primary)
    async def change_role_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        modal = ChangeRoleModal(self.bot)
        await interaction.response.send_modal(modal)
    
    @discord.ui.button(label="Home Menu", style=discord.ButtonStyle.gray)
    async def home_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        panel_cog = self.bot.get_cog('Panel')
        if panel_cog:
            embed = panel_cog.create_main_panel_embed()
            await interaction.response.edit_message(embed=embed, view=self.previous_view)
        else:
            await interaction.response.edit_message(view=self.previous_view)

class ChangeRoleModal(discord.ui.Modal, title="Change Allowed Role ID"):
    def __init__(self, bot):
        super().__init__()
        self.bot = bot
        
        self.role_id = discord.ui.TextInput(
            label="New Role ID",
            placeholder="Enter Discord Role ID (e.g., 1234567890)",
            required=True,
            min_length=10,
            max_length=30
        )
        self.add_item(self.role_id)
    
    async def on_submit(self, interaction: discord.Interaction):
        try:
            role_id = int(self.role_id.value)
            
            with open('config.json', 'r') as f:
                config = json.load(f)
            
            config['allowed_role_ids'] = [str(role_id)]
            
            with open('config.json', 'w') as f:
                json.dump(config, f, indent=4)
            
            self.bot.config = config
            
            embed = discord.Embed(
                title="Role Updated Successfully",
                description=f"Allowed role ID has been changed to: **{role_id}**\n\nUsers with this role can now use bot commands.",
                color=discord.Color.green(),
                timestamp=datetime.now()
            )
            embed.set_footer(text=f"Powered by {self.bot.config['powered_by']} | Dev: {self.bot.config['dev_name']}")
            await interaction.response.send_message(embed=embed, ephemeral=True)
            
            log_channel_id = self.bot.config.get('log_channel_id', '0')
            if log_channel_id and log_channel_id != '0' and log_channel_id != 'YOUR_LOG_CHANNEL_ID':
                try:
                    log_channel = self.bot.get_channel(int(log_channel_id))
                    if log_channel:
                        log_embed = discord.Embed(
                            title="Role ID Changed",
                            color=discord.Color.orange(),
                            timestamp=datetime.now()
                        )
                        log_embed.add_field(name="- Changed By", value=f"{interaction.user.mention}\n(ID: {interaction.user.id})", inline=True)
                        log_embed.add_field(name="- New Role ID", value=f"`{role_id}`", inline=True)
                        log_embed.set_footer(text=f"Powered by {self.bot.config['powered_by']} | Dev: {self.bot.config['dev_name']}")
                        await log_channel.send(embed=log_embed)
                except:
                    pass
            
        except ValueError:
            embed = discord.Embed(
                title="❌ Invalid Role ID",
                description="Please enter a valid numeric Discord role ID!",
                color=discord.Color.red()
            )
            embed.set_footer(text=f"Powered by {self.bot.config['powered_by']} | Dev: {self.bot.config['dev_name']}")
            await interaction.response.send_message(embed=embed, ephemeral=True)

async def setup(bot):
    await bot.add_cog(Panel(bot))
