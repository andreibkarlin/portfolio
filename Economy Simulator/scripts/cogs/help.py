import discord
from discord.ext import commands

from scripts.helpers import get_guides

class Help(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @discord.slash_command(description="See tutorials for the bot!")
    @discord.option(name="guide", description="Which guide do you want to see?",
                    choices=["Main Tutorial", "Money Making", "Shops", "Companies", "Government", "Gambling"])
    async def tutorial(self, ctx, guide: str):
        data = await get_guides()
        guide_desc = ""
        for line in data[guide]:
            guide_desc += line + "\n"
        embed = discord.Embed(title=guide, description=guide_desc, color=discord.Color.blurple())
        await ctx.respond(embed=embed)

def setup(bot):
    bot.add_cog(Help(bot))
