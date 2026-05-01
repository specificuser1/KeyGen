import discord
from discord.ext import commands
from discord import app_commands
import os
from datetime import datetime
import random

class KeyCommands(commands.Cog):
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
    
    def get_random_key(self, category, duration):
        file_path = f"./{category}/{duration}.txt"
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
    
    async def send_log(self, interaction, key, category, duration):
        log_channel = self.bot.get_channel(int(self.bot.config['log_channel_id']))
        if not log_channel:
            return
            
        embed = discord.Embed(
            title="Key Generated",
            color=discord.Color.from_str(self.bot.config['embed_color']),
            timestamp=datetime.now()
        )
        embed.add_field(name="- User", value=f"{interaction.user.mention}\n({interaction.user.id})", inline=True)
        embed.add_field(name="- Category", value=category, inline=True)
        embed.add_field(name="- Duration", value=self.bot.config['duration_names'][duration], inline=True)
        embed.add_field(name="- Key", value=f"``{key}``", inline=False)
        embed.add_field(name="- Channel", value=interaction.channel.mention, inline=True)
        embed.set_footer(text=f"Powered by {self.bot.config['powered_by']} | Dev: {self.bot.config['dev_name']}")
        
        await log_channel.send(embed=embed)
    
    @app_commands.command(name="bp", description="Get a Bypass key")
    @has_permission()
    @app_commands.describe(
        member="Mention a member (optional)",
        amount="Amount of keys (optional)"
    )
    async def bp_key(self, interaction: discord.Interaction, member: discord.Member = None, amount: int = 1):
        await interaction.response.defer(ephemeral=True)
        
        files = self.get_available_files("BP")
        if not files:
            embed = discord.Embed(
                title="Chut Chut Chut",
                description="Bypass Keys Ka Stock Nahi Ha...",
                color=discord.Color.red()
            )
            embed.set_footer(text=f"Powered by {self.bot.config['powered_by']} | Dev: {self.bot.config['dev_name']}")
            await interaction.followup.send(embed=embed, ephemeral=True)
            return
        
        embed = discord.Embed(
            title="Available Bypass Keys",
            color=discord.Color.from_str(self.bot.config['embed_color'])
        )
        
        for duration, count in files.items():
            duration_name = self.bot.config['duration_names'].get(duration, duration)
            embed.add_field(
                name=f"{duration_name}",
                value=f"Stock: {count} keys",
                inline=True
            )
        
        embed.set_footer(text=f"Powered by {self.bot.config['powered_by']} | Dev: {self.bot.config['dev_name']}")
        
        view = KeySelectView(self.bot, "BP", member, amount)
        await interaction.followup.send(embed=embed, view=view, ephemeral=True)
    
    @app_commands.command(name="hk", description="Get a HK key")
    @has_permission()
    @app_commands.describe(
        member="Mention a member (optional)",
        amount="Amount of keys (optional)"
    )
    async def hk_key(self, interaction: discord.Interaction, member: discord.Member = None, amount: int = 1):
        await interaction.response.defer(ephemeral=True)
        
        files = self.get_available_files("HK")
        if not files:
            embed = discord.Embed(
                title="Chut Chut Chut",
                description="Hack Keys ka Stock Nahi Ha...",
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
                name=f"{duration_name}",
                value=f"Stock: {count} keys",
                inline=True
            )
        
        embed.set_footer(text=f"Powered by {self.bot.config['powered_by']} | Dev: {self.bot.config['dev_name']}")
        
        view = KeySelectView(self.bot, "HK", member, amount)
        await interaction.followup.send(embed=embed, view=view, ephemeral=True)

class KeySelectView(discord.ui.View):
    def __init__(self, bot, category, member, amount):
        super().__init__(timeout=60)
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
                    with open(os.path.join(folder_path, file), 'r') as f:
                        count = len([line for line in f if line.strip()])
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
                options=options,
                min_values=1,
                max_values=1
            )
            self.select_menu.callback = self.select_callback
            self.add_item(self.select_menu)
    
    async def select_callback(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        
        duration = self.select_menu.values[0]
        
        # Get keys
        keys = []
        for _ in range(self.amount):
            key = self.get_random_key(f"./{self.category}/{duration}.txt")
            if key:
                keys.append(key)
                # Save to redeem
                with open('./redeem.txt', 'a') as f:
                    f.write(f"{key}\n")
        
        if not keys:
            embed = discord.Embed(
                title="❌ Out of Stock",
                description="No keys available for this duration!",
                color=discord.Color.red()
            )
            embed.set_footer(text=f"Powered by {self.bot.config['powered_by']} | Dev: {self.bot.config['dev_name']}")
            await interaction.followup.send(embed=embed, ephemeral=True)
            return
        
        # Send keys to mentioned member or channel
        embed = discord.Embed(
            title="Key Generated",
            color=discord.Color.from_str(self.bot.config['embed_color']),
            timestamp=datetime.now()
        )
        embed.add_field(name="- Category", value=self.category, inline=True)
        embed.add_field(name="- Duration", value=self.bot.config['duration_names'][duration], inline=True)
        embed.add_field(name="- Amount", value=str(len(keys)), inline=True)
        
        keys_text = ""
        for i, key in enumerate(keys, 1):
            keys_text += f"Key {i}: ```{key}```\n"
        
        embed.add_field(name="Keys:", value=keys_text, inline=False)
        
        if self.member:
            embed.add_field(name="Generated For", value=self.member.mention, inline=True)
            try:
                dm_embed = discord.Embed(
                    title="You Received Keys",
                    description=f"Your {self.category} keys ({self.bot.config['duration_names'][duration]}):",
                    color=discord.Color.from_str(self.bot.config['embed_color'])
                )
                dm_embed.add_field(name="Keys:", value=keys_text, inline=False)
                dm_embed.set_footer(text=f"Powered by {self.bot.config['powered_by']} | Dev: {self.bot.config['dev_name']}")
                await self.member.send(embed=dm_embed)
            except:
                pass
        
        embed.set_footer(text=f"Powered by {self.bot.config['powered_by']} | Dev: {self.bot.config['dev_name']}")
        
        # Send to channel
        await interaction.channel.send(embed=embed)
        
        # Log
        log_channel = self.bot.get_channel(int(self.bot.config['log_channel_id']))
        if log_channel:
            log_embed = discord.Embed(
                title="Key Generated",
                color=discord.Color.from_str(self.bot.config['embed_color']),
                timestamp=datetime.now()
            )
            log_embed.add_field(name="- User", value=f"{interaction.user.mention}\n({interaction.user.id})", inline=True)
            log_embed.add_field(name="- Category", value=self.category, inline=True)
            log_embed.add_field(name="- Duration", value=self.bot.config['duration_names'][duration], inline=True)
            log_embed.add_field(name="- Amount", value=str(len(keys)), inline=True)
            log_embed.add_field(name="- Keys", value=keys_text, inline=False)
            log_embed.add_field(name="- Channel", value=interaction.channel.mention, inline=True)
            if self.member:
                log_embed.add_field(name="For", value=self.member.mention, inline=True)
            log_embed.set_footer(text=f"Powered by {self.bot.config['powered_by']} | Dev: {self.bot.config['dev_name']}")
            await log_channel.send(embed=log_embed)
        
        await interaction.followup.send("✅ Keys Generated", ephemeral=True)
    
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
        
        return selected_key

async def setup(bot):
    await bot.add_cog(KeyCommands(bot))
