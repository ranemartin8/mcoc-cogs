import discord
from .utils import checks
from discord.ext import commands
from cogs.utils.dataIO import dataIO
import os
import asyncio
from timezonefinder import TimezoneFinder
from geopy.geocoders import Nominatim



class mcocProfile:
	"""Commands for creating and managing your Marvel Contest of Champions Profile"""

	def __init__(self, bot):
		self.bot = bot
		self.profJSON = "data/mcocProfile/profiles.json"
		self.mcocProf = dataIO.load_json(self.profJSON)
		self.stopSkip = {
			'skip':'Question skipped! On to the next one...',
			'stop':'You\'ve exited this profile-making session.'
			}

#    @checks.is_owner()
	@commands.group(pass_context=True)
	async def mcoc_profile(self, ctx):
		"""mcocProfile allows you to create and manage your MCOC Profile."""
		if ctx.invoked_subcommand is None:
			await send_cmd_help(ctx)
			return
		
	@mcoc_profile.command(pass_context=True, name="make")
	async def _newprofile(self, ctx):
		"""Create a new profile"""
		message = ctx.message
		user = message.author
		channel = message.channel
		
		if author.id in self.mcocProf or self.mcocProf[author.id] == True:
			data = discord.Embed(colour=user.colour)
			data.add_field(name="Error:warning:",value="Oops, it seems like you already have a profile, {}.".format(user.mention))
			await self.bot.say(embed=data)
		else:
			self.mcocProf[author.id] = {}
			dataIO.save_json(self.profJSON, self.mcocProf)
			await self.bot.say("Hi {}! Let's begin setting up your Summonor profile! You can reply **skip** to"
							   "skip a question or **stop** to exit this session. This session will automatically"
							   "end after 3 minutes without a response.\nNow, start by telling me your in-game name.".format(user))
			
			game_name = await self.bot.wait_for_message(channel=channel, author=author, timeout=180.0)
			
			if game_name.content is None:
				await self.bot.say('{0.mention}, your session has timed out.'.format(author))
				return
			if game_name.content.lower() in self.stopSkip:
				await self.bot.say('{}'.format(self.stopSkip[game_name.content.lower()]))
				if game_name.content.lower() == 'stop': 
					return 
					
			await ctx.invoke(self.game_name, game_name.content)
			
			await self.bot.say("Now let's set your timezone. Where do you live? (City/State/Country)")
			
			location = await self.bot.wait_for_message(channel=channel, author=author, timeout=180.0)
			if location.content is None:
				await self.bot.say('{0.mention}, your session has timed out.'.format(author))
				return
			if location.content.lower() in self.stopSkip:
				await self.bot.say('{}'.format(self.stopSkip[location.content.lower()]))
				if location.content.lower() == 'stop': 
					return 	
			await ctx.invoke(self.timezone, location.content)	
			
			await self.bot.say("done!")
			return
			
#			
#		if author.id not in self.mcocProf or self.mcocProf[author.id] == False:
#			self.mcocProf[author.id] = {}
#			dataIO.save_json(self.profJSON, self.mcocProf)
#			
#		if user.id not in self.nerdie[server.id]:
#			self.nerdie[server.id][user.id] = {}
#			dataIO.save_json(self.profile, self.nerdie)
#			data = discord.Embed(colour=user.colour)
#			data.add_field(name="Congrats!:sparkles:", value="You have officaly created your acconut for **{}**, {}.".format(server, user.mention))
#			await self.bot.say(embed=data)
#		else: 
#			data = discord.Embed(colour=user.colour)
#			data.add_field(name="Error:warning:",value="Opps, it seems like you already have an account, {}.".format(user.mention))
#			await self.bot.say(embed=data)

	async def edit_field(self, field, ctx, value):
		user = ctx.message.author
		if author.id not in self.mcocProf or self.mcocProf[author.id] == False:
			self.mcocProf[author.id] = {}
			dataIO.save_json(self.profJSON, self.mcocProf)
		self.mcocProf[author.id].update({field : value})
		dataIO.save_json(self.profJSON, self.mcocProf)
#		value = self.mcocProf[author.id][field]
		if field in self.mcocProf[author.id]:
			value = self.mcocProf[author.id][field]
			await self.bot.say('Your **{}** is set to **{}**.'.format(field, value))
		else:
			await self.bot.say('Something went wrong')
			return
		
#	def gettimezone(self, query):
#		geolocator = Nominatim()
#		location = geolocator.geocode(query)
#		latitude = location.latitude 
#		longitude = location.longitude
#		tf = TimezoneFinder()
#		tz = tf.timezone_at(lng=longitude, lat=latitude)
#		return tz
		
#    def get_champion(self, cdict):
#        mcoc = self.bot.get_cog('MCOC')
#        champ_attr = {self.attr_map[k]: cdict[k] for k in self.attr_map.keys()}
#        return mcoc.get_champion(cdict['Id'], champ_attr)	
		
	@mcoc_profile.command(pass_context=True)
	async def game_name(self, ctx, *, game_name : str):
		"""
		Set your In-Game Name"""			

		await self.edit_field('game_name', ctx, game_name)
	
	@mcoc_profile.command(pass_context=True)
	async def timezone(self, ctx, *, location : str):
		"""
		Set your timezone"""			
		geolocator = Nominatim()
		location_obj = geolocator.geocode(location)
		latitude = location_obj.latitude 
		longitude = location_obj.longitude
		tf = TimezoneFinder()
		tz = tf.timezone_at(lng=longitude, lat=latitude)
		await self.edit_field('timezone', ctx, tz)
		
#		if author.id not in self.mcocProf or self.mcocProf[author.id] == False:
#			self.mcocProf[author.id] = {}
#			dataIO.save_json(self.profJSON, self.mcocProf)
#		
#		self.mcocProf[author.id].update({"game_name" : game_name})
#		dataIO.save_json(self.profJSON, self.mcocProf)
#		game_name = self.mcocProf[author.id]["game_name"]
#
#		await self.bot.say("Your in-game name is set to: **{}**.".format(game_name))
#
#		await self.bot.say("Take your time and tell me, what do you want in your help embed footer!")
#
#		message = await self.bot.wait_for_message(channel=channel, author=author)
#
#		if message is not None:
#			self.customhelp["embedFooter"] = message.content
#			dataIO.save_json(self.file, self.customhelp)
#			await self.bot.say("Congrats, the help embed footer has been set to: ```{}```".format(message.content))
#		else:
#			await self.bot.say("There was an error.")		
#		
def check_folder():
	if not os.path.exists("data/mcocProfile"):
		print("Creating data/mcocProfile folder...")
		os.makedirs("data/mcocProfile")
		print("Folder created!")

def check_file():
	data = {}
	f = "data/mcocProfile/profiles.json"
	if not dataIO.is_valid_json(f):
		print("Creating data/mcocProfile/profiles.json file...")
		dataIO.save_json(f, data)
		print("File created!")
		
def setup(bot):
	check_folder()
	check_file()
	n = mcocProfile(bot)
	bot.add_cog(n)