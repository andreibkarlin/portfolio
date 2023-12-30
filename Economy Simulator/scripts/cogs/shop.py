import discord
from discord.ext import commands

from scripts.helpers import check_account, get_companies, get_company, remove_inv, add_inv, add_shop, get_shops, \
    get_company_from_id, get_shop, change_shop, delete_shop, get_all_items, get_item_info, add_offer, get_offers, \
    calculate_price, get_offer, get_money, get_inv, change_money, add_inv_company, remove_inv_company, \
    change_money_company, change_offer, delete_offer, log
from scripts.views import YesNo, ValueModal

class Shop(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    shop = discord.SlashCommandGroup("shop", "Commands relating to shops.")
    offer = shop.create_subgroup("offer", "Commands relating to shop offers.")

    # region Autocomplete
    @staticmethod
    async def get_companies(ctx: discord.AutocompleteContext):
        companies = await get_companies()
        result = [company[1] for company in companies]
        result2 = []
        for company in result:
            if await get_company(company, "owner") == ctx.interaction.user.id:
                result2.append(company)
        return result2

    @staticmethod
    async def get_shops(ctx: discord.AutocompleteContext):
        shops = await get_shops()
        if ctx.command.name in ["manage", "add", "remove"]:
            result = []
            for shop in shops:
                company = await get_company_from_id(shop[1])
                if await get_company(company, "owner") == ctx.interaction.user.id:
                    result.append(shop[2])
            return result
        else:
            return [shop[2] for shop in shops]

    @staticmethod
    async def get_offers(ctx: discord.AutocompleteContext):
        shop = ctx.options["shop"]
        if shop is None:
            return []
        offers = await get_offers(shop)
        return [offer[2] for offer in offers]

    @staticmethod
    async def get_all_items(ctx: discord.AutocompleteContext):  # noqa
        items = await get_all_items()
        return [item[0] for item in items]
    # endregion

    @shop.command(description="Create a shop.")
    @discord.option(name="company", description="The name of the company you own that you are creating the shop for.",
                    autocomplete=discord.utils.basic_autocomplete(get_companies))
    @discord.option(name="name", description="The name of the shop.", max_length=50)
    async def create(self, ctx, company: str, name: str):
        if await check_account(ctx.author, ctx):
            return
        if await get_company(company, 'owner') != ctx.author.id:
            await ctx.respond("You are not the owner of that company.")
            return
        if await get_shop(name, "name") is not None:
            await ctx.respond(f"A shop with that name already exists.")
            return
        check = await remove_inv_company(company, "Wood", 10)
        if check == "notenough":
            await ctx.respond("The company doesn't have enough wood. You need 10.")
            return
        if check == "noitem":
            await ctx.respond("The company doesn't have any wood. You need 10.")
            return
        view = YesNo(ctx.author)
        embed = discord.Embed(title="Create a shop", color=discord.Color.blurple(),
                              description="Do you confirm that you wish to start a shop? This will cost 10 wood.")
        embed.set_footer(text=f"{ctx.author.name}", icon_url=ctx.author.avatar)
        interaction = await ctx.respond(embed=embed, view=view)
        msg = await interaction.original_response()
        await view.wait()
        if view.value is None:
            view.children[0].disabled = True  # noqa
            view.children[1].disabled = True  # noqa
            await msg.edit(view=view)
        if view.value in [None, False]:
            await msg.reply("Cancelled.")
            await add_inv(ctx.author, "Wood", 10)
            return
        company_id = await get_company(company, 'id')
        await add_shop(name, company_id)
        embed = discord.Embed(title="Shop created", color=discord.Color.green(),
                              description="You have created a shop under the name " + name + ".")
        embed.set_footer(text=f"{ctx.author.name}", icon_url=ctx.author.avatar)
        await msg.reply(embed=embed)
        await log(f"Company created with name {name} under company {company}", ctx)

    @shop.command(description="Accept an offer from a shop, and buy or sell items.")
    @discord.option(name="shop", autocomplete=discord.utils.basic_autocomplete(get_shops),
                    description="The shop you are buying from or selling to.")
    @discord.option(name="offer", description="The offer from the shop you are accepting.",
                    autocomplete=discord.utils.basic_autocomplete(get_offers))
    @discord.option(name="amount", description="The a")
    async def accept(self, ctx, shop: str, offer: str, amount: int = 1):
        if await get_shop(shop, 'id') is None:
            await ctx.respond("Invalid shop. Use the autocorrect.")
            return
        if await get_shop(shop, 'open') == 0:
            await ctx.respond("This shop is closed.")
            return
        offer = await get_offer(shop, offer)
        if offer is None:
            await ctx.respond("That offer is not valid for that shop. Use the autocorrect.")
            return
        direction = offer[4]
        item = offer[3]
        company_id = await get_shop(shop, 'company')
        company = await get_company_from_id(company_id)
        price = await calculate_price(shop, offer[1], amount)
        if direction == 1:
            if price > await get_money(ctx.author):
                await ctx.respond(f"You cannot afford to buy this. (${price} > ${await get_money(ctx.author)})")
                return
            result = await remove_inv_company(company_id, item, amount)
            if result == "noitem":
                await ctx.respond("That company is out of stock.")
                return
            elif result == "notenough":
                await ctx.respond("That company doesn't have enough stock.")
                return
            await change_money(ctx.author, -price)
            await change_money_company(company, price)
            await add_inv(ctx.author, item, amount)
            embed = discord.Embed(title="Item bought from shop", description=f"<@{ctx.author.id}> bought {amount} " +
                                  f"{item} from {shop} for ${price}.", color=discord.Color.yellow())
            await ctx.respond(embed=embed)
            await log(f"Bought {amount} {item} from {shop} for ${price}", ctx)
        else:
            if amount > await get_inv(ctx.author, item):
                await ctx.respond("You do not have enough of that item to sell it.")
                return
            company_money = await get_company(company, 'money')
            if price > company_money:
                await ctx.respond("The company doesn't have enough money to accept your sale at this price. " +
                                  f"(${company_money} < ${price})")
                return
            await change_money(ctx.author, price)
            await change_money_company(company, -price)
            await add_inv_company(company_id, item, amount)
            await remove_inv(ctx.author, item, amount)
            embed = discord.Embed(title="Item sold to shop", color=discord.Color.yellow(),
                                  description=f"<@{ctx.author.id}> sold {amount} {item} to {shop} for ${price}.")
            await ctx.respond(embed=embed)
            await log(f"Sold {amount} {item} to {shop} for ${price}", ctx)

    @shop.command(description="Manage a shop you own.")
    @discord.option(name="shop", description="The shop.",
                    autocomplete=discord.utils.basic_autocomplete(get_shops))
    async def manage(self, ctx, shop: str):
        if await get_shop(shop, 'id') is None:
            await ctx.respond("Invalid shop. Use the autocorrect.")
            return
        company = await get_company_from_id(await get_shop(shop, 'company'))
        if await get_company(company, 'owner') != ctx.author.id:
            await ctx.respond("You are not the owner of the company running this shop.")
            return
        embed = discord.Embed(title="Managing shop", color=discord.Color.blurple(),
                              description=f"Managing {shop}.")
        embed.set_footer(text=f"{ctx.author.name}", icon_url=ctx.author.avatar)
        view = ManageView(ctx.author)
        interaction = await ctx.respond(embed=embed, view=view)
        msg = await interaction.original_response()
        await view.wait()
        if view.value is None:
            return
        if view.value[0] == "Rename":
            view.disable_all_items()
            await msg.edit(view=view)
            if await get_shop(view.value[1], "name") is not None:
                await msg.reply(f"A shop with that name ({view.value[1]}) already exists.")
                return
            embed = discord.Embed(title="Shop renamed", color=discord.Color.green(),
                                  description=f"You have renamed {shop} to {view.value[1]}")
            embed.set_footer(text=f"{ctx.author.name}", icon_url=ctx.author.avatar)
            await msg.reply(embed=embed)
            await change_shop(shop, "name", view.value[1])
            await log(f"Shop renamed from '{shop}' to '{view.value[1]}'", ctx)
        elif view.value[0] == "Delete":
            view = YesNo(ctx.author)
            embed = discord.Embed(title="Delete shop", color=discord.Color.dark_red(),
                                  description="Do you confirm that you wish to delete this shop? " +
                                  "**All of its offers will be destroyed.**")
            embed.set_footer(text=f"{ctx.author.name}", icon_url=ctx.author.avatar)
            msg = await msg.reply(embed=embed, view=view)
            await view.wait()
            if view.value in [None, False]:
                await msg.reply("Cancelled.")
                return
            await delete_shop(shop)
            await add_inv_company(company, "Wood", 10)
            embed = discord.Embed(title="Shop deleted", color=discord.Color.red(),
                                  description=f"Shop {shop} has been deleted. The wood has been refunded.")
            await msg.reply(embed=embed)
            await log(f"Shop {shop} deleted", ctx)
        elif view.value[0] == "Open":
            view.disable_all_items()
            await msg.edit(view=view)
            if await get_shop(shop, "open") == 1:
                await msg.reply("The shop is already open.")
                return
            embed = discord.Embed(title="Shop opened", color=discord.Color.green(),
                                  description=f"You have opened your shop '{shop}'.")
            embed.set_footer(text=f"{ctx.author.name}", icon_url=ctx.author.avatar)
            await msg.reply(embed=embed)
            await change_shop(shop, "open", 1)
            await log(f"Shop {shop} opened", ctx)
        elif view.value[0] == "Close":
            view.disable_all_items()
            await msg.edit(view=view)
            if await get_shop(shop, "open") == 0:
                await msg.reply("The shop is already closed.")
                return
            embed = discord.Embed(title="Shop opened", color=discord.Color.red(),
                                  description=f"You have closed your shop '{shop}'.")
            embed.set_footer(text=f"{ctx.author.name}", icon_url=ctx.author.avatar)
            await msg.reply(embed=embed)
            await change_shop(shop, "open", 0)
            await log(f"Shop {shop} closed", ctx)
        elif view.value[0] == "Set Description":
            view.disable_all_items()
            await msg.edit(view=view)
            embed = discord.Embed(title="Shop description set", color=discord.Color.green(),
                                  description=f"You have set the description of your shop '{shop}' to:\n{view.value[1]}")
            embed.set_footer(text=f"{ctx.author.name}", icon_url=ctx.author.avatar)
            await msg.reply(embed=embed)
            await change_shop(shop, "description", view.value[1])
            await log(f"Shop {shop} description set to: {view.value[1]}", ctx)

    @offer.command(description="Add an offer to a shop you own.")
    @discord.option(name="shop", description="The name of the shop.",
                    autocomplete=discord.utils.basic_autocomplete(get_shops))
    @discord.option(name="item", description="The item you are adding as an offer.",
                    autocomplete=discord.utils.basic_autocomplete(get_all_items))
    @discord.option(name="offer", description="Name of the offer, which will show in the shop.",
                    max_length=50)
    @discord.option(name="direction", choices=["Buy", "Sell"],
                    description="Are customers buying this item from you, or selling this item to you?")
    @discord.option(name="price", description="The base price of the item (at the target supply).", min_value=0)
    @discord.option(name="target", description="The target supply of the offer. "
                    + "If the supply is lower, the price will be higher, and vice versa.", min_value=1)
    @discord.option(name="elasticity", description="How much the price varies based on the supply. "
                    + "The higher, the more it varies. Default: 0.5", min_value=0, max_value=5)
    @discord.option(name="min_price", description="The minimum price. It will never drop below this.", min_value=0)
    @discord.option(name="max_price", description="The maximum price. It will never go above this.", min_value=0)
    @discord.option(name="rank", min_value=1,
                    description="The rank of the offer. This determines how high it shows up in your shop.")
    async def add(self, ctx, shop: str, item: str, offer: str, direction: str, price: int, target: int,
                  elasticity: float = 0.5, min_price: int = None, max_price: int = None, rank: int = 0):
        shop_id = await get_shop(shop, 'id')
        if shop_id is None:
            await ctx.respond("Invalid shop. Use the autocorrect.")
            return
        company = await get_company_from_id(await get_shop(shop, 'company'))
        if await get_company(company, 'owner') != ctx.author.id:
            await ctx.respond("You are not the owner of the company running this shop.")
            return
        if await get_item_info(item, 'name') is None:
            await ctx.respond("Invalid item. Use the autocorrect.")
            return
        if min_price is not None and max_price is not None:
            if min_price > max_price:
                ctx.respond("The minimum price must be lower than the maximum price.")
                return
        direction_num = (1 if direction == "Buy" else -1)
        elasticity = round(elasticity, 2)
        result = await add_offer(shop_id, item, offer, direction_num, price, target, elasticity, min_price, max_price,
                                 rank)
        if result == "alreadyexists":
            await ctx.respond("An offer already exists with that name for this shop.")
            return
        embed = discord.Embed(title="Offer Created", description=f"Created to shop {shop}.\n\n",
                              color=discord.Color.green())
        embed.set_footer(text=f"{ctx.author.name}", icon_url=ctx.author.avatar)
        embed.description += f"**Rank**: {result}\n"
        embed.description += f"**Name**: {offer}\n"
        embed.description += f"**Direction**: {direction}\n"
        embed.description += f"**Item**: {item}\n"
        embed.description += f"**Base Price**: {price}\n"
        embed.description += f"**Target Supply**: {target}\n"
        embed.description += f"**Elasticity**: {elasticity}\n"
        embed.description += f"**Minimum Price**: {min_price}\n"
        embed.description += f"**Maximum Price**: {max_price}"
        await ctx.respond(embed=embed)
        await log(f"Shop {shop} added offer: " +
                  str([result, offer, direction, item, price, target, elasticity, min_price, max_price]), ctx)

    @offer.command(description="Remove an offer from a shop you own.")
    @discord.option(name="shop", description="The name of the shop.",
                    autocomplete=discord.utils.basic_autocomplete(get_shops))
    @discord.option(name="name", description="Name of the offer you are removing.",
                    autocomplete=discord.utils.basic_autocomplete(get_offers))
    async def remove(self, ctx, shop: str, name: str):
        shop_id = await get_shop(shop, 'id')
        if shop_id is None:
            await ctx.respond("Invalid shop. Use the autocorrect.")
            return
        company = await get_company_from_id(await get_shop(shop, 'company'))
        if await get_company(company, 'owner') != ctx.author.id:
            await ctx.respond("You are not the owner of the company running this shop.")
            return
        if await get_offer(shop, name) is None:
            await ctx.respond("Invalid offer. Use the autocorrect.")
            return
        await delete_offer(shop_id, name)
        embed = discord.Embed(title="Offer deleted", color=discord.Color.red(),
                              description=f"Offer '{name}' has been deleted from shop '{shop}'.")
        await ctx.respond(embed=embed)
        await log(f"Shop {shop} removed offer {name}", ctx)

    # region offer edit
    # @offer.command(description="Edit an offer of your shop.")
    # @discord.option(name="shop", description="The name of the shop.",
    #                 autocomplete=discord.utils.basic_autocomplete(get_shops))
    # @discord.option(name="offer", description="The offer you are editing.",
    #                 autocomplete=discord.utils.basic_autocomplete(get_offers))
    # @discord.option(name="name", description="Name of the offer, which will show in the shop.", max_length=50)
    # @discord.option(name="item", description="The item you are adding as an offer.",
    #                 autocomplete=discord.utils.basic_autocomplete(get_all_items))
    # @discord.option(name="direction", choices=["Buy", "Sell"],
    #                 description="Are customers buying this item from you, or selling this item to you?")
    # @discord.option(name="price", description="The base price of the item (at the target supply).", min_value=0)
    # @discord.option(name="target", description="The target supply of the offer. "
    #                 + "If the supply is lower, the price will be higher, and vice versa.", min_value=1)
    # @discord.option(name="elasticity", description="How much the price varies based on the supply. "
    #                 + "The higher, the more it varies. Default: 0.5", min_value=0, max_value=5)
    # @discord.option(name="min_price", min_value=-1,
    #                 description="The minimum price. It will never drop below this. Put -1 to have no minimum.")
    # @discord.option(name="max_price", min_value=-1,
    #                 description="The maximum price. It will never go above this. Put -1 to have no maximum.")
    # @discord.option(name="rank", min_value=1,
    #                 description="The rank of the offer. This determines how high it shows up in your shop.")
    # async def edit(self, ctx, shop: str, offer: str, name: str = None, item: str = None, direction: str = None,
    #                price: int = None, target: int = None, elasticity: float = None, min_price: int = None,
    #                max_price: int = None, rank: int = None):
    #     shop_id = await get_shop(shop, 'id')
    #     if shop_id is None:
    #         await ctx.respond("Invalid shop. Use the autocorrect.")
    #         return
    #     company = await get_company_from_id(await get_shop(shop, 'company'))
    #     if await get_company(company, 'owner') != ctx.author.id:
    #         await ctx.respond("You are not the owner of the company running this shop.")
    #         return
    #     original_offer = await get_offer(shop, offer)
    #     if original_offer is None:
    #         await ctx.respond("That offer is not valid for that shop. Use the autocorrect.")
    #         return
    #     if name is None:
    #         name = original_offer[2]
    #     if item is None:
    #         item = original_offer[3]
    #     elif await get_item_info(item, 'name') is None:
    #         await ctx.respond("Invalid item. Use the autocorrect.")
    #         return
    #     if direction is None:
    #         direction_id = original_offer[4]
    #         direction = "Buy" if direction_id == 1 else "Sell"
    #     else:
    #         direction_id = (1 if direction == "Buy" else -1)
    #     if price is None:
    #         price = original_offer[5]
    #     if target is None:
    #         target = original_offer[6]
    #     if elasticity is None:
    #         elasticity = original_offer[7]
    #     else:
    #         elasticity = round(elasticity, 2)
    #     if min_price is None:
    #         min_price = original_offer[8]
    #     elif min_price == -1:
    #         min_price = None
    #     if max_price is None:
    #         max_price = original_offer[9]
    #     elif max_price == -1:
    #         max_price = None
    #     if min_price is not None and max_price is not None:
    #         if min_price > max_price:
    #             ctx.respond("The minimum price must be lower than the maximum price.")
    #             return
    #     if rank is None:
    #         rank = original_offer[1]
    #     result = await change_offer(shop_id, offer, name, item, direction_id, price, target, elasticity, min_price,
    #                                 max_price, rank, original_offer[1])
    #     embed = discord.Embed(title="Offer edited", description=f"Edited in shop {shop}.\n\n",
    #                           color=discord.Color.green())
    #     embed.set_footer(text=f"{ctx.author.name}", icon_url=ctx.author.avatar)
    #     embed.description += f"**Rank**: {result}\n"
    #     embed.description += f"**Name**: {name}\n"
    #     embed.description += f"**Direction**: {direction}\n"
    #     embed.description += f"**Item**: {item}\n"
    #     embed.description += f"**Base Price**: {price}\n"
    #     embed.description += f"**Target Supply**: {target}\n"
    #     embed.description += f"**Elasticity**: {elasticity}\n"
    #     embed.description += f"**Minimum Price**: {min_price}\n"
    #     embed.description += f"**Maximum Price**: {max_price}"
    #     await ctx.respond(embed=embed)
    # endregion

def setup(bot):
    bot.add_cog(Shop(bot))

class ManageView(discord.ui.View):
    def __init__(self, user):
        super().__init__(timeout=30)
        self.value = None
        self.user = user

    @discord.ui.select(placeholder="Select an option.", options=[
        discord.SelectOption(label="Rename", description="Rename the shop."),
        discord.SelectOption(label="Delete", description="Delete the shop."),
        discord.SelectOption(label="Open", description="Open the shop."),
        discord.SelectOption(label="Close", description="Close the shop."),
        discord.SelectOption(label="Set Description", description="Change the description for the shop.")])
    async def select_callback(self, select, interaction):
        if interaction.user != self.user:
            await interaction.response.send_message(content="You aren't using this.", ephemeral=True)
            return
        self.value = [select.values[0]]
        if select.values[0] == "Rename":
            modal = ValueModal("New Name")
            await interaction.response.send_modal(modal)
            await modal.wait()
            self.value.append(modal.value)
        elif select.values[0] == "Set Description":
            modal = ValueModal("New Description", True)
            await interaction.response.send_modal(modal)
            await modal.wait()
            self.value.append(modal.value)
        else:
            self.disable_all_items()
            await interaction.response.edit_message(view=self)
        self.stop()

    async def on_timeout(self):
        self.disable_all_items()
        await self.message.edit(content="Timed out", view=self)
