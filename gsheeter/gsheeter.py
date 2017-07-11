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

class gsheet_cog:
	"""Just playing around."""
	def __init__(self, bot):
		self.bot = bot
		self.data_dir = 'data/gsheeter/members/'
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

	def save_shell_file(self,data,filename):                           #(step two)
		if not os.path.exists(self.shell_json.format(filename)):       #check if the FILE exists
			if not os.path.exists(self.data_dir):                  #if not, check if the FOLDER exists
				os.makedirs(self.data_dir)                         #if not, MAKE the FOLDER
			dataIO.save_json(self.shell_json.format(filename), data)   #then save  file in that folder
		dataIO.save_json(self.shell_json.format(filename), data)
		
	def main(self,sheet,range_headers,range_body,groupby_key,file_name):
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
		else:
			output_dict = {}
			for row in body_values:
				dict_zip = dict(zip(header_values[0], row))
				groupby = row[groupby_value]
				output_dict.update({groupby:dict_zip})
			self.save_shell_file(output_dict,file_name)

	if __name__ == '__main__':
		main()

	
	@commands.command(pass_context=True,aliases=['updatemembers',], no_pm=True)
	async def refreshmembers(self, ctx):
		"""Refreshs members json from google sheet"""
		server = ctx.message.server
		sheet = '1kI0Dzsb6idFdJ6qzLIBYh2oIypB1O4Ko4BdRita-Vvg'
		range_headers = 'ASSGR_members!1:1'
		range_body = 'ASSGR_members!A2:ab'
		groupby_key = 'id'
		file_name = server.id
		try:
			self.main(sheet,range_headers,range_body,groupby_key,file_name)
			await self.bot.say("Members - Update Success!")
		except:
			await self.bot.say("Something went wrong.")
			raise
			
	@commands.command(pass_context=True,aliases=['getmember',], no_pm=True)
	async def member(self, ctx, *, user: discord.Member=None):
		"""Get Member Info"""
		author = ctx.message.author
		server = ctx.message.server
		file_name = server.id
		if not user:
			user = author
		user_id = user.id
		if not os.path.exists(self.shell_json.format(filename)):
			await self.bot.say("No members file detected. Reply **[prefix]updatemembers**.")
			return
		member_json = dataIO.load_json(self.shell_json.format(filename))
		try:
			if not member_json[user_id]:
				await self.bot.say("User not found.")
				return
			memberInfo = member_json[user_id]
			em = discord.Embed(color=0xDEADBF)
			em.set_thumbnail(url=user.default_avatar_url)
			em.add_field(name='Member Info For ' + memberInfo.name.upper(), value='Battlegroup: '+memberInfo.bg+'\nTimezone: '+memberInfo.timezone)
			await self.bot.say(embed=em)
		except:
			await self.bot.say("Something went wrong.")
			raise
			
def setup(bot):
	bot.add_cog(gsheet_cog(bot))