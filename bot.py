import asyncio
import datetime
import logging
import os
import sys
import traceback
from collections import Counter

import discord
import django
from discord.ext import commands

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "spacelaunchnow.settings")
django.setup()

from spacelaunchnow import config

debug_mode = config.SQUID_BOT_DEBUG_MODE
if not isinstance(debug_mode, bool):
    # SQUID_BOT_DEBUG_MODE can be set to either 'false' or 'no'. Case insensitive
    debug_mode = not (debug_mode.lower() in ['false', 'no'])

github_url = 'https://github.com/ItsCalebJones/SpaceLaunchNow-Server/'

description = """
Hello! I am a bot written by Koun7erfit with a backbone from R Danny.
For the nitty gritty, checkout the project GitHub: {0}
""".format(github_url)
initial_extensions = ["bot.cogs.reddit", "bot.cogs.notifications", "bot.cogs.launches", "bot.cogs.about", "bot.cogs.twitter"]

discord_logger = logging.getLogger('discord')
discord_logger.setLevel(logging.CRITICAL)
log = logging.getLogger()
log.setLevel(logging.INFO)
bot_start_time = datetime.datetime.utcnow()

logs_dir = 'log/{0}/{1}'.format(bot_start_time.strftime('%Y'), bot_start_time.strftime('%m'))
os.makedirs(logs_dir, exist_ok=True)
log_filename = '{0}/squid_bot.{1}.log'.format(logs_dir, bot_start_time.strftime('%Y-%m-%d.%H-%M-%S'))

handler = logging.FileHandler(filename=log_filename, encoding='utf-8', mode='w')
log.addHandler(handler)
help_attrs = dict(hidden=True)
prefix = ['?']
bot = commands.Bot(command_prefix=prefix, description=description, pm_help=None, help_attrs=help_attrs)


@bot.event
async def on_command_error(error, ctx):
    if isinstance(error, commands.NoPrivateMessage):
        await bot.send_message(ctx.message.author, 'This command cannot be used in private messages.')
    elif isinstance(error, commands.DisabledCommand):
        await bot.send_message(ctx.message.author, 'Sorry. This command is disabled and cannot be used.')
    elif isinstance(error, commands.CommandInvokeError):
        print('In {0.command.qualified_name}:'.format(ctx), file=sys.stderr)
        traceback.print_tb(error.original.__traceback__)
        print('{0.__class__.__name__}: {0}'.format(error.original), file=sys.stderr)


@bot.event
async def on_ready():
    print('Logged in as:')
    print('Username: ' + bot.user.name)
    print('ID: ' + bot.user.id)
    print('Debug: ' + str(debug_mode))
    print('------')
    log.info('Logged in as:\nUsername: {0.user.name}\nID: {0.user.id}\nDebug: {1}\n------'.format(bot, str(debug_mode)))
    if not hasattr(bot, 'uptime'):
        bot.uptime = bot_start_time
    squid_bot_game = discord.Game(name='Watching for launches * spacelaunchnow.me', url=github_url, type=0)
    await bot.change_presence(game=squid_bot_game, status=discord.Status.online, afk=False)


@bot.event
async def on_resumed():
    print('resumed...')


@bot.event
async def on_command(command, ctx):
    bot.commands_used[command.name] += 1
    message = ctx.message
    destination = None
    if message.channel.is_private:
        destination = 'Private Message'
    else:
        destination = '#{0.channel.name} ({0.server.name})'.format(message)
    print('{0.timestamp}: {0.author.name} in {1}: {0.content}'.format(message, destination))
    log.info('{0.timestamp}: {0.author.name} in {1}: {0.content}'.format(message, destination))


@bot.event
async def on_message(message):
    if message.author.bot:
        return
    await bot.process_commands(message)


if __name__ == '__main__':
    if any('debug' in arg.lower() for arg in sys.argv):
        bot.command_prefix = '$'

    bot.client_id = config.SQUID_BOT_CLIENT_ID
    bot.commands_used = Counter()
    for extension in initial_extensions:
        try:
            bot.load_extension(extension)
        except Exception as e:
            print('Failed to load extension {}\n{}: {}'.format(extension, type(e).__name__, e))
    bot.run(config.SQUID_BOT_TOKEN)
    handlers = log.handlers[:]
    for hdlr in handlers:
        hdlr.close()
        log.removeHandler(hdlr)
