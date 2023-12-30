import discord
from discord.ext import commands
import logging

tester = False
bot = commands.Bot(intents=discord.Intents.all())
bot.remove_command("help")

@bot.event
async def on_ready():
    await bot.change_presence(activity=discord.Activity(name="with your mom.", type=discord.ActivityType.playing))
    print(f"Logged into {bot.user}")

cogs = ['economy', 'gambling', 'items', 'work', 'games', 'company', 'shop', 'shops', 'government', 'finance', 'help']
for cog in cogs:
    bot.load_extension(f"cogs.{cog}")

@bot.event
async def on_application_command_error(ctx: discord.ApplicationContext, error: discord.DiscordException):
    if isinstance(error, commands.CommandNotFound):
        return
    elif isinstance(error, commands.MissingPermissions):
        await ctx.respond("You don't have the permissions to do that.", ephemeral=True)
    elif isinstance(error, commands.BotMissingPermissions):
        await ctx.respond("I do not have the permissions to do that.", ephemeral=True)
    elif isinstance(error, commands.MissingPermissions):
        await ctx.respond("I am missing permissions.")
    elif isinstance(error, commands.MessageNotFound):
        await ctx.respond("I cannot reply to the original message.", ephemeral=True)
    elif isinstance(error, commands.CommandOnCooldown):
        cooldown = error.retry_after
        if cooldown > 3600:
            hours = round(cooldown // 3600)
            minutes = round((cooldown / 60) % 60, 2)
            msg = f"{hours} hour{'s' if hours != 1 else ''} and {minutes} minute{'s' if minutes != 1 else ''}"
        elif cooldown > 60:
            minutes = round(cooldown // 60)
            seconds = round(cooldown % 60, 2)
            msg = f"{minutes} minute{'s' if minutes != 1 else ''} and {seconds} second{'s' if seconds != 1 else ''}"
        else:
            seconds = round(cooldown, 2)
            msg = f"{seconds} second{'s' if seconds != 1 else ''}"
        await ctx.respond(f"You are on cooldown. Try again in {msg}.", ephemeral=True)
    else:
        try:
            await ctx.send("Unknown error. If this error was unexpected, report this to Meep so it can be fixed.")
        except discord.errors.Forbidden:
            return  # No perms to speak.
        raise error

@bot.command(description="Sends the bot's latency.")
async def ping(self, ctx):
    await ctx.respond(f"Pong! \n{round(self.bot.latency * 1000, 2)}ms")

@bot.command(description="Get information about the bot!")
async def about(self, ctx):  # noqa
    embed = discord.Embed(title="About", description="", color=discord.Color.blurple())
    embed.description = "This is a custom bot for Generic Decentralized Democracy, by Meep. " + \
                        "For a tutorial use the /tutorial command. " + \
                        "Current major features include: Working, Companies, Gambling, Shops, Government."
    await ctx.respond(embed=embed)

logging.basicConfig(filename="../files/logs.log", encoding="utf-8", level=logging.INFO,
                    format="%(levelname)s (%(asctime)s) - %(message)s", datefmt="%Y.%m.%d %I:%M:%S %p")

if tester:
    bot.run("MTA3NzI5MzE2NDc0ODA5OTc0NA.G6SbO0.GZsJ-3HAjVcBXb8UHCUgW85p_7PiRWmmaaM__s")
else:
    bot.run("MTA3NjM2MDY5NzI1ODE5Mjk3Ng.GVyvgS.3jWsg4dLivBAClZg8siVUDtTWouXU8x4zCRZhA")
