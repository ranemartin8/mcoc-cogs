from __future__ import print_function
import httplib2
import os
import json

from apiclient import discovery
from oauth2client import client
from oauth2client import tools
from oauth2client.file import Storage

import discord
from discord.ext import commands
import aiohttp
import asyncio
import logging
import requests
import re
from pprint import pprint
import os
from .utils.dataIO import dataIO
from .utils.dataIO import fileIO
from datetime import tzinfo, timedelta, datetime
import pytz
from colour import Color
import difflib

colors = {
	'red': discord.Color(0xff3333 ), 'orange': discord.Color(0xcc6600),
	'yellow': discord.Color(0xffcc33), 'green': discord.Color(0x33cc33),
	'blue': discord.Color(0x3399ff), 'purple': discord.Color(0x663399),
	'dark_blue': discord.Color(0x333399), 'teal': discord.Color(0x339999),
	'light_green': discord.Color(0x33ff99), 'pink': discord.Color(0xcc3366),
	'salmon': discord.Color(0xcc6666), 'dark_red': discord.Color(0x660000),
	'default': discord.Color(0xcc6600),'while': discord.Color(0xffffff),
	'grey': discord.Color(0x666666)
	}
maps = {
	'map5a':'http://i.imgur.com/hAAQ3Az.jpg',
	'map5b':'http://i.imgur.com/C4q8TaG.jpg',
	'map5c':'http://i.imgur.com/xTCQ6WE.jpg',
	'aw':'https://i.imgur.com/6jkgZXj.png'
	}
c_times = {
		'1260':'1','100':'1','960':'10','1000':'10','1030':'1030','1060':'11','1100':'11',
		'1130':'1130','1160':'12','1200':'12','1230':'1230','130':'130','160':'2','200':'2',
		'230':'230','260':'3','300':'3','330':'330','360':'4','400':'4','430':'430','460':'5',
		'500':'5','530':'530','560':'6','600':'6','630':'630','660':'7','700':'7','730':'730',
		'760':'8','800':'8','830':'830','860':'9','900':'9','930':'930'
		}
#def time_roundup(dt, delta):
#		return dt + (datetime.min - dt) % delta	
	
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
	
class MemberFinder(commands.Converter):
	async def convert(self):
		message = self.ctx.message
		user_string = self.argument
		server = self.ctx.message.server
		user = None
		find_method = None
		result_names = []
		matches = []
		if message.mentions:
			user = message.mentions[0]
			find_method = 'User found by mention.'
		elif server.get_member_named(str(user_string)):
			user = server.get_member_named(str(user_string))
			find_method = 'User found by "get_member_named"'
		else:
			mem_dict = {}
			for member in server.members:
				mem_dict.update({member.display_name:member.id})
			results = []
			for key,value in mem_dict.items():
				checkfor_str = key.find(user_string)
				if checkfor_str != -1:
					results.append(str(value))
			if results:
				#TOO MANY: if there are 5 or more possible results
				if len(results) > 4: 
					results_count = len(results) - 4
					for mem_id in results:
						ser_mem = server.get_member(mem_id)
						result_names.append(ser_mem.display_name)
					firstfour = ', '.join(result_names[0:4])
					user = 'user_toomany'
					await self.ctx.bot.say("Too many possible matches found: ```{} and {} others.```"
										   "\nPlease be more specific and try again.".format(firstfour,results_count))
				#Less than 4 results
				else:
					firstresult = results[0]
					user = server.get_member(firstresult)
					find_method = 'User found by partial string matching'
					if len(results) > 1: 
						for mem_id in results:
							ser_mem = server.get_member(mem_id)
							result_names.append(ser_mem.display_name)
						await self.ctx.bot.say("A few possible matches were found: ```{}```\n\n"
											   "So I just went with first match: **{}**"
											   " ".format(', '.join(result_names),user.display_name))
			else:
				matches = difflib.get_close_matches(user_string,mem_dict.keys(), n=3, cutoff=0.5)
				if matches:
					bestmatch = matches[0]
					match_id = mem_dict[bestmatch]
					user = server.get_member(match_id)
					find_method = 'User found by fuzzy matching'
					if len(matches) > 1:
						await self.ctx.bot.say("A few fuzzy matches were found: ```{}```\n\n"
											   "So I just went with closest match:"
											   " **{}**".format(', '.join(matches),user.display_name))
				else:
					user = 'user_error'
		if find_method: print('Search Method: '+find_method)
		if len(result_names) > 0: print('Result(s): '+', '.join(result_names))
		if len(matches) > 0: print('Match(es): '+', '.join(matches))
		return user
	
