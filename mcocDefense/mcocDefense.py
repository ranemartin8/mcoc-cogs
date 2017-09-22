import discord
from .utils import checks
from discord.ext import commands
from cogs.utils.dataIO import dataIO
import os
import asyncio
import pytz
from .mcoc import ChampConverter, ChampConverterMult, QuietUserError
import re
import collections

class AmbiguousArgError(QuietUserError):
	pass

class mcocDefense:
	"""Commands for coordinating Alliance War Defense diversity."""

	def __init__(self, bot, **kwargs):
		self.bot = bot
		self.defendersPATH = "data/mcocDefense/defenders.json"
		self.defendersJSON = dataIO.load_json(self.defendersPATH)

	@commands.group(no_pm=True, pass_context=True, name="defense", invoke_without_command=True)
	async def mcoc_defense(self, ctx):
		"""Set or update defenders."""
		if ctx.invoked_subcommand is None:
			await self.bot.send_cmd_help(ctx)
			return
		
	async def defense_update(self,change_type,champs,message,change_amount):
		server = message.server
		server_id = server.id
			
		if server_id not in self.defendersJSON or self.defendersJSON[server_id] == False:
			self.defendersJSON[server_id] = {}
			dataIO.save_json(self.defendersPATH, self.defendersJSON)
		champ_list = []
		for champ in champs:
			hookid = champ.hookid
			fullname = champ.full_name
			#Get Original Value
			if hookid not in self.defendersJSON[server_id]:
				original_value = 0
			else:
				original_value = self.defendersJSON[server_id][hookid]
			if change_type == "override":
				value = change_amount
			else:
				value = original_value + change_amount
			if value < 0:
				value = 0
			
			self.defendersJSON[server_id].update({hookid : value})
			dataIO.save_json(self.defendersPATH, self.defendersJSON)
			
			if hookid not in self.defendersJSON[server_id]:
				await self.bot.say('Something went wrong.')
				return
			entry = "**{}** is updated from **{}** to __**{}**__".format(fullname,original_value,value)
			champ_list.append(entry)
		await self.bot.say(":white_check_mark: Done!\n{}".format('\n'.join(champ_list)))
		return

	
	@mcoc_defense.command(no_pm=True, pass_context=True)
	async def clear(self, ctx):
		"""
		Clear all defenders for this server.
		
		"""
		server_id = ctx.message.server.id
		if server_id not in self.defendersJSON or self.defendersJSON[server_id] == False:
			self.defendersJSON[server_id] = {}
			dataIO.save_json(self.defendersPATH, self.defendersJSON)
		self.defendersJSON[server_id] = {}
		dataIO.save_json(self.defendersPATH, self.defendersJSON)
		await self.bot.say(":white_check_mark: Done! All champions have been removed.")
		return
		
	@mcoc_defense.command(no_pm=True, pass_context=True)
	async def add(self, ctx, *, champions):
		"""
		Add single or multiple defenders.
		
		EXAMPLE: !defense add sw ironman yj
		
		NOTE: This command increases the quantity for each champion by 1.
		
		"""	
		try:
			champs = await ChampConverterMult(ctx, champions).convert()
			await self.defense_update('add', champs, ctx.message, 1)
		except:
			await self.bot.say('Defenders not added. Please try again.')
			return
		
	@mcoc_defense.command(no_pm=True, pass_context=True)
	async def remove(self, ctx, *, champions):
		"""
		Remove single or multiple defenders.
		
		EXAMPLE: !defense remove bpcw capwwii hawkwye
		
		NOTE: This command DECREASES the quantity for each champion by 1.
		"""	
		try:
			champs = await ChampConverterMult(ctx, champions).convert()
			await self.defense_update('remove', champs, ctx.message, -1)
		except:
			await self.bot.say('Defenders not removed. Please try again.')
			return
		
	@mcoc_defense.command(no_pm=True, pass_context=True)
	async def set(self, ctx, amount: int, *,champions):
		"""
		Set the quantities of single or multiple defenders.

		Use plain value to OVERRIDE existing values.
		Add "+" or "-" before amount to ADD or SUBTRACT from existing values.
		
		EXAMPLE:
		!defense set 3 bw groot
		(Overrides existing values)
		=
		Black Widow (3)
		Groot (3)

		-------

		!defense set +2 groot
		(+ or - existing value)
		=
		Groot (5)
		

		NOTE: Use "!defense add/remove" to simply increase or decrease multiple champions by 1.
		"""
		change_type = "override"
		amount_str = str(amount)
		#if contains +
		if amount_str.find('+') != -1:
			change_type = "add"
		if amount_str.find('-') != -1:
			change_type = "remove"			

		try:
			champs = await ChampConverterMult(ctx, champions).convert()
			await self.defense_update(change_type, champs, ctx.message, amount)
		except:
			await self.bot.say('Defenders not updated. Please try again.')
			return
		
	@mcoc_defense.command(no_pm=True, pass_context=True)
	async def safe(self, ctx):
		"""
		View ALL safe defender options.
		
		ie. Quantity = 0 or 2 & up
		"""
		server_id = ctx.message.server.id
		if server_id not in self.defendersJSON or self.defendersJSON[server_id] == False:
			self.defendersJSON[server_id] = {}
			dataIO.save_json(self.defendersPATH, self.defendersJSON)
			await self.bot.say('No defenders have been added yet!')
			return
		safelist = []
		
		for champ,value in self.defendersJSON[server_id].items():
			champ_object = await ChampConverter(ctx, champ).convert()
			fullname = champ_object.full_name
			if value != 1:
				entry = "{} - ({} placed)".format(fullname,value)
				safelist.append(entry)
		total = len(safelist)
		await self.bot.say("**{} Safe Champions**\n{}".format(total,'\n'.join(safelist)))
		return

	@mcoc_defense.command(no_pm=True, pass_context=True)
	async def unsafe(self, ctx):
		"""
		View all unsafe defenders to avoid.
		
		ie. Quantity = 1
		"""
		server_id = ctx.message.server.id
		if server_id not in self.defendersJSON or self.defendersJSON[server_id] == False:
			self.defendersJSON[server_id] = {}
			dataIO.save_json(self.defendersPATH, self.defendersJSON)
			await self.bot.say('No defenders have been added yet!')
			return
		safelist = []
		
		for champ,value in self.defendersJSON[server_id].items():
			champ_object = await ChampConverter(ctx, champ).convert()
			fullname = champ_object.full_name
			if value == 1:
				entry = "{}".format(fullname)
				safelist.append(entry)
		total = len(safelist)
		await self.bot.say("**{} Unsafe Champions**\n{}".format(total,'\n'.join(safelist)))
		return
	
	@mcoc_defense.command(no_pm=True, pass_context=True)
	async def viewall(self, ctx):
		"""
		View ALL defender quantities.
		
		NOTE: Use "!defense safe" to just view the safe defender options.
		"""
		server_id = ctx.message.server.id
		if server_id not in self.defendersJSON or self.defendersJSON[server_id] == False:
			self.defendersJSON[server_id] = {}
			dataIO.save_json(self.defendersPATH, self.defendersJSON)
			await self.bot.say('No defenders have been added yet!')
			return
		all_values = self.defendersJSON[server_id].values()
		if len(all_values) == 0:
 			await self.bot.say('No defenders have been added yet!')
 			return
		
		running_total = 0
		for value in all_values:
			running_total = running_total + value
		champlist = []
		for champ,value in self.defendersJSON[server_id].items():
			champ_object = await ChampConverter(ctx, champ).convert()
			fullname = champ_object.full_name
			entry = "{} - ({} placed)".format(fullname,value)
			champlist.append(entry)
		await self.bot.say("**{} Champions are placed.**\n{}".format(running_total,'\n'.join(champlist)))
		return	
			      
def check_folder():
	if not os.path.exists("data/mcocDefense"):
		print("Creating data/mcocDefense folder...")
		os.makedirs("data/mcocDefense")
		print("Defenders Folder created!")
		
def check_file():
	data = {}
	g = "data/mcocDefense/defenders.json"
	if not dataIO.is_valid_json(g):
		print("Creating data/mcocDefense/defenders.json file...")
		dataIO.save_json(g, data)
		print("Defenders File created!")
		
def setup(bot):
	check_folder()
	check_file()
	n = mcocDefense(bot)
	bot.add_cog(n)





			      
