import discord
import aiohttp
import json
import bs4
from bs4 import BeautifulSoup
from __main__ import send_cmd_help
from .utils import chat_formatting as chat
from discord.ext import commands

IMAGE_SEARCH = 'http://www.dnd.beyond.com/{}?filter-search={}'

# numbs = {
#     "rewind" : "⏪",
#     "next": "➡",
#     "back": "⬅",
#     "choose": "⏺",
#     "fast_forward": "⏩",
#     "exit": "❌",
# }

# schema=(
#         'spells':(
#             'name',
#             'level',
#             'casting_time',
#             'range',
#             'components',
#             'duration',
#             'school',
#             'desc',
#             'higher_level',
#             'material',
#             'ritual',
#             'concentration',
#             'classes',
#             'subclasses',
#             'phb',),
#     'equipment':(
#             'name',
#             'cost',
#             'damage',
#             'weight',
#             'properties',),
#             'desc',
#             'type',
#             'subtype',
#             'weapon_range'
#             'weapon_category',
#     'monsters':(
#         'name',
#         'size',
#         'type',
#         'subtype',
#         'allignment',
#         'strength',
#         'dexterity',
#         'constitution',
#         'intelligence',
#         'wisdom',
#         'charisma',
#         'challenge_rating',
#         'armor_class',
#         'hit_points',
#         'hit_dice',
#         'speed',
#         'dexterity_save',
#         'constitution_save',
#         'wisdom_save',
#         'charisma_save',
#         'perception',
#         'stealth',
#         'damage_vulnerabilities',
#         'damage_resistances',
#         'damage_immunities',
#         'condition_immunities',
#         'senses',
#         'languages',
#         'special_abilities',
#         'actions',
#         'legendary_actions',
#         ),
#     'classes':(),
#     'features':('level','class'),
#     'races':(),
#     )

    # 'subraces':discord.Color.discord.Color.(0xf29214),
    # 'traits':discord.Color.(0xf29214),
    # 'ability-scores': discord.Color.(0xf29214),
    # 'skills' : discord.Color.(0xf29214),
    # 'proficiencies' : discord.Color.(0xf29214),
    # 'languages': discord.Color.(0xf29214),
        # 'starting-equipment':discord.Color.blue(),
    # 'spellcasting':discord.Color.purple(),
    # 'subclasses':discord.Color.(0xf29214),
        # 'levels':discord.Color.(0xf29214),
        
COLORS = {
    'spells' : discord.Color.purple(),
    'equipment': discord.Color.blue(),
    'monsters' : discord.Color.red(),
    'classes' : discord.Color.orange(),
    'features': discord.Color.orange(),
    'races': discord.Color.orange()
}

BASEURL = 'http://dnd5eapi.co/api/'
SELECTION = 'Enter selection for more {} information.'

class DND:
    '''D&D Lookup Stuff'''

    def __init__(self, bot):
        self.bot = bot

    @commands.group(pass_context=True)
    async def dnd(self, ctx):
        if ctx.invoked_subcommand is None:
            await send_cmd_help(ctx)
            return

    @dnd.command(name='spells', pass_context=True)
    async def lookup_spells(self, ctx, *, search=None):
        '''Lookup Spells'''
        CATEGORY = 'spells'
        await self._process_category(ctx, CATEGORY, search)

    @dnd.command(name='features', pass_context=True)
    async def lookup_features(self, ctx, *, search=None):
        '''Lookup Features'''
        CATEGORY = 'features'
        await self._process_category(ctx, CATEGORY, search)

    @dnd.command(name='classes', pass_context=True)
    async def lookup_classes(self, ctx, *, search=None):
        '''Lookup classes'''
        CATEGORY = 'classes'
        await self._process_category(ctx, CATEGORY, search)

    @dnd.command(name='monsters', pass_context=True)
    async def lookup_monsters(self, ctx, *, search=None):
        '''Lookup Monsters'''
        CATEGORY = 'monsters'
        await self._process_category(ctx, CATEGORY, search)

    @dnd.command(name='equipment', pass_context=True)
    async def lookup_equipment(self, ctx, *, search=None):
        '''Lookup equipment'''
        CATEGORY = 'equipment'
        await self._process_category(ctx, CATEGORY, search)

    async def _process_category(self, ctx, CATEGORY, search):
        if not search:
            url = '{}{}'.format(BASEURL, CATEGORY)
            print(url)
            menu_pages = await self._present_list(url, CATEGORY)
            # await self.bot.say('Press ⏺ to select:')
            await self.pages_menu(ctx, embed_list=menu_pages, category=CATEGORY, message=None, page=0, timeout=30)
        elif search.isnumeric():
            url = '{}{}/{}'.format(BASEURL,CATEGORY.lower(),search)
            await self.bot.say('{} search: <{}>'.format(CATEGORY, url))
            await self._process_item(ctx,url,CATEGORY)
            # except:
        else:
