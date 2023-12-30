import discord
from discord.ext import commands

from scripts.helpers import check_account, add_government, get_government, has_govt_perm, change_government, \
    get_money, change_money, add_inv, remove_inv, get_items, get_item_info, \
    change_money_govt, add_inv_govt, remove_inv_govt, get_inv_govt, log

class Government(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    government = discord.SlashCommandGroup("government", "Commands relating to governments.")
    perms = ["Administrator", "Head of Government", "Treasurer", "Inventory Manager", "Money Printer"]

    @government.command(description="(Admin only) Set up the government of the server.")
    @discord.option(name="name", description="The name of the government.", max_length=50)
    @discord.option(name="admin", description="The role with administrator powers over the government.")
    @commands.has_permissions(administrator=True)
    async def setup(self, ctx, name: str, admin: discord.Role):
        if await check_account(ctx.author, ctx):
            return
        if await get_government(ctx.guild_id, 'name') is not None:
            await ctx.respond("A government already exists for this server.")
            return
        await add_government(ctx.guild_id, name, admin.id)
        embed = discord.Embed(title="Government set up", color=discord.Color.green(),
                              description=f"You have set up the government under the name '{name}'" +
                                          f" with the admin role '{admin.name}'.")
        embed.set_footer(text=f"{ctx.author.name}", icon_url=ctx.author.avatar)
        await ctx.respond(embed=embed)
        await log(f"Government for {ctx.guild_id} has been set up under name {name}", ctx)

    @government.command(name="set-permission", description="Set a role to a permission in the government.")
    @discord.option(name="permission", description="The permission you are assigning a role to.", choices=perms)
    @discord.option(name="role", description="The role you are assigning to that permission.")
    async def setperm(self, ctx, permission: str, role: discord.Role):
        if await check_account(ctx.author, ctx):
            return
        if permission == "Administrator":
            if not ctx.author.guild_permissions.administrator:
                await ctx.respond("Only server administrators can set the government administrator role.")
                return
        else:
            if not await has_govt_perm(ctx.guild_id, ctx.author, "Administrator"):
                await ctx.respond("You do not have the government administrator permission.")
                return
        await change_government(ctx.guild_id, permission, role.id)
        embed = discord.Embed(color=discord.Color.green(), title="Permission Set",
                              description=f"The permission '{permission}' has been set to the role <@&{role.id}>.")
        await ctx.respond(embed=embed)
        await log(f"Government {ctx.guild_id}: The permission '{permission}' has been set to {role.id}", ctx)

    @government.command(description="See information about the government of this server.")
    async def info(self, ctx):
        if await check_account(ctx.author, ctx):
            return
        server = ctx.guild_id
        embed = discord.Embed(title=f"Info on **{await get_government(server, 'name')}**", color=discord.Color.blue(),
                              description=f"Money: ${await get_government(server, 'money')}\n\n**Permissions**:")
        for perm in self.perms:
            embed.description += f"\n{perm}: <@&{await get_government(server, perm)}>"
        await ctx.respond(embed=embed)

    @government.command(description="Rename the government.")
    @discord.option(name="name", description="The new name.")
    async def rename(self, ctx, name: str):
        server = ctx.guild_id
        if not await has_govt_perm(server, ctx.author, 'Head of Government'):
            await ctx.respond("You do not have the required permission (Head of Government).")
            return
        old = await get_government(server, 'name')
        embed = discord.Embed(title="Government renamed", color=discord.Color.green(),
                              description=f"You have renamed {old} to {name}")
        embed.set_footer(text=f"{ctx.author.name}", icon_url=ctx.author.avatar)
        await ctx.respond(embed=embed)
        await change_government(server, "name", name)
        await log(f"Government {ctx.guild_id}: Renamed from '{old}' to '{name}'", ctx)

    @government.command(name="pay-in", description="Give money or items to the government.")
    @discord.option(name="amount", description="How much money/items?", min_value=1)
    @discord.option(name="item", description="What item are you giving/taking? Leave this blank for money.",
                    autocomplete=discord.utils.basic_autocomplete(get_items))
    async def pay(self, ctx, amount: int, item: str = "Money"):
        server = ctx.guild_id
        if await check_account(ctx.author, ctx):
            return
        if item == "Money":
            if await get_money(ctx.author) < amount:
                await ctx.respond("You do not have the money to give.")
                return
            money = await change_money(ctx.author, -amount)
            await change_money_govt(server, amount)
            embed = discord.Embed(title="Payment", description=f"You gave ${amount} to the government.",
                                  color=discord.Color.yellow())
            embed.set_footer(text=f"{ctx.author.name} • Balance: ${money}", icon_url=ctx.author.avatar)
            await ctx.respond(embed=embed)
            await log(f"Government {ctx.guild_id} has recieved ${amount}", ctx)
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
            await add_inv_govt(server, item, amount)
            embed = discord.Embed(title="Payment",
                                  description=f"You gave {amount} {item} to the government.",
                                  color=discord.Color.yellow())
            embed.set_footer(text=f"{ctx.author.name}", icon_url=ctx.author.avatar)
            await ctx.respond(embed=embed)
            await log(f"Government {ctx.guild_id} has recieved {amount} {item}", ctx)

    @government.command(name="pay-out",
                        description="Take out money or items from the government and give it to someone.")
    @discord.option(name="amount", description="How much money/items?", min_value=1)
    @discord.option(name="member", description="Who is receiving this transfer?")
    @discord.option(name="item", description="What item are you giving/taking? Leave this blank for money.",
                    autocomplete=discord.utils.basic_autocomplete(get_items))
    async def payout(self, ctx, amount: int, member: discord.Member, item: str = "Money"):
        server = ctx.guild_id
        if await check_account(ctx.author, ctx):
            return
        if item == "Money":
            if not await has_govt_perm(server, ctx.author, 'Treasurer'):
                await ctx.respond("You do not have the required permission (Treasurer).")
                return
            if await get_government(server, "money") < amount:
                await ctx.respond("The government doesn't have that much.")
                return
            money = await change_money(member, amount)
            await change_money_govt(server, -amount)
            embed = discord.Embed(title="Transfer", description=f"<@{member.id}> got ${amount} from the government.",
                                  color=discord.Color.green())
            embed.set_footer(text=f"{member.name} • Balance: ${money}", icon_url=member.avatar.url)
            await ctx.respond(f"<@{member.id}>", embed=embed)
            await log(f"Government {ctx.guild_id} has given ${amount} to {member.id}", ctx)
        else:
            if not await has_govt_perm(server, ctx.author, 'Inventory Manager'):
                await ctx.respond("You do not have the required permission (Inventory Manager).")
                return
            if await get_item_info(item, "name") is None:
                await ctx.respond("Invalid item. Use the autocorrect.")
                return
            remove = await remove_inv_govt(server, item, amount)
            if remove == "notenough":
                await ctx.respond("The government doesn't have enough of that item.")
                return
            if remove == "noitem":
                await ctx.respond("The government doesn't have that item.")
                return
            await add_inv(member, item, amount)
            embed = discord.Embed(title="Transfer",
                                  description=f"<@{member.id}> got {amount} {item} from the government.",
                                  color=discord.Color.green())
            embed.set_footer(text=f"{member.name}", icon_url=member.avatar.url)
            await ctx.respond(f"<@{member.id}>", embed=embed)
            await log(f"Government {ctx.guild_id} has given {amount} {item} to {member.id}", ctx)

    @government.command(description="See the contents of the governments's inventory.")
    async def inventory(self, ctx):
        server = ctx.guild_id
        embed = discord.Embed(title="Inventory", color=discord.Color.blue())
        embed.description = f"Inventory of **{await get_government(server, 'name')}**:"
        #value = await net_worth(ctx.author.id) - await get_money(ctx.author)
        # embed.set_footer(text=f"{ctx.author.name} • Value of inventory: ${value}", icon_url=str(member.avatar))
        inv = await get_inv_govt(server, None)
        for item in inv:  # 0 is name, 1 is amount.
            desc = await get_item_info(item[0], "description")
            embed.add_field(name=f"{item[0]}: {item[1]}", value=desc, inline=False)
        if len(embed.fields) == 0:
            embed.description += "\n\n**Empty.**"
        await ctx.respond(embed=embed)

    @government.command(description="Print money using paper.")
    @discord.option(name="paper", description="The amount of paper you are converting into money.", min_value=1)
    async def print(self, ctx, paper: int):
        server = ctx.guild_id
        if await check_account(ctx.author, ctx):
            return
        if await get_government(server, "can print?") == 0:
            await ctx.respond("This government does not have the ability to print money.")
            return
        if not await has_govt_perm(server, ctx.author, 'Money Printer'):
            await ctx.respond("You do not have the required permission (Money Printer).")
            return
        check = await remove_inv_govt(server, "Paper", paper)
        if check == "notenough":
            await ctx.respond("The government doesn't have that much paper.")
            return
        if check == "noitem":
            await ctx.respond("The government doesn't have any paper.")
            return
        amount = paper * 10
        await change_money_govt(server, amount)
        embed = discord.Embed(title="Money Printed", color=discord.Color.green(),
                              description=f"You printed ${amount} for the government, using {paper} paper.")
        embed.set_footer(text=f"{ctx.author.name}", icon_url=ctx.author.avatar.url)
        await ctx.respond(embed=embed)
        await log(f"Government {ctx.guild_id} has printed ${amount} using {paper} paper", ctx)

    # @government.command(description="Equally distribute money to people with a role.")
    # @discord.option(name="role", description="The role the government is distributing money to.")
    # @discord.option(name="amount", description="The amount of money being distributed per person or in total.",
    #                 min_value=1)
    # @discord.option(name="distribution_type", description="How are you distributing this money?",
    #                 choices=["Giving the amount to each role", "Splitting the amount equally between each role"])
    # async def distribute(self, ctx, role: discord.Role, amount: int, distribution_type: str):
    #     server = ctx.guild_id
    #     if await check_account(ctx.author, ctx):
    #         return
    #     if not await has_govt_perm(server, ctx.author, 'Treasurer'):
    #         await ctx.respond("You do not have the required permission (Treasurer).")
    #         return
    #     # CALCULATE COST, GET ALL THE PEOPLE, GET NUMBER OF PEOPLE
    #     # CHECK IF GOVT HAS ENOUGH MONEY
    #     embed = discord.Embed(title="Distribute confirmation", color=discord.Color.blurple())
    #     embed.description = "Are you sure you want to do this?\n"
    #     if distribution_type[0] == "G":
    #         embed.description += f"This will cost BLAHB ABLHABAKDBG"
    #     if distribution_type[0] == "S":
    #         embed.description += f"This will give X to Y people, leaving N over..."
    #     embed.set_footer(text=f"{ctx.author.name} • Government Money: ${await get_government(server, 'money')}",
    #                      icon_url=ctx.author.avatar)
    #     view = YesNo(ctx.author)
    #     interaction = await ctx.respond(embed=embed, view=view)
    #     msg = interaction.original_response()
    #     # GIVE OUT THE MONEY
    #     await msg.reply("h")

def setup(bot):
    bot.add_cog(Government(bot))
