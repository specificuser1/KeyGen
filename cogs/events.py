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
        embed = discord.Embed(
            title="Maa ki Chut",
            color=discord.Color.red()
        )
        
        if isinstance(error, commands.MissingPermissions):
            embed.description = "Gand Masti Na Kr Loray."
        elif isinstance(error, commands.MissingRole):
            embed.description = "Teri Maa Ki Chuut Chiye Ya Command Use Krney Ky Liya."
        elif isinstance(error, commands.CommandOnCooldown):
            embed.description = f"Mutti Time, Kuch Deer Bd Try Kro {error.retry_after:.1f}s"
        elif isinstance(error, commands.BadArgument):
            embed.description = "❌ Invalid argument provided!"
        else:
            embed.description = f"❌ An error occurred: {str(error)}"
            
        embed.set_footer(text=f"Powered by {self.bot.config['powered_by']} | Dev: {self.bot.config['dev_name']}")
        await ctx.send(embed=embed, ephemeral=True)

async def setup(bot):
    await bot.add_cog(Events(bot))
