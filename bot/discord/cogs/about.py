from discord.ext import commands

url = 'https://spacelaunchnow.me'


class About(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name='info')
    async def info(self, context):
        """Gives the URL of the project."""
        channel = context.message.channel
        await channel.send('You can find out more about us here: {}'.format(url))


def setup(bot):
    bot.add_cog(About(bot))
