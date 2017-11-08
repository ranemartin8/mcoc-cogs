import discord
from .utils import checks
from .utils.chat_formatting import pagify
from discord.ext import commands
from cogs.utils.dataIO import dataIO
import os
import asyncio
import pytz
from .mcoc import ChampConverter, ChampConverterMult, QuietUserError
import re
import collections

all_champs = {'abomination','agentvenom','angela','antman','archangel',
	      'beast','blackbolt','blackpanther','blackpanthercivilwar',
	      'blackwidow','cable','captainamerica','captainamericawwii',
	      'captainmarvel','carnage','civilwarrior','colossus','crossbones',
	      'cyclops90s','cyclops','daredevil','daredevilnetflix','deadpool',
	      'deadpoolxforce','doctoroctopus','drstrange','brothervoodoo',
	      'dormammu','drax','electro','elektra','falcon','gambit',
	      'gamora','ghostrider','greengoblin','groot','guillotine',
	      'gwenpool','hawkeye','howardtheduck','hulk','hulkbuster',
	      'hyperion','iceman','ironfistwhite','ironfist','ironman',
	      'ironpatriot','joefixit','juggernaut','kang','karnak','grootking',
	      'kingpin','loki','lukecage','magik','magneto','magnetomarvelnow',
	      'medusa','moonknight','karlmordo','msmarvel','kamalakhan','nebula',
	      'nightcrawler','wolverineoldman','phoenix','psylockexforce','punisher',
	      'p99','quake','redhulk','rhino','rocket','rogue','ronan','scarletwitch',
	      'shehulk','spidergwen','spiderman','spidermanmcu','spidermanblack',
	      'spidermanmorales','starlord','storm','superiorironman','thanos','hood',
	      'thor','thorjanefoster','ultronclassic','ultron','unstoppablecolossus',
	      'venom','venompool','vision','thevision','vulture','warmachine','wintersoldier',
	      'wolverine','x23','yellowjacket','yondu'}

bg_list = {'bg1','bg2','bg3'}

class AmbiguousArgError(QuietUserError):
	pass

class mcocDefense:
	"""Commands for coordinating Alliance War Defense diversity."""

	def __init__(self, bot, **kwargs):
		self.bot = bot
		self.defendersPATH = "data/mcocDefense/defenders.json"
		self.defendersJSON = dataIO.load_json(self.defendersPATH)

	@commands.group(no_pm=True, pass_context=True, name="defense", invoke_without_command=True,aliases=['def',])
	async def mcoc_defense(self, ctx):
		"""Set or update defenders."""
		if ctx.invoked_subcommand is None:
			await self.bot.send_cmd_help(ctx)
			return
		
	async def defense_update(self, battlegroup, change_type,champs,message,change_amount):
		server = message.server
		server_id = server.id
		battlegroup = battlegroup.lower()
		if battlegroup not in bg_list or bg_list[battlegroup] == False:
			await self.bot.say('<:warning_circle:340371702225567744> Invalid Battlegroup. Please indicate **bg1, bg2 or bg3**.')
			return                       
		if server_id not in self.defendersJSON or self.defendersJSON[server_id] == False:
			self.defendersJSON[server_id] = {"bg1":{},"bg2":{},"bg3":{}}
			dataIO.save_json(self.defendersPATH, self.defendersJSON)
		champ_list = []
		for champ in champs:
			hookid = champ.hookid
			fullname = champ.full_name
			#Get Original Value
			if hookid not in self.defendersJSON[server_id]:
				original_value = 0
			else:
				original_value = self.defendersJSON[server_id][battlegroup][hookid]
			if change_type == "override":
				value = change_amount
			else:
				value = original_value + change_amount
			if value < 0:
				value = 0
			
			self.defendersJSON[server_id][battlegroup].update({hookid : value})
			dataIO.save_json(self.defendersPATH, self.defendersJSON)
			
			if hookid not in self.defendersJSON[server_id][battlegroup]:
				await self.bot.say('<:warning_circle:340371702225567744>  Something went wrong.')
				return
			entry = "**{}** is updated from **{}** to __**{}**__".format(fullname,original_value,value)
			champ_list.append(entry)
		await self.bot.say("<:circlecheck:340371185730846720>  **{}** defenders are updated!\n{}".format(battlegroup,'\n'.join(champ_list)))
		return

	
	@mcoc_defense.command(no_pm=True, pass_context=True)
	@checks.mod_or_permissions(manage_roles=True)
	async def clear(self, ctx, battlegroup):
		"""
		OFFICERS ONLY. Clear all defenders.
		
		"""
		server_id = ctx.message.server.id
		battlegroup = battlegroup.lower()
		if battlegroup not in bg_list or bg_list[battlegroup] == False:
			await self.bot.say('<:warning_circle:340371702225567744> Invalid Battlegroup. Please indicate **bg1, bg2 or bg3**.')
			return 	
		if server_id not in self.defendersJSON or self.defendersJSON[server_id] == False:
			self.defendersJSON[server_id] = {'bg1':{},'bg2':{},'bg3':{}}
			dataIO.save_json(self.defendersPATH, self.defendersJSON)
		self.defendersJSON[server_id][battlegroup].update({})
