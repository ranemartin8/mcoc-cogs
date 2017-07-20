import discord
import aiohttp
import json
import bs4
from bs4 import BeautifulSoup
from __main__ import send_cmd_help
from .utils import chat_formatting as chat
from discord.ext import commands

       
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
                return await self.pages_menu(ctx, embed_list, category, message=message, page=next_page, timeout=timeout)
            elif react == "⬅": #previous_page
                next_page = (page - 1) % len(cog_list)
                return await self.pages_menu(ctx, cog_list, category, message=message, page=next_page, timeout=timeout)
            elif react == "⏪": #rewind
                next_page = (page - 5) % len(cog_list)
                return await self.pages_menu(ctx, cog_list, category, message=message, page=next_page, timeout=timeout)
            elif react == "⏩": # fast_forward
                next_page = (page + 5) % len(cog_list)
                return await self.pages_menu(ctx, cog_list, category, message=message, page=next_page, timeout=timeout)
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
        if 'count' in json_file: # Present list
            menu_pages = await self._present_list(url, category)
            await self.pages_menu(ctx, menu_pages, category, message=None, page=0, timeout=30)
        elif category in COLORS: #process endpoint
            try:
                name = json_file['name']
            except KeyError:
                name = category
                print('KeyError: json_file[\'name\']. Category used instead')
            try:
                em = discord.Embed(color=COLORS[category],title=name)
                img_available = ['monsters', 'equipment']
                if category in img_available:
                    if category == 'equipment':
                        gettype = json_file['equipment_category']
                    else:
                        gettype = json_file['type']
                image = await self.image_search(category,name.lower(),gettype.lower())
                if not image:
                    em.set_thumbnail(url='https://static-waterdeep.cursecdn.com/1-0-6409-23253/Skins/Waterdeep/images/dnd-beyond-logo.svg')
                else:
                    em.set_thumbnail(url=image)
                await self.bot.say(embed=em)
            except:
                await self.bot.say('Something went wrong in _process_item')
                raise
        else:
            print('_process_item error')

    async def _present_list(self, url, category):
        print(url)
        json_file = await self._get_file(url)
        results = json_file['results']
        package = []
        i = 1
        for row in results:
            package.append('{} {}'.format(i, row['name']))
            i += 1
        pages = chat.pagify('\n'.join(package), delims=['\n'], escape=True, shorten_by=8, page_length=350)
        menu_pages = []
        for page in pages:
            em=discord.Embed(color=COLORS[category], title=category, description=chat.box(page))
            em.add_field(name='Press ⏺ to select',value='------------------')
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


    async def image_search(self,category,name,gettype):
        plus_name = name.replace(' ','+')
        type_dash = gettype.replace(' ','-')
        icon_url = 'https://static-waterdeep.cursecdn.com/1-0-6409-23253/Skins/Waterdeep/images/icons/{}/{}.jpg'
        default_url = 'https://static-waterdeep.cursecdn.com/1-0-6409-23253/Skins/Waterdeep/images/dnd-beyond-logo.svg'
        monster_types = ['aberration','beast','celestial','construct','dragon','elemental','fey',
                 'humanoid','fiend','giant','ooze','plant','undead','monstrosity']
        equip_type = ['adventuring-gear','ammunition','mount','vehicle','weapon','tool','poison',
                      'potion','pack','armor','holy-symbol','druidic-focus','arcane-focus']
        
        IMAGE_SEARCH = 'http://www.dnd.beyond.com/{}?filter-search={}'
        
        if category == 'equipment':
            if type_dash not in equip_type:
                return default_url
            else:
                result_url = icon_url.format(category,type_dash)
                return result_url
        elif category == 'monsters':
            try:
                url = IMAGE_SEARCH.format(category,plus_name)
                async with aiohttp.get(url) as response:
                    soupObject = BeautifulSoup(await response.text(), "html.parser")
                image_url = soupObject.find(class_='row monster-icon').contents[0].get('href')
                return image_url
            except:
                if type_dash not in monster_types:
                    return default_url
                else:
                    result_url = icon_url.format(category,type_dash+'@2x')
                    return result_url
        else:
            return default_url
        

def setup(bot):
    bot.add_cog(DND(bot))