class gsheet_cog:
	"""[in progress]. This cog contains commands that interact with Google Sheets."""
	def __init__(self, bot):
		self.bot = bot
		self.data_dir = 'data/gsheeter/{}/'
		self.shell_json = self.data_dir + '{}.json'
	try:
		import argparse
		flags = argparse.ArgumentParser(parents=[tools.argparser]).parse_args()
	except ImportError:
		flags = None
	# If modifying these scopes, delete your previously saved credentialsat ~/.credentials/sheets.googleapis.com-python-quickstart.json
	SCOPES = 'https://www.googleapis.com/auth/spreadsheets'
	CLIENT_SECRET_FILE = 'client_secret.json'
	APPLICATION_NAME = 'Google Sheets API Python Quickstart'

	def get_credentials(self):
		"""https://developers.google.com/sheets/api/quickstart/python
		"""
		home_dir = os.path.expanduser('~')
		credential_dir = os.path.join(home_dir, '.credentials')
		if not os.path.exists(credential_dir):
			os.makedirs(credential_dir)
		credential_path = os.path.join(credential_dir,
									'sheets.googleapis.com-python-quickstart1.json')
		store = Storage(credential_path)
		credentials = store.get()
		if not credentials or credentials.invalid:
			flow = client.flow_from_clientsecrets(CLIENT_SECRET_FILE, SCOPES)
			flow.user_agent = APPLICATION_NAME
			if flags:
				credentials = tools.run_flow(flow, store, flags)
			else: # Needed only for compatibility with Python 2.6
				credentials = tools.run(flow, store)
			print('Storing credentials to ' + credential_path)
		return credentials

	def save_shell_file(self,data,foldername,filename):                           #(step two)
		if not os.path.exists(self.shell_json.format(foldername,filename)):       				#check if the FILE exists
			if not os.path.exists(self.data_dir.format(foldername)):                  #if not, check if the FOLDER exists
				os.makedirs(self.data_dir.format(foldername))                         #if not, MAKE the FOLDER
			dataIO.save_json(self.shell_json.format(foldername,filename), data)   #then save  file in that folder
		dataIO.save_json(self.shell_json.format(foldername,filename), data)
		
	async def main(self,sheet,range_headers,range_body,foldername,filename,groupby_key):
		"""Shows basic usage of the Sheets API."""
		credentials = self.get_credentials()
		http = credentials.authorize(httplib2.Http())
		discoveryUrl = ('https://sheets.googleapis.com/$discovery/rest?version=v4')
		service = discovery.build('sheets', 'v4', http=http, discoveryServiceUrl=discoveryUrl)
		headers_get = service.spreadsheets().values().get(spreadsheetId=sheet, range=range_headers).execute()
		body_get = service.spreadsheets().values().get(spreadsheetId=sheet, range=range_body).execute()
		
		header_values = headers_get.get('values', [])
		body_values = body_get.get('values', [])
		output_dict = {}
		warn = ''
		if not body_values:
			print('No data found.')
			return
		else:
			output_dict = {}
			if not groupby_key: 
				groupby_value = 0
				warn = ":warning:  No <GROUP_BY> value provided in command string. By default, JSON rows grouped by 1st Column: **{}**"
			else:
				try:
					groupby_value = header_values[0].index(groupby_key)
				except ValueError:
					groupby_value = 0
					warn = ":warning:  <GROUP_BY> value not found in <HEADER_ROW> range. By default, JSON rows grouped by 1st Column: **{}**"
					
			grouped_by = header_values[0][groupby_value]
			for row in body_values:
				dict_zip = dict(zip(header_values[0], row))
				groupby = row[groupby_value]
				output_dict.update({groupby:dict_zip})				

			self.save_shell_file(output_dict,foldername,filename)
			if warn: await self.bot.say(warn.format(grouped_by.upper()))
				
	if __name__ == '__main__':
		main()
		
	@commands.command(pass_context=True,aliases=['loadsheet',], no_pm=True)
	async def savesheet(self, ctx, header_row: str, data_range: str,filename: str,sheet_id: str, groupRowsBy: str=None):
		"""Save a Google Sheet as a JSON file.
		Requires a PUBLISHED Google Sheet with Link Sharing turned ON and set to "Anybody with link can edit". 
		
		
		ARGS: *Required
		---------------
		<HEADER_ROW>*
		 - Set as JSON keys
		 - EX: Sheet1!1:1
		<DATA_RANGE>*
		 - Set as JSON values
		 - EX: Sheet1!A2:D
		<FILENAME>*
		 - Ex: MyJSONFile
		<SHEETID>*
		 - Pull from spreadsheet URL
		 - https://docs.google.com/spreadsheets/d/[SHEETID]/pubhtml
		 - EX: 1kI0Dzsb6idFdJ6qzLIBYh2oIypB1O4Ko4BdRita-Vvg
		<GROUP_BY> 
		 - Optional (Default=1st Column)
		 - Header Value of Column to group rows by.
		 - Column must contain UNIQUE VALUES. 
		 - EX: UserID

		EX:
		 >> [p]savesheet Sheet1!1:1 Sheet1!A2:D MembersData 1kI0Dzsb6idFdJ6qzLIBYh2oIypB1O4Ko4BdRita-Vvg UserID
		
		File Location when Saved: /data/gsheeter/[user-id]
		
		"""
		search_msg = await self.bot.say('Saving...')
		server = ctx.message.server
		foldername = ctx.message.author.id
		a1_notation_check = re.compile(r'\'?[\w\d]+\'?![\w\d]+\:[\w\d]+')
		if not a1_notation_check.fullmatch(header_row):
			await self.bot.say("Use correct A1 Notation for the Header Row"
							   "(single row only): Ex. Sheet1!A2:Z2 or 'This Sheet'!1:1")
			return
		if not a1_notation_check.fullmatch(data_range):
			await self.bot.say("Use correct A1 Notation for the Data Range:"
							   " Ex. Sheet1!A2:D or 'My Sheet'!B2:Z1000")
			return
		try:
			await self.main(sheet_id,header_row,data_range,foldername,filename,groupRowsBy)
			em = self.quickembed("Success!","This file has been saved.")
			await self.bot.say(embed=em)
			await self.bot.delete_message(search_msg)
		except:
			await self.bot.say("Something went wrong.")
			await self.bot.delete_message(search_msg)
			raise
			
			