##		self.defendersJSON[server_id] = {'bg1':{},'bg2':{},'bg3':{}}
		dataIO.save_json(self.defendersPATH, self.defendersJSON)
		await self.bot.say("<:circlecheck:340371185730846720>  Done! All **{}** champions have been removed.".format(battlegroup))
		return
		
	@mcoc_defense.command(no_pm=True, pass_context=True)
	async def add(self, ctx, battlegroup, *, champions):
		"""
		Add single or multiple defenders.
		
		EXAMPLE: !defense add bg2 sw ironman yj
		
		NOTE: This command increases the quantity for each champion by 1.
		
		"""	
		try:
			champs = await ChampConverterMult(ctx, champions).convert()
			await self.defense_update(battlegroup,'add', champs, ctx.message, 1)
		except:
			await self.bot.say('<:warning_circle:340371702225567744>  Defenders not added. Please try again.')
			return
		
	@mcoc_defense.command(no_pm=True, pass_context=True)
	async def remove(self, ctx, battlegroup, *, champions):
		"""
		Remove single or multiple defenders.
		
		EXAMPLE: !defense remove bg1 bpcw capwwii hawkwye
		
		NOTE: This command DECREASES the quantity for each champion by 1.
		"""	
		try:
			champs = await ChampConverterMult(ctx, champions).convert()
			await self.defense_update(battlegroup,'remove', champs, ctx.message, -1)
		except:
			await self.bot.say('<:warning_circle:340371702225567744>  Defenders not removed. Please try again.')
			return
		
	@mcoc_defense.command(no_pm=True, pass_context=True)
	async def set(self, ctx, battlegroup, amount: int, *,champions):
		"""
		Set the quantities of single or multiple defenders.

		Use plain value to OVERRIDE existing values.
		Add "+" or "-" before amount to ADD or SUBTRACT from existing values.
		
		EXAMPLE:
		!defense set bg3 3 bw groot
		(Overrides existing values)
		=
		Black Widow (3)
		Groot (3)

		-------

		!defense set bg1 +2 groot
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
			await self.defense_update(battlegroup, change_type, champs, ctx.message, amount)
		except:
			await self.bot.say('<:warning_circle:340371702225567744>  Defenders not updated. Please try again.')
			return
		
##	@mcoc_defense.command(no_pm=True, pass_context=True)
##	async def free(self, ctx):
##		"""
##		View available defenders.
##		
##		These defenders have not yet been placed.
##		"""
##		server_id = ctx.message.server.id
##		if server_id not in self.defendersJSON or self.defendersJSON[server_id] == False:
##			self.defendersJSON[server_id] = {}
##			dataIO.save_json(self.defendersPATH, self.defendersJSON)
##			await self.bot.say('<:warning_circle:340371702225567744>  All defenders are available right now, because no defenders have been added yet!')
##			return
##		safelist = []
##		hookid_list = []
##		for champ,value in self.defendersJSON[server_id].items():
##			hookid_list.append(champ)
##			champ_object = await ChampConverter(ctx, champ).convert()
##			fullname = champ_object.full_name				
##			if value == 0:
##				entry = "{}".format(fullname,value)
##				safelist.append(entry)
##				
##		for champ in all_champs:
##			if champ not in hookid_list:
##				champ_object = await ChampConverter(ctx, champ).convert()
##				fullname = champ_object.full_name				
##				entry = "{}".format(fullname)
##				safelist.append(entry)					
##		total = len(safelist)
##		safelist.sort()
##		msg = pagify("<:aw:340368013112901633>  **{} Available Defenders**\n{}".format(total,'\n'.join(safelist)))
##		
##		for page in msg:
##			await self.bot.say(page)
##		return	

	@mcoc_defense.command(no_pm=True, pass_context=True)
	async def placed(self, ctx, battlegroup):
		"""
		View which defenders to avoid.
		
		Defenders in this list are ones who have already been placed.
		Placing a duplicate would not contribute to defender diversity.
		"""
		server_id = ctx.message.server.id
		battlegroup = battlegroup.lower()
		if battlegroup not in bg_list or bg_list[battlegroup] == False:
			await self.bot.say('<:warning_circle:340371702225567744> Invalid Battlegroup. Please indicate **bg1, bg2 or bg3**.')
			return 		
		if server_id not in self.defendersJSON or self.defendersJSON[server_id] == False:
			self.defendersJSON[server_id] = {'bg1':{},'bg2':{},'bg3':{}}
			dataIO.save_json(self.defendersPATH, self.defendersJSON)
			await self.bot.say('<:warning_circle:340371702225567744>  No defenders have been added yet!')
			return
		safelist = []
		
		for champ,value in self.defendersJSON[server_id][battlegroup].items():
			champ_object = await ChampConverter(ctx, champ).convert()
			fullname = champ_object.full_name
			if value > 0:
				entry = "{} - **{}**".format(fullname,value)
				safelist.append(entry)
		total = len(safelist)
		running_total = 0
		for value in self.defendersJSON[server_id][battlegroup].values():
			running_total = running_total + value
		safelist.sort()
		msg = pagify("<:aw:340368013112901633>  **{} Placed Defenders**\n[{} Unique]\n{}".format(running_total,total,'\n'.join(safelist)))
		for page in msg:
			await self.bot.say(page)
		return
	
