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
from django.template import defaultfilters

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "spacelaunchnow.settings")
django.setup()

from api.models import Launch
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
initial_extensions = ["bot.cogs.reddit", "bot.cogs.notifications", "bot.cogs.launches", "bot.cogs.about", "bot.cogs.twitter", "bot.cogs.news"]

log = logging.getLogger('bot.discord')
help_attrs = dict(hidden=True)
prefix = ['?']
bot = commands.Bot(command_prefix=prefix, description=description, pm_help=None, help_attrs=help_attrs)
bot_start_time = datetime.datetime.utcnow()


def writePidFile():
    pid = str(os.getpid())
    filename = '/var/run/spacelaunchnow/discord.pid'
    os.makedirs(os.path.dirname(filename), exist_ok=True)
    current_file = open(filename, 'w')
    current_file.write(pid)
    current_file.close()


@bot.event
async def on_command_error(error, ctx):
    if isinstance(error, commands.NoPrivateMessage):
        await bot.send_message(ctx.message.author, 'This command cannot be used in private messages.')
    elif isinstance(error, commands.DisabledCommand):
        await bot.send_message(ctx.message.author, 'Sorry. This command is disabled and cannot be used.')
    elif isinstance(error, commands.CommandInvokeError):
        log.info('In {0.command.qualified_name}:'.format(ctx), file=sys.stderr)
        traceback.print_tb(error.original.__traceback__)
        log.info('{0.__class__.__name__}: {0}'.format(error.original), file=sys.stderr)


@bot.event
async def on_ready():
    log.info('Logged in as:')
    log.info('Username: ' + bot.user.name)
    log.info('ID: ' + bot.user.id)
    log.info('Debug: ' + str(debug_mode))
    log.info('------')
    log.info('Logged in as:\nUsername: {0.user.name}\nID: {0.user.id}\nDebug: {1}\n------'.format(bot, str(debug_mode)))
    if not hasattr(bot, 'uptime'):
        bot.uptime = bot_start_time

@bot.event
async def on_resumed():
    log.info('resumed...')


@bot.event
async def on_command(command, ctx):
    bot.commands_used[command.name] += 1
    message = ctx.message
    destination = None
    if message.channel.is_private:
        destination = 'Private Message'
    else:
        destination = '#{0.channel.name} ({0.server.name})'.format(message)
    log.info('{0.timestamp}: {0.author.name} in {1}: {0.content}'.format(message, destination))


@bot.event
async def on_message(message):
    if message.author.bot:
        return
    await bot.process_commands(message)


if __name__ == '__main__':
    if any('debug' in arg.lower() for arg in sys.argv):
        bot.command_prefix = '$'

    if os.name != 'nt':
        writePidFile()

    bot.client_id = config.SQUID_BOT_CLIENT_ID
    bot.commands_used = Counter()
    for extension in initial_extensions:
        try:
            bot.load_extension(extension)
        except Exception as e:
            log.info('Failed to load extension {}\n{}: {}'.format(extension, type(e).__name__, e))
    bot.run(config.SQUID_BOT_TOKEN)
