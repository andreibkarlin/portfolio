import discord
from discord.ext import commands

from scripts.helpers import check_account, add_company, add_inv, remove_inv, get_company, get_companies, \
    change_company, delete_company, change_money, get_money, get_items, add_inv_company, remove_inv_company, \
    get_item_info, change_money_company, get_inv_company, log

from scripts.views import YesNo, ValueModal

class Company(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    company = discord.SlashCommandGroup("company", "Commands relating to companies.")

    @staticmethod
    async def get_companies(ctx: discord.AutocompleteContext):
        companies = await get_companies()
        result = [company[1] for company in companies]
        if ctx.command.name in ["manage", "transfer"]:
            result2 = []
            for company in result:
                if await get_company(company, "owner") == ctx.interaction.user.id:
                    result2.append(company)
            return result2
        return result

    @company.command(description="Create a company.")
    @discord.option(name="name", description="The name of the company.", max_length=50)
    async def create(self, ctx, name: str):
        if await check_account(ctx.author, ctx):
            return
        if await get_company(name, 'name') is not None:
            await ctx.respond("A company with this name already exists.")
            return
        check = await remove_inv(ctx.author, "Paper", 50)
        if check == "notenough":
            await ctx.respond("You don't have enough paper. You need 50.")
            return
        if check == "noitem":
            await ctx.respond("You don't have any paper.")
            return
        view = YesNo(ctx.author)
        embed = discord.Embed(title="Create a company", color=discord.Color.blurple(),
                              description="Do you confirm that you wish to start a company? This will cost 50 paper.")
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
            await add_inv(ctx.author, "Paper", 50)
            return
        await add_company(name, ctx.author.id)
        embed = discord.Embed(title="Company created", color=discord.Color.green(),
                              description="You have created a company under the name " + name + ".")
        embed.set_footer(text=f"{ctx.author.name}", icon_url=ctx.author.avatar)
        await msg.reply(embed=embed)
        await log(f"Company created with name {name}", ctx)

    @company.command(description="See information about a company.")
    @discord.option(name="name", description="The company.",
                    autocomplete=discord.utils.basic_autocomplete(get_companies))
    async def info(self, ctx, name: str):
        if await check_account(ctx.author, ctx):
            return
        if await get_company(name, 'name') != name:
            await ctx.respond("Invalid name. Use the autocorrect.")
            return
        embed = discord.Embed(title=f"Company Info", color=discord.Color.blue(),
                              description=f"**{name}**\nOwner: <@{await get_company(name, 'owner')}>\n" +
                              f"Money: ${await get_company(name, 'money')}")
        embed.set_footer(text=f"{ctx.author.name}", icon_url=ctx.author.avatar)
        await ctx.respond(embed=embed)

    @company.command(description="Manage a company you own.")
    @discord.option(name="name", description="The company.",
                    autocomplete=discord.utils.basic_autocomplete(get_companies))
    async def manage(self, ctx, name: str):
        if await get_company(name, 'owner') != ctx.author.id:
            await ctx.respond("You are not the owner of that company.")
            return
        embed = discord.Embed(title="Managing company", color=discord.Color.blurple(),
                              description=f"Managing {name}.")
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
            if await get_company(view.value[1], "name") is not None:
                await msg.reply(f"A company with that name ({view.value[1]}) already exists.")
                return
            embed = discord.Embed(title="Company renamed", color=discord.Color.green(),
                                  description=f"You have renamed {name} to {view.value[1]}")
            embed.set_footer(text=f"{ctx.author.name}", icon_url=ctx.author.avatar)
            await msg.reply(embed=embed)
            await change_company(name, "name", view.value[1])
            await log(f"Company {name} renamed to {view.value[1]}", ctx)
        elif view.value[0] == "Delete":
            view = YesNo(ctx.author)
            embed = discord.Embed(title="Delete company", color=discord.Color.dark_red(),
                                  description="Do you confirm that you wish to delete this company? " +
                                  "**Everything in the company (shops, inventory) will be destroyed.**" +
                                  "Money will be transferred to the owner.")
            embed.set_footer(text=f"{ctx.author.name}", icon_url=ctx.author.avatar)
            msg = await msg.reply(embed=embed, view=view)
            await view.wait()
            if view.value in [None, False]:
                await msg.reply("Cancelled.")
                return
            await change_money(ctx.author, get_company(name, 'money'))
            await delete_company(name)
            embed = discord.Embed(title="Company deleted", color=discord.Color.red(),
                                  description=f"Company {name} has been deleted.")
            await msg.reply(embed=embed)
            await log(f"Company {name} has been deleted", ctx)

    @company.command(name="pay-in", description="Give money or items to a company.")
    @discord.option(name="name", description="The name of the company.",
                    autocomplete=discord.utils.basic_autocomplete(get_companies))
    @discord.option(name="amount", description="How much money/items?", min_value=1)
    @discord.option(name="item", description="What item are you giving/taking? Leave this blank for money.",
                    autocomplete=discord.utils.basic_autocomplete(get_items))
    async def pay(self, ctx, name, amount: int, item: str = "Money"):
        if await check_account(ctx.author, ctx):
            return
        if item == "Money":
            if await get_money(ctx.author) < amount:
                await ctx.respond("You do not have the money to give.")
                return
            money = await change_money(ctx.author, -amount)
            await change_money_company(name, amount)
            embed = discord.Embed(title="Payment", description=f"You gave ${amount} to {name}.",
                                  color=discord.Color.yellow())
            embed.set_footer(text=f"{ctx.author.name} • Balance: ${money}", icon_url=ctx.author.avatar)
            await ctx.respond(embed=embed)
            await log(f"Company {name} has recieved ${amount}", ctx)
        else:
            if await get_item_info(item, "name") is None:
                await ctx.respond("Invalid item. Use the autocorrect.")
                return
            remove = await remove_inv(ctx.author, item, amount)
            if remove == "notenough":
                await ctx.respond("You don't have enough of that item in your inventory.")
                return
            if remove == "noitem":
                await ctx.respond("You do not have the item in your inventory.")
                return
            await add_inv_company(await get_company(name, 'id'), item, amount)
            embed = discord.Embed(title="Payment",
                                  description=f"You gave {amount} {item} to {name}.",
                                  color=discord.Color.yellow())
            embed.set_footer(text=f"{ctx.author.name}", icon_url=ctx.author.avatar)
            await ctx.respond(embed=embed)
            await log(f"Company {name} has recieved {amount} {item}", ctx)

    @company.command(name="pay-out",
                     description="Take out money or items from a company you own and give it to someone.")
    @discord.option(name="name", description="The company.",
                    autocomplete=discord.utils.basic_autocomplete(get_companies))
    @discord.option(name="amount", description="How much money/items?", min_value=1)
    @discord.option(name="member", description="Who is receiving this transfer?")
    @discord.option(name="item", description="What item are you giving/taking? Leave this blank for money.",
                    autocomplete=discord.utils.basic_autocomplete(get_items))
    async def payout(self, ctx, name, amount: int, member: discord.Member, item: str = "Money"):
        if await get_company(name, 'owner') != ctx.author.id:
            await ctx.respond("You are not the owner of that company.")
            return
        if await check_account(ctx.author, ctx):
            return
        if item == "Money":
            if await get_company(name, "money") < amount:
                await ctx.respond("The company doesn't have that much.")
                return
            money = await change_money(member, amount)
            await change_money_company(name, -amount)
            embed = discord.Embed(title="Transfer", description=f"<@{member.id}> got ${amount} from {name}.",
                                  color=discord.Color.green())
            embed.set_footer(text=f"{member.name} • Balance: ${money}", icon_url=member.avatar.url)
            await ctx.respond(f"<@{member.id}>", embed=embed)
            await log(f"Company {name} has given ${amount} to {member.id}", ctx)
        else:
            if await get_item_info(item, "name") is None:
                await ctx.respond("Invalid item. Use the autocorrect.")
                return
            remove = await remove_inv_company(await get_company(name, 'id'), item, amount)
            if remove == "notenough":
                await ctx.respond("The company doesn't have enough of that item.")
                return
            if remove == "noitem":
                await ctx.respond("The company doesn't have that item.")
                return
            await add_inv(member, item, amount)
            embed = discord.Embed(title="Transfer",
                                  description=f"<@{member.id}> got {amount} {item} from {name}.",
                                  color=discord.Color.green())
            embed.set_footer(text=f"{member.name}", icon_url=member.avatar.url)
            await ctx.respond(f"<@{member.id}>", embed=embed)
            await log(f"Company {name} has given {amount} {item} to {member.id}", ctx)

    @company.command(description="See the contents of a company's inventory.")
    @discord.option(name="name", description="The name of the company.",
                    autocomplete=discord.utils.basic_autocomplete(get_companies))
    async def inventory(self, ctx, name: str):
        if await check_account(ctx.author, ctx):
            return
        embed = discord.Embed(title="Inventory", color=discord.Color.blue())
        embed.description = f"Inventory of **{name}**:"
        #value = await net_worth(ctx.author.id) - await get_money(ctx.author)
        # embed.set_footer(text=f"{ctx.author.name} • Value of inventory: ${value}", icon_url=str(member.avatar))
        inv = await get_inv_company(await get_company(name, 'id'), None)
        for item in inv:  # 0 is name, 1 is amount.
            desc = await get_item_info(item[0], "description")
            embed.add_field(name=f"{item[0]}: {item[1]}", value=desc, inline=False)
        if len(embed.fields) == 0:
            embed.description += "\n\n**Empty.**"
        await ctx.respond(embed=embed)

def setup(bot):
    bot.add_cog(Company(bot))

class ManageView(discord.ui.View):
    def __init__(self, user):
        super().__init__(timeout=30)
        self.value = None
        self.user = user

    @discord.ui.select(placeholder="Select an option.", options=[
        discord.SelectOption(label="Rename", description="Rename the company."),
        discord.SelectOption(label="Delete", description="Delete the company.")])
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
        elif select.values[0] == "Delete":
            self.disable_all_items()
            await interaction.response.edit_message(view=self)
        self.stop()

    async def on_timeout(self):
        self.disable_all_items()
        await self.message.edit(content="Timed out", view=self)
