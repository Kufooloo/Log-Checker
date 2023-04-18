import requests
import discord
from discord.ext import tasks, commands
from discord.commands import option 
import datetime
from urllib.parse import urlparse
import asyncio

class utility(commands.Cog):
    def __init__(self, bot) -> None:
        super().__init__()
        self.bot = bot
        self.response = []
    @commands.Cog.listener()
    async def on_message(self, ctx):
        if ctx.author.id == 1062903042099392522:
            return
        content = ctx.content
        print(content)
        token_list = token(content)
        print(token_list)
        i = 0
        test =True
        url = ""
        while i < len(token_list) and test == True:
            o = urlparse(token_list[i])
            print(o)
            if o.netloc == 'twitter.com':
                print('found twitter link')
                url = o._replace(netloc="www.vxtwitter.com").geturl()
                test = False
            i+=1
        await ctx.delete()   
        await ctx.channel.send(url)   

        
        return
        
        


                

def token(string):
    start, i = 0, 0
    token_list = []
    for x in range(0, len(string)):
        if " " == string[i:i+1]:
            token_list.append(string[start:i+1])
            start = i + 1
        i += 1
    token_list.append(string[start:i+1])
    return token_list
    
