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
	try:
		import argparse
		flags = argparse.ArgumentParser(parents=[tools.argparser]).parse_args()
	except ImportError:
		flags = None
	# If modifying these scopes, delete your previously saved credentialsat ~/.credentials/sheets.googleapis.com-python-quickstart.json
	SCOPES = 'https://www.googleapis.com/auth/spreadsheets'
	CLIENT_SECRET_FILE = 'client_secret.json'
	APPLICATION_NAME = 'Google Sheets API Python Quickstart'
	def get_credentials():
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

    def __init__(self, bot):
        self.bot = bot
        self.syn_data_dir = 'data/gsheeter/members/'
        self.shell_json = self.syn_data_dir + '{}.json'

    def save_shell_file(self,data,filename):                           #(step two)
        if not os.path.exists(self.shell_json.format(filename)):       #check if the FILE exists
            if not os.path.exists(self.syn_data_dir):                  #if not, check if the FOLDER exists
                os.makedirs(self.syn_data_dir)                         #if not, MAKE the FOLDER
            dataIO.save_json(self.shell_json.format(filename), data)   #then save  file in that folder
			
	def main(self,sheet,range_headers,range_body,groupby_key,file_name):
		"""Shows basic usage of the Sheets API."""
		credentials = get_credentials()
		http = credentials.authorize(httplib2.Http())
		discoveryUrl = ('https://sheets.googleapis.com/$discovery/rest?'
						'version=v4')
		service = discovery.build('sheets', 'v4', http=http,
									discoveryServiceUrl=discoveryUrl)
	#		spreadsheetId = '1kI0Dzsb6idFdJ6qzLIBYh2oIypB1O4Ko4BdRita-Vvg'
	#		rangeHeaders = 'ASSGR_members!1:1'
	#		rangeBody = 'ASSGR_members!A2:ab'
	#		groupby_key = 'id'
		headers_get = service.spreadsheets().values().get(
					spreadsheetId=spreadsheetId, range=range_headers).execute()
		body_get = service.spreadsheets().values().get(
				spreadsheetId=spreadsheetId, range=range_body).execute()
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
			self.save_shell_file(json.dumps(output_dict),file_name)
#			print(json.dumps(output_dict))
			
	if __name__ == '__main__':
		main()

	
	@commands.command(pass_context=True,aliases=['member',])
	async def members(self, ctx, *, user: discord.Member=None):
        """Gets member info"""
		author = ctx.message.author
		server = ctx.message.server
		if not user:
			user = author
		sheet = '1kI0Dzsb6idFdJ6qzLIBYh2oIypB1O4Ko4BdRita-Vvg'
		range_headers = 'ASSGR_members!1:1'
		range_body = 'ASSGR_members!A2:ab'
		groupby_key = 'id'
		file_name = server.id
		self.main(sheet,range_headers,range_body,groupby_key,file_name)
		return print('done!')
		
def setup(bot):
    bot.add_cog(gsheet_cog(bot))