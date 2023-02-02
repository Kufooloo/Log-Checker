import requests
import discord
from discord.ext import tasks, commands
from discord.commands import option 
import json
from urllib.parse import urlparse

SUPPORTED_FIGHTS = ["TOP"]

class WipePoint(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.slash_command()
    @option("fight", desciption="Fight to look for", autocomplete=discord.utils.basic_autocomplete(SUPPORTED_FIGHTS))
    async def wipepoint(self, ctx, report:String, fight):
        #check if report is valid
        o = urlparse(fight_url)
        print(o)
        if o.netloc != 'www.fflogs.com':
            await ctx.respond("This is not a link to fflogs.")
            return
        url_path = o.path
        print(url_path[:8])
        if url_path[:9] != '/reports/':
            await ctx.respond("This is not a report.")
            return
        report_id = url_path[9:]
        if report_id[-1] == '/':
            report_id = url_path[9:-1]
        print(report_id)
        


        




def returnFightStartEndTImes(report:String, encounterID:int):
    fight_times = []
    url = "https://www.fflogs.com/api/v2/client/"

    payload = "{\"query\":\"query report($code:String!){\\n\\treportData{\\n\\t\\treport(code:$code){\\n\\t\\t\\tfights{\\n\\t\\t\\t\\tstartTime\\n\\t\\t\\t\\tendTime\\n\\t\\t\\t\\tencounterID\\n\\t\\t\\t}\\n\\t\\t}\\n\\t}\\n}\",\"operationName\":\"report\",\"variables\":{\"code\":\"" + report + "\"}}"
    headers = {
        "Content-Type": "application/json",
        "Authorization": "Bearer " + bearer_token 
    }

    response = requests.request("POST", url, data=payload, headers=headers)
    contents = response.json()
    fightList = contents['data']['reportData']['report']['fights']
    for fight in fightList:
        if fight.get("encounterID") == encounterID:
            temp = (fight.get("startTime"), fight.get("endTime"))
            fight_times.append(temp)
    
    return fight_times


