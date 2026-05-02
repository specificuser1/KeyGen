import discord
from discord.ext import commands
from datetime import datetime

class Events(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        
    @commands.Cog.listener()
    async def on_ready(self):
        print("Events cog is ready!")
        
    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
        if isinstance(error, commands.CommandNotFound):
            return
            
        embed = discord.Embed(
            title="❌ Error",
            color=discord.Color.red()
        )
        
        if isinstance(error, commands.MissingPermissions):
            embed.description = "Gand Masti Na Kr Loray."
        elif isinstance(error, commands.MissingRole):
            embed.description = "Panel Use Krney Ky Liye Russian Chutt Chiye."
        elif isinstance(error, commands.CommandOnCooldown):
            embed.description = f"Mutti Time! Try in Later {error.retry_after:.1f}s"
        else:
            embed.description = f"❌ An error occurred!"
            print(f"Error: {error}")
            
        embed.set_footer(text=f"Powered by {self.bot.config['powered_by']} | Dev: {self.bot.config['dev_name']}")
        
        try:
            await ctx.send(embed=embed, ephemeral=True)
        except:
            pass

    @commands.Cog.listener()
    async def on_interaction(self, interaction: discord.Interaction):
        # Log interactions for debugging
        if interaction.type == discord.InteractionType.component:
            print(f"Component interaction: {interaction.user} used {interaction.data}")

async def setup(bot):
    await bot.add_cog(Events(bot))
