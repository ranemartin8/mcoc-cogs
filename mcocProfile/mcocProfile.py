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
from .gsheeter import MemberFinder

field_names = {'summonerlevel':'Summoner Level','herorating':'Total Base Hero Rating','timezone':'Timezone','gamename':'In-Game Name','aq':'Alliance Quest','awd':'AW Defense','awo':'AW Offense','alliance':'Alliance','bg':'Battlegroup','achievements':'Achievements'}
hook_fields = {'awo','awd','aq'}
fields_list = field_names.keys()
valid_fields = set(fields_list)
valid_int = {'1','2','3','4','5'}
valid_stop = {'stop','end','cancel'}
achievements_set = {'rol','lol','rtl','100%act4'}
bg_set = {'bg1','bg2','bg3'}
remote_data_basepath = 'https://raw.githubusercontent.com/JasonJW/mcoc-cogs/master/mcoc/data/'

def getLocalTime(datetime_obj,timezone):
	utcmoment = datetime_obj.replace(tzinfo=pytz.utc)
	get_time = utcmoment.astimezone(pytz.timezone(timezone))
	return get_time

def clock_emoji(datetime_obj):
	time_int = int(datetime_obj.strftime("%I%M").lstrip('0'))
	clock_times = [1260, 100, 960, 1000, 1030, 1060, 1100, 1130, 1160, 1200, 1230,
				   130, 160, 200, 230, 260, 300, 330, 360, 400, 430, 460, 500, 530,
				   560, 600, 630, 660, 700, 730, 760, 800, 830, 860, 900, 930]
	closest_time = min(clock_times, key=lambda x:abs(x-time_int))
	clock_time = c_times[str(closest_time)]
	if clock_time:
		return ':clock' + clock_time + ':'
	else:
		return ':alarm_clock:'
	
c_times = {
		'1260':'1','100':'1','960':'10','1000':'10','1030':'1030','1060':'11','1100':'11',
		'1130':'1130','1160':'12','1200':'12','1230':'1230','130':'130','160':'2','200':'2',
		'230':'230','260':'3','300':'3','330':'330','360':'4','400':'4','430':'430','460':'5',
		'500':'5','530':'530','560':'6','600':'6','630':'630','660':'7','700':'7','730':'730',
		'760':'8','800':'8','830':'830','860':'9','900':'9','930':'930'
		}

