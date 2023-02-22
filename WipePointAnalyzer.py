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
        self.queue = {}

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
        if type(timeStamps) is str:
            await ctx.followup.send(timeStamps)
            return 
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
        try:
            contents = response.json()
        except:
            await ctx.send(str(response))
        try:
            for item in contents['data']['reportData']['report']:
                print(item)
                furthestCast = returnMatchingCastsFromLog(contents['data']['reportData']['report'][item], lookForID)
                print(furthestCast)
                print(f"Start: {start_time} End: {end_time}")
                for key, content in furthestCast.items():
                    if content:
                        report[key] += 1
                        break
        except TypeError as err:
            print("Error")
            await ctx.send(err)
        

        
        print(f"Final Report: {report}") 
        message_embed = discord.Embed(title=ENCOUNTERS[lookForID], url=fight_url, color=message_color)
        message_embed.set_thumbnail(url=f"https://assets.rpglogs.com/img/ff/bosses/{lookForID}-icon.jpg")
        message_embed.set_author(name="LogChecker", icon_url="https://gamepress.gg/arknights/sites/arknights/files/2022-11/TexalterAvatar.png")
        for key, num in report.items():
            if num != 0:
                title = f"{TOP_PROG_POINTS[key]} - {round(num/fight_num, 2)*100}%"
                body = f"Wiped {num} time(s)"
                print(f"title {title} body {body}")

                message_embed.add_field(name= title, value= body)
        time_now = datetime.datetime.now()
        diff = time_now - time_at_call
        duration = diff.total_seconds()
        message_embed.set_footer(text=f"{fight_num} pulls. Took {duration} to proccess")
        await ctx.followup.send(embed = message_embed)
    
    @commands.slash_command()
    @option("fight", desciption="Fight to look for", autocomplete=discord.utils.basic_autocomplete(SUPPORTED_FIGHTS))
    async def guild_wipepoints(self, ctx, guild_name, fight):
        """Do not use"""
        code_list = return_guide_code_list(guild_name)
        time_dict = {}
        time_at_call = datetime.datetime.now()
        await ctx.defer()
        report = createTopData()
        for report_id in code_list: 
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
            payload = FIGHT_TIME_STARTS
            fight_num = 0

            if type(timeStamps) is str:
                await ctx.followup.send(timeStamps)
                return 
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
            try:
                contents = response.json()
            except:
                await ctx.send(str(response))
            try:
                for item in contents['data']['reportData']['report']:
                    print(item)
                    furthestCast = returnMatchingCastsFromLog(contents['data']['reportData']['report'][item], lookForID)
                    print(furthestCast)
                    print(f"Start: {start_time} End: {end_time}")
                    for key, content in furthestCast.items():
                        if content:
                            report[key] += 1
                            break
            except TypeError as err:
                print("Error")
                await ctx.send(err)
        
        print(f"Final Report: {report}") 
        message_embed = discord.Embed(title=guild_name, color=message_color)
        message_embed.set_thumbnail(url=f"https://assets.rpglogs.com/img/ff/bosses/{lookForID}-icon.jpg")
        message_embed.set_author(name="LogChecker", icon_url="https://gamepress.gg/arknights/sites/arknights/files/2022-11/TexalterAvatar.png")
        for key, num in report.items():
            if num != 0:
                title = f"{TOP_PROG_POINTS[key]} - {round(num/fight_num, 2)}%"
                body = f"Wiped {num} time(s)"
                print(f"title {title} body {body}")

                message_embed.add_field(name= title, value= body)
        time_now = datetime.datetime.now()
        diff = time_now - time_at_call
        duration = diff.total_seconds()
        message_embed.set_footer(text=f"{fight_num} pulls. Took {duration} to proccess")
        await ctx.followup.send(embed = message_embed)

    @commands.slash_command(guild_ids=[932734358870188042])
    async def add_queue(self, ctx, fight_url):
        if self.queue.get(ctx.author.id) is None:
            self.queue.update({ctx.author.id:[fight_url]})
        else:
            self.queue[ctx.author.id].append(fight_url)
        await ctx.respond(f"Added report with url {fight_url}")
    
    @commands.slash_command(guild_ids=[932734358870188042])
    async def list_queue(self, ctx):
        message_embed = discord.Embed(title="Queue List", color = 0x82878f)
        message_embed.set_author(name="LogChecker", icon_url="https://gamepress.gg/arknights/sites/arknights/files/2022-11/TexalterAvatar.png")
        body = ""
        if self.queue.get(ctx.author.id) is None:
            await ctx.respond("You don't have a list")
            return
        for item in self.queue.get(ctx.author.id):
            body = body + item + "\n"
        message_embed.add_field(name="Reports", value=body)
        await ctx.respond(embed=message_embed)
    @commands.slash_command(guild_ids=[932734358870188042])
    async def delete_queue(self, ctx):
        if self.queue.get(ctx.author.id) is None:
            await ctx.respond("You don't have a queue")
            return
        self.queue.pop(ctx.author.id)
        await ctx.respond("Deleted", hidden=True)
    @commands.slash_command(guild_ids=[932734358870188042])
    @option("fight", desciption="Fight to look for", autocomplete=discord.utils.basic_autocomplete(SUPPORTED_FIGHTS))
    async def analyze_queue(self, ctx, fight):
        queue = self.queue.get(ctx.author.id)
        if queue is None:
            await ctx.respond("You don't have a queue")
            return
        for item in queue:
            await WipePoint.wipepoint(ctx, item, fight)

        
        


                


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
    if contents.get('errors') is not None:
        return contents['errors'][0].get('message')
    fightList = contents['data']['reportData']['report']['fights']

    for fight in fightList:
        if fight.get("encounterID") == encounterID:
            fight_times.append((fight.get("startTime"), fight.get("endTime"), fight.get("kill"), fight.get("lastPhase"), fight.get("encounterID")))
    print(f"Fight Times length {len(fight_times)}")
    return fight_times


def returnMatchingCastsFromLog(contents, id):
    
    print(type(contents))
    print(contents)
    data = contents['data']['entries']
    test_dict = {}
    match id:
        case 1068:
            prog_dict = TOP_PROG_POINTS
    for key in prog_dict.keys():
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

def return_guide_code_list(guild_name):
    code_list = []
    url = "https://www.fflogs.com/api/v2/client/"
    zone_id = 53
    payload = "{\"query\":\"query  reports($name: String!, $zone: Int){\\n\\treportData{\\n\\t\\treports(guildName: $name , zoneID: $zone){\\n\\t\\t\\t\\n\\t\\t\\tdata{\\n\\t\\t\\tcode\\n\\t\\t\\tvisibility\\n\\t\\t\\t}\\n\\t\\t}\\n\\t}\\n}\\n\",\"operationName\":\"reports\",\"variables\":{\"name\":\"" + guild_name + "\",\"zone\":" + str(zone_id) + "}}"
    headers = {
        "Content-Type": "application/json",
        "Authorization": "Bearer " + bearer_token 
    }
    response = requests.request("POST", url, data=payload, headers=headers)

    print(response.text)   
            
    contents = response.json()

    data = contents['data']['reportData']['reports']['data']
    for item in data:
        if item.get('visibility') == 'public':
            code_list.append(item.get('code'))

    return code_list







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

