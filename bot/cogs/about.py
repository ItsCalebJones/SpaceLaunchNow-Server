import discord

from discord.ext import commands


class About:
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name='git')
    async def give_github_url(self):
        """Gives the URL of the Github repo"""
        await self.bot.say('You can find out more about me here: {}'.format(github_url))


def setup(bot):
    bot.add_cog(About(bot))
