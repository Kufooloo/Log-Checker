from bot_token import bot_token, bearer_token
import requests
import discord
from discord.ext import tasks, commands
from discord.commands import option 
import json
from urllib.parse import urlparse 
from data import WORLDS, ENCOUNTERS, PHASES, FIGHTS, RELEASE_DATES
import math
from WipePointAnalyzer import WipePoint
from utility import utility
intents = discord.Intents.all()

bot = discord.Bot(intents=intents)

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user} (ID: {bot.user.id})")
    print("------")

class FFlogs(commands.Cog):
    def __init__(self, bot) -> None:
        super().__init__()
        self.bot = bot
        self.prev_leaderboard = {}
    @commands.slash_command()
    async def rate_check(self, ctx):
        payload = "{\"query\":\"query{\\n\\trateLimitData{\\n\\t\\tlimitPerHour\\n\\t\\tpointsSpentThisHour\\n\\t\\tpointsResetIn\\n\\t}\\t\\n}\"}"
        headers = {
        "Content-Type": "application/json",
        "Authorization": "Bearer " + bearer_token 
        }
        url = "https://www.fflogs.com/api/v2/client/"
        response = requests.request("POST", url, data=payload, headers=headers)
        contents = response.json()

        message_embed = discord.Embed(title=f"Rate Limit Data", color=discord.Color.dark_grey())
        message_embed.set_author(name="LogChecker", icon_url="https://gamepress.gg/arknights/sites/arknights/files/2022-11/TexalterAvatar.png")
        if contents.get("status") == 429:
            message_embed.add_field(name="Error", value=contents.get('error'))
        else:
            data = contents['data']['rateLimitData']
            for key, item in data.items():
                message_embed.add_field(name=key, value=item)


        await ctx.respond(embed=message_embed)
        




    @commands.slash_command(name="log_check", guild_ids=[932734358870188042])
    @option("first_name", description="Players first name.")
    @option("last_name", description="Players last name.")
    @option("world", desciption="World the player is from", autocomplete=discord.utils.basic_autocomplete(WORLDS))
    async def log_check(self, 
        ctx: discord.ApplicationContext,
        first_name: str,
        last_name: str,
        world: str
    ):
        """Searches for information on the given user"""
        await ctx.respond(f"First name: {first_name} Last Name: {last_name} World {world}")
        clear_times =  earliest_clear_date(first_name, last_name, world)  
        if clear_times is None:
            await ctx.send("No character with given information.")
            return
        message_embed = discord.Embed(title=f"{first_name} {last_name} @ {world}", color=discord.Color.dark_grey())
        message_embed.set_author(name="LogChecker", icon_url="https://gamepress.gg/arknights/sites/arknights/files/2022-11/TexalterAvatar.png")
        
        print(clear_times)
        #check for shb and below ults
        #ucob
        
        fight_name = clear_times.get('Ucob')

        title = "The Unending Coil of Bahamut"
        match fight_name:
            case 'SB_Ucob':
                body = "Cleared in Stormblood"
            case 'ShB_Ucob':
                body = "Cleared in ShadowBringers"
            case 'Ew_Ucob':
                body = "Cleared in Endwalker"
            case None:
                body = "Has not cleared Ucob"
        
        message_embed.add_field(name=title, value=body)

        #uwu
        fight_name = clear_times.get('Uwu')

        title = "The Weapon's Refrain"
        match fight_name:
            case 'SB_Uwu':
                body = "Cleared in Stormblood"
            case 'ShB_Uwu':
                body = "Cleared in ShadowBringers"
            case 'Ew_Uwu':
                body = "Cleared in Endwalker"
            case None:
                body = "Has not cleared"
        
        message_embed.add_field(name=title, value=body)

        fight_name = clear_times.get('Tea')

        title = "The Epic of Alexander"
        match fight_name:
            case 'ShB_Tea':
                body = "Cleared in ShadowBringers"
            case 'Ew_Tea':
                body = "Cleared in Endwalker"
            case None:
                body = "Has not cleared Tea"
        
        message_embed.add_field(name=title, value=body)
                
        title = "Dragonsong's Reprise"
        fight_time = clear_times.get('Dsr')
        print(fight_time)

        if fight_time is None:
            body = "Has not cleared Dsr"
        else:
            days = math.trunc(abs(int(str(fight_time)[:10]) - RELEASE_DATES['Ew_Dsr']) / 86400 )
            body =  f"Cleared {days} days after release day"
        
        message_embed.add_field(name=title, value=body)

        add_field_raid(message_embed, clear_times, "Verse")
        add_field_raid(message_embed, clear_times, "Promise")
        add_field_raid(message_embed, clear_times, "Asphodelos")
        add_field_raid(message_embed, clear_times, "Abyssos")
        
        message_embed.set_footer(text=check_fflogs_ult(first_name, last_name, world))


        await ctx.send(embed=message_embed)
        return


    @commands.slash_command(name="leaderboard", guild_ids=[932734358870188042], cog="WorldRaceing")
    async def leaderboard(self, ctx):
        """Gives the top 5 teams in the current world first race"""
        data = check_wfr()
        message = discord.Embed(title=data.get('name'), description="Leaderboard for the current FFXIV world first race!", url="https://www.fflogs.com/zone/race/latest")
        message.set_author(name="LogChecker", icon_url="https://gamepress.gg/arknights/sites/arknights/files/2022-11/TexalterAvatar.png")
        message.set_thumbnail(url=data.get('image'))
        for i in range(5):
            team = data.get(i)
            if team[2]:
                body = f"Killed at <t:{str(team[3])[:10]}> with {team[4]} pulls"
            else:
                body = f"Progress: {team[1]} Pulls: {team[4]}"
            message.add_field(name=team[0], value=body, inline=False)
        await ctx.respond(embed=message)

class ReportAnalysis(commands.Cog):
    def __init__(self, bot) -> None:
        super().__init__()
        self.bot = bot
        self.encounters = ENCOUNTERS

    @commands.slash_command(name="analyze")
    @option("fight", desciption="Fight to look for", autocomplete=discord.utils.basic_autocomplete(FIGHTS))
    async def analyze(self, ctx, fight_url, fight):
        """Reports how many times you wiped to each phase in the given log"""
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
        data = check_report(report_id)
        if data[0] == "error":
            await ctx.respond("This is not a valid report")
            return
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
            case "Top":
                lookForID = 1068
                message_color = 0x82878f
        embed_data = {}
        for fight in data:
            encounterID = fight.get('encounterID')
            encounter_name = ENCOUNTERS.get(encounterID)
            print(encounterID)
            print(encounter_name)
            if encounterID == lookForID:
                if fight.get('kill') == True:
                    if embed_data.get('Kills') is None:
                        embed_data.update({'Kills':1})
                    else:
                        embed_data['Kills'] += 1
                else:
                    phase = fight.get('lastPhaseAsAbsoluteIndex')
                    if embed_data.get(phase) is None:
                        embed_data.update({phase:1})
                    else:
                        embed_data[phase] += 1

        message_embed = discord.Embed(title=ENCOUNTERS[lookForID], url=fight_url, color=message_color)
        message_embed.set_thumbnail(url=f"https://assets.rpglogs.com/img/ff/bosses/{lookForID}-icon.jpg")
        message_embed.set_author(name="LogChecker", icon_url="https://gamepress.gg/arknights/sites/arknights/files/2022-11/TexalterAvatar.png")
        for i in range(10):
            if embed_data.get(i) is not None:
                body = f"Wiped {embed_data.get(i)} time(s)"
                title = PHASES[ENCOUNTERS.get(lookForID)][i]
                message_embed.add_field(name= title, value= body)
        if embed_data.get('kills') is not None:
            body = f"Killed {embed_data.get('kills')} time(s)"
            title = "kills"
            message_embed.add_field(name= title, value= body)

        await ctx.respond(embed=message_embed)
    





def check_fflogs_ult(first_name:str, last_name:str, world:str):
    name = first_name + " " + last_name

    url = "https://www.fflogs.com/api/v2/client/"

    payload = "{\"query\":\"query {\\n\\tcharacterData {\\n\\t\\tcharacter(\\n\\t\\t\\tname: \\\"" + name + "\\\"\\n\\t\\t\\tserverSlug: \\\"" + world + "\\\"\\n\\t\\t\\tserverRegion: \\\"NA\\\"\\n\\t\\t) {\\n\\t\\t\\thidden\\n\\t\\t\\tCurrent_EW: zoneRankings(zoneID: 45)\\n\\t\\t\\tLegacy_EW: zoneRankings(zoneID: 43)\\n\\t\\t\\tCurrent_ShB: zoneRankings(zoneID: 32)\\n\\t\\t\\tLegacy_ShB: zoneRankings(zoneID: 30)\\n\\t\\t\\t\\n\\t\\t}\\n\\t}\\n}\\n\",\"variables\":{\"name\":\"Emilia Makise\",\"serverSlug\":\"Halicarnassus\",\"serverRegion\":\"NA\"}}"
    headers = {
        "Content-Type": "application/json",
        "Authorization": "Bearer " + bearer_token 
    }

    response = requests.request("POST", url, data=payload, headers=headers)


    contents = response.json()
    character = contents['data']['characterData']['character']
    if character is None:
        return "Character not found. Perhaps you misstyped something?"
    if character['hidden']:
        return "Character Profile is Hidden!"
    message = {}
    character.pop('hidden')
    for key, content in character.items():
        rankings = content.get('rankings')
        print(rankings)
        for items in rankings:
            if items.get("totalKills") != 0:
                print(f"Cleared {items['encounter']['name']} {items.get('totalKills')}")
                kills = items.get('totalKills')
                if kills != 0:
                    if message.get(items['encounter']['name']) is None:
                        message.update({items['encounter']['name']:kills})
                    else:
                        message[items['encounter']['name']] += kills
    
    print(message)
    if len(message) == 0:
        return "This person has not cleared an ultimate"
    ret = ""
    for fight, kill in message.items():
        ret += f"{fight} {kill} times. "


    return ret
        
def check_wfr():
    
    url = "https://www.fflogs.com/api/v2/client/"
    return_dict = {}

    payload = "{\"query\":\"query {\\n\\tprogressRaceData{\\n\\t\\tprogressRace\\n\\t}\\n}\\n\",\"variables\":{}}"
    headers = {
        "Content-Type": "application/json",
        "Authorization": "Bearer " + bearer_token 
    }
    response = requests.request("POST", url, data=payload, headers=headers)
    contents = response.json()
    data = contents['data']['progressRaceData']['progressRace']
    return_dict.update({'image':data[0]['encounters'][0].get('backgroundImageUrl')})
    return_dict.update({'fight':data[0]['encounters'][0].get('name')})

    for i in range(5):
        team_name = data[i].get('name')
        encounter = data[i].get('encounters')
        bestPercent = encounter[0].get('bestPercentForDisplay')
        killed = encounter[0].get('isKilled')
        kill_time = encounter[0].get('killedAtTimestamp')
        pull_count = encounter[0].get('pullCount')

        return_dict.update({i:[team_name, bestPercent, killed, kill_time, pull_count]})
    print(return_dict)
    return return_dict

def check_report(report_id:str):
    url = "https://www.fflogs.com/api/v2/client/"
    payload = "{\"query\":\"query reportData($report:String!) {\\n\\treportData {\\n\\t\\treport(code: $report) {\\n\\t\\t\\tfights{\\n\\t\\t\\t\\tlastPhase\\n\\t\\t\\t\\tkill\\n\\t\\t\\t\\tencounterID\\n\\t\\t\\t\\tfightPercentage\\n\\t\\t\\t\\tlastPhaseIsIntermission\\n\\t\\t\\t\\tlastPhaseAsAbsoluteIndex\\n\\t\\t\\t}\\n\\n\\t\\t\\t}\\n\\t\\t\\t}\\n\\t\\t}\\n\\n\",\"operationName\":\"reportData\",\"variables\":{\"report\":\"" + report_id + "\"}}"
    headers = {
        "Content-Type": "application/json",
        "Authorization": "Bearer " + bearer_token 
    }

    response = requests.request("POST", url, data=payload, headers=headers)
    print(response.text)
    contents = response.json()
    print(contents.keys())
    for key in contents.keys():
        if key == 'errors':
            return ["error"]
    data = contents['data']['reportData']['report']['fights']
    return data

def earliest_clear_date(first_name, last_name, world):
    url = "https://www.fflogs.com/api/v2/client/"
    name = f"{first_name} {last_name}"

    payload = "{\"query\":\"query characterData(\\n\\t$name: String!\\n\\t$serverSlug: String!\\n) {\\n\\tcharacterData {\\n\\t\\tcharacter(\\n\\t\\t\\tname: $name\\n\\t\\t\\tserverSlug: $serverSlug\\n\\t\\t\\tserverRegion: \\\"NA\\\"\\n\\t\\t) {\\n\\t\\t\\tSB_Ucob: encounterRankings(encounterID: 19, partition:-1)\\n\\t\\t\\tSB_Uwu: encounterRankings(encounterID: 23, partition:-1)\\n\\t\\t\\tShB_Ucob: encounterRankings(encounterID: 1047, partition:-1)\\n\\t\\t\\tShB_Uwu: encounterRankings(encounterID: 1048, partition:-1)\\n\\t\\t\\tShB_Tea: encounterRankings(encounterID: 1050, partition:-1)\\n\\t\\t\\tEw_Ucob: encounterRankings(encounterID: 1060, partition:-1)\\n\\t\\t\\tEw_Uwu: encounterRankings(encounterID: 1061, partition:-1)\\n\\t\\t\\tEw_Tea: encounterRankings(encounterID: 1062, partition:-1)\\n\\t\\t\\tEw_Dsr: encounterRankings(encounterID: 1065, partition:-1)\\n\\t\\t\\tEw_Top: encounterRankings(encounterID: 1068, partition:-1)\\n\\t\\t\\tVerse: encounterRankings(encounterID: 72, partition:-1, difficulty:101)\\n\\t\\t\\tPromise: encounterRankings(encounterID: 77, partition:-1, difficulty:101)\\n\\t\\t\\tAsphodelos: encounterRankings(encounterID: 82, partition:-1, difficulty:101)\\n\\t\\t\\tAbyssos: encounterRankings(encounterID: 87, partition:-1, difficulty:101)\\n\\t\\t}\\n\\t}\\n}\\n\",\"operationName\":\"characterData\",\"variables\":{\"name\":\"" + name + "\",\"serverSlug\":\"" + world + "\"}}"
    headers = {
        "Content-Type": "application/json",
        "Authorization": "Bearer " + bearer_token 
    }
    response = requests.request("POST", url, data=payload, headers=headers)

    print(response.text)
    content = response.json()
    data = content['data']['characterData']['character']
    if data is None:
        return None
    return_data = {}

    #check for ucob
    ucob_releases = ["SB_Ucob", "ShB_Ucob", "Ew_Ucob"]
    found = False
    for release in ucob_releases:
        if not found:
            if data[release].get('totalKills') != 0:
                return_data.update({"Ucob":release})
                found = True
    
    #check for uwu
    uwu_releases = ["SB_Uwu", "ShB_Uwu", "Ew_Uwu"]
    found = False
    for release in uwu_releases:
        if not found:
            if data[release].get('totalKills') != 0:
                return_data.update({"Uwu":release})
                found = True

    #check for tea
    tea_releases = ["ShB_Tea", "Ew_Tea"]
    found = False
    for release in tea_releases:
        if not found:
            if data[release].get('totalKills') != 0:
                return_data.update({"Tea":release})
                found = True

    #check dsr (with release date)
    dsr_releases = ["Ew_Dsr"]
    for release in dsr_releases:
        fights = data[release]['ranks']
        if len(fights) > 0:
            lowest_date = fights[0]['startTime']
            for fight in fights:
                time = fight['startTime']
                if time < lowest_date:
                    lowest_date = time
    if len(fights) > 0:
        return_data.update({'Dsr':lowest_date})
    
    #check Verse
    fights = data['Verse']['ranks']
    if len(fights) > 0:
        lowest_date = fights[0]['startTime']
        for fight in fights:
            time = fight['startTime']
            if time < lowest_date:
                lowest_date = time
    if len(fights) > 0:
        return_data.update({'Verse':lowest_date})

    #check Promise
    fights = data['Promise']['ranks']
    if len(fights) > 0:
        lowest_date = fights[0]['startTime']
        for fight in fights:
            time = fight['startTime']
            if time < lowest_date:
                lowest_date = time
    if len(fights) > 0:
        return_data.update({'Promise':lowest_date})

    #check Asphodelos
    fights = data['Asphodelos']['ranks']
    if len(fights) > 0:
        lowest_date = fights[0]['startTime']
        for fight in fights:
            time = fight['startTime']
            if time < lowest_date:
                lowest_date = time
    if len(fights) > 0:
        return_data.update({'Asphodelos':lowest_date})

    #check abyssos
    fights = data['Abyssos']['ranks']
    if len(fights) > 0:
        lowest_date = fights[0]['startTime']
        for fight in fights:
            time = fight['startTime']
            if time < lowest_date:
                lowest_date = time
    if len(fights) > 0:
        return_data.update({'Abyssos':lowest_date})





    return return_data


def add_field_raid(embed, data, fight_name):
    fight_time = data.get(fight_name)
    if fight_time is None:
        embed.add_field(name=fight_name, value=f"Did not clear")
        return


    fight_time = int(str(fight_time)[:10])

    days = math.trunc(abs(fight_time - RELEASE_DATES[fight_name]) / 86400 )

    embed.add_field(name=fight_name, value=f"Cleared {days} days after the release of the tier")
    return




    



bot.add_cog(FFlogs(bot))
bot.add_cog(ReportAnalysis(bot))
bot.add_cog(WipePoint(bot))
bot.add_cog(utility(bot))
bot.run(bot_token)

