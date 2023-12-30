import discord
import math
from discord.ext import commands

from scripts.helpers import check_account, get_shops, get_company_from_id, get_offers, get_shop, calculate_price, \
    get_inv_company
from scripts.views import Pages

class Shops(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @staticmethod
    async def get_shops(ctx: discord.AutocompleteContext):  # noqa
        shops = await get_shops()
        return [shop[2] for shop in shops]

    @discord.slash_command(description="See shops, and the offers they have.")
    @discord.option(name="shop", description="A specific shop you want to view. If unset, will show all shops.",
                    autocomplete=discord.utils.basic_autocomplete(get_shops))
    async def shops(self, ctx, shop: str = None):
        if await check_account(ctx.author, ctx):
            return
        if shop is not None and await get_shop(shop, 'id') is None:
            await ctx.respond("Invalid shop. Use the autocorrect.")
            return
        page = 1
        if shop is None:
            embed, pages = await generate_shops_embed(page)
        else:
            embed, pages = await generate_offers_embed(page, shop)
        view = Pages(ctx.author, page, pages)
        view.disable_buttons()
        interaction = await ctx.respond(embed=embed, view=view)
        msg = await interaction.original_response()
        await pages_manager(ctx, view, page, msg, shop)

def setup(bot):
    bot.add_cog(Shops(bot))

async def pages_manager(ctx, view, page, msg, shop):
    await view.wait()
    if view.value is None:
        view.disable_buttons()
        await msg.edit(view=view)
    elif view.value != 0:
        page += view.value
        if shop is None:
            embed, pages = await generate_shops_embed(page)
        else:
            embed, pages = await generate_offers_embed(page, shop)
        view = Pages(ctx.author, page, pages)
        view.disable_buttons()
        await msg.edit(embed=embed, view=view)
        await pages_manager(ctx, view, page, msg, shop)

async def generate_shops_embed(page):
    shops = await get_shops()
    embed = discord.Embed(title="Shops", color=discord.Color.blue(),
                          description="View the offers of a shop with /shops. Accept an offer with /shop accept.")
    if len(shops) == 0:
        embed.description = "No shop yet. Create a shop with /shop create."
        return embed, 1
    pages = math.ceil(len(shops) / 5)
    if page > pages:
        page = pages
    embed.set_footer(text=f"Page {page}/{pages}")
    start = (page - 1) * 5
    for i in range(start, start + 5):
        if i < len(shops):
            if shops[i][4] == 1:
                embed.add_field(name=f"{shops[i][2]} - {await get_company_from_id(shops[i][1])}",
                                value=shops[i][3], inline=False)
        else:
            break
    return embed, pages

async def generate_offers_embed(page, shop):
    offers = await get_offers(shop)
    company_id = await get_shop(shop, 'company')
    embed = discord.Embed(title=shop, description=f"{await get_shop(shop, 'description')}\n\n",
                          color=discord.Color.blue())
    if await get_shop(shop, 'open') == 0:
        embed.description += "**This shop is closed.**\n\n"
    if len(offers) == 0:
        embed.description += "No offers yet. Add offers with /shop offers add."
        return embed, 1
    pages = math.ceil(len(offers) / 10)
    if page > pages:
        page = pages
    embed.set_footer(text=f"Page {page}/{pages}")
    start = (page - 1) * 10
    for i in range(start, start + 10):
        if i < len(offers):
            embed.description += f"{offers[i][1]}. **{offers[i][2]}**: {'Buy' if offers[i][4] == 1 else 'Sell'} " + \
                                f"{offers[i][3]} for ${await calculate_price(shop, offers[i][1])}. " + \
                                f"(Stock: {await get_inv_company(company_id, offers[i][3])})\n"
        else:
            break
    return embed, pages
