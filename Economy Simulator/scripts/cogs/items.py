import discord
from discord.ext import commands

from scripts.helpers import check_account, get_money, change_money, get_item_info, get_inv, add_inv, remove_inv,\
    net_worth, get_items, log
from scripts.views import YesNo

class Items(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @discord.slash_command(description="See the contents of an inventory, by default yours.")
    @discord.option(name="member", description="Another person whose inventory you want to see.")
    async def inventory(self, ctx, member: discord.Member = None):
        if await check_account(ctx.author, ctx):
            return
        embed = discord.Embed(title="Inventory", color=discord.Color.blue())
        if member is None:
            member = ctx.author
            embed.description = ""
        else:
            embed.description = f"Inventory of <@{member.id}>:"
        value = await net_worth(ctx.author.id) - await get_money(ctx.author)
        embed.set_footer(text=f"{ctx.author.name} • Value of inventory: ${value}", icon_url=str(member.avatar))
        inv = await get_inv(member)
        for item in inv:  # 0 is name, 1 is amount.
            desc = await get_item_info(item[0], "description")
            embed.add_field(name=f"{item[0]}: {item[1]}", value=desc, inline=False)
        if len(embed.fields) == 0:
            embed.description += "\n\n**Empty.**"
        await ctx.respond(embed=embed)

    @discord.slash_command(description="Consume an item.")
    @discord.option(name="item", description="The item you are consuming. Shows usable items in your inventory.",
                    autocomplete=discord.utils.basic_autocomplete(get_items))
    @discord.option(name="amount", description="Amount of the item you are using.", min_value=1)
    async def use(self, ctx, item, amount: int = 1):
        if await check_account(ctx.author, ctx):
            return
        if await get_item_info(item, "use") in [False or None]:
            await ctx.respond("Invalid item for usage. Use the autocorrect.")
            return
        use = await remove_inv(ctx.author, item, amount)
        if use == "notenough":
            await ctx.respond("You don't have enough of that item in your inventory.")
            return
        if use == "noitem":
            await ctx.respond("You do not have the item in your inventory.")
            return
        embed = discord.Embed(title="Item use", color=discord.Color.blue(),
                              description=f"You used {amount if amount != 1 else 'a'}" +
                                          f" **{item}**{'s' if amount != 1 else ''}.")
        # await update_data(ctx.author, value=shopdata[item]["use"]["status"], var="status")
        # embed.add_field(name="Status", value=shopdata[item]["use"]["status"].title())
        await ctx.respond(get_item_info(item, "use"), embed=embed)
        await log(f"Used {amount} {item}", ctx)

    @commands.slash_command(description="Sell an item to another user.")
    @discord.option(name="member", description="The member you are selling to.")
    @discord.option(name="item", description="The item you are selling. Shows sellable items in your inventory.",
                    autocomplete=discord.utils.basic_autocomplete(get_items))
    @discord.option(name="price", description="The price you are selling it at. If 0, you will give the item to them.",
                    min_value=0)
    @discord.option(name="amount", description="The amount of the item you are selling.", min_value=1)
    async def sell(self, ctx, member: discord.Member, item, price: int, amount: int = 1):
        if await check_account(ctx.author, ctx):
            return
        if await check_account(member, ctx):
            return
        if await get_item_info(item, "sellable") in [None, 0]:
            await ctx.respond("Invalid item for selling. Use the autocorrect.")
            return
        count = await get_inv(ctx.author, item)
        if count == 0:
            await ctx.respond("You do not have the item in your inventory.")
            return
        if count < amount:
            await ctx.respond("You don't have enough of that item in your inventory.")
            return
        if await get_money(member) < price != 0:
            await ctx.respond("They can't afford that.")
            return
        if price == 0:
            await add_inv(member, item, amount)
            embed = discord.Embed(title="Item Transfer", color=discord.Color.blue())
            embed.set_footer(text=ctx.author.name, icon_url=ctx.author.avatar)
            if amount == 1:
                embed.description = f"You gave {member.name} a **{item}**."
            else:
                embed.description = f"You gave {member.name} {amount} **{item}**s."
            await ctx.respond(embed=embed)
        else:
            view = YesNo(member)
            embed = discord.Embed(title="Sale Request", color=discord.Color.blurple())
            embed.description = (f"<@{member.id}>, do you wish to buy {amount} of "
                                 + f"**{item}**{'s' if amount != 1 else ''}"
                                 + f" from <@{ctx.author.id}>, for the price of ${price}?")
            embed.set_footer(text=f"{member.name} • Balance: ${await get_money(member)}", icon_url=str(member.avatar))
            interaction = await ctx.respond(f"<@{member.id}>", embed=embed, view=view)
            msg = await interaction.original_response()
            await view.wait()
            if view.value is None:
                await msg.reply("They did not respond in time.")
                view.children[0].disabled = True  # noqa
                view.children[1].disabled = True  # noqa
                await msg.edit(view=view)
            elif view.value:
                if price > await get_money(member):
                    await msg.reply("They accepted, but can't afford it anymore.")
                    return
                remove = await remove_inv(ctx.author, item, amount)
                if remove == "notenough":
                    await msg.reply("They accepted, but you don't have enough of the item anymore.")
                    return
                if remove == "noitem":
                    await msg.reply("They accepted, but you don't have the item anymore.")
                    return
                await change_money(member, -price)
                money = await change_money(ctx.author, price)
                await add_inv(member, item, amount)
                embed = discord.Embed(title="Sale", color=discord.Color.green())
                embed.description = (f"<@{member.id}> bought {amount} "
                                     + f"**{item}**{'s' if amount != 1 else ''} from"
                                     + f" <@{ctx.author.id}> for ${price}.")
                embed.set_footer(text=f"{ctx.author.name} • Balance: ${money}", icon_url=ctx.author.avatar)
                await msg.reply(embed=embed)
                await log(f"Sold {amount} {item} to {member.id} for ${price}", ctx)
            else:
                await msg.reply("They declined.")

    @commands.slash_command(description="Buy an item from another user.")
    @discord.option(name="member", description="The member you are buying from.")
    @discord.option(name="item",
                    description="The item you are buying from the user. Shows sellable items in their inventory.",
                    autocomplete=discord.utils.basic_autocomplete(get_items))
    @discord.option(name="price", description="The price you are buying it at.",
                    min_value=0)
    @discord.option(name="amount", description="The amount of the item you are buying.", min_value=1)
    async def buy(self, ctx, member: discord.Member, item, price: int, amount: int = 1):
        if await check_account(ctx.author, ctx):
            return
        if await check_account(member, ctx):
            return
        if await get_item_info(item, "sellable") in [None, 0]:
            await ctx.respond("Invalid item for buying. Use the autocorrect.")
            return
        count = await get_inv(member, item)
        if count == 0:
            await ctx.respond("They do not have the item in their inventory.")
            return
        if count < amount:
            await ctx.respond("They do not have enough of that item in their inventory.")
            return
        if await get_money(ctx.author) < price:
            await ctx.respond("You can't afford that.")
            return
        view = YesNo(member)
        embed = discord.Embed(title="Buy Request", color=discord.Color.blurple())
        embed.description = (f"<@{member.id}>, do you wish to sell {amount} of "
                             + f"your **{item}**s"
                             + f" to <@{ctx.author.id}>, in exchange for ${price}?")
        embed.set_footer(text=f"{member.name} • Balance: ${await get_money(member)}",
                         icon_url=str(member.avatar))
        interaction = await ctx.respond(f"<@{member.id}>", embed=embed, view=view)
        msg = await interaction.original_response()
        await view.wait()
        if view.value is None:
            await msg.reply("They did not respond in time.")
            view.children[0].disabled = True  # noqa
            view.children[1].disabled = True  # noqa
            await msg.edit(view=view)
        elif view.value:
            if price > await get_money(ctx.author):
                await msg.reply("They accepted, but you can't afford it anymore.")
                return
            count = await get_inv(member, item)
            if count == 0:
                await msg.reply("They accepted, but you do not have that item in your inventory anymore.")
                return
            if amount > count:
                await msg.reply("They accepted, but they don't have enough items to sell anymore.")
                return
            money = await change_money(ctx.author, -price)
            await change_money(member, price)
            await remove_inv(member, item, amount)
            await add_inv(ctx.author, item, amount)
            embed = discord.Embed(title="Purchase", color=discord.Color.yellow())
            embed.description = (f"<@{ctx.author.id}> bought {amount} "
                                 + f"**{item}**{'s' if amount != 1 else ''} from"
                                 + f" <@{member.id}> for ${price}.")
            embed.set_footer(text=f"{ctx.author.name} • Balance: ${money}", icon_url=ctx.author.avatar)
            await msg.reply(embed=embed)
            await log(f"Bought {amount} {item} from {member.id} for ${price}", ctx)
        else:
            await msg.reply("They declined.")

def setup(bot):
    bot.add_cog(Items(bot))
