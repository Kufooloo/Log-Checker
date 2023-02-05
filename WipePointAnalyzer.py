import requests
import discord
from discord.ext import tasks, commands
from discord.commands import option 
import json
from urllib.parse import urlparse
from bot_token import bearer_token
from data import TOP_PROG_POINTS, ENCOUNTERS
SUPPORTED_FIGHTS = ["TOP"]




class WipePoint(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.slash_command()
    @option("fight", desciption="Fight to look for", autocomplete=discord.utils.basic_autocomplete(SUPPORTED_FIGHTS))
    async def wipepoint(self, ctx, url:str , fight):
        """Shows the furthest prog point for each fight in a log"""
        #check if report is valid
        o = urlparse(url)
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
                print(report)
                print(timeStamps)
                for item in timeStamps:
                    if item[2] == "true":
                        report['Clear'] += 1

                    start_time = item[0]
                    end_time = item[1]
                    furthestCast = returnMatchingCastsFromLog(start_time, end_time, report_id, lookForID)
                    print(furthestCast)
                    print(f"Start: {start_time} End: {end_time}")
                    for key, content in furthestCast.items():
                        if content:
                            report[key] += 1
                            break
                

                
                print(f"Final Report: {report}") 
        message_embed = discord.Embed(title=ENCOUNTERS[lookForID], url=url, color=message_color)
        message_embed.set_thumbnail(url=f"https://assets.rpglogs.com/img/ff/bosses/{lookForID}-icon.jpg")
        message_embed.set_author(name="LogChecker", icon_url="https://gamepress.gg/arknights/sites/arknights/files/2022-11/TexalterAvatar.png")
        for key, num in report.items():
            if num != 0:
                title = TOP_PROG_POINTS[key]
                body = f"Wiped {num} time(s)"
                print(f"title {title} body {body}")

                message_embed.add_field(name= title, value= body)
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


def returnMatchingCastsFromLog(startTime:int, endTime: int, report:str, fight:int):
    url = "https://www.fflogs.com/api/v2/client/"

    payload = "{\"query\":\"query report($report: String!, $stime: Float, $etime: Float)\\n{\\n\\treportData{\\n\\t\\treport(code: $report){\\n\\t\\t\\ttable(startTime: $stime, endTime: $etime, hostilityType:Enemies, dataType: Casts, viewBy:Ability)\\n\\t\\t}\\n\\t}\\n}\",\"operationName\":\"report\",\"variables\":{\"report\":\""+report+"\",\"stime\":"+ str(startTime)+",\"etime\":"+str(endTime)+ "}}"
    headers = {
        "Content-Type": "application/json",
        "Authorization": "Bearer " + bearer_token 
    }
    response = requests.request("POST", url, data=payload, headers=headers)
    contents = response.json()
    data = contents['data']['reportData']['report']['table']['data']['entries']
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