#CREATE MEMBER OBJECT  

	async def memberObject(self,message,user_id,name): #memberObj = memberObject(ctx,user_id)
		"""
		Errors: memberObject['err_type'] -- no_file, no_user, unknown, success
		"""
		
		server = message.server
		user = server.get_member(user_id)
		foldername = message.author.id
		
		set_color = user.color
		if set_color == discord.Color.default(): set_color = colors['default']
			
		memberObject = {'fileExists':'false','dataExists':'false','obj':{'color':set_color},
						'err_type':'unknown','err_msg':'Something went wrong. Please try again.'} #EMPTY SHELL
		
	#CHECK FOR FILE! Update 'fileexists' to 'true' if found
		if os.path.exists(self.shell_json.format(foldername,'MemberInfo')):
			memberObject = {**memberObject, **{'fileExists':'true'}}

	#NO FILE - ERROR! Return memberObject 
		if memberObject['fileExists'] == 'false':
			err_msg = "No members file detected."
			memberObject = {**memberObject, **{'err_type':'no_file','err_msg':err_msg}}
			return memberObject
	#FILE FOUND!
		else:
			member_json = dataIO.load_json(self.shell_json.format(foldername,'MemberInfo'))
			try:
				memberjson = member_json[user_id]
				dataExists = 'true'
			except KeyError:
				dataExists = 'false'
			memberObject = {**memberObject, **{'dataExists':dataExists}}
			
	#NO DATA - ERROR! Return memberObject
			if memberObject['dataExists'] == 'false':
				err_msg = "User info for **{}** not found in spreadsheet data.".format(name)
				memberObject = {**memberObject, **{'err_type':'no_user','err_msg':err_msg}}
				return memberObject
	#DATA FOUND!
			else:
				memberInfo = {}
				memberInfo = {
					'localtime':'unknown', 'clockemoji':':alarm_clock:', 'map5a_img': maps['map5a'],
					'map5b_img': maps['map5b'], 'map5c_img': maps['map5c'], 'aw_img': maps['aw'], 'localtime_raw':'unknown',
					'a_team':'', 'b_team':'', 'defense':'', 'paths':'','bg_settings':''
					}
				memberInfo.update(memberjson)
				memberInfo['name'] = memberInfo.get('name',user.display_name) #replace empty name entries with username
				
		# BUILD ROSTER ARRAYS
				defense = [memberInfo.get('awd_1'), memberInfo.get('awd_2'), memberInfo.get('awd_3'),
						   memberInfo.get('awd_4'), memberInfo.get('awd_5')]
				a_team = [memberInfo.get('a_team_1'),memberInfo.get('a_team_2'),memberInfo.get('a_team_3')]
				b_team = [memberInfo.get('b_team_1'),memberInfo.get('b_team_2'),memberInfo.get('b_team_3')]
				memberInfo = {**memberInfo, **{'defense':defense,'a_team':a_team,'b_team':b_team}}
				
		# BUILD PATH STRING
				path_list = []
				if memberInfo['map5a']: path_list.append('Map 5a:  '+memberInfo['map5a'])
				if memberInfo['map5b']: path_list.append('Map 5b:  '+memberInfo['map5b'])
				if memberInfo['map5c']: path_list.append('Map 5c:  '+memberInfo['map5c'])
				if memberInfo['aw']: path_list.append('Alliance War:  '+memberInfo['aw'])
				if len(path_list) == 0:
					path_str = 'No paths found'
				else: 
					path_str = '\n'.join(path_list)
			# >> UPDATE memberInfo	
				memberInfo = {**memberInfo, **{'paths':path_str}}
				
		# SET TIMEZONE & CLOCK EMOJI
				if memberInfo['timezone']:
					get_tz = memberInfo['timezone']
					utcmoment_naive = datetime.utcnow()
					get_time = getLocalTime(utcmoment_naive,get_tz)
					localtime = get_time.strftime("%I:%M").lstrip('0') + ' ' + get_time.strftime("%p").lower()
					clockemoji = clock_emoji(get_time)			# CUSTOM CLOCK EMOJI
			# >> UPDATE memberInfo	
					memberInfo = {**memberInfo, **{'clockemoji':clockemoji,'localtime':localtime}}
				
		# GET ALLIANCE JSON	 (bg colors and map images)
				bg_defaults = {
					'colorVal':'default','color_py':'default','color_dec':0xcc6600,'color_hex':'#cc6600',
					'map5a':maps['map5a'],'map5b':maps['map5b'],'map5c':maps['map5c'],'aw':maps['aw']
					}
