import discord
from discord.ext import commands
import random

from scripts.helpers import check_account, get_money, change_money
from scripts.views import YesNo

class Games(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @discord.slash_command(description="Challenge someone to a game of tic tac toe.")
    @discord.option(name="stake", description="Amount at stake. Winner will get this amount from the loser.",
                    min_value=0)
    async def tictactoe(self, ctx, member: discord.Member, stake: int = 0):
        if await check_account(ctx.author, ctx):
            return
        if await check_account(member, ctx):
            return
        if await get_money(ctx.author) < stake:
            await ctx.respond("You don't have that much money.")
            return
        if await get_money(member) < stake:
            await ctx.respond("They don't have that much money.")
            return
        view = YesNo(member)
        embed = discord.Embed(title="Tic Tac Toe Request", color=discord.Color.blurple())
        embed.description = f"<@{member.id}>, do you wish to play Tic Tac Toe with <@{ctx.author.id}>?\n"
        embed.set_footer(text=f"{member.name}", icon_url=str(member.avatar))
        if stake > 0:
            embed.description += f"${stake} will be at stake."
            embed.set_footer(text=f"{member.name} • Balance: ${await get_money(member)}")
        interaction = await ctx.respond(f"<@{member.id}>", embed=embed, view=view)
        msg = await interaction.original_response()
        await view.wait()
        if view.value is None:
            for button in view.children:
                button.disabled = True
            await msg.edit(view=view)
            await msg.reply("They did not respond in time.")
        elif view.value:
            await change_money(ctx.author, -stake)
            await change_money(member, -stake)
            view = TicTacToe([ctx.author, member], stake)
            embed = discord.Embed(title="Tic Tac Toe", color=discord.Color.blurple())
            embed.description = f"The game has begun. X's turn: <@{view.playerX.id}>"
            embed.set_footer(text=f"{view.playerX.name}", icon_url=view.playerX.avatar)
            if stake > 0:
                embed.description += f"\n${stake} is at stake."
                money = await get_money(view.current_player)
                embed.set_footer(text=f"{view.playerX.name} • Balance: ${money}",
                                 icon_url=view.playerX.avatar)
            msg = await msg.reply(embed=embed, view=view)
            await view.wait()
            if view.value is None:
                for button in view.children:
                    button.disabled = True
                embed.description = f"<@{view.current_player.id}> did not respond in time and has automatically lost."
                if view.current_player == ctx.author:
                    await change_money(member, stake)
                else:
                    await change_money(ctx.author, stake)
                await msg.edit(embed=embed, view=view)
        else:
            await ctx.respond("They declined.")

def setup(bot):
    bot.add_cog(Games(bot))

class TicTacToeButton(discord.ui.Button):
    def __init__(self, x: int, y: int):
        super().__init__(style=discord.ButtonStyle.gray, label="➖", row=y)  # \u200b
        self.x = x
        self.y = y

    async def callback(self, interaction: discord.Interaction):
        view: TicTacToe = self.view
        if interaction.user not in view.players:
            await interaction.response.send_message(content="You aren't playing this game.", ephemeral=True)
            return
        if interaction.user != view.current_player:
            await interaction.response.send_message(content="It's not your turn.", ephemeral=True)
            return
        self.disabled = True
        view.board[self.y][self.x] = view.current_type
        if view.current_type == "X":
            self.style = discord.ButtonStyle.blurple
            self.label = "❌"
        else:
            self.style = discord.ButtonStyle.green
            self.label = "⭕"
        win = view.find_win()
        embed = discord.Embed(title="Tic Tac Toe", color=discord.Color.blurple())
        content = ""
        if win == "-":
            if view.current_type == "X":
                view.current_type = "O"
                view.current_player = view.playerO
                content = f"It is now O's turn: <@{view.playerO.id}>"
            else:
                view.current_type = "X"
                view.current_player = view.playerX
                content = f"It is now X's turn: <@{view.playerX.id}>"
        else:
            if win == "X":
                content = f"X wins: <@{view.playerX.id}>"
                if view.amount > 0:
                    content += f"wins ${2 * view.amount}."
                    await change_money(view.playerX, 2 * view.amount)
            elif win == "O":
                content = f"O wins: <@{view.playerO.id}>"
                if view.amount > 0:
                    content += f"wins ${2 * view.amount}."
                    await change_money(view.playerO, 2 * view.amount)
            elif win == "Tie":
                content = "It's a tie."
                if view.amount > 0:
                    content += f" Both players get their ${view.amount} bet back."
                    await change_money(view.playerO, view.amount)
                    await change_money(view.playerX, view.amount)
            for button in view.children:
                button.disabled = True
            view.value = "End"
            embed.colour = discord.Color.green()
        embed.description = content
        embed.set_footer(text=view.current_player.name, icon_url=view.current_player.avatar)
        if view.amount > 0:
            if view.value != "End":
                embed.description += f"\n${view.amount} is at stake."
            money = await get_money(view.current_player)
            embed.set_footer(text=f"{view.current_player.name}" +
                                  f" • Balance: ${money}",
                             icon_url=view.current_player.avatar)
        await interaction.response.edit_message(embed=embed, view=view)

class TicTacToe(discord.ui.View):
    def __init__(self, players, amount):
        super().__init__(timeout=120)
        self.players = players
        pick = random.randrange(0, 2)
        self.playerX = players[pick]  # A random player is picked.
        self.playerO = players[(pick + 1) % 2]  # The other player is picked.
        self.current_player = self.playerX
        self.current_type = "X"
        self.board = []
        self.value = None
        self.amount = amount
        for y in range(3):
            self.board.append([])
            for x in range(3):
                self.board[-1].append("-")
                self.add_item(TicTacToeButton(x, y))

    def find_win(self):
        board = self.board
        # Check rows, then columns, then diagonals. Then check for ties.
        for row in board:
            if row[0] == row[1] == row[2] != "-":
                return row[0]
        for col in range(3):
            if board[0][col] == board[1][col] == board[2][col] != "-":
                return board[0][col]
        if board[0][0] == board[1][1] == board[2][2] != "-":
            return board[0][0]
        if board[0][2] == board[1][1] == board[2][0] != "-":
            return board[0][2]
        for row in board:
            for tile in row:
                if tile == "-":
                    return "-"  # The game continues.
        return "Tie"