class mcocProfile:
	"""Commands for creating and managing your Marvel Contest of Champions Profile"""

	def __init__(self, bot):
		self.bot = bot
		self.profJSON = "data/mcocProfile/profiles.json"
		self.mcocProf = dataIO.load_json(self.profJSON)
		self.hookPath = "data/hook/users/{}"
		self.hookJSON = "data/hook/users/{}/champs.json"
		
	@commands.group(no_pm=True, pass_context=True, name="profiler",aliases=['account','prof',])
	async def mcoc_profile(self, ctx):
		"""mcocProfile allows you to create and manage your MCOC Profile."""
		if ctx.invoked_subcommand is None:
			await self.bot.send_cmd_help(ctx)
			return
		
	async def is_number(self,s):
		try:
			float(s)
			return True
		except ValueError:
			return False
		
	async def check_field(self, field, value):
		field_checks = {'summonerlevel','herorating'}
		validity = {'status':'valid','reason':'n/a'}
		if field not in field_checks:
			return validity
		if field == 'summonerlevel':
			if str(value).find(',') != -1:
				value = str(value).replace(',','')
			is_number = await self.is_number(value)
			if is_number is False:
				validity.update({'status':'invalid','reason':'Summoner Level must be a number. Summoner Level not set.'})
			elif int(value) > 60 or int(value) < 0:
				validity.update({'status':'invalid','reason':'Summoner Level must fall between 0 and 60. Summoner Level not set.'})
			else:
				pass
		if field == 'herorating':
			if str(value).find(',') != -1:
				value = str(value).replace(',','')
			is_number = await self.is_number(value)
			if is_number is False:
				validity.update({'status':'invalid','reason':'Hero Rating must be a number. Hero Rating not set.'})
		return validity
			

	async def hook_file(self, userid):
		data = {}
		if not os.path.exists(self.hookPath.format(userid)):
			os.makedirs(self.hookPath.format(userid))
		f = self.hookJSON.format(userid)
		if not dataIO.is_valid_json(f):
			dataIO.save_json(f, data)
		return dataIO.load_json(f)
		
				
	async def gettimezone(self, query):
		geolocator = Nominatim()
		try:
			location = geolocator.geocode(query)
		except:
			await self.bot.say('Location not found.')
			return			
		latitude = location.latitude 
		longitude = location.longitude
		tf = TimezoneFinder()
		tz = tf.timezone_at(lng=longitude, lat=latitude)
		return tz
		
	def get_avatar(self):
		image = '{}portraits/portrait_{}.png'.format(remote_data_basepath, self.mcocportrait)
		print(image)
		return image
	
	async def edit_field(self,user_id,field, ctx, value,src='author'):
		identifier = 'Your'
		if src != 'author':
			get_mem = ctx.server.get_member(user_id)
			identifier = get_mem.display_name + "'s"
		check = await self.check_field(field,value)
		if check['status'] == 'invalid':
			await self.bot.say(check['reason'])
			return
		if user_id not in self.mcocProf or self.mcocProf[user_id] == False:
			self.mcocProf[user_id] = {}
			dataIO.save_json(self.profJSON, self.mcocProf)
		self.mcocProf[user_id].update({field : value})
		dataIO.save_json(self.profJSON, self.mcocProf)
		if field not in field_names:
			field_name = field
		else:
			field_name = field_names[field]
			
		if field in self.mcocProf[user_id]:
			value = self.mcocProf[user_id][field]
			await self.bot.say('{} **{}** is set to **{}**.'.format(identifier,field_name, value))
		else:
			await self.bot.say('Something went wrong. **{}** not set'.format(field_name))
			return
		
	async def hook_update(self,user_id,team,champs, message,src='author'):
		identifier = 'Your'
		if src != 'author':
			get_mem = message.server.get_member(user_id)
			identifier = get_mem.display_name + "'s"
		hook = await self.hook_file(user_id)
		author = message.author
		channel = message.channel
		team_max = {"awd":5,"awo":3,"aq":3}
		max_int = team_max[team]
		team_name = field_names[team]
		champ_list = []
		for champ in champs:
			entry = champ.rank_sig_str + ' ' + champ.full_name
			champ_list.append(entry)
		if len(champ_list)< max_int and len(champ_list) > 1:
			await self.bot.say('You can only swap out one champion at a time or replace all {} at once.'.format(max_int))
			return
		if len(champ_list) > max_int:
			await self.bot.say('You can only set a maximum of **{}** champions for this team.'.format(max_int))
			return
		
		if len(champ_list) == 1: #updating one champion
			try:
				existing_champs = hook[team]
				ext_len = len(existing_champs) #extlen = 3, max = 5. if 3 < 5
				if ext_len < max_int: 
					count = ext_len
					while count < max_int:
						existing_champs.append('[empty slot]')
						count += 1
			except KeyError:
				existing_champs = placeholders[team]
			i = 1
			current_champs = []
			for champ in existing_champs:
				current_champs.append('**'+ str(i) +'.**    ' +champ)
				i += 1

			await self.bot.say('New Team Member: **{}**\n\nReply with the # (1 - {}) of the '
							   'champion you\'d like to replace:\n{}\n\nReply **stop** to cancel.'.format(champ_list[0],max_int,'\n'.join(current_champs)))
			check = lambda m: m.content in valid_int or m.content in valid_stop
			response = await self.bot.wait_for_message(channel=channel, author=author, check=check, timeout=60.0)
			if response is None:
				await self.bot.say('Request timed out.')
				return
			if response.content in valid_stop:
				await self.bot.say('Request cancelled.')
				return
			resp_int = int(response.content)
			if resp_int > max_int or resp_int < 1:
				await self.bot.say('Number must fall between 1 and {}. Team not updated.'.format(max_int))
				return
			pos = resp_int-1
			existing_champs[pos] = champ_list[0]
			newchamps = existing_champs
			hook.update({team : newchamps})
			dataIO.save_json(self.hookJSON.format(user_id), hook)
			await self.bot.say(':white_check_mark:  {} updated **{}** team:\n{}'.format(identifier,team_name,'\n'.join(newchamps)))	
		else: #updating the whole team
			hook.update({team : champ_list})
			dataIO.save_json(self.hookJSON.format(user_id), hook)
			await self.bot.say(':white_check_mark:  {} updated **{}** team:\n{}'.format(identifier,team_name,'\n'.join(champ_list)))		

	
	@mcoc_profile.command(no_pm=True, pass_context=True,hidden=True)
	@checks.is_owner()
	async def edit(self, ctx, user : str, field : str, *, value : str):
		"""
		OWNER ONLY. Update member profile fields."""
		user = await MemberFinder(ctx, user).convert()
		user_id = user.id
		if field not in valid_fields:
			await self.bot.say('**{}** is not a valid field. Try again with a valid '
							   'field from the following list: \n- {}'.format(field,'\n- '.join(fields_list)))
			return
		if field not in hook_fields:
			await self.edit_field(user_id, field, ctx, value,)
			return
		else:
			champs = await ChampConverter(ctx, value).convert()
			await self.hook_update(user_id, field, value, ctx.message)
			return
		
	@mcoc_profile.command(no_pm=True, pass_context=True,aliases=['del',])
	async def delete(self, ctx, *, field : str):
		"""
		Delete a field from your profile."""
		author = ctx.message.author
		if field not in valid_fields:
			await self.bot.say('**{}** is not a valid field. Try again with a valid '
							   'field from the following list: \n- {}'.format(field,'\n- '.join(fields_list)))
			return
		if field == "awd" or field == "awo" or field == "aq":
			hook = await self.hook_file(author.id)
			if field in hook:
				del hook[field]
				dataIO.save_json(self.hookJSON.format(author.id), hook)
				await self.bot.say(':white_check_mark:  Your **{}** team has been deleted.'.format(field_names[field]))
				return
			else:
				await self.bot.say('No **{}** team available to delete.'.format(field_names[field]))
		else:
			if author.id not in self.mcocProf or self.mcocProf[author.id] == False:
				self.mcocProf[author.id] = {}
				dataIO.save_json(self.profJSON, self.mcocProf)	
			if field not in field_names:
				field_name = field
			else:
				field_name = field_names[field]
			if field in self.mcocProf[author.id]:
				del self.mcocProf[author.id][field]
				dataIO.save_json(self.profJSON, self.mcocProf)
				await self.bot.say(':white_check_mark:  Your **{}** has been deleted.'.format(field_name))
			else: 
				await self.bot.say('No **{}** available to delete.'.format(field_name))
				
	@mcoc_profile.command(no_pm=True, pass_context=True)
	async def display(self, ctx, show_or_hide : str, field: str):
		"""
		Toggle the visibility of a field on your profile."""	
		author = ctx.message.author
		user_id = author.id
		toggles = {'show','hide'}
		toggle = show_or_hide.lower()
		field.lower()
		if field not in valid_fields:
			await self.bot.say('**{}** is not a valid field. Try again with a valid '
							   'field from the following list: \n- {}'.format(field,'\n- '.join(fields_list)))
			return
		if toggle not in toggles:
			await self.bot.say('Display setting must equal "show" or "hide".')
			return	
		field_name = field_names[field]
		if author.id not in self.mcocProf or self.mcocProf[author.id] == False:
			self.mcocProf[author.id] = {}
			dataIO.save_json(self.profJSON, self.mcocProf)	
		if 'hidden_fields' not in self.mcocProf[author.id]:
			self.mcocProf[author.id]['hidden_fields'] = []
		if toggle == 'hide':
			if field not in self.mcocProf[author.id]['hidden_fields']:
				self.mcocProf[author.id]['hidden_fields'].append(field)
				dataIO.save_json(self.profJSON, self.mcocProf)
				await self.bot.say(':white_check_mark:  **{}** is now hidden from your profile.'.format(field_name))
			else:
				await self.bot.say('**{}** was already hidden from your profile.'.format(field_name))
				return					
		else:
			if field not in self.mcocProf[author.id]['hidden_fields']:
				await self.bot.say('**{}** is already visible on your profile.'.format(field_name))
				return	
			else:
				self.mcocProf[author.id]['hidden_fields'].remove(field)
				dataIO.save_json(self.profJSON, self.mcocProf)
				await self.bot.say(':white_check_mark:  **{}** is now visible on your profile.'.format(field_name))
				
	@mcoc_profile.command(no_pm=True, pass_context=True)
	async def gamename(self, ctx, *, gamename : str):
		"""
		Set your In-Game Name."""
		user_id = ctx.message.author.id
		await self.edit_field(user_id, 'gamename', ctx, gamename)
	
	@mcoc_profile.command(no_pm=True, pass_context=True)
	async def timezone(self, ctx, *, location : str):
		"""
		Provide your location to set your timezone."""	
		user_id = ctx.message.author.id		
		timezone = await self.gettimezone(location)
		await self.edit_field(user_id, 'timezone', ctx, timezone)
	
	@mcoc_profile.command(no_pm=True, pass_context=True,aliases=['summonerlevel',])
	async def level(self, ctx, *, summonerlevel : str):
		"""
		Set your Summonor Level (0 - 60)."""		
		user_id = ctx.message.author.id
		await self.edit_field(user_id, 'summonerlevel', ctx, summonerlevel)
		
	@mcoc_profile.command(no_pm=True, pass_context=True,aliases=['rating',])
	async def herorating(self, ctx, *, herorating : str):
		"""
		Set your Total Base Hero Rating."""	
		user_id = ctx.message.author.id
		await self.edit_field(user_id, 'herorating', ctx, herorating)
		
	@mcoc_profile.command(no_pm=True, pass_context=True)
	async def profilechamp(self, ctx, *, champ: ChampConverter):
		"""
		Set your Profile champion."""
		name = champ.hookid
		user_id = ctx.message.author.id
		await self.edit_field(user_id, 'profilechamp', ctx, name)

	@mcoc_profile.command(no_pm=True, pass_context=True)
	async def alliance(self, ctx, *, alliance:str):
		"""
		Set your Alliance Name."""
		user_id = ctx.message.author.id
		await self.edit_field(user_id, 'alliance', ctx, alliance)			
	
	@mcoc_profile.command(no_pm=True, pass_context=True)
	async def defense(self, ctx, *, champs : ChampConverterMult):
		"""
		Set your Alliance War Defense team."""	
		user_id = ctx.message.author.id
		await self.hook_update(user_id,'awd', champs, ctx.message)

	@mcoc_profile.command(no_pm=True, pass_context=True)
	async def offense(self, ctx, *, champs : ChampConverterMult):
		"""
		Set your Alliance War Offense team."""	
		user_id = ctx.message.author.id
		await self.hook_update(user_id,'awo', champs, ctx.message)
		
	@mcoc_profile.command(no_pm=True, pass_context=True)
	async def aq(self, ctx, *, champs : ChampConverterMult):
		"""
		Set your Alliance Quest team."""	
		user_id = ctx.message.author.id
		await self.hook_update(user_id,'aq', champs, ctx.message)


	@mcoc_profile.command(no_pm=True, pass_context=True)
	async def view(self, ctx, *, user: str):
		"""
		View a users profile."""			
		author = ctx.message.author
		if not user:
			user = author
		else:
			user = await MemberFinder(ctx, user).convert()
		user_id = user.id
		
		if user_id not in self.mcocProf or self.mcocProf[user_id] == False:
			self.mcocProf[user_id] = {}
			dataIO.save_json(self.profJSON, self.mcocProf)
		
		profile = self.mcocProf[user_id]
		if 'hidden_fields' not in profile:
			profile['hidden_fields'] = []
		hidden_fields = profile['hidden_fields']
		
		em = discord.Embed(color=user.color)
		
		if "gamename" not in profile or "gamename" in hidden_fields:
			em.add_field(name="**Summoner**", value=user.display_name,inline=False)
		else:
			gamename = profile["gamename"]
			em.add_field(name="**"+field_names["gamename"]+"**", value=gamename,inline=False)
			
		if "alliance" not in profile or "alliance" in hidden_fields:
			display_name = user.display_name
			ally_pattern = re.compile(r'\[.*\]')
			if not ally_pattern.search(display_name):
				pass
			else:
				alliance = ally_pattern.search(display_name)
				em.add_field(name="**"+field_names["alliance"]+"**", value=alliance,inline=False)
		else:
			alliance = profile["alliance"]
			em.add_field(name="**"+field_names["alliance"]+"**", value=alliance,inline=False)
			
		if "summonerlevel" not in profile or "summonerlevel" in hidden_fields:
			pass
		else:
			summonerlevel = profile["summonerlevel"]
			summonerlevel = int(summonerlevel)
			em.add_field(name="**"+field_names["summonerlevel"]+"**", value='{:,}'.format(summonerlevel),inline=False)
			
		if "herorating" not in profile or "herorating" in hidden_fields:
			pass
		else:
			herorating = profile["herorating"]
			herorating = int(herorating)
			em.add_field(name="**"+field_names["herorating"]+"**", value='{:,}'.format(herorating),inline=False)
			
		if "achievements" in hidden_fields:
			pass
		else:
			roles = user.roles
			role_names = set()
			for role in roles:
				role_names.add(role.name.lower())
			achievements = role_names & achievements_set
			if len(achievements) == 0:
				pass
			else:
				em.add_field(name="**"+field_names["achievements"]+"**", value=str(', '.join(achievements)).upper(),inline=False)
	
		if "bg" in hidden_fields:
			pass
		else:
			roles = user.roles
			bg_names = []
			for role in roles:
				if role.name in bg_set:
					bg_names.append(role.name)
			if len(bg_names) == 0:
				pass
			else:
				em.add_field(name="**"+field_names["bg"]+"**", value=bg_names[0].upper(),inline=False)
	
		if "timezone" not in profile or "timezone" in hidden_fields:
			pass
		else:
			timezone = profile["timezone"]
			utcmoment_naive = datetime.utcnow()
			get_time = getLocalTime(utcmoment_naive,timezone)
			localtime = get_time.strftime("%I:%M").lstrip('0') + ' ' + get_time.strftime("%p")
			# CUSTOM CLOCK EMOJI.lower()
			clockemoji = clock_emoji(get_time)		
			em.add_field(name="**Time**", value='Timezone: ' + timezone + '\nLocal Time: ' + localtime + '  ' + clockemoji,inline=False)	
		
		if "profilechamp" not in profile or "profilechamp" in hidden_fields:
			if user.avatar_url:
				em.set_thumbnail(url=user.avatar_url)
		else:
			profilechamp = profile["profilechamp"]
			champ = await ChampConverter(ctx, profilechamp).convert()
			em.set_thumbnail(url=champ.get_avatar())
			
		hook = await self.hook_file(user_id)
		if 	"aq" not in hook or "aq" in hidden_fields:
			pass
		else:
			aq_list = hook["aq"]
			em.add_field(name="**"+field_names["aq"]+"**", value='\n'.join(aq_list))
		if 	"awo" not in hook or "awo" in hidden_fields:
			pass
		else:
			awo_list = hook["awo"]
			em.add_field(name="**"+field_names["awo"]+"**", value='\n'.join(awo_list))
		if 	"awd" not in hook or "awd" in hidden_fields:
			pass
		else:
			awd_list = hook["awd"]
			em.add_field(name="**"+field_names["awd"]+"**", value='\n'.join(awd_list))
		await self.bot.say(embed=em)
		
	@mcoc_profile.command(no_pm=True, pass_context=True)
	async def make(self, ctx):
		"""Create a new profile"""
		message = ctx.message
		author = message.author
		channel = message.channel
		
		self.mcocProf[author.id] = {}
		dataIO.save_json(self.profJSON, self.mcocProf)
		await self.bot.say("Hi **{}**! Let's begin setting up your Summonor profile!\n - You can reply **skip** to"
						   " skip a question or **stop** to exit this session. \n - This session will automatically "
						   "end after *3 minutes* without a response.\n\nNow, start by telling me your **in-game name**.".format(author))

		response = await self.bot.wait_for_message(channel=channel, author=author, timeout=180.0)
		
		if response.content is None:
			await self.bot.say('{0.mention}, your session has timed out.'.format(author))
			return
		if response.content.lower() == 'stop':
			await self.bot.say('You\'ve exited this profile-making session.')
			return
		elif response.content.lower() == 'skip':
			await self.bot.say('Question skipped!')
		else: 
			await self.edit_field('gamename', ctx, response.content)

		await self.bot.say("Now let's set your timezone. Where do you live? (City/State/Country)")
		
		response = await self.bot.wait_for_message(channel=channel, author=author, timeout=180.0)
		if response.content is None:
			await self.bot.say('{0.mention}, your session has timed out.'.format(author))
			return
		if response.content.lower() == 'stop':
			await self.bot.say('You\'ve exited this profile-making session.')
			return
		elif response.content.lower() == 'skip':
			await self.bot.say('Question skipped!')
		else:
			timezone = await self.gettimezone(response.content)
			await self.edit_field('timezone', ctx, timezone)

		await self.bot.say("What is your Summonor Level? (0-60)")	
		response = await self.bot.wait_for_message(channel=channel, author=author, timeout=180.0)
		if response.content is None:
			await self.bot.say('{0.mention}, your session has timed out.'.format(author))
			return
		if response.content.lower() == 'stop':
			await self.bot.say('You\'ve exited this profile-making session.')
			return
		elif response.content.lower() == 'skip':
			await self.bot.say('Question skipped!')
		else: 
			await self.edit_field('summonerlevel', ctx, response.content)		
			
		await self.bot.say("What is your Total Base Here Rating?")	
		response = await self.bot.wait_for_message(channel=channel, author=author, timeout=180.0)
		if response.content is None:
			await self.bot.say('{0.mention}, your session has timed out.'.format(author))
			return
		if response.content.lower() == 'stop':
			await self.bot.say('You\'ve exited this profile-making session.')
			return
		elif response.content.lower() == 'skip':
			await self.bot.say('Question skipped!')
		else: 
			content = response.content
			if content.find(',') != -1:
				content.replace(',','')
			await self.edit_field('herorating', ctx, content)			

		await self.bot.say("Who is your Profile Champion?")	
		response = await self.bot.wait_for_message(channel=channel, author=author, timeout=180.0)
		if response.content is None:
			await self.bot.say('{0.mention}, your session has timed out.'.format(author))
			return
		if response.content.lower() == 'stop':
			await self.bot.say('You\'ve exited this profile-making session.')
			return
		elif response.content.lower() == 'skip':
			await self.bot.say('Question skipped!')
		else: 
			await self.edit_field('profilechamp', ctx, response.content)	
			
		return await self.bot.say("All done!")			

placeholders = {
"aq" : [
	"[empty slot]",
	"[empty slot]",
	"[empty slot]"
],
"awd" : [
	"[empty slot]",
	"[empty slot]",
	"[empty slot]",
	"[empty slot]",
	"[empty slot]"
],
	"awo" : [
		"[empty slot]",
		"[empty slot]",
		"[empty slot]"
	]
}

def check_folder():
	if not os.path.exists("data/mcocProfile"):
		print("Creating data/mcocProfile folder...")
		os.makedirs("data/mcocProfile")
		print("Profiles Folder created!")
		
	if not os.path.exists("data/hook/users"):
		print("Creating data/hook/users folder...")
		os.makedirs("data/hook/users")
		print("Hook Users Folder created!")
		
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