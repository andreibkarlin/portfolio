import asyncio
import random
import discord
import time
from discord.ext import commands
from discord.ui import View

from scripts.helpers import check_account, get_money, change_money, change_money_company, get_company, log

casino = "Casino"
win_amount = 0.5

class Gambling(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    gambling = discord.SlashCommandGroup("gambling", "Commands relating to gambling and casinos.")

    @gambling.command(description="Bet a certain amount of money and gain or lose it.")
    @discord.option(name="amount", description="Amount being betted.", min_value=0)
    async def coinflip(self, ctx, amount: int):
        if await check_account(ctx.author, ctx):
            return
        money = await get_money(ctx.author)
        if money < amount:
            await ctx.respond("You do not have the money to gamble.")
            return
        bet_limit = await get_company(casino, 'money') // 2
        if amount > bet_limit:
            await ctx.respond(f"The casino doesn't have enough money for you to place that bet. Limit: ${bet_limit}.")
            return
        success = random.randint(0, 2)
        embed = discord.Embed(title="Coin flip")
        if success == 1:
            money = await change_money(ctx.author, round(amount*win_amount))
            await change_money_company(casino, -round(amount*win_amount))
            embed.description = f"You won the bet and earned ${amount}."
            embed.colour = discord.Color.green()
            await log(f"Coinflip won for ${amount} with casino {casino}", ctx)
        else:
            money = await change_money(ctx.author, -amount)
            await change_money_company(casino, amount)
            embed.description = f"You lost the bet and lost ${amount}."
            embed.colour = discord.Color.red()
            await log(f"Coinflip lost for ${amount} with casino {casino}", ctx)
        embed.set_footer(text=f"{ctx.author.name} • Balance: ${money}", icon_url=ctx.author.avatar)
        await ctx.respond(embed=embed)

    @gambling.command(description="Play the slot machine, with the potential to win a lot of money.")
    @discord.option(name="amount", description="Amount being betted.", min_value=0)
    async def slots(self, ctx, amount: int):
        if await check_account(ctx.author, ctx):
            return
        money = await get_money(ctx.author)
        if money < amount:
            await ctx.respond("You do not have the money to gamble.")
            return
        bet_limit = await get_company(casino, 'money') // 2
        if amount > bet_limit:
            await ctx.respond(f"The casino doesn't have enough money for you to place that bet. Limit: ${bet_limit}.")
            return
        final = []
        for i in range(3):
            final.append(random.choice(["X", "O", "+"]))
        embed = discord.Embed(title="Slot machine")
        win = final[0] == final[1] == final[2]
        winnings = amount*5 if win else -amount
        money = await change_money(ctx.author, winnings)
        await change_money_company(casino, -winnings)
        embed.set_footer(text=f"{ctx.author.name} • Balance: ${money}", icon_url=ctx.author.avatar)
        embed.colour = discord.Color.green() if win else discord.Color.red()
        embed.description = f"`[ {final[0]} | {final[1]} | {final[2]} ]`" + \
                            f"\nYou {'won' if win else 'lost'} ${abs(winnings)}."
        await ctx.respond(embed=embed)
        if win:
            await log(f"Slots won for ${winnings} with casino {casino}", ctx)
        else:
            await log(f"Slots lost for ${amount} with casino {casino}", ctx)

    @gambling.command(description="Start a roulette game, where anyone can bet the specified amount on a color.")
    @discord.option(name="amount", description="Amount being betted.", min_value=0)
    @commands.cooldown(1, 60, commands.BucketType.user)
    async def roulette(self, ctx, amount: int):
        if await check_account(ctx.author, ctx):
            return
        bet_limit = await get_company(casino, 'money') // 5
        if amount > bet_limit:
            await ctx.respond(f"The casino doesn't have enough money for you to place that bet. Limit: ${bet_limit}.")
            return
        cooldown = 30
        future_time = round(time.time()) + cooldown + 1
        embed = discord.Embed(title="Roulette Game",
                              description=f"The bet is ${amount}.\n" +
                              f"Select a color. There are 18 red spaces, 18 black spaces, and one green space.\n" +
                              f"<t:{future_time}:R>, the ball will roll, and the winners will be declared.",
                              color=discord.Color.blurple())
        colors = ["red", "black", "green"]
        result = random.choices(colors, weights=[48.6, 48.6, 2.8], k=1)[0]
        view = Roulette(amount)
        interaction = await ctx.respond(embed=embed, view=view)
        msg = await interaction.original_response()
        await asyncio.sleep(cooldown)
        bets = view.bets
        view.children[0].disabled = True  # noqa
        view.children[1].disabled = True  # noqa
        view.children[2].disabled = True  # noqa
        await msg.edit(view=view)
        embed = discord.Embed(title="Roulette Game", description="The ball is rolling...", color=discord.Color.yellow())
        msg = await msg.reply(embed=embed)
        await asyncio.sleep(2)
        embed.description = f"The ball has landed on {result}."
        winnings = round((1 + win_amount) * amount)
        if result == "red":
            embed.colour = discord.Color.dark_red()
        elif result == "black":
            embed.colour = discord.Color.default()
        elif result == "green":
            embed.description += " This is a rare occurance."
            embed.colour = discord.Color.dark_green()
            winnings = round(35 * win_amount) * amount
        embed.description += f"\n\n**Winners:**"
        embed.set_footer(text=f"Winnings: ${winnings - amount}")
        for bet in bets:
            if bets[bet] == result:
                await change_money(bet, winnings)
                await change_money_company(casino, -winnings)
                embed.add_field(name="", value=f"<@{bet.id}>")
                await log(f"Roulette won for ${winnings} with casino {casino} for user {bet.id} landing on {result}",
                          ctx)
            else:
                await log(f"Roulette lost for ${winnings} with casino {casino} for user {bet.id} landing on {result}" +
                          f"as they picked {bets[bet]}", ctx)
        if len(embed.fields) == 0:
            embed.description += "\nNone."
        await msg.edit(embed=embed)

    @gambling.command(description="Play a game of blackjack.")
    @discord.option(name="amount", description="Amount being betted.", min_value=0)
    async def blackjack(self, ctx, amount: int):
        if await check_account(ctx.author, ctx):
            return
        money = await change_money(ctx.author, -amount)
        if money < 0:
            await change_money(ctx.author, amount)
            await ctx.respond("You don't have that much money.")
            return
        bet_limit = await get_company(casino, 'money') // 2
        if amount > bet_limit:
            await ctx.respond(f"The casino doesn't have enough money for you to place that bet. Limit: ${bet_limit}.")
            await change_money(ctx.author, amount)
            return
        await change_money_company(casino, amount)
        embed = discord.Embed(title="Blackjack Game", color=discord.Color.blurple(),
                              description="Hit - Take another card.\nStand - End your turn."
                              + "\nDouble Down - Double your bet, hit, and stand."
                              + "\nSurrender - Get back half of your bet.")
        embed.set_footer(text=f"{ctx.author.name} • Balance: ${money}", icon_url=ctx.author.avatar)
        view = Blackjack(ctx.author, money, amount)
        values = view.calculate_values()
        embed.add_field(name="Your cards", value=values[0], inline=False)
        embed.add_field(name="Dealer's cards", value=values[1], inline=False)
        if view.player == 21:
            embed.description = "You got a blackjack and won! (Even without playing the game)"
            embed.colour = discord.Color.dark_green()
            view.end_game()
            winnings = round(amount * (1 + bet_limit * 1.5))
            money = await change_money(ctx.author, winnings)
            await change_money_company(casino, -winnings)
            embed.set_footer(text=f"{ctx.author.name} • Balance: ${money}", icon_url=ctx.author.avatar)
            await log(f"Blackjack won through automatic blackjack for ${winnings} with casino {casino}", ctx)
            return
        interaction = await ctx.respond(embed=embed, view=view)
        msg = await interaction.original_response()
        await view.wait()
        if view.value is None:
            await view.surrender(msg)
            embed.description = "Time out. You lose."
            embed.colour = discord.Color.red()
            await log(f"Blackjack lost through timeout for ${amount} with casino {casino}", ctx)
            await msg.edit(embed=embed)
        else:
            await log(f"Blackjack {view.value} for ${view.amount} with casino {casino}", ctx)

def setup(bot):
    bot.add_cog(Gambling(bot))

class Blackjack(View):
    def __init__(self, user, money, amount):
        super().__init__(timeout=120)
        self.value = None
        self.user = user
        self.money = money
        self.amount = amount
        self.cards = {"Two": 2, "Three": 3, "Four": 4, "Five": 5, "Six": 6, "Seven": 7, "Eight": 8, "Nine": 9,
                      "Jack": 10, "Queen": 10, "King": 10, "Ace": 11}
        self.player_cards = random.choices(list(self.cards.keys()), k=2)
        self.dealer_cards = [random.choice(list(self.cards.keys())), "Hidden"]
        self.player = 0
        self.dealer = 0

    @discord.ui.button(label="Hit", style=discord.ButtonStyle.blurple)
    async def hit_button(self, button: discord.ui.Button, interaction: discord.Interaction):  # noqa
        if interaction.user == self.user:
            await self.hit(interaction)
        else:
            await interaction.response.send_message(content="This wasn't directed towards you.", ephemeral=True)

    @discord.ui.button(label="Stand", style=discord.ButtonStyle.green)
    async def stand(self, button: discord.ui.Button, interaction: discord.Interaction):  # noqa
        if interaction.user == self.user:
            self.dealer_cards[1] = random.choice(list(self.cards.keys()))
            await self.stand_recursive(interaction)
        else:
            await interaction.response.send_message(content="This wasn't directed towards you.", ephemeral=True)

    @discord.ui.button(label="Surrender", style=discord.ButtonStyle.red)
    async def surrender_button(self, button: discord.ui.Button, interaction: discord.Interaction):  # noqa
        if interaction.user == self.user:
            await self.surrender(interaction.message)
            await interaction.response.send_message("You surrendered.", ephemeral=True)
            self.stop()
        else:
            await interaction.response.send_message(content="This wasn't directed towards you.", ephemeral=True)

    @discord.ui.button(label="Double Down", style=discord.ButtonStyle.gray)
    async def double_down(self, interaction: discord.Interaction, button: discord.ui.Button):  # noqa
        if interaction.user == self.user:
            money = await get_money(interaction.user)
            if money < self.amount:
                await interaction.response.send_message(
                    content="You don't have enough money to double down.", ephemeral=True)
            else:
                await change_money(interaction.user, -self.amount)
                await change_money_company(casino, self.amount)
                self.amount *= 2
                game = await self.hit(interaction, False)
                if game:
                    self.dealer_cards[1] = random.choice(list(self.cards.keys()))
                    await self.stand_recursive(interaction)
        else:
            await interaction.response.send_message(content="This wasn't directed towards you.", ephemeral=True)

    async def hit(self, interaction, response=True):
        self.player_cards.append(random.choice(list(self.cards.keys())))
        values = self.calculate_values()
        embed = interaction.message.embeds[0]
        embed.set_field_at(0, name="Your cards", value=values[0], inline=False)
        embed.set_field_at(1, name="Dealer's cards", value=values[1], inline=False)
        if self.player == 21 and len(self.player_cards) == 2:
            await self.end(embed, interaction, "You got a blackjack and won!", discord.Color.dark_green(),
                           1 + (1.5 * win_amount), "won through blackjack")
            return False
        if self.player > 21:
            await self.end(embed, interaction, "You busted and lost.", discord.Color.red(), 0, "lost through busting")
            return False
        else:
            embed.description = "The game continues."
            self.money = await get_money(self.user)
            embed.set_footer(text=f"{self.user.name} • Balance: ${self.money}", icon_url=self.user.avatar)
            if response:
                await interaction.response.edit_message(embed=embed)
            else:
                await interaction.message.edit(embed=embed)
            return True

    async def surrender(self, msg: discord.Message):
        embed = msg.embeds[0]
        embed.description = "You surrendered and lost half of the bet."
        embed.colour = discord.Color.red()
        view = self.end_game()
        self.money = await change_money(self.user, self.amount // 2)
        await change_money_company(casino, -(self.amount // 2))
        embed.set_footer(text=f"{self.user.name} • Balance: ${self.money}", icon_url=self.user.avatar)
        await msg.edit(embed=embed, view=view)
        self.value = "surrendered"
        view.stop()

    async def stand_recursive(self, interaction):
        values = self.calculate_values()
        embed = interaction.message.embeds[0]
        embed.set_field_at(0, name="Your cards", value=values[0], inline=False)
        embed.set_field_at(1, name="Dealer's cards", value=values[1], inline=False)
        if self.dealer == self.player:
            await self.end(embed, interaction, "Push. You get back your bet.", discord.Color.yellow(), 1,
                           "tied through push")
        elif self.dealer > 21:
            await self.end(embed, interaction, "Dealer bust. You win!", discord.Color.green(), 1 + win_amount,
                           "won through dealer busting")
        elif self.dealer > self.player:
            await self.end(embed, interaction, "You lose.", discord.Color.red(), 0, "lost")
        else:
            await interaction.message.edit(embed=embed)
            await asyncio.sleep(0.5)
            self.dealer_cards.append(random.choice(list(self.cards.keys())))
            await self.stand_recursive(interaction)

    def calculate_values(self):
        self.player = sum([self.cards[card] for card in self.player_cards])
        self.dealer = sum([self.cards[card] for card in self.dealer_cards if card != "Hidden"])
        return [str.join(", ", self.player_cards) + f" ({self.player})",
                str.join(", ", self.dealer_cards) + f" ({self.dealer})"]

    async def end(self, embed, interaction, description, color, multiple, status):
        embed.description = description
        embed.colour = color
        view = self.end_game()
        self.money = await change_money(self.user, round(self.amount * multiple))
        await change_money_company(casino, -round(self.amount * multiple))
        embed.set_footer(text=f"{self.user.name} • Balance: ${self.money}", icon_url=self.user.avatar)
        await interaction.response.edit_message(embed=embed, view=view)
        self.value = status
        view.stop()

    def end_game(self):
        view = self
        buttons = [x for x in view.children]
        for button in buttons:
            button.disabled = True
        return view

class Roulette(View):
    def __init__(self, amount):
        super().__init__()
        self.amount = amount
        self.bets = {}

    async def place_bet(self, interaction, color):
        if await check_account(interaction.user, None):
            await interaction.response.send_message("You do not have a bank account. You can open one with !register",
                                                    ephemeral=True)
            return
        embed = discord.Embed(title="Roulette Bet",
                              description=f"<@{interaction.user.id}> has bet ${self.amount} on {color}.")
        if color == "red":
            embed.colour = discord.Color.dark_red()
        elif color == "green":
            embed.colour = discord.Color.dark_green()
        money = await get_money(interaction.user)
        has_user = interaction.user in self.bets
        if has_user:
            previous_bet = self.bets[interaction.user]
            embed.description += f"\nThey switched their bet from {previous_bet}."
            if previous_bet == color:
                embed.description = f"<@{interaction.user.id}> has cancelled their bet."
                embed.set_footer(text=f"{interaction.user.name} • Balance: ${money + self.amount}")
                self.bets.pop(interaction.user)
                await change_money(interaction.user, self.amount)
                await change_money_company(casino, -self.amount)
                await interaction.response.send_message(embed=embed)
                return
        else:
            if money < self.amount:
                await interaction.response.send_message(
                    f"You do not have the money to place this bet. Your money: ${money}.", ephemeral=True)
                return
            await change_money(interaction.user, -self.amount)
            await change_money_company(casino, self.amount)
            money -= self.amount
        self.bets[interaction.user] = color
        embed.set_footer(text=f"{interaction.user.name} • Balance: ${money}")
        await interaction.response.send_message(embed=embed)

    @discord.ui.button(label="Red", style=discord.ButtonStyle.red)
    async def red(self, button: discord.ui.Button, interaction: discord.Interaction):  # noqa
        await self.place_bet(interaction, "red")

    @discord.ui.button(label="Black", style=discord.ButtonStyle.blurple)
    async def black(self, button: discord.ui.Button, interaction: discord.Interaction):  # noqa
        await self.place_bet(interaction, "black")

    @discord.ui.button(label="Green", style=discord.ButtonStyle.green)
    async def green(self, interaction: discord.Interaction, button: discord.ui.Button):  # noqa
        await self.place_bet(interaction, "green")
