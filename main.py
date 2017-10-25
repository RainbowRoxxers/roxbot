#!/usr/env python
import logging
import os.path
import datetime
import traceback


import discord
from discord.ext import commands

import load_config
from config.server_config import ServerConfig


# Sets up Logging that discord.py does on its own
logger = logging.getLogger('discord')
logger.setLevel(logging.DEBUG)
handler = logging.FileHandler(filename='discord.log', encoding='utf-8', mode='w')
handler.setFormatter(logging.Formatter('%(asctime)s:%(levelname)s:%(name)s: %(message)s'))
logger.addHandler(handler)


server_config = ServerConfig()
bot = commands.Bot(command_prefix=load_config.command_prefix, description=load_config.description)
bot.dev = True # For debugging
bot.owner = load_config.owner

def blacklisted(user):
	with open("config/blacklist.txt", "r") as fp:
		for line in fp.readlines():
			if user.id+"\n" == line:
				return True
	return False

@bot.event
async def on_ready():
	server_config.error_check(bot.servers)
	print("Discord.py version: " + discord.__version__)
	print("Client logged in\n")
	bot.owner = load_config.owner

	print("Cogs Loaded:")
	for cog in load_config.cogslist:
		bot.load_extension(cog)
		print(cog)
	print("")

	print("Servers I am currently in:")
	for server in bot.servers:
		print(server)
	print("")

	# Testing Code
	game = discord.Game(name="Rewriting Moi for v{}".format(load_config.version), type=0)
	await bot.change_presence(game=game)
	print("Game Changed")


@bot.event
async def on_server_join(server):
	server_config.servers = server_config.load_config()
	server_config.servers[server.id] = server_config.servers_template["example"]
	server_config.update_config(server_config.servers)


@bot.event
async def on_server_remove(server):
	server_config.servers = server_config.load_config()
	server_config.servers.pop(server.id)
	server_config.update_config(server_config.servers)


@bot.event
async def on_message(message):
	# TODO: Check for words for reactions and check blacklist
	if blacklisted(message.author):
		return
	return await bot.process_commands(message)

# Bot Debug and Info

# TODO: Add command that has things like uptime in it and is outputted as a rich embed

# Error Handling, thanks for Der Eddy who did most of this stuff. <3

@bot.event
async def on_error(event, *args, **kwargs):
	if bot.dev:
		traceback.print_exc()
	else:
		embed = discord.Embed(title=':x: Event Error', colour=0xe74c3c) #Red
		embed.add_field(name='Event', value=event)
		embed.description = '```py\n%s\n```' % traceback.format_exc()
		embed.timestamp = datetime.datetime.utcnow()
		try:
			await bot.send_message(bot.owner, embed=embed)
		except:
			pass

@bot.event
async def on_command_error(error, ctx):
	if isinstance(error, commands.NoPrivateMessage):
		await bot.send_message(ctx.message.author, "This command cannot be used in private messages.")
	elif isinstance(error, commands.DisabledCommand):
		await bot.send_message(ctx.message.channel, content="This command is disabled.")
	elif isinstance(error, commands.CheckFailure):
		await bot.send_message(ctx.message.channel, content="You do not have permission to do this. Back off, thot!")
	elif isinstance(error, commands.CommandInvokeError):
		if bot.dev:
			raise error
		else:
			embed = discord.Embed(title=':x: Command Error', colour=0x992d22) #Dark Red
			embed.add_field(name='Error', value=str(error))
			embed.add_field(name='Server', value=ctx.message.server)
			embed.add_field(name='Channel', value=ctx.message.channel)
			embed.add_field(name='User', value=ctx.message.author)
			embed.add_field(name='Message', value=ctx.message.clean_content)
			embed.timestamp = datetime.datetime.utcnow()
			try:
				await bot.send_message(bot.owner, embed=embed)
			except:
				pass


if not os.path.isfile("settings/preferences.ini"):
	print("PREFERENCE FILE MISSING. Something has gone wrong. Please make sure there is a file called 'preferences.ini' in the settings folder")
else:
	bot.run(load_config.token)
