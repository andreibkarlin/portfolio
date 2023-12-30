import discord
from discord.ext import commands

from scripts.helpers import db_fetch

class Finance(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @discord.slash_command(name="economy-stats", description="See statistics about the global economy.")
    async def stats(self, ctx):
        users = [x[0] for x in await db_fetch(f"SELECT money FROM bank")]
        companies = [x[0] for x in await db_fetch(f"SELECT money FROM companies")]
        governments = [x[0] for x in await db_fetch(f"SELECT money FROM governments")]
        embed = discord.Embed(title="Economy Stats", color=discord.Color.green(),
                              description=f"Money held by individuals: ${sum(users)}.\n" +
                                          f"Money held by companies: ${sum(companies)}.\n" +
                                          f"Money held by governments: ${sum(governments)}.\n\n" +
                                          f"Total money supply: ${sum(users) + sum(companies) + sum(governments)}.")
        await ctx.respond(embed=embed)

def setup(bot):
    bot.add_cog(Finance(bot))