##	@mcoc_defense.command(no_pm=True, pass_context=True)
##	async def all(self, ctx):
##		"""
##		View ALL available defender & quantities.
##		
##		NOTE: Use "!defense safe" to just view the safe defender options.
##		"""
##		server_id = ctx.message.server.id
##		if server_id not in self.defendersJSON or self.defendersJSON[server_id] == False:
##			self.defendersJSON[server_id] = {}
##			dataIO.save_json(self.defendersPATH, self.defendersJSON)
##			await self.bot.say('<:warning_circle:340371702225567744>  No defenders have been added yet!')
##			return
##		all_values = self.defendersJSON[server_id].values()
##		if len(all_values) == 0:
## 			await self.bot.say('<:warning_circle:340371702225567744>  No defenders have been added yet!')
## 			return
##		
##		running_total = 0
##		for value in all_values:
##			running_total = running_total + value
##		champlist = []
##		hookid_list = []
##		for champ,value in self.defendersJSON[server_id].items():
##			hookid_list.append(champ)
##			champ_object = await ChampConverter(ctx, champ).convert()
##			fullname = champ_object.full_name
##			entry = "{} - **{}**".format(fullname,value)
##			champlist.append(entry)
##			
##		for champ in all_champs:
##			if champ not in hookid_list:
##				champ_object = await ChampConverter(ctx, champ).convert()
##				fullname = champ_object.full_name				
##				entry = "{} - **0**".format(fullname)
##				champlist.append(entry)
##		champlist.sort()
##		msg = pagify("<:aw:340368013112901633>  **All Defenders**\n[{} Total Placed]\n{}".format(running_total,'\n'.join(champlist)))
##		for page in msg:
##			await self.bot.say(page)
##		return	
			      
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





			      
