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


class gsheet_cog:
	"""Just playing around."""
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
		
	def main(self,sheet,range_headers,range_body,groupby_key,foldername,filename):
		"""Shows basic usage of the Sheets API."""
		credentials = self.get_credentials()
		http = credentials.authorize(httplib2.Http())
		discoveryUrl = ('https://sheets.googleapis.com/$discovery/rest?'
						'version=v4')
		service = discovery.build('sheets', 'v4', http=http,
									discoveryServiceUrl=discoveryUrl)
		headers_get = service.spreadsheets().values().get(
					spreadsheetId=sheet, range=range_headers).execute()
		body_get = service.spreadsheets().values().get(
				spreadsheetId=sheet, range=range_body).execute()
		header_values = headers_get.get('values', [])
		groupby_value = header_values[0].index(groupby_key)
		body_values = body_get.get('values', [])
		output_dict = {}
		if not body_values:
			print('No data found.')
			return
		else:
			output_dict = {}
			for row in body_values:
				dict_zip = dict(zip(header_values[0], row))
				groupby = row[groupby_value]
				output_dict.update({groupby:dict_zip})
			self.save_shell_file(output_dict,foldername,filename)

	if __name__ == '__main__':
		main()

#    @commands.group(name="imgur", no_pm=True, pass_context=True)
#    async def _imgur(self, ctx):
#        """Retrieves pictures from imgur"""
#        if ctx.invoked_subcommand is None:
#            await self.bot.send_cmd_help(ctx)
			
	@commands.command(pass_context=True,aliases=['loadsheet',], no_pm=True)
	async def savesheet(self, ctx, header_row: str, data_range: str, groupRowsBy: str,filename: str,sheet_id: str):
		"""Save a Google Sheet as JSON or refresh an existing JSON. 
		
		File Location: data/gsheeter/[server-id]
		
		Example:
		!savesheet Sheet1!1:1 Sheet1!A2:D FirstName MembersData 1kI0Dzsb6idFdJ6qzLIBYh2oIypB1O4Ko4BdRita-Vvg
		"""
		server = ctx.message.server
		foldername = server.id
		a1_notation_check = re.compile(r'\'?[\w\d]+\'?![\w\d]+\:[\w\d]+')
		if not a1_notation_check.fullmatch(header_row):
			await self.bot.say("Use correct A1 Notation for the Header Row (single row only): Ex. Sheet1!A2:Z2 or 'This Sheet'!1:1")
			return
		if not a1_notation_check.fullmatch(data_range):
			await self.bot.say("Use correct A1 Notation for the Data Range: Ex. Sheet1!A2:D or 'My Sheet'!B2:Z1000")
			return
		try:
			self.main(sheet_id,header_row,data_range,groupRowsBy,foldername,filename)
			await self.bot.say("This file has been saved!")
		except:
			await self.bot.say("Something went wrong.")
			raise
			
	@commands.command(pass_context=True,aliases=['updateinfo',], no_pm=True)
	async def refreshmembers(self, ctx):
		"""Refreshs members json from google sheet"""
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
		foldername = server.id
		try:
			self.main(sheet,range_headers,range_body,groupby_key,foldername,filename)
			await self.bot.say("Success! File has been updated!")
		except:
			await self.bot.say("Something went wrong.")
			raise
			
	@commands.command(pass_context=True,aliases=['getmember',], no_pm=True)
	async def member(self, ctx, *, user: discord.Member=None):
		"""Get Member Info"""
		author = ctx.message.author
		server = ctx.message.server
		foldername = server.id
		if not user:
			user = author
		user_id = user.id
		if not os.path.exists(self.shell_json.format(foldername,'MemberInfo')):
			await self.bot.say("No members file detected. Use command **[prefix]savesheet** to save a Google Sheet as Members file. **File Name must be 'MemberInfo'**")
			return
		member_json = dataIO.load_json(self.shell_json.format(foldername,'MemberInfo'))
		alliance_json = dataIO.load_json(self.shell_json.format(foldername,'AllianceInfo'))
		try:
			if not member_json[user_id]:
				await self.bot.say("User not found.")
				return
			memberInfo = member_json[user_id]
			bg = memberInfo.get('bg','all')
#			colorVal = 0xff9933
			colorVal = alliance_json[bg.lower()].get('color_dec') if alliance_json[bg.lower()]['color_dec'] else 0xff9933

#			if alliance_json:
#				colorVal = alliance_json[bg.lower()].get('color_dec')
			if memberInfo['timezone']:
				get_tz = memberInfo['timezone']
				utcmoment_naive = datetime.utcnow()
				utcmoment = utcmoment_naive.replace(tzinfo=pytz.utc)
				localFormat = "%I:%M%p"
				get_time = utcmoment.astimezone(pytz.timezone(get_tz))
				localtime = get_time.strftime(localFormat)
			else:
				localtime = "not found"
			em = discord.Embed(color=discord.Color(colorVal))
			em.set_thumbnail(url=user.avatar_url)
			em.add_field(name='Member Info For ' + memberInfo.get('name','not found').upper(), value='Battlegroup: '+memberInfo.get('bg','not found')+'\nLocal Time: '+localtime)
			await self.bot.say(embed=em)
		except:
			await self.bot.say("Something went wrong.")
			raise
			
def setup(bot):
	bot.add_cog(gsheet_cog(bot))