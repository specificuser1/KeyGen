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
        # Check if user is owner
        if interaction.user.id in self.bot.config.get('owner_ids', []):
            return True
            
        # Check if user has allowed role
        user_roles = [role.id for role in interaction.user.roles]
        allowed_roles = self.bot.config.get('allowed_role_ids', [])
        
        # Convert role IDs to int for comparison
        allowed_roles_int = []
        for role_id in allowed_roles:
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
    
    def get_random_key(self, file_path):
        if not os.path.exists(file_path):
            return None
        
        with open(file_path, 'r') as f:
            keys = [line.strip() for line in f if line.strip()]
        
        if not keys:
            return None
        
        selected_key = random.choice(keys)
        keys.remove(selected_key)
        
        with open(file_path, 'w') as f:
            f.write('\n'.join(keys))
        
        # Save to redeem file
        with open('./redeem.txt', 'a') as f:
            f.write(f"{selected_key}\n")
        
        return selected_key
    
    @app_commands.command(name="bp", description="Get a BP key")
    @app_commands.describe(
        member="Mention a member (optional)",
        amount="Amount of keys (optional, default: 1)"
    )
    async def bp_key(self, interaction: discord.Interaction, member: discord.Member = None, amount: int = 1):
        # Check permission
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
                description="There are no BP keys available in stock!",
                color=discord.Color.red()
            )
            embed.set_footer(text=f"Powered by {self.bot.config['powered_by']} | Dev: {self.bot.config['dev_name']}")
            await interaction.followup.send(embed=embed, ephemeral=True)
            return
        
        embed = discord.Embed(
            title="🎮 Available BP Keys",
            color=discord.Color.from_str(self.bot.config['embed_color'])
        )
        
        for duration, count in files.items():
            duration_name = self.bot.config['duration_names'].get(duration, duration)
            embed.add_field(
                name=f"⏰ {duration_name}",
                value=f"📦 Stock: {count} keys",
                inline=True
            )
        
        embed.set_footer(text=f"Powered by {self.bot.config['powered_by']} | Dev: {self.bot.config['dev_name']}")
        
        view = KeySelectView(self.bot, "BP", member, amount)
        await interaction.followup.send(embed=embed, view=view, ephemeral=True)
    
    @app_commands.command(name="hk", description="Get a HK key")
    @app_commands.describe(
        member="Mention a member (optional)",
        amount="Amount of keys (optional, default: 1)"
    )
    async def hk_key(self, interaction: discord.Interaction, member: discord.Member = None, amount: int = 1):
        # Check permission
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
            title="🎮 Available HK Keys",
            color=discord.Color.from_str(self.bot.config['embed_color'])
        )
        
        for duration, count in files.items():
            duration_name = self.bot.config['duration_names'].get(duration, duration)
            embed.add_field(
                name=f"⏰ {duration_name}",
                value=f"📦 Stock: {count} keys",
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
                    
                    if count > 0:  # Only show options with keys available
                        options.append(
                            discord.SelectOption(
                                label=duration_name,
                                value=duration,
                                description=f"Stock: {count} keys",
                                emoji="🔑"
                            )
                        )
        
        if options:
            self.select_menu = discord.ui.Select(
                placeholder=f"Select {category} key duration...",
                options=options[:25],  # Discord limit is 25 options
                min_values=1,
                max_values=1
            )
            self.select_menu.callback = self.select_callback
            self.add_item(self.select_menu)
        else:
            # Add a disabled option if no keys available
            self.select_menu = discord.ui.Select(
                placeholder="No keys available...",
                options=[discord.SelectOption(label="No keys available", value="none")],
                disabled=True
            )
            self.add_item(self.select_menu)
    
    async def select_callback(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        
        if not interaction.user.id in self.bot.config.get('owner_ids', []):
            user_roles = [role.id for role in interaction.user.roles]
            allowed_roles_int = [int(rid) for rid in self.bot.config.get('allowed_role_ids', [])]
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
            
            # Save to redeem
            with open('./redeem.txt', 'a') as f:
                f.write(f"{key}\n")
            
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
        
        # Send keys to channel
        embed = discord.Embed(
            title="🎁 Key Redeemed Successfully",
            color=discord.Color.from_str(self.bot.config['embed_color']),
            timestamp=datetime.now()
        )
        embed.add_field(name="📁 Category", value=self.category, inline=True)
        embed.add_field(name="⏰ Duration", value=self.bot.config['duration_names'].get(duration, duration), inline=True)
        embed.add_field(name="📦 Amount", value=str(len(keys)), inline=True)
        
        keys_text = ""
        for i, key in enumerate(keys, 1):
            keys_text += f"**Key {i}:** ||{key}||\n"
        
        embed.add_field(name="🔑 Keys", value=keys_text, inline=False)
        
        if self.member:
            embed.add_field(name="👤 Redeemed For", value=self.member.mention, inline=True)
            try:
                dm_embed = discord.Embed(
                    title="🎁 You Received Keys!",
                    description=f"Here are your **{self.category}** keys (**{self.bot.config['duration_names'].get(duration, duration)}**):",
                    color=discord.Color.from_str(self.bot.config['embed_color'])
                )
                dm_embed.add_field(name="🔑 Keys", value=keys_text, inline=False)
                dm_embed.set_footer(text=f"Powered by {self.bot.config['powered_by']} | Dev: {self.bot.config['dev_name']}")
                await self.member.send(embed=dm_embed)
            except:
                pass
        
        embed.set_footer(text=f"Powered by {self.bot.config['powered_by']} | Dev: {self.bot.config['dev_name']}")
        
        # Send to channel
        await interaction.channel.send(embed=embed)
        
        # Send log
        log_channel_id = self.bot.config.get('log_channel_id', '0')
        if log_channel_id and log_channel_id != '0' and log_channel_id != 'YOUR_LOG_CHANNEL_ID':
            try:
                log_channel = self.bot.get_channel(int(log_channel_id))
                if log_channel:
                    log_embed = discord.Embed(
                        title="🔑 Key Redeemed",
                        color=discord.Color.from_str(self.bot.config['embed_color']),
                        timestamp=datetime.now()
                    )
                    log_embed.add_field(name="👤 User", value=f"{interaction.user.mention}\n(ID: {interaction.user.id})", inline=True)
                    log_embed.add_field(name="📁 Category", value=self.category, inline=True)
                    log_embed.add_field(name="⏰ Duration", value=self.bot.config['duration_names'].get(duration, duration), inline=True)
                    log_embed.add_field(name="📦 Amount", value=str(len(keys)), inline=True)
                    log_embed.add_field(name="📺 Channel", value=interaction.channel.mention, inline=True)
                    if self.member:
                        log_embed.add_field(name="👤 For", value=self.member.mention, inline=True)
                    log_embed.set_footer(text=f"Powered by {self.bot.config['powered_by']} | Dev: {self.bot.config['dev_name']}")
                    await log_channel.send(embed=log_embed)
            except:
                pass
        
        # Confirm to user
        confirm_embed = discord.Embed(
            title="✅ Success",
            description=f"Successfully redeemed {len(keys)} {self.category} key(s)!",
            color=discord.Color.green()
        )
        await interaction.followup.send(embed=confirm_embed, ephemeral=True)

async def setup(bot):
    await bot.add_cog(KeyCommands(bot))