#            if ' ' in search:
#                search = search.replace(' ', '+')
            search = search.replace(' ','+')
            url = '{}{}/?name={}'.format(BASEURL, CATEGORY, search)
            json_file = await self._get_file(url)
            await self.bot.say('{} search: <{}>'.format(CATEGORY, json_file['results'][0]['url']))
            await self._process_item(ctx,url,CATEGORY)

    async def pages_menu(self, ctx, embed_list, category, message: discord.Message=None, page=0, timeout: int=30):
        """menu control logic for this taken from
           https://github.com/Lunar-Dust/Dusty-Cogs/blob/master/menu/menu.py"""
        print('list len = {}'.format(len(embed_list)))
        em = embed_list[page]
        if not message:
            message = await self.bot.say(embed=em)
            await self.bot.add_reaction(message, "⏪")
            await self.bot.add_reaction(message, "⬅")
            await self.bot.add_reaction(message,"⏺")
            await self.bot.add_reaction(message, "❌")
            await self.bot.add_reaction(message, "➡")
            await self.bot.add_reaction(message, "⏩")
        else:
            message = await self.bot.edit_message(message, embed=em)
        react = await self.bot.wait_for_reaction(message=message, user=ctx.message.author, timeout=timeout,emoji=["➡", "⬅", "❌", "⏪", "⏩","⏺"])
        if react is None:
            try:
                try:
                    await self.bot.clear_reactions(message)
                except:
                    await self.bot.remove_reaction(message,"⏪", self.bot.user) #rewind
                    await self.bot.remove_reaction(message, "⬅", self.bot.user) #previous_page
                    await self.bot.remove_reaction(message, "❌", self.bot.user) # Cancel
                    await self.bot.remove_reaction(message,"⏺",self.bot.user) #choose
                    await self.bot.remove_reaction(message, "➡", self.bot.user) #next_page
                    await self.bot.remove_reaction(message,"⏩", self.bot.user) # fast_forward
            except:
                pass
            return None
        else:
            react = react.reaction.emoji
            if react == "➡": #next_page
                next_page = (page + 1) % len(embed_list)
                return await self.pages_menu(ctx, embed_list, message=message, page=next_page, timeout=timeout)
            elif react == "⬅": #previous_page
                next_page = (page - 1) % len(cog_list)
                return await self.pages_menu(ctx, cog_list, message=message, page=next_page, timeout=timeout)
            elif react == "⏪": #rewind
                next_page = (page - 5) % len(cog_list)
                return await self.pages_menu(ctx, cog_list, message=message, page=next_page, timeout=timeout)
            elif react == "⏩": # fast_forward
                next_page = (page + 5) % len(cog_list)
                return await self.pages_menu(ctx, cog_list, message=message, page=next_page, timeout=timeout)
            elif react == "⏺": #choose
                await self.bot.say(SELECTION.format(category+' '))
                answer = await self.bot.wait_for_message(timeout=10, author=ctx.message.author)
                if answer is None:
                    await self.bot.say('Request timed out.')
                else:
                    answer = answer.content
                    answer = answer.lower().strip()
                    answer = int(answer)
                    await self.bot.say('Processing choice : {}'.format(answer))
                    url = '{}{}/{}'.format(BASEURL,category,answer)
                    await self._process_item(ctx, url, category)
            else:
                try:
                    return await self.bot.delete_message(message)
                except:
                    pass

    async def _process_item(self, ctx, url, category):
        json_file = await self._get_file(url)
