import discord
from .utils import checks
from discord.ext import commands
from cogs.utils.dataIO import dataIO
import os
import asyncio
import pytz
from .mcoc import ChampConverter, ChampConverterMult, QuietUserError
#from .gsheeter import MemberFinder, TooManyMatches, NoMemberFound 
import re
import collections
from .utils.chat_formatting import pagify



fields = ['o_tier', 'o_rating', 'o_awakened', 'd_tier','d_rating', 'd_awakened',
		  'd_boss_candidate', 'note', 'utility', 'aq_utility', 't4cc_candidate']
emoji = {
	'All':'<:all2:339511715920084993>',
	'Cosmic':'<:cosmic2:339511716104896512>',
	'Tech':'<:tech2:339511716197171200>',
	'Mutant':'<:mutant2:339511716201365514>',
	'Skill':'<:skill2:339511716549230592>',
	'Science':'<:science2:339511716029267969>',
	'Mystic':'<:mystic2:339511716150771712>',
	'boss':'<:boss:340371184824614912>'
	}

remote_data_basepath = 'https://raw.githubusercontent.com/JasonJW/mcoc-cogs/master/mcoc/data/'
gs = "https://docs.google.com/spreadsheets/d/1OpsBpJwbd_JocgOKHT_khnyHzlIk4GxPqpvu2mLoTZ0/edit#gid=1913588485"

class mcocSearch:
	"""Commands for creating and managing your Marvel Contest of Champions Profile"""

	def __init__(self, bot, **kwargs):
		self.bot = bot
		self.searchJSON = "data/gsheeter/245589956012146688/mcocSearch.json"
		#self.seatinJSON = "data/mcocSeatin/Seatin_TierList.json"
		self.searchData = dataIO.load_json(self.searchJSON)

	def get_avatar(self):
		image = '{}portraits/portrait_{}.png'.format(remote_data_basepath, self.mcocportrait)
		print(image)
		return image
		
	@commands.command(pass_context=True)
	async def search(self, ctx, *, query):
		"""
		Get a list of champions matching your search query. """
		search_msg = await self.bot.say('Searching...')

		if not self.searchData:
			await self.bot.say('<:warning_circle:340371702225567744>  Sorry, I was unable to find the mcocSearch.json file.')
			return
		matching_champs = []
		for hook_id,values in self.searchData.items():
			terms = values["terms"]
			if terms.find(query) != -1:
				hookid = values["hookid"]
				champ_object = await ChampConverter(ctx, hookid).convert()
				fullname = champ_object.full_name
				matching_champs.append(fullname)
		if len(matching_champs) == 0:
			await self.bot.say('<:unknown:340371702317842433>  Sorry, no results found for **\"{}\"**.'.format(query))
			return
		matching_champs.sort()
		msg = pagify("<:circlecheck:340371185730846720>  Search Results for **\"{}\"**\n{}".format(query,'\n'.join(matching_champs)))				
		for page in msg:
			await self.bot.say(page)
		await self.bot.delete_message(search_msg)
		return

	@commands.command(pass_context=True)
	async def lookup(self, ctx, *, champ : ChampConverter):
		"""
		Look up the abilities of a champion. """
		search_msg = await self.bot.say('Searching...')

		if not self.searchData:
			await self.bot.say('<:warning_circle:340371702225567744>  Sorry, I was unable to find the mcocSearch.json file.')
			return
		
		hookid = champ.hookid
		
		if hookid not in self.searchData or self.searchData[hookid] == False:	
			await self.bot.say('<:warning_circle:340371702225567744>  Sorry, there is no Abilities Data for **{}**.'.format(champ.full_name))
			return
		champ_data = self.searchData[hookid]
		
		em = discord.Embed(color=champ.class_color,title="**Champion Abilities**",url=gs)
		em.set_thumbnail(url=champ.get_avatar())
		em.set_author(name=champ.full_name,icon_url=champ.get_avatar())	
		
		tag_ability = "Unknown"
		hashtags = "Unknown"
			
		if champ_data["tag_ability"]:
			tag_ability = champ_data["tag_ability"]
		if champ.hashtags:
			hashtag_list = []
			for tag in champ.hashtags:
				hashtag_list.append(tag)
			hashtags = ", ".join(hashtag_list)
					
		em.add_field(name="**Abilities**", value=tag_ability,inline=False)	
		em.add_field(name="**Hashtags**", value=hashtags,inline=False)
		em.add_field(name="**Class**", value=champ.klass,inline=False)			   
			
			
		#em.set_footer(text="Seatin's Champion Tier List",icon_url=seatin_icon)
		await self.bot.say(embed=em)
		await self.bot.delete_message(search_msg)	

	
		
def setup(bot):
	n = mcocSearch(bot)
	bot.add_cog(n)
