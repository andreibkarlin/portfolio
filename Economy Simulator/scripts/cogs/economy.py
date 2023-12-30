import math
import discord
from discord.ext import commands

from scripts.helpers import get_money, change_money, check_account, create_account, db_fetch, net_worth, log
from scripts.views import Pages, YesNo

class Economy(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.slash_command(description="Register a bank account with the bot, so you can use the economy.")
    async def register(self, ctx):
        await create_account(ctx)

    @commands.slash_command(description="See the bank account balance of a member.")
    @discord.option(name="member", description="Another person whose bank account you want to see.")
    async def balance(self, ctx, member: discord.Member = None):
        if member is None:
            member = ctx.author
        if await check_account(member, ctx):
            return
        money = await get_money(member)
        wealth = await net_worth(member.id)
        embed = discord.Embed(title="Balance", color=discord.Color.blue(), description=f"Balance of <@{member.id}>:")
        embed.add_field(name="Money", value=f"${money}")
        embed.add_field(name="Net Worth", value=f"${wealth}")
        embed.set_footer(text=member.name, icon_url=str(member.avatar))
        await ctx.respond(embed=embed)

    @commands.slash_command(description="Give another user money.")
    @discord.option(name="member", description="The person who you want to give money to.")
    @discord.option(name="amount", description="The amount of money you are giving.", min_value=0)
    async def pay(self, ctx, member: discord.Member, amount: int):
        if await check_account(ctx.author, ctx):
            return
        if await check_account(member, ctx):
            return
        if member == ctx.author:
            await ctx.respond("You can't pay yourself!")
            return
        if await get_money(ctx.author) < amount:
            await ctx.respond("You do not have the money to give.")
            return
        money = await change_money(ctx.author, -amount)
        await change_money(member, amount)
        embed = discord.Embed(title="Payment", description=f"You gave <@{member.id}> ${amount}.",
                              color=discord.Color.yellow())
        embed.set_footer(text=f"{ctx.author.name} • Balance: ${money}", icon_url=ctx.author.avatar)
        await ctx.respond(embed=embed)
        await log(f"${money} paid to {member.id}", ctx)

    @commands.slash_command(description="See the leaderboard.")
    @discord.option(name="page", description="Page of the leaderboard you want to check.", min_value=1)
    @discord.option(name="category", description="What type of entity you are looking at the leaderboard of.",
                    choices=["People", "Companies", "Governments"])
    @discord.option(name="sort", description="What you want the leaderboard to sort by.",
                    choices=["Bank Account", "Net Worth"])
    async def leaderboard(self, ctx, page: int = 1, category: str = "People", sort: str = "Bank Account"):
        if await check_account(ctx.author, ctx):
            return
        embed, pages = await generate_leaderboard_embed(ctx.author, page, sort, category)
        if page > pages:
            page = pages
        view = Pages(ctx.author, page, pages)
        view.disable_buttons()
        interaction = await ctx.respond(embed=embed, view=view)
        msg = await interaction.original_response()
        await recursive_leaderboard(ctx, view, page, msg, sort, category)

    @commands.slash_command(description="Rob people and steal their money.", cooldown=86400)
    @commands.cooldown(1, 86400, commands.BucketType.user)
    async def rob(self, ctx, member: discord.Member):
        if await check_account(ctx.author, ctx):
            return
        if await check_account(member, ctx):
            return
        if member == ctx.author:
            await ctx.respond("You can't rob yourself!")
            return
        their_money = await get_money(member)
        your_money = await get_money(ctx.author)
        if your_money <= 0:
            await ctx.respond("You have no money.")
            return
        if their_money <= 0:
            await ctx.respond("They don't have any money to rob.")
            return
        rob = min(your_money * 2, their_money // 3)
        # locks = await get_inv(member, "lock")
        embed = discord.Embed(title="Robbery confirmation", color=discord.Color.blurple())
        embed.description = f"Are you sure you want to do this?"  # They have {locks} lock{'' if locks==1 else 's'}."
        embed.set_footer(text=f"{ctx.author.name} • Balance: ${your_money}", icon_url=ctx.author.avatar)
        view = YesNo(ctx.author)
        interaction = await ctx.respond(embed=embed, view=view)
        msg = interaction.original_response()
        await view.wait()
        if view.value is None or not view.value:
            await msg.reply("You chose not to rob them, or timed out.")
            return
        # if locks > 0:
        #     lockpick = await get_inv(ctx.author, "lockpick")
        #     if lockpick == 0:
        #         await ctx.respond("You don't have a lockpick.")
        #         return
        #     else:
        #         await remove_inv(ctx.author, "lockpick", 1)
        #         if random.random() < 1 / (1 + locks):
        #             await remove_inv(member, "lock", locks)
        #         else:
        #             embed = discord.Embed(title="Robbery Fail", color=discord.Color.red())
        #             embed.description = "You were unable to pick their locks. Your lockpick was consumed."
        #             embed.set_footer(text=ctx.author.name, icon_url=ctx.author.avatar)
        #             await ctx.respond(embed=embed)
        #             return
        money = await change_money(ctx.author, rob)
        await change_money(member, -rob)
        embed = discord.Embed(title="Robbery", description=f"You robbed ${rob} from <@{member.id}>.",
                              color=discord.Color.green())
        # if locks > 0:
        #     embed.description += f"\nYou picked {locks} lock{'' if locks==1 else 's'}. Your lockpick was consumed."
        embed.set_footer(text=f"{ctx.author.name} • Balance: ${money}", icon_url=ctx.author.avatar)
        await ctx.respond(f"<@{member.id}>", embed=embed)
        await log(f"${rob} robbed from {member.id}", ctx)

async def recursive_leaderboard(ctx, view, page, msg, version, category):
    await view.wait()
    if view.value is None:
        view.children[0].disabled = True
        view.children[1].disabled = True
        await msg.edit(view=view)
    elif view.value != 0:
        page += view.value
        lb = await generate_leaderboard_embed(ctx.author, page, version, category)
        view = Pages(ctx.author, page, lb[1])
        view.disable_buttons()
        await msg.edit(embed=lb[0], view=view)
        await recursive_leaderboard(ctx, view, page, msg, version, category)

async def generate_leaderboard_embed(user, page, sort, category):
    # data = await db_fetch("SELECT * FROM bank ORDER BY money DESC LIMIT 10 OFFSET " + str((page - 1) * 10))
    if category == "People":
        data = await db_fetch(f"SELECT userid, money FROM bank ORDER BY money DESC")
    elif category == "Companies":
        data = await db_fetch(f"SELECT name, money FROM companies ORDER BY money DESC")
    else:  # Governments
        data = await db_fetch(f"SELECT name, money FROM governments ORDER BY money DESC")
    lb = []
    for entity in data:
        lb.append(entity)
        if category == "People":
            lb[-1] = (f"<@{entity[0]}>", entity[1])
        # if sort == "Net Worth":
        #     lb[-1]['money'] = await net_worth(person[0])
    lb.sort(key=lambda row: row[1], reverse=True)
    pages = math.ceil(len(lb) / 10)
    if page > pages:
        page = pages
    embed = discord.Embed(title=f"Richest {category}", description="", color=discord.Color.blue())
    embed.set_footer(text=f"Page {page}/{pages}")
    if category == "People":
        rank = "Invalid"
        for i in range(len(lb)):
            if lb[i][0] == user.id:
                rank = i + 1
                break
        embed.set_footer(text=f"Page {page}/{pages} • Your rank: {rank}")
    if sort == "Net Worth":
        embed.description = "By total net worth:\n"
    start = (page - 1) * 10
    for i in range(start, start + 10):
        if i < len(lb):
            embed.description += f"{i + 1}. {lb[i][0]} - ${lb[i][1]} \n"
        else:
            break
    return embed, pages

def setup(bot):
    bot.add_cog(Economy(bot))
