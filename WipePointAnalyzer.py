import requests
import discord
from discord.ext import tasks, commands
from discord.commands import option 
import json
from urllib.parse import urlparse
from bot_token import bearer_token
from data import TOP_PROG_POINTS, ENCOUNTERS
from payloads import FIGHT_TIME_STARTS
import datetime
SUPPORTED_FIGHTS = ["TOP"]




class WipePoint(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.slash_command()
    @option("fight", desciption="Fight to look for", autocomplete=discord.utils.basic_autocomplete(SUPPORTED_FIGHTS))
    async def wipepoint(self, ctx, fight_url:str , fight):
        """Shows the furthest prog point for each fight in a log"""
        time_at_call = datetime.datetime.now()
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

        lookForID = 0
        message_color = 0
        print(report_id)
        payload = FIGHT_TIME_STARTS
        fight_num = 0
        await ctx.defer()
        match fight:
            case "Ucob":
                lookForID = 1060
                message_color = 0xe08514
            case "Uwu":
                lookForID = 1061
                message_color = 0x6ddedc
            case "Tea":
                lookForID = 1062
                message_color = 0xcfb319
            case "Dsr":
                lookForID = 1065
                message_color = 0x7792a3
            case "TOP":
                lookForID = 1068
                message_color = 0x82878f
                timeStamps = returnFightStartEndTImes(report_id, lookForID)
                report = createTopData()
                for item in timeStamps:
                    if item[2] == "true":
                        report['Clear'] += 1
                    else:
                        start_time = item[0]
                        end_time = item[1]
                        payload += "\\n\\t\\t\\tfight_" + str(fight_num) + ": table(startTime: " +  str(start_time) + ", endTime: " +  str(end_time) + ", hostilityType:Enemies, dataType: Casts, viewBy:Ability)"
                        fight_num += 1
         
                payload += "\\n\\t\\t}\\n\\t}\\n}\\n\\n\",\"operationName\":\"report\",\"variables\":{\"report\":\"" + report_id + "\"}}"
                headers = {
                "Content-Type": "application/json",
                "Authorization": "Bearer " + bearer_token 
                }
                url = "https://www.fflogs.com/api/v2/client/"
                response = requests.request("POST", url, data=payload, headers=headers)
                contents = response.json()
                for item in contents['data']['reportData']['report']:
                    print(item)
                    furthestCast = returnMatchingCastsFromLog(contents['data']['reportData']['report'][item])
                    print(furthestCast)
                    print(f"Start: {start_time} End: {end_time}")
                    for key, content in furthestCast.items():
                        if content:
                            report[key] += 1
                            break
                

                
                print(f"Final Report: {report}") 
        message_embed = discord.Embed(title=ENCOUNTERS[lookForID], url=fight_url, color=message_color)
        message_embed.set_thumbnail(url=f"https://assets.rpglogs.com/img/ff/bosses/{lookForID}-icon.jpg")
        message_embed.set_author(name="LogChecker", icon_url="https://gamepress.gg/arknights/sites/arknights/files/2022-11/TexalterAvatar.png")
        for key, num in report.items():
            if num != 0:
                title = TOP_PROG_POINTS[key]
                body = f"Wiped {num} time(s)"
                print(f"title {title} body {body}")

                message_embed.add_field(name= title, value= body)
        time_now = datetime.datetime.now()
        diff = time_now - time_at_call
        duration = diff.total_seconds()
        message_embed.set_footer(text=f"Took {duration} seconds from call")
        await ctx.followup.send(embed = message_embed)

                


def returnFightStartEndTImes(report:str, encounterID:int):
    fight_times = []
    url = "https://www.fflogs.com/api/v2/client/"

    payload = "{\"query\":\"query report($report_data: String!)\\n{\\n\\treportData{\\n\\t\\treport(code: $report_data){\\n\\t\\t\\tvisibility\\n\\t\\t\\tfights{\\n\\t\\t\\t\\tstartTime\\n\\t\\t\\t\\tendTime\\n\\t\\t\\t\\tencounterID\\n\\t\\t\\t\\tkill\\n\\t\\t\\t\\tlastPhase\\n\\t\\t\\t}\\n\\t\\t}\\n\\t}\\n}\",\"operationName\":\"report\",\"variables\":{\"report_data\":\"" + report + "\"}}"
    headers = {
        "Content-Type": "application/json",
        "Authorization": "Bearer " + bearer_token 
    }

    response = requests.request("POST", url, data=payload, headers=headers)
    contents = response.json()
    print(contents)
    fightList = contents['data']['reportData']['report']['fights']
    for fight in fightList:
        if fight.get("encounterID") == encounterID:
            fight_times.append((fight.get("startTime"), fight.get("endTime"), fight.get("kill"), fight.get("lastPhase"), fight.get("encounterID")))
    print(f"Fight Times length {len(fight_times)}")
    return fight_times


def returnMatchingCastsFromLog(contents):
    
    print(type(contents))
    print(contents)
    data = contents['data']['entries']
    test_dict = {}
    for key in TOP_PROG_POINTS.keys():
        test_dict.update({key:False})
    for cast in data:
        for name in test_dict.keys():
            if name == 'Cosmo Memory':
                if cast.get('name') == name and cast.get('actorName') == "Alpha Omega":
                    test_dict.update({name:True})
            elif cast.get('name') == name:
                test_dict.update({name:True})
    print(test_dict)

    return test_dict

        
        
            







def createTopData():
    topReport = {}
    keys = TOP_PROG_POINTS.keys()
    for key in keys:
        topReport.update({key:0})
    return topReport

def main():
    report = "L6qYp8g7tmrvZnDV"
    print(returnFightStartEndTImes(report, 1068))

if __name__ == "__main__":
    main() 

