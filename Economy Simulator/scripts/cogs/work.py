import discord
from discord.ext import commands

from scripts.helpers import check_account, add_inv, get_inv, remove_inv, log
from scripts.minigames import NumPad, SelectPad
from scripts.views import YesNo

class Work(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    work = discord.SlashCommandGroup("work", "Commands relating to working.")

    @work.command(description="Get wood by chopping trees.")
    async def chop(self, ctx):
        if await check_account(ctx.author, ctx):
            return
        embed = discord.Embed(title="Chopping trees", color=discord.Color.blurple(),
                              description="Hit all of the buttons in increasing order." +
                                          "\nTrees chopped: **0**\nProgress: 0%")
        embed.set_footer(text=f"{ctx.author.name} • Wood: {await get_inv(ctx.author, 'Wood')}",
                         icon_url=ctx.author.avatar)
        progress = 0
        requirement = 4
        trees = 0
        view = discord.ui.View
        view.value = True
        interaction = await ctx.respond(embed=embed)
        msg = await interaction.original_response()
        while view.value is not None:
            view = NumPad(ctx.author, 3)
            await msg.edit(embed=embed, view=view)
            await view.wait()
            if view.value == "Win":
                progress += 1
            if progress >= requirement:
                trees += 1
                progress -= requirement
                embed.colour = discord.Color.green()
                await add_inv(ctx.author, "Wood")
            embed.description = "Hit all of the buttons in increasing order." + \
                f"\nTrees chopped: {trees}\nProgress: {round(100 * progress / requirement)}%"
            embed.set_footer(text=f"{ctx.author.name} • Wood: {await get_inv(ctx.author, 'Wood')}",
                             icon_url=ctx.author.avatar)
            try:
                await msg.edit(embed=embed, view=view)
            except discord.errors.HTTPException:
                await msg.edit("You broke it.")
        embed = discord.Embed(title="Chopping trees", description=f"You timed out.\nTrees chopped: **{trees}**",
                              color=(discord.Color.green() if trees > 0 else discord.Color.blurple()))
        for button in view.children:
            button.disabled = True
        await msg.edit(embed=embed, view=view)
        if trees > 0:
            await log(f"Trees chopped for {trees} wood", ctx)

    @work.command(description="Craft items from raw materials.")
    @discord.option(name="recipe", description="The crafting recipe you are using",
                    choices=["Paper (1 wood = 10 paper)"])
    async def craft(self, ctx, recipe):
        if await check_account(ctx.author, ctx):
            return
        embed = discord.Embed(title="Crafting confirmation", color=discord.Color.blurple())
        embed.description = "Are you sure you want to consume 1 wood to craft 10 paper? " + \
                            "If you fail the minigame this will not be refunded."
        embed.set_footer(text=f"{ctx.author.name} • Wood: {await get_inv(ctx.author, 'Wood')}",
                         icon_url=ctx.author.avatar)
        view = YesNo(ctx.author)
        interaction = await ctx.respond(embed=embed, view=view)
        msg = await interaction.original_response()
        await view.wait()
        if view.value is None or not view.value:
            await msg.reply("Cancelled.")
            return
        use = await remove_inv(ctx.author, "Wood", 1)
        if use == "notenough":
            await ctx.respond("You don't have enough of that item in your inventory.")
            return
        if use == "noitem":
            await ctx.respond("You do not have the item in your inventory.")
            return
        embed = discord.Embed(title="Crafting paper", color=discord.Color.blurple(),
                              description="Hit the red button.\nProgress: 0%")
        embed.set_footer(text=f"{ctx.author.name}", icon_url=ctx.author.avatar)
        progress = 0
        requirement = 10
        view = discord.ui.View
        view.value = True
        msg = await msg.reply(embed=embed)
        while view.value is not None:
            view = SelectPad(ctx.author, 3)
            await msg.edit(embed=embed, view=view)
            await view.wait()
            if view.value == "Loss":
                embed = discord.Embed(title="Crafting Paper", description=f"You failed.", color=discord.Color.red())
                view.disable_all_items()
                await msg.edit(embed=embed, view=view)
                await log(f"Crafting failed, 1 wood consumed", ctx)
                return
            elif view.value == "Win":
                progress += 1
                if progress >= requirement:
                    embed = discord.Embed(title="Crafting Paper", description=f"You have crafted 10 paper.",
                                          color=discord.Color.green())
                    await add_inv(ctx.author, "Paper", 10)
                    view.disable_all_items()
                    await msg.edit(embed=embed, view=view)
                    await log(f"Crafting succeeded, 1 wood consumed for 10 paper", ctx)
                    return
            embed.description = f"Hit the red button.\nProgress: {round(100 * progress / requirement)}%"
            embed.set_footer(text=f"{ctx.author.name}", icon_url=ctx.author.avatar)
        embed = discord.Embed(title="Crafting Paper", description=f"You timed out.", color=discord.Color.red())
        view.disable_all_items()
        await msg.edit(embed=embed, view=view)
        await log(f"Crafting failed due to time out, 1 wood consumed", ctx)

def setup(bot):
    bot.add_cog(Work(bot))
