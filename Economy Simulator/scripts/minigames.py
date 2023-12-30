import discord
from discord.ui import View
import random

class NumPad(View):
    def __init__(self, user, size):
        super().__init__(timeout=30)
        self.user = user
        self.board = range(size*size)
        self.board = [x+1 for x in self.board]
        self.size = size
        self.num = 1
        self.value = None
        self.start = False
        random.shuffle(self.board)
        for i in range(len(self.board)):
            self.add_item(NumPadButton(self.board[i], i % size, i // size))

class NumPadButton(discord.ui.Button):
    def __init__(self, num: int, x: int, y: int):
        super().__init__(style=discord.ButtonStyle.green, label=str(num), row=y)
        self.num = num
        self.x = x
        self.y = y

    async def callback(self, interaction: discord.Interaction):
        view: NumPad = self.view
        view.start = True
        if view.timeout == 30:
            view.timeout = 12
        if interaction.user != view.user:
            await interaction.response.send_message(content="You aren't playing this game.", ephemeral=True)
            return
        self.disabled = True
        if view.num == self.num:
            view.num += 1
            if view.num > view.size ** 2:
                view.value = "Win"
                view.stop()
        else:
            view.value = "Loss"
            view.stop()
        await interaction.response.edit_message(view=view)

class SelectPad(View):
    def __init__(self, user, size):
        super().__init__(timeout=10)
        self.user = user
        self.size = size
        self.select = random.randint(0, size**2 - 1)
        self.value = None
        for i in range(size**2):
            self.add_item(SelectPadButton(i % size, i // size, self.size, self.select))

class SelectPadButton(discord.ui.Button):
    def __init__(self, x: int, y: int, size: int, select: int):
        self.num = y * size + x
        super().__init__(style=discord.ButtonStyle.red if self.num == select else discord.ButtonStyle.green,
                         label="➖", row=y)
        self.x = x
        self.y = y

    async def callback(self, interaction: discord.Interaction):
        view: SelectPad = self.view
        view.start = True
        if interaction.user != view.user:
            await interaction.response.send_message(content="You aren't playing this game.", ephemeral=True)
            return
        if self.num == view.select:
            view.value = "Win"
            view.stop()
        else:
            view.value = "Loss"
            view.stop()
        await interaction.response.defer()
