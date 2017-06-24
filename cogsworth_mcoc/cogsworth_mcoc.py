import discord
from discord.ext import commands
import aiohttp
import asyncio
import logging
import requests
import re
from pprint import pprint
import json
import os
from .utils.dataIO import dataIO
from .utils.dataIO import fileIO

class anothercog:
    """This is a cog named Cogsworth."""

    def __init__(self, bot):
        self.bot = bot
        self.syn_data_dir = 'data/hook/synergies/'
        self.syn_file = self.syn_data_dir + 'synergies.json'
        self.hook_en_file = self.syn_data_dir + 'data_en.json'
        #self.effectjson_file = self.syn_data_dir + 'effectids.json'
        self.effectval_file = self.syn_data_dir + 'effectvalues.json'
        self.shell_json = self.syn_data_dir + '{}.json'

    def save_shell_file(self,data,filename):                  #(step two)
        if not os.path.exists(self.shell_json.format(filename)):       #check if the FILE exists
            if not os.path.exists(self.syn_data_dir):   #if not, check if the FOLDER exists
                os.makedirs(self.syn_data_dir)          #if not, MAKE the FOLDER
            dataIO.save_json(self.shell_json.format(filename), data)       #then save  file in that folder

    # def save_effectjson_file(self,data):                  #(step two)
    #     if not os.path.exists(self.effectjson_file):       #check if the FILE exists
    #         if not os.path.exists(self.syn_data_dir):   #if not, check if the FOLDER exists
    #             os.makedirs(self.syn_data_dir)          #if not, MAKE the FOLDER
    #         dataIO.save_json(self.effectjson_file, data)       #then save  file in that folder

    def save_effectval_file(self,data):                  #(step two)
        if not os.path.exists(self.effectval_file):       #check if the FILE exists
            if not os.path.exists(self.syn_data_dir):   #if not, check if the FOLDER exists
                os.makedirs(self.syn_data_dir)          #if not, MAKE the FOLDER
            dataIO.save_json(self.effectval_file, data)       #then save  file in that folder

    def save_hookjson_file(self,data):                  #(step two)
        if not os.path.exists(self.hook_en_file):       #check if the FILE exists
            if not os.path.exists(self.syn_data_dir):   #if not, check if the FOLDER exists
                os.makedirs(self.syn_data_dir)          #if not, MAKE the FOLDER
            dataIO.save_json(self.hook_en_file, data)       #then save  file in that folder

    def create_syn_file(self):                          #(step two)
        if not os.path.exists(self.syn_file):           #check if the FILE exists
            if not os.path.exists(self.syn_data_dir):   #if not, check if the FOLDER exists
                os.makedirs(self.syn_data_dir)          #if not, MAKE the FOLDER
            self.save_syn_data('')                        #then save an empty file in that folder

    def load_syn_data(self):                            #(step one)
        self.create_syn_file()                          #call create_syn_file function to check if folder/file exists (& if not, create them)
        self.save_syn_data('')
        return dataIO.load_json(self.syn_file)          #Load the new or existing file

    def save_syn_data(self, data):                      #(step three)
        dataIO.save_json(self.syn_file, data)           #save the file

    #@commands.command(pass_context=True)
    def geteffectids(self):
        url = 'https://raw.githubusercontent.com/hook/champions/master/src/data/ids/effects.js'
        async with aiohttp.get(url) as response:
            effectids_txt = await response.text()
            effectids = effectids_txt.strip().split('\n')
            effectid_dict = {}
            for line in effectids:
                line = line.strip()
                effectname_res = re.search(r'(?<=const\s)(\w+)',line)
                effectid_res = re.search(r'(?<=\=\s\')(\w+)',line)
                effectname = effectname_res.group(0).lower()
                effectid = effectid_res.group(0).lower()
                effectid_dict.update({effectname:effectid})
            self.save_shell_file(effectid_dict,'effectvalues')
            print('effect json file saved!')

    @commands.command(pass_context=True,hidden=True)
    async def geteffectvalues(self):
        url = 'https://raw.githubusercontent.com/hook/champions/master/src/data/effects.js'
        async with aiohttp.get(url) as response:
            effectval_txt = await response.text()
            find_start = effectval_txt.find('EFFECT_STARS_AMOUNT = {') + len('EFFECT_STARS_AMOUNT = {') #finds first occurance of "...fromId"
            find_end = effectval_txt.find('};') - len('};')
            val_lines = effectval_txt[find_start:find_end].strip().split('\n')
            effectvals_dict = {}
            for line in val_lines:
                line = line.strip()
                effectname_res = re.search(r'(?<=EFFECT\.)(\w+)',line)
                effectval_res = re.search(r'(\d+),\s(\d+),\s(\d+)',line)
                effectname = effectname_res.group(0).lower()
                ef1 = effectval_res.group(1)
                ef2 = effectval_res.group(2)
                ef3 = effectval_res.group(3)
                effectvals = [ef1,ef2,ef3]
                effectvals_dict.update({effectname:effectvals})
            self.save_effectval_file(effectvals_dict)
            print('effect value json file saved!')



    @commands.command(pass_context=True,aliases=['hookjson',])
    async def get_hook_json(self,ctx):
        """This command grabs Hook's english data json and stores it"""
        url = 'https://raw.githubusercontent.com/hook/champions/master/src/data/lang/en.json'
        async with aiohttp.get(url) as response:
            hookjson = await response.json()
            self.save_hookjson_file(hookjson)
            print('hook json file saved!')

    @commands.command(pass_context=True,aliases=['updatesyn','synjson','pull_syn',])
    async def synergy_json(self,ctx):
        """This command translates Hooks JS synergies file into a readable json file"""
        url = 'https://raw.githubusercontent.com/hook/champions/master/src/data/synergies.js'
        async with aiohttp.get(url) as response:
            hook = await response.text()
            self.geteffectids()
            find_start = hook.find('...fromId(') #finds first occurance of "...fromId"
            find_end = hook.find('].map((synergy') #finds first occurance of "].map((synergy"
            hk_slice = hook[find_start:find_end].replace("DRVOODOO","BROTHERVOODOO").split('...fromId') #slice out all syns & split into blocks by "from" champion
            c_all = {} #define output dictionary
            for champblock in hk_slice:
                syn_blk = champblock.split('...fromStars') #separate into rows by "to" champion
                i = 0
                synrows = {} #define row dictionary
                ch_dict = {} #define championblock dictionary
                for champline in syn_blk:
                    pattern_fromchamp = re.compile(r'(?<=CHAMPION\.)(\w+)') #regex matching text immediately after "CHAMPION."
                    pattern_tochamp = re.compile(r'\(\d+,\s\d') #regex matching "(#, #..."
                    if pattern_tochamp.match(champline):  #if the line starts with "(#, #..." aka a 'toChamp' line
                        stars = re.search(r'(\d+),\s(\d+)',champline) #find numbers (star values)
                        effect = re.search(r'(?<=EFFECT\.)(\w+)',champline) #find effect values
                        ch_count = champline.count('CHAMPION') #count # of "CHAMPION" occurances
                        if ch_count > 1: #if there are more than 1 champions listed in this line, give each it's own line
                            cnt = 0
                            while cnt < ch_count:
                                champname = re.findall(r'(?<=CHAMPION\.)\w+',champline)
                                tochamp = [champname[cnt].lower(),effect.group(0).lower(),stars.group(1),stars.group(2)]
                                synrows.update({"{}".format(i) : tochamp})
                                cnt += 1
                                i += 1
                        else:
                            champname = re.search(r'(?<=CHAMPION\.)(\w+)',champline)
                            tochamp = [champname.group(0).lower(),effect.group(0).lower(),stars.group(1),stars.group(2)]
                            synrows.update({"{}".format(i) : tochamp}) #set contains of synergy row
                            i += 1
                    elif pattern_fromchamp.search(champline): #if the line contains "CHAMPION.#####"
                        frmchamp = champline.strip()
                        fchamp = re.search(r'(?<=CHAMPION\.)(\w+)',frmchamp)
                        fromchamp = fchamp.group(0).lower()
                        ch_dict.update({fromchamp : [synrows]}) #set contents of champion block with champ name and syn rows
                c_all.update(ch_dict) #append all champion blocks to final output dictionary
            if find_start > 0:
                try:
                    #str_all = c_all.replace('\'',"\"").replace("drvoodoo","brothervoodoo") #convert to string. and json doesn't like single quotes
                    self.load_syn_data()
                    self.save_syn_data(c_all)
                    await self.bot.say("Synergies.json - Update Success.")
                    await self.bot.send_file(ctx.message.channel,self.syn_file)
                #    text_file = open("data/Synergies.json", "w")
                #    text_file.write(str_all) #overwrites existing content
                #    text_file.close()
                except:
                    raise #idk...
            else:
                await self.bot.say("Something went wrong.")
    # @commands.command(pass_context=True)
    # async def git_text(self):
    #     """test github push"""
    #     await self.bot.say("It works!")
    #
    # @commands.command(pass_context=True)
    # async def champsyn_beta(self,ctx, *, champ: str):
    #     """finds syneries"""
    #     #print(len(champs))
    #     if len(champ) > 0:
    #         with open('data/Synergies.json') as data_file:
    #             synergies = json.load(data_file)
    #     #    pprint(data)
    #         try:
    #             champ = champ.lower().strip().replace(" ","")
    #             if synergies[champ]:
    #                 tochampions = synergies[champ][0]
    #                 #pprint(tochampions)
    #                 i = 0
    #                 out_text = ''
    #                 for tochamp in tochampions:
    #                     idx = str(i)
    #                     c_name = tochampions[idx][0]
    #                     c_syn = tochampions[idx][1]
    #                     out_text += 'Champ: {} - Synergy: {} \n'.format(c_name.title(),c_syn.title())
    #                     i += 1
    #                 await self.bot.say("**Synergies for {}**\n\n{}".format(champ.title(),out_text.replace("_"," ")))
    #             else:
    #                 await self.bot.say("No synergies found")
    #         except:
    #             raise
    #     else:
    #         await self.bot.say("No champion provided.")

#-------------- setup -------------
def check_syn_folders():
    if not os.path.exists("data/hook/synergies"):
        print("Creating data/hook/synergies folder...")
        os.makedirs("data/hook/synergies")
        #transfer_info()
def setup(bot):
    bot.add_cog(anothercog(bot))