#				bg_dict = {'color_cy':'default'}
				if not dataIO.is_valid_json(self.shell_json.format(foldername,'AllianceInfo')): 		#No file
					bg_dict = bg_defaults
				else:
					alliance_json = dataIO.load_json(self.shell_json.format(foldername,'AllianceInfo'))
					if not alliance_json: 																#No data in file
						bg_dict = bg_defaults
					else:
						try:
							bg_json = alliance_json[memberInfo.get('bg','all').lower()]				#GET BG DICT()
							bg_dict = {**bg_defaults,**bg_json} #merge
							try:									#check if valid color
								colorCheck = colors[bg_dict['color_py']] 
							except KeyError:
								bg_dict['color_py'] = 'default'
						except KeyError:
							bg_dict = bg_defaults
													
			# >> UPDATE memberInfo	
				memberInfo = {**memberInfo, **{'bg_settings':bg_dict}}
				memberObject['obj'] = memberInfo
				memberObject['err_type'] = 'success'
				memberObject['err_msg'] = 'Member Object success'
		print(memberObject)
		return memberObject
				

			
	@commands.command(pass_context=True,aliases=['updateinfo',], no_pm=True)
	async def refreshmembers(self, ctx):
		"""Refreshs members json from Google Sheet"""
		server = ctx.message.server
		command = ctx.message.content.split(" ")[0]
		sheet = '1kI0Dzsb6idFdJ6qzLIBYh2oIypB1O4Ko4BdRita-Vvg'
		range_headers = 'ASSGR_members!1:1'
		range_body = 'ASSGR_members!A2:ab'
		groupby_key = 'id'
		filename = 'MemberInfo'
		if command == '-updateinfo':
			range_headers = 'ASSGR_info!1:1'
			range_body = 'ASSGR_info!A2:ab'
			groupby_key = 'group'
			filename = 'AllianceInfo'
		foldername = ctx.message.author.id
		try:
			self.main(sheet,range_headers,range_body,foldername,filename,groupby_key)
			await self.bot.say("Success! File has been updated!")
		except:
			await self.bot.say("Something went wrong.")
			raise
			
	@commands.command(pass_context=True,aliases=['getmember',], no_pm=True)
	async def member(self, ctx, *, user_string: str=None):
		"""Get Member Info"""
		search_msg = await self.bot.say('Searching...')
		type = await self.bot.type()
		author = ctx.message.author
		server = ctx.message.server
		if not user_string:
			user = author
		else:
			user = await MemberFinder(ctx, user_string).convert()
		if user == 'user_toomany':
			await self.bot.delete_message(search_msg)
			return
		if user == 'user_error':
			await self.bot.delete_message(search_msg)
			await self.bot.say("No users found matching: `{}`. Please try again.".format(user_string))
			return
		user_id = user.id
		avatar = user.avatar_url
		if not avatar: avatar = user.default_avatar_url 
			
		try:
			memberObj = await self.memberObject(ctx.message,user_id,user.display_name)
			getErr = memberObj['err_type']
			getMsg = memberObj['err_msg']
			memInfo = memberObj['obj']
			memInfo_status = 'success'
		except KeyError:
			getErr = 'other'
			getMsg = 'Error unknown.'
			memInfo_status = 'failure'
			
		if getErr != 'success':
			memInfo_status = 'failure'	
			if getErr == 'no_file' or getErr == 'no_user':
				showError = 'true'
				getMsg = memberObj['err_msg']
				print(getMsg)
			else:
				showError = 'false'
				print(getMsg)
			
	#ALL MEMBERS
		joined_at = user.joined_at
		since_joined = (ctx.message.timestamp - joined_at).days
		user_joined = joined_at.strftime("%b %e %Y")
		joined_on = "Joined: **{}**\n({} days ago)".format(user_joined, since_joined)
		status = "Current Status: **{}**".format(user.status)
		roles = [x.name for x in user.roles if x.name != "@everyone"]
		if roles:
			roles = sorted(roles, key=[x.name for x in server.role_hierarchy if x.name != "@everyone"].index)
			roles = ", ".join(roles)
		else:
			roles = "None"
		try:
			try_color = memInfo['color_cy']
			if not try_color or try_color == 'default' or not colors[try_color]:
				final_color = user.color
			else:
				final_color = colors[try_color]
		except KeyError:
			final_color = user.color
			
		em = discord.Embed(color=final_color)
		em.set_thumbnail(url=avatar)

		if memInfo_status == 'failure' or not memInfo:
			em.add_field(name='**'+user.display_name+'**',value='\n'+status+'\n'+joined_on+'\n\n',inline=False)	
			em.add_field(name='**Roles**',value=roles,inline=False)	
			if showError == 'true':
				em.add_field(name='**User Info**',value=getMsg)
		else:
			em.add_field(name='**'+memInfo['name']+'**',value='\n'+status+'\n'+joined_on+'\n\n'
						 'Battlegroup: **'+memInfo['bg']+'**\n'
						 'Local Time: **'+memInfo['localtime']+'**  '+memInfo['clockemoji'],inline=False)
			a_team = '\n'.join(filter(None, memInfo['a_team']))
			b_team = '\n'.join(filter(None, memInfo['b_team']))
			defense = '\n'.join(filter(None, memInfo['defense']))
			if a_team:
				em.add_field(name='**A-Team**',value=a_team)
			if b_team:
				em.add_field(name='**B-Team**',value=b_team)
			if defense:
				em.add_field(name='**AW Defense**',value=defense)
			if memInfo['paths']:
				em.add_field(name='**Paths**',value=memInfo['paths'],inline=False)
