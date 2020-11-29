# coding: utf-8
import datetime
import logging
import os
import sys
import traceback
from collections import Counter

import django
from discord.ext import commands
os.environ["DJANGO_ALLOW_ASYNC_UNSAFE"] = "true"
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "spacelaunchnow.settings")
django.setup()

from spacelaunchnow import config

debug_mode = config.SQUID_BOT_DEBUG_MODE
if not isinstance(debug_mode, bool):
    # SQUID_BOT_DEBUG_MODE can be set to either 'false' or 'no'. Case insensitive
    debug_mode = not (debug_mode.lower() in ['false', 'no'])

description = """
Hey there spacefarer - thanks for choosing the Space Launch Bot for your notifications needs. 
Please use the prefix .sln - to get started try the .sln help command!

Check out this project at https://spacelaunchnow.me!
"""


log = logging.getLogger('bot.discord')
help_attrs = dict(hidden=False)
prefix = ['.sln ']
bot = commands.Bot(command_prefix=prefix, description=description, pm_help=None, help_attrs=help_attrs)
bot_start_time = datetime.datetime.utcnow()
initial_extensions = ['bot.discord.cogs.admin', 'bot.discord.cogs.about', 'bot.discord.cogs.launches',
                      'bot.discord.cogs.notifier', 'bot.discord.cogs.reddit', 'bot.discord.cogs.twitter',
                      'bot.discord.cogs.news']


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
        print('In {0.command.qualified_name}:'.format(ctx), file=sys.stderr)
        traceback.print_tb(error.original.__traceback__)
        print('{0.__class__.__name__}: {0}'.format(error.original), file=sys.stderr)


@bot.event
async def on_ready():
    log.info('Logged in as:')
    log.info('Username: ' + bot.user.name)
    log.info('ID: ' + str(bot.user.id))
    log.info('Debug: ' + str(debug_mode))
    log.info('Total Servers: %s' % len(bot.guilds))
    member_count = 0
    for server in bot.guilds:
        # log.info("Server: %s" % server.name)
        # log.info("Server: %s" % server.id)
        # log.info("Owner: %s#%s" % (server.owner.name,server.owner.discriminator))
        # log.info("Owner ID: %s" % server.owner.id)
        # log.info("Members: %s" % server.member_count)
        # log.info(server.icon_url)
        # log.info(server.splash_url)
        # log.info('++++++')
        if server.id != 264445053596991498:
            member_count += server.member_count
    log.info("Currently serving %s members in %s servers." % (member_count, len(bot.guilds)))
    log.info('------')
    log.info('Logged in as:\nUsername: {0.user.name}\nID: {0.user.id}\nDebug: {1}\n------'.format(bot, str(debug_mode)))
    if not hasattr(bot, 'uptime'):
        bot.uptime = bot_start_time

@bot.event
async def on_resumed():
    log.info('resumed...')


@bot.event
async def on_command(ctx):
    message = ctx.message
    destination = "Unknown"
    if message.channel.type.name is 'private':
        destination = 'Private Message'
    else:
        destination = '{0.guild.name}:#{0.channel.name}'.format(message)
    log.info('{0.author.name} in {1}: {0.content}'.format(message, destination))


@bot.event
async def on_message(message):
    if message.author.bot:
        return
    await bot.process_commands(message)


if __name__ == '__main__':
    if any('debug' in arg.lower() for arg in sys.argv):
        bot.command_prefix = '$'

    if os.name != 'nt' and os.name != 'posix':
        writePidFile()

    bot.client_id = os.getenv('BOT_CLIENT_ID', config.SQUID_BOT_CLIENT_ID)
    bot.commands_used = Counter()
    for extension in initial_extensions:
        try:
            bot.load_extension(extension)
        except Exception as e:
            log.info('Failed to load extension {}\n{}: {}'.format(extension, type(e).__name__, e))
    bot.run(os.getenv('BOT_TOKEN', config.SQUID_BOT_TOKEN))

