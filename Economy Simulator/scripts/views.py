import discord
from discord.ui import View

class YesNo(View):
    def __init__(self, user):
        super().__init__(timeout=300)
        self.value = None
        self.user = user

    @discord.ui.button(label="Yes", style=discord.ButtonStyle.green, custom_id="Yes")
    async def yes_button_callback(self, button: discord.ui.Button, interaction: discord.Interaction):
        if interaction.user == self.user:
            button.disabled = True
            view = self
            other_button = [x for x in view.children if x.custom_id == "No"][0]  # noqa
            other_button.disabled = True
            await interaction.response.edit_message(view=self)
            self.value = True
            self.stop()
        else:
            await interaction.response.send_message(content="This wasn't directed towards you.", ephemeral=True)

    @discord.ui.button(label="No", style=discord.ButtonStyle.red, custom_id="No")
    async def no_button_callback(self, button: discord.ui.Button, interaction: discord.Interaction):
        if interaction.user == self.user:
            button.disabled = True
            view = self
            other_button = [x for x in view.children if x.custom_id == "Yes"][0]  # noqa
            other_button.disabled = True
            await interaction.response.edit_message(view=self)
            self.value = False
            self.stop()
        else:
            await interaction.response.send_message(content="This wasn't directed towards you.", ephemeral=True)

class Pages(View):
    def __init__(self, user, page, pages):
        super().__init__(timeout=60)
        self.value = None
        self.user = user
        self.page = page
        self.pages = pages

    def disable_buttons(self):
        if self.page == 1:
            previous_button = [x for x in self.children if x.custom_id == "Previous"][0]  # noqa
            previous_button.disabled = True
        if self.page == self.pages:
            next_button = [x for x in self.children if x.custom_id == "Next"][0]  # noqa
            next_button.disabled = True

    @discord.ui.button(label="Previous Page", style=discord.ButtonStyle.blurple, custom_id="Previous")
    async def previous_page_callback(self, button: discord.ui.Button, interaction: discord.Interaction):
        if interaction.user == self.user:
            button.disabled = True
            view = self
            other_button = [x for x in view.children if x.custom_id == "Next"][0]  # noqa
            other_button.disabled = True
            await interaction.response.edit_message(view=self)
            self.value = -1
            self.stop()
        else:
            await interaction.response.send_message(content="This wasn't directed towards you.", ephemeral=True)

    @discord.ui.button(label="Next Page", style=discord.ButtonStyle.blurple, custom_id="Next")
    async def next_page_callback(self, button: discord.ui.Button, interaction: discord.Interaction):
        if interaction.user == self.user:
            button.disabled = True
            view = self
            other_button = [x for x in view.children if x.custom_id == "Previous"][0]  # noqa
            other_button.disabled = True
            await interaction.response.edit_message(view=self)
            self.value = 1
            self.stop()
        else:
            await interaction.response.send_message(content="This wasn't directed towards you.", ephemeral=True)

class ValueModal(discord.ui.Modal):
    def __init__(self, value, paragraph = False) -> None:
        super().__init__(title="Input value")
        if paragraph:
            self.add_item(discord.ui.InputText(label=value, max_length=500, style=discord.InputTextStyle.long))
        else:
            self.add_item(discord.ui.InputText(label=value, max_length=50))
        self.value = None

    async def callback(self, interaction: discord.Interaction):
        self.value = self.children[0].value
        await interaction.response.send_message(f"You have entered: {self.value}", ephemeral=True)