#		print(em.to_dict())
		try:
			await self.bot.say(embed=em)
			await self.bot.delete_message(search_msg)
		except:
			await self.bot.say("Something went wrong.")
			raise
	
	@commands.command(pass_context=True,aliases=['localtime',], no_pm=True)
	async def time(self, ctx, *, user: discord.Member=None):
		"""Get the local time of an Alliance Member.
		This command requires a Google Sheet containing Alliance member info. Set up command coming soon.
		* = Required
		Columns Name: | id* (discord.user.id) | bg | timezone |
		"""
		author = ctx.message.author
		server = ctx.message.server
		foldername = ctx.message.author
		if not user:
			user = author
		user_id = user.id
		if not os.path.exists(self.shell_json.format(foldername,'MemberInfo')):
			await self.bot.say("No members file detected. Use command **[prefix]savesheet**"
							   " to save a Google Sheet as Members file. **File Name must be 'MemberInfo'**")
			return
		member_json = dataIO.load_json(self.shell_json.format(foldername,'MemberInfo'))
		alliance_json = dataIO.load_json(self.shell_json.format(foldername,'AllianceInfo'))
		try:
			if not member_json[user_id]:
				await self.bot.say("User info not found in spreadsheet data.")
				return
			memberInfo = member_json[user_id]
			bg = memberInfo.get('bg','all')
			colorVal = colors[alliance_json[bg.lower()].get('color_py','default')]
			clockemoji = ':alarm_clock:'
			if memberInfo['timezone']:
				get_tz = memberInfo['timezone']
				utcmoment_naive = datetime.utcnow()
				get_time = getLocalTime(utcmoment_naive,get_tz)
				localtime = get_time.strftime("%I:%M").lstrip('0') + ' ' + get_time.strftime("%P")
				# CUSTOM CLOCK EMOJI.lower()
				clockemoji = clock_emoji(get_time)
			else:
				localtime = "not found"
			em = discord.Embed(color=colorVal)
			em.set_thumbnail(url=user.avatar_url)
			em.add_field(name=clockemoji + '  ' + memberInfo.get('name','not found'),
						 value='Battlegroup: **'+memberInfo.get('bg','not found')+'**\nLocal Time: **'+localtime+'**')
			
			await self.bot.say(embed=em)
		except:
			await self.bot.say("Something went wrong.")
			raise
		
		def quickembed(self,title,desc):
			if not title:
				title = "{} says:".format(self.bot.user.display_name())
			if not desc:
				desc = "Hmmm, something is missing here..."
			em = discord.Embed(color=colors['default'])
			em.add_field(name=title,value=desc)
			return em

			
def setup(bot):
	bot.add_cog(gsheet_cog(bot))
	
