import discord
from discord.ext import commands
from .utils.dataIO import dataIO
from .utils import checks

class ClanMod:

    def __init__(self, bot):
        self.bot = bot

    @commands.command(no_pm=True, pass_context=True)
    @checks.admin_or_permissions(manage_nicknames=True)
    async def assign_clan(self, ctx, user : discord.Member, *, clanname=""):
        """Change user's nickname to match his clan

        Leaving the nickname empty will remove it."""
        nickname = '[{}] {}'.format(clanname.strip(), user.name)
        if clanname == "":
            nickname = None
        try:
            await self.bot.change_nickname(user, nickname)
            await self.bot.say("Done.")
        except discord.Forbidden:
            await self.bot.say("I cannot do that, I lack the "
                "\"Manage Nicknames\" permission.")


    async def on_message(self,message):
        channel = message.channel
        author = message.author

        if message.server is None:
            return

        if author == self.bot.user:
            return

        if message.attachements > 0:
            await self.bot.say('DEBUG: File attachement detected.')

        await bot.process_commands(message)



def setup(bot):
    bot.add_cog(ClanMod(bot))