#        keys = json_file.keys()
#        messages = []
        if 'count' in json_file: # Present list
            menu_pages = await self._present_list(url, category)
            await self.pages_menu(ctx, menu_pages, category, message=None, page=0, timeout=30)
        elif category in COLORS: #process endpoint
            try:
                name = json_file['name']
            except KeyError:
                name = category
                print('KeyError: json_file[\'name\']. Category used instead')
#            embeds = []
            try:
                em = discord.Embed(color=COLORS[category],title=name)
                img_available = ['monsters', 'equipment']
                if category in img_available:
                    if category == 'equipment':
                        gettype = json_file['equipment_category']
                    else:
                        gettype = json_file['type']
#                image = await self.image_search(category,name.lower(),gettype)
#                em.set_image(url=image)
                await self.bot.say(embed=em)
            except:
                await self.bot.say('Something went wrong in _process_item')
                raise
#            messages.append(said)
        else:
            print('_process_item error')



    async def _present_list(self, url, category):
        print(url)
        json_file = await self._get_file(url)
        results = json_file['results']
        package = []
#        for i in range(1,json_file['count']):
#            package.append('{} {}'.format(i, json_file['results'][i-1]['name']))
#            c = i+1
        i = 1
        for row in results:
            package.append('{} {}'.format(i, row['name']))
            i += 1
        pages = chat.pagify('\n'.join(package), delims=['\n'], escape=True, shorten_by=8, page_length=350)
        menu_pages = []
        for page in pages:
            em=discord.Embed(color=COLORS[category], title=category, description=chat.box(page))
            em.add_field(name='Press ⏺ to select',value='-------------')
            em.set_footer(text='From [dnd5eapi.co](http://www.dnd5eapi.co)',icon_url='http://www.dnd5eapi.co/public/favicon.ico')
            menu_pages.append(em)
        return menu_pages


    async def _get_file(self,url):
        async with aiohttp.get(url) as response:
            print('_get_file('+url+')')
            json_file = await response.json()
            if json_file is not None:
                return json_file
            else:
                await self.bot.say('json_file returned empty')
                return
                
#async def _get_file(url):
#    async with aiohttp.ClientSession() as session:
#        async with session.get(url) as response:
#            print('_get_file('+url+')')
#            json_file = await response.json()
#            if json_file is not None:
#                return json_file

    async def image_search(self,category,name,gettype):
        plus_name = name.replace(' ','+')
        url = IMAGE_SEARCH.format(category,plus_name)
        try:
            async with aiohttp.get(url) as response:
                soupObject = BeautifulSoup(await response.text(), "html.parser")
            image_url = soupObject.find(class_='monster-icon').find('a').get('href')
            return image_url
        except:
            type_dash = gettype.replace(' ','-')
            url_2 = 'https://static-waterdeep.cursecdn.com/1-0-6409-23253/Skins/Waterdeep/images/icons/{}/{}.jpg'
            try:
                async with aiohttp.get(url_2.format(category,gettype)) as response:
                    image_url = await response.text()
                    return image_url
            except:
                return 'https://static-waterdeep.cursecdn.com/1-0-6409-23253/Skins/Waterdeep/images/dnd-beyond-logo.svg'

def setup(bot):
    bot.add_cog(DND(bot))

