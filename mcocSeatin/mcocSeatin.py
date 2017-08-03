import discord
from .utils import checks
from discord.ext import commands
from cogs.utils.dataIO import dataIO
import os
import asyncio
from timezonefinder import TimezoneFinder
from geopy.geocoders import Nominatim
from datetime import tzinfo, timedelta, datetime
import pytz
from .mcoc import ChampConverter, ChampConverterMult, QuietUserError
from .gsheeter import MemberFinder, TooManyMatches, NoMemberFound 
import re
import collections

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

seatin_gs = "https://docs.google.com/spreadsheets/d/1beR2CAlBQ2XBA3M1jJ1aPEfwE46eQt6LU-lzA0babxQ/edit#gid=1632065512"

seatin_icon = "http://i.imgur.com/N8B9qq5.jpg"


class mcocSeatin:
	"""Commands for creating and managing your Marvel Contest of Champions Profile"""

	def __init__(self, bot, **kwargs):
		self.bot = bot
		self.seatinJSON = "data/mcocSeatin/Seatin_TierList.json"
		self.seatinData = dataIO.load_json(self.seatinJSON)

	def get_avatar(self):
		image = '{}portraits/portrait_{}.png'.format(remote_data_basepath, self.mcocportrait)
		print(image)
		return image
		
	@commands.command(pass_context=True)
	async def seatin(self, ctx, *, champ: ChampConverter):
		"""
		Get Seatin Rank and Info for a champion. """
		search_msg = await self.bot.say('Searching...')
		hookid = champ.hookid
		
		if hookid not in self.seatinData or self.seatinData[hookid] == False:	
			await self.bot.say(':warning:  Sorry, there is no Seatin Data for **{}**.'.format(hookid))
			return
		champ_data = self.seatinData[hookid]
		
		em = discord.Embed(color=champ.class_color,title="**Seatin Rank & Rating**",url=seatin_gs)
		em.set_thumbnail(url=champ.get_avatar())
		em.set_author(name=champ.full_name,icon_url=champ.get_avatar())	
		
		o_tier=d_tier = "Unknown"
		o_rating=o_awakened=d_rating=d_awakened = "N/A"
		d_boss_candidate=note=utility=aq_utility = ""
		t4cc_candidate = "No"
			
		if champ_data["o_tier"]:
			o_tier = champ_data["o_tier"]
		if champ_data["o_rating"]:
			o_rating = champ_data["o_rating"]			
		if champ_data["o_awakened"]:
			o_awakened = champ_data["o_awakened"]	
		
		offense = "**Tier:** {}\n**Rating:** {}\n**Needs Sig Ability?** {}".format(o_tier,o_rating,o_awakened)
			
		em.add_field(name="**Offense**", value=offense,inline=False)	
			
		if champ_data["d_tier"]:
			d_tier = champ_data["d_tier"]
		if champ_data["d_rating"]:
			d_rating = champ_data["d_rating"]			
		if champ_data["d_awakened"]:
			d_awakened = champ_data["d_awakened"]					
		if champ_data["d_boss_candidate"]:
			d_boss_candidate = champ_data["d_boss_candidate"]					
		if champ_data["note"]:
			note = champ_data["note"]				
		defense = "**Tier:** {}\n**Rating:** {}\n**Needs Sig Ability?** {}".format(d_tier,d_rating,d_awakened)
		
		if d_boss_candidate:
			defense = emoji["boss"] + " **Boss Candidate**\n" + defense
		if note:
			defense = defense + "\n\* *{}*".format(note)
		
		em.add_field(name="**Defense**", value=defense,inline=False)
		
		if champ_data["utility"]:
			utility = champ_data["utility"]
		if champ_data["aq_utility"]:
			aq_utility = champ_data["aq_utility"]
		
		if len(utility+aq_utility) != 0:
			if utility:
				utility = "**General:** " + utility
			if aq_utility:
				aq_utility = "\n**AQ:** " + aq_utility
			util = utility + aq_utility
			em.add_field(name="**Utility**", value=util,inline=False)	
		if champ_data["t4cc_candidate"]:
			t4cc_candidate = champ_data["t4cc_candidate"]
			em.add_field(name="**T4CC Candidate**", value=t4cc_candidate,inline=False)	
			
		em.set_footer(text="Seatin Tier List",icon_url=seatin_icon)
		await self.bot.say(embed=em)
		await self.bot.delete_message(search_msg)		
		
		
def setup(bot):
	n = mcocSeatin(bot)
	bot.add_cog(n)