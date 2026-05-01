import discord
from discord.ext import commands
from discord import app_commands
import os
from datetime import datetime
import random
import json

class KeyCommands(commands.Cog):
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
    
    def get_available_files(self, category):
        folder_path = f"./{category}"
        files = {}
        if os.path.exists(folder_path):
            for file in os.listdir(folder_path):
                if file.endswith('.txt'):
                    file_path = os.path.join(folder_path, file)
                    with open(file_path, 'r') as f:
                        keys = [line.strip() for line in f if line.strip()]
                    files[file.replace('.txt', '')] = len(keys)
        return files
    
    @app_commands.command(name="bp", description="Get BP keys from stock")
    @app_commands.describe(
        member="Mention a member to send keys (optional)",
        amount="Number of keys to redeem (1-100, default: 1)"
    )
    async def bp_key(self, interaction: discord.Interaction, member: discord.Member = None, amount: int = 1):
        if not await self.check_permission(interaction):
            embed = discord.Embed(
                title="❌ Access Denied",
                description="You don't have permission to use this command!\n\nRequired: Bot Owner or Allowed Role",
                color=discord.Color.red()
            )
            embed.set_footer(text=f"Powered by {self.bot.config['powered_by']} | Dev: {self.bot.config['dev_name']}")
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        await interaction.response.defer(ephemeral=True)
        
        if amount < 1 or amount > 100:
            embed = discord.Embed(
                title="❌ Invalid Amount",
                description="Amount must be between 1 and 100!",
                color=discord.Color.red()
            )
            embed.set_footer(text=f"Powered by {self.bot.config['powered_by']} | Dev: {self.bot.config['dev_name']}")
            await interaction.followup.send(embed=embed, ephemeral=True)
            return
        
        files = self.get_available_files("BP")
        if not files:
            embed = discord.Embed(
                title="❌ No Keys Available",
                description="There are no Bypass keys available in stock!",
                color=discord.Color.red()
            )
            embed.set_footer(text=f"Powered by {self.bot.config['powered_by']} | Dev: {self.bot.config['dev_name']}")
            await interaction.followup.send(embed=embed, ephemeral=True)
            return
        
        embed = discord.Embed(
            title="Available BP Keys",
            description="Select a duration from the dropdown below:",
            color=discord.Color.from_str(self.bot.config['embed_color'])
        )
        
        for duration, count in files.items():
            duration_name = self.bot.config['duration_names'].get(duration, duration)
            emoji = "🔴" if count == 0 else "🟢" if count < 10 else "🟡"
            embed.add_field(
                name=f"{duration_name}",
                value=f"{emoji} Stock: **{count}** keys",
                inline=True
            )
        
        embed.set_footer(text=f"Powered by {self.bot.config['powered_by']} | Dev: {self.bot.config['dev_name']}")
        
        view = KeySelectView(self.bot, "BP", member, amount)
        await interaction.followup.send(embed=embed, view=view, ephemeral=True)
    
    @app_commands.command(name="hk", description="Get HK keys from stock")
    @app_commands.describe(
        member="Mention a member to send keys (optional)",
        amount="Number of keys to redeem (1-100, default: 1)"
    )
    async def hk_key(self, interaction: discord.Interaction, member: discord.Member = None, amount: int = 1):
        if not await self.check_permission(interaction):
            embed = discord.Embed(
                title="❌ Access Denied",
                description="You don't have permission to use this command!\n\nRequired: Bot Owner or Allowed Role",
                color=discord.Color.red()
            )
            embed.set_footer(text=f"Powered by {self.bot.config['powered_by']} | Dev: {self.bot.config['dev_name']}")
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        await interaction.response.defer(ephemeral=True)
        
        if amount < 1 or amount > 100:
            embed = discord.Embed(
                title="❌ Invalid Amount",
                description="Amount must be between 1 and 100!",
                color=discord.Color.red()
            )
            embed.set_footer(text=f"Powered by {self.bot.config['powered_by']} | Dev: {self.bot.config['dev_name']}")
            await interaction.followup.send(embed=embed, ephemeral=True)
            return
        
        files = self.get_available_files("HK")
        if not files:
            embed = discord.Embed(
                title="❌ No Keys Available",
                description="There are no HK keys available in stock!",
                color=discord.Color.red()
            )
            embed.set_footer(text=f"Powered by {self.bot.config['powered_by']} | Dev: {self.bot.config['dev_name']}")
            await interaction.followup.send(embed=embed, ephemeral=True)
            return
        
        embed = discord.Embed(
            title="Available HK Keys",
            description="Select a duration from the dropdown below:",
            color=discord.Color.from_str(self.bot.config['embed_color'])
        )
        
        for duration, count in files.items():
            duration_name = self.bot.config['duration_names'].get(duration, duration)
            emoji = "🔴" if count == 0 else "🟢" if count < 10 else "🟡"
            embed.add_field(
                name=f"{duration_name}",
                value=f"{emoji} Stock: **{count}** keys",
                inline=True
            )
        
        embed.set_footer(text=f"Powered by {self.bot.config['powered_by']} | Dev: {self.bot.config['dev_name']}")
        
        view = KeySelectView(self.bot, "HK", member, amount)
        await interaction.followup.send(embed=embed, view=view, ephemeral=True)