#import discord
#import aiohttp
#import json
#from __main__ import send_cmd_help
#from .utils import chat_formatting as chat
#from discord.ext import commands
#from bs4 import BeautifulSoup
#
#numbs = {
#    "rewind" : "⏪",
#    "next": "➡",
#    "back": "⬅",
#    "choose": "⏺",
#    "fast_forward": "⏩",
#    "exit": "❌",
#}
#
## schema=(
##     'spells':{'higher_level','range','components','material','ritual','duration','concentration','casting_time', 'level', 'school','classes','subclasses','url'},
##     'equipment':{'equipment_category','weapon_category','weapon_range','category_range','cost',},
##     'monsters':{},
##     'classes':{},
##     'features':{'level','class'},
##     'races':{},
##     )
#
#
#
#COLORS = { 
#    'spells' : discord.Color.purple(),
#    'equipment': discord.Color.blue(),
#    # 'starting-equipment':discord.Color.blue(),
#    # 'spellcasting':discord.Color.purple(),
#    'monsters' : discord.Color.red(),
#    'classes' : discord.Color.orange(),
#    # 'subclasses':discord.Color.(0xf29214),
#    'features': discord.Color.orange(),
#    # 'levels':discord.Color.(0xf29214),
#    'races': discord.Color.orange(),
#    # 'subraces':discord.Color.discord.Color.(0xf29214),
#    # 'traits':discord.Color.(0xf29214),
#    # 'ability-scores': discord.Color.(0xf29214),
#    # 'skills' : discord.Color.(0xf29214),
#    # 'proficiencies' : discord.Color.(0xf29214),
#    # 'languages': discord.Color.(0xf29214),
#}
#
#BASEURL = 'http://dnd5eapi.co/api/'
#SELECTION = 'Enter selection for more {}information.'
#
#IMAGE_SEARCH = 'https://www.dndbeyond.com/{}?filter-search={}'
#
#class DND:
#    '''D&D Lookup Stuff'''
#
#    def __init__(self, bot):
#        self.bot = bot
#
#    @commands.group(pass_context=True)
#    async def dnd(self, ctx):
#        if ctx.invoked_subcommand is None:
#            await send_cmd_help(ctx)
#            return
#
#    @dnd.command(name='spells', pass_context=True)
#    async def lookup_spells(self, ctx, *, search=None):
#        '''Lookup Spells'''
#        CATEGORY = 'Spells'
#        await self._process_category(ctx, search, CATEGORY)
#
#    @dnd.command(name='features', pass_context=True)
#    async def lookup_features(self, ctx, *, search=None):
#        '''Lookup Features'''
#        CATEGORY = 'Features'
#        await self._process_category(ctx, search, CATEGORY)
#
#    @dnd.command(name='classes', pass_context=True)
#    async def lookup_classes(self, ctx, *, search=None):
#        '''Lookup classes'''
#        CATEGORY = 'classes'
#        await self._process_category(ctx, search, CATEGORY)
#
#    @dnd.command(name='monsters', pass_context=True)
#    async def lookup_monsters(self, ctx, *, search=None):
#        '''Lookup Monsters'''
#        CATEGORY = 'Monsters'
#        await self._process_category(ctx, search, CATEGORY)
#
#    @dnd.command(name='equipment', pass_context=True)
#    async def lookup_equipment(self, ctx, *, search=None):
#        '''Lookup equipment'''
#        CATEGORY = 'equipment'
#        await self._process_category(ctx, search, CATEGORY)
#
#
#		
#    async def _process_category(self, ctx, search=None, CATEGORY=None):
#        if search is None:
#            url = '{}{}'.format(BASEURL, CATEGORY)
#            menu_pages = await _present_list(self, url, CATEGORY)
#            await self.bot.say('Press ⏺ to select:')
#            await self.cogs_menu(ctx, menu_pages, CATEGORY, message=None, page=0, timeout=30)
#        elif search.isnumeric():
#            url = '{}{}/{}'.format(BASEURL,CATEGORY.lower(),search)
#            await self.bot.say('{} search: <{}>'.format(CATEGORY, url))
#            await self._process_item(ctx=ctx,url=url,category=CATEGORY)
#            # except:
#        else:
#            if ' ' in search:
#                search = search.replace(' ', '+')
#            search = search.replace(' ','+')
#            url = '{}{}/?name={}'.format(BASEURL, CATEGORY.lower(), search)
#            json_file = await _get_file(url)
#            await self.bot.say('{} search: <{}>'.format(CATEGORY, json_file['results'][0]['url']))
#
#    async def cogs_menu(self, ctx, cog_list: list, category, message: discord.Message=None, page=0, timeout: int=30):
#        """menu control logic for this taken from
#           https://github.com/Lunar-Dust/Dusty-Cogs/blob/master/menu/menu.py"""
#        cog = cog_list[page]
#        if not message:
#            message =\
#                await self.bot.send_message(ctx.message.channel, embed=cog)
#            await self.bot.add_reaction(message, "⏪")
#            await self.bot.add_reaction(message, "⬅")
#            await self.bot.add_reaction(message,"⏺")
#            await self.bot.add_reaction(message, "❌")
#            await self.bot.add_reaction(message, "➡")
#            await self.bot.add_reaction(message, "⏩")
#        else:
#            message = await self.bot.edit_message(message, embed=cog)
#        react = await self.bot.wait_for_reaction(
#            message=message, user=ctx.message.author, timeout=timeout,
#            emoji=["➡", "⬅", "❌", "⏪", "⏩","⏺"]
#        )
#        if react is None:
#            try:
#                try:
#                    await self.bot.clear_reactions(message)
#                except:
#                    await self.bot.remove_reaction(message,"⏪", self.bot.user)
#                    await self.bot.remove_reaction(message, "⬅", self.bot.user)
#                    await self.bot.remove_reaction(message, "❌", self.bot.user)
#                    await self.bot.remove_reaction(message,"⏺",self.bot.user)
#                    await self.bot.remove_reaction(message, "➡", self.bot.user)
#                    await self.bot.remove_reaction(message,"⏩", self.bot.user)
#            except:
#                pass
#            return None
#        elif react is not None:
#            reacts = {v: k for k, v in numbs.items()}
#            react = reacts[react.reaction.emoji]
#            if react == "next":
#                next_page = (page + 1) % len(cog_list)
#                return await self.cogs_menu(ctx, cog_list, message=message,
#                                            page=next_page, timeout=timeout)
#            elif react == "back":
#                next_page = (page - 1) % len(cog_list)
#                return await self.cogs_menu(ctx, cog_list, message=message,
#                                            page=next_page, timeout=timeout)
#            elif react == "rewind":
#                next_page = (page - 5) % len(cog_list)
#                return await self.cogs_menu(ctx, cog_list, message=message,
#                                                page=next_page, timeout=timeout)
#            elif react == "fast_forward":
#                next_page = (page + 5) % len(cog_list)
#                return await self.cogs_menu(ctx, cog_list, message=message,
#                                                page=next_page, timeout=timeout)
#            elif react == "choose":
#                await self.bot.say(SELECTION.format(category+' '))
#                answer = await self.bot.wait_for_message(timeout=10, author=ctx.message.author)
#                if answer is not None:
#                    await self.bot.say('Process choice : {}'.format(answer.content.lower().strip()))
#                    url = '{}{}/{}'.format(BASEURL,category,answer.content.lower().strip())
#
#                    await self._process_item(ctx, url=url, category=category)
#                    # Write URL item processing function (CATEGORY, URL)
#            else:
#                try:
#                    return await self.bot.delete_message(message)
#                except:
#                    pass
#				
#from bs4 import BeautifulSoup
#IMAGE_SEARCH = 'https://www.dndbeyond.com/{}?filter-search={}'
#
#class DND:
#    '''D&D Lookup Stuff'''
#
#    def __init__(self, bot):
#        self.bot = bot	
#		
#async def _process_item(self, ctx=None, url=None, category=None):		
#	#OTHER CODE ABOVE THIS POINT
#	elif category.lower() in COLORS:
#		category=category.lower()
#		img_available = ['monsters','equipment']
#		if category in img_available:
#			name = json_file['name']
#			if category == 'equipment':
#				gettype = json_file['equipment_category']
#			else:	
#				gettype = json_file['type']
#			image = await self.image_search(category,name.lower(),gettype)
#		#OTHER CODE OTHER CODE BELOW THIS POINT
#				
#async def image_search(self,category,name,gettype):
#	plus_name = name.replace(' ','+')
#	url = IMAGE_SEARCH.format(category,plus_name)
#	try:
#		async with aiohttp.get(url) as response:
#			soupObject = BeautifulSoup(await response.text(), "html.parser")			
#		image_url = soupObject.find(class_='monster-icon').find('a').get('href')
#		return image_url
#	except:
#		type_dash = gettype.replace(' ','-')
#		url_2 = 'https://static-waterdeep.cursecdn.com/1-0-6409-23253/Skins/Waterdeep/images/icons/{}/{}.jpg'
#		try:
#			async with aiohttp.get(url_2.format(category,gettype)) as response:
#				image_url = await response.text()
#				return image_url
#		except:	
#			return 'https://static-waterdeep.cursecdn.com/1-0-6409-23253/Skins/Waterdeep/images/dnd-beyond-logo.svg'
#
#		
#    async def _process_item(self, ctx=None, url=None, category=None):
#        json_file = await _get_file(url)
#        if 'count' in json_file:
#            menu_pages = await _present_list(self, url, CATEGORY)
#            await self.bot.say('Press ⏺ to select:')
#            await self.cogs_menu(ctx, menu_pages, CATEGORY, message=None, page=0, timeout=30)
#        elif category.lower() in COLORS:
#			
#		#RANE RANE RANE RANE RANE 
#            category=category.lower()
#            img_available = ['monsters','equipment']
#            if category in img_available:
#                name = json_file['name']
#                if category == 'equipment':
#                    gettype = json_file['equipment_category']
#                else:	
#                    gettype = json_file['type']
#                image = await self.image_search(category,name.lower(),gettype)
#				
#				
#            keys = json_file.keys()
#            if 'desc' in keys:
#                desc = chat.pagify('\n'.join(json_file['desc']), delims=['\n\n'], escape=True, shorten_by=8, page_length=1000)
#                desc_pages = []
#                for page in desc:
#                    desc_pages.append(page)
#                for page in desc_pages:
#                    if page == desc_pages[0]:
#                        em=discord.Embed(color=COLORS[category],title=json_file['name'],description=page)
#                        await self.bot.say(embed=em)
#                    elif page == desc_pages[len(desc_pages)-1]:
#                        em=discord.Embed(color=COLORS[category],title='',description=page)
#                    else:
#                        em=discord.Embed(color=COLORS[category],title='',description=page)
#                        await self.bot.say(embed=em)
#            else:
#                em=discord.Embed(color=COLORS[category],title='',description='something')
#            for key in keys:
#                if key not in {'_id','index','name','desc'}:
#                    key2 = key.replace('_',' ').title()
#                    if isinstance(json_file[key],list):
#                        try:
#                            em.add_field(name=key2,value='\n'.join(j['name'] for j in json_file[key]))
#                        except:
#                            em.add_field(name=key2,value='\n'.join(j for j in json_file[key]))
#                    elif isinstance(json_file[key],tuple):
#                        try:
#                            em.add_field(name=key2,value='\n'.join(j['name'] for j in json_file[key]))
#                        except:
#                            em.add_field(name=key2,value='\n'.join(j for j in json_file[key]))
#                    elif isinstance(json_file[key],dict):
#                        em.add_field(name=key2,value=json_file[key]['name'])
#                    elif isinstance(json_file[key],str):
#                        em.add_field(name=key2,value=json_file[key])
#                    elif isinstance(json_file[key],int):
#                        em.add_field(name=key2,value=json_file[key])
#                    else:
#                        em.add_field(name=key2,value='something else detected')
#            await self.bot.say(embed=em)
#
#async def _get_file(url):
#    async with aiohttp.ClientSession() as session:
#        async with session.get(url) as response:
#            print('_get_file('+url+')')
#            json_file = await response.json()
#            if json_file is not None:
#                return json_file
#
#async def _present_list(self, url, category):
#    json_file = await _get_file(url)
#    if json_file is not None:
#        results = json_file['results']
#        package = []
#        for i in range(0,int(json_file['count'])):
#            c = i+1
#            package.append('{} {}'.format(c, json_file['results'][i]['name']))
#
#        pages = chat.pagify('\n'.join(package), delims=['\n'], escape=True, shorten_by=8, page_length=350)
#        menu_pages = []
#
#        for page in pages:
#            em=discord.Embed(color=discord.Color.red(), title=category, description=chat.box(page))
#            em.set_footer(text='From dnd5eapi.co',icon_url='http://www.dnd5eapi.co/public/favicon.ico')
#            menu_pages.append(em)
#
#        return menu_pages
#
#
#def setup(bot):
#    bot.add_cog(DND(bot))