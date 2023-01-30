from bot_token import bot_token, bearer_token
import requests
import discord
from discord.ext import tasks, commands
from discord.commands import option 
import json
from urllib.parse import urlparse 
from data import WORLDS, ENCOUNTERS, PHASES, FIGHTS

intents = discord.Intents.default()

bot = discord.Bot()

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user} (ID: {bot.user.id})")
    print("------")

class FFlogs(commands.Cog):
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
        await ctx.send(check_fflogs_ult(first_name, last_name, world))
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
                body = f"Killed at {team[3]} with {team[4]} pulls"
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
                    if embed_data.get('kills') is None:
                        embed_data.update({'kills':1})
                    else:
                        embed_data['kills'] += 1
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
        ret += f"{fight} {kill} times\n"


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


bot.add_cog(FFlogs(bot))
bot.add_cog(ReportAnalysis(bot))

bot.run(bot_token)