class KeySelectView(discord.ui.View):
    def __init__(self, bot, category, member, amount):
        super().__init__(timeout=120)
        self.bot = bot
        self.category = category
        self.member = member
        self.amount = amount
        
        options = []
        folder_path = f"./{category}"
        if os.path.exists(folder_path):
            for file in os.listdir(folder_path):
                if file.endswith('.txt'):
                    duration = file.replace('.txt', '')
                    duration_name = bot.config['duration_names'].get(duration, duration)
                    file_full_path = os.path.join(folder_path, file)
                    with open(file_full_path, 'r') as f:
                        count = len([line for line in f if line.strip()])
                    
                    if count > 0:
                        options.append(
                            discord.SelectOption(
                                label=duration_name,
                                value=duration,
                                description=f"Stock: {count} keys available",
                                emoji="🔑"
                            )
                        )
        
        if options:
            self.select_menu = discord.ui.Select(
                placeholder=f"Select {category} key duration...",
                options=options[:25],
                min_values=1,
                max_values=1
            )
            self.select_menu.callback = self.select_callback
            self.add_item(self.select_menu)
        else:
            self.select_menu = discord.ui.Select(
                placeholder="No keys available...",
                options=[discord.SelectOption(label="No keys available", value="none")],
                disabled=True
            )
            self.add_item(self.select_menu)
    
    async def select_callback(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        
        # Check permission again
        if not interaction.user.id in self.bot.config.get('owner_ids', []):
            user_roles = [role.id for role in interaction.user.roles]
            allowed_roles_int = [int(rid) for rid in self.bot.config.get('allowed_role_ids', []) if rid.isdigit()]
            if not any(role_id in user_roles for role_id in allowed_roles_int):
                embed = discord.Embed(
                    title="❌ Access Denied",
                    description="You don't have permission!",
                    color=discord.Color.red()
                )
                await interaction.followup.send(embed=embed, ephemeral=True)
                return
        
        duration = self.select_menu.values[0]
        
        # Get keys
        keys = []
        file_path = f"./{self.category}/{duration}.txt"
        
        for i in range(self.amount):
            if not os.path.exists(file_path):
                break
                
            with open(file_path, 'r') as f:
                available_keys = [line.strip() for line in f if line.strip()]
            
            if not available_keys:
                break
            
            key = random.choice(available_keys)
            available_keys.remove(key)
            
            with open(file_path, 'w') as f:
                f.write('\n'.join(available_keys))
            
            # Save to redeem file with details
            with open('./redeem.txt', 'a') as f:
                f.write(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {self.category}/{duration} - {interaction.user.name} - {key}\n")
            
            keys.append(key)
        
        if not keys:
            embed = discord.Embed(
                title="❌ Out of Stock",
                description="No keys available for this duration!",
                color=discord.Color.red()
            )
            embed.set_footer(text=f"Powered by {self.bot.config['powered_by']} | Dev: {self.bot.config['dev_name']}")
            await interaction.followup.send(embed=embed, ephemeral=True)
            return
        
        # Send keys to channel with beautiful embed
        embed = discord.Embed(
            title="Keys Generated",
            color=discord.Color.from_str(self.bot.config['embed_color']),
            timestamp=datetime.now()
        )
        
        embed.add_field(
            name="- Category",
            value=f"**{self.bot.config['category_names'].get(self.category, self.category)}**",
            inline=True
        )
        embed.add_field(
            name="- Duration",
            value=f"**{self.bot.config['duration_names'].get(duration, duration)}**",
            inline=True
        )
        embed.add_field(
            name="- Amount",
            value=f"**{len(keys)}** keys",
            inline=True
        )
        
        # Display keys in clean format
        if len(keys) <= 5:
            keys_display = ""
            for i, key in enumerate(keys, 1):
                keys_display += f"**#{i}:** ||`{key}`||\n"
        else:
            keys_display = ""
            for i, key in enumerate(keys[:5], 1):
                keys_display += f"**#{i}:** ||`{key}`||\n"
            keys_display += f"\n*... and {len(keys) - 5} more keys*"
        
        embed.add_field(
            name="Keys",
            value=keys_display,
            inline=False
        )
        
        if self.member:
            embed.add_field(
                name="- Generated For",
                value=self.member.mention,
                inline=True
            )
            
            # Try to DM the member
            try:
                dm_embed = discord.Embed(
                    title="Your Generated Key!",
                    description=f"Here are your **{self.category}** keys (**{self.bot.config['duration_names'].get(duration, duration)}**):",
                    color=discord.Color.from_str(self.bot.config['embed_color']),
                    timestamp=datetime.now()
                )
                
                dm_keys_display = ""
                for i, key in enumerate(keys, 1):
                    dm_keys_display += f"**#{i}:** ||`{key}`||\n"
                
                dm_embed.add_field(
                    name="Your Key",
                    value=dm_keys_display,
                    inline=False
                )
                dm_embed.set_footer(text=f"Powered by {self.bot.config['powered_by']} | Dev: {self.bot.config['dev_name']}")
                await self.member.send(embed=dm_embed)
            except:
                pass
        
        embed.set_footer(text=f"Powered by {self.bot.config['powered_by']} | Dev: {self.bot.config['dev_name']}")
        
        # Send to channel
        await interaction.channel.send(embed=embed)
        
        # Send detailed log
        await self.send_detailed_log(interaction, keys, duration)
        
        # Confirm to user
        confirm_embed = discord.Embed(
            title="✅ Success",
            description=f"Generated **{len(keys)}** {self.category} key(s)!",
            color=discord.Color.green()
        )
        await interaction.followup.send(embed=confirm_embed, ephemeral=True)
    
    async def send_detailed_log(self, interaction, keys, duration):
        log_channel_id = self.bot.config.get('log_channel_id', '0')
        if log_channel_id and log_channel_id != '0' and log_channel_id != 'YOUR_LOG_CHANNEL_ID':
            try:
                log_channel = self.bot.get_channel(int(log_channel_id))
                if log_channel:
                    log_embed = discord.Embed(
                        title="Key Generated Log",
                        color=discord.Color.from_str(self.bot.config['embed_color']),
                        timestamp=datetime.now()
                    )
                    
                    log_embed.add_field(
                        name="- Redeemed By",
                        value=f"{interaction.user.mention}\n**Name:** {interaction.user.name}\n**ID:** {interaction.user.id}",
                        inline=True
                    )
                    log_embed.add_field(
                        name="- Category",
                        value=self.bot.config['category_names'].get(self.category, self.category),
                        inline=True
                    )
                    log_embed.add_field(
                        name="- Duration",
                        value=self.bot.config['duration_names'].get(duration, duration),
                        inline=True
                    )
                    log_embed.add_field(
                        name="- Amount",
                        value=f"**{len(keys)}** keys",
                        inline=True
                    )
                    log_embed.add_field(
                        name="- Channel",
                        value=interaction.channel.mention,
                        inline=True
                    )
                    
                    if self.member:
                        log_embed.add_field(
                            name="- Redeemed For",
                            value=f"{self.member.mention}\n**Name:** {self.member.name}\n**ID:** {self.member.id}",
                            inline=True
                        )
                    
                    # Show ALL keys in log
                    if len(keys) <= 20:
                        keys_log = ""
                        for i, key in enumerate(keys, 1):
                            keys_log += f"**#{i}:** `{key}`\n"
                    else:
                        keys_log = f"*{len(keys)} keys redeemed - check redeem.txt for full list*"
                    
                    log_embed.add_field(
                        name="- Generated Keys",
                        value=keys_log,
                        inline=False
                    )
                    
                    log_embed.set_footer(text=f"Powered by {self.bot.config['powered_by']} | Dev: {self.bot.config['dev_name']}")
                    await log_channel.send(embed=log_embed)
            except Exception as e:
                print(f"Log error: {e}")

async def setup(bot):
    await bot.add_cog(KeyCommands(bot))
