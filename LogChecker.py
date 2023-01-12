from bot_token import bot_token, bearer_token
import requests
import discord
from discord.commands import option
import json

intents = discord.Intents.default()

bot = discord.Bot()

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user} (ID: {bot.user.id})")
    print("------")

WORLDS = [
    #Aether
    "Adamantoise",
    "Cactuar",
    "Faerie",
    "Gilgamesh",
    "Jenova",
    "Midgardsormr", 
    "Sargatanas",
    "Siren",
    #Crystal
    "Balmung",
    "Brynhildr",
    "Coeurl",
    "Diablos",
    "Goblin",
    "Malboro",
    "Mateus",
    "Zalera",
    #Dynamis
    "Halicarnassus",
    "Maduin",
    "Marilith",
    "Seraph",
    #Primal
    "Behemoth",
    "Excalibur",
    "Exodus",
    "Famfrit",
    "Hyperion",
    "Lamia",
    "Leviathan",
    "Ultros"
]

@bot.slash_command(name="log_check")
@option("first_name", description="Players first name.")
@option("last_name", description="Players last name.")
@option("world", desciption="World the player is from", autocomplete=discord.utils.basic_autocomplete(WORLDS))
async def log_check(
    ctx: discord.ApplicationContext,
    first_name: str,
    last_name: str,
    world: str
):
    """Searches for information on the given user"""
    await ctx.respond(f"First name {first_name} Last Name {last_name} World {world}")
    await ctx.respond(check_fflogs(first_name, last_name, world))
    return

def check_fflogs(first_name:str, last_name:str, world:str):
    name = first_name + " " + last_name

    url = "https://www.fflogs.com/api/v2/client/"

    payload = "{\"query\":\"query {\\n\\tcharacterData {\\n\\t\\tcharacter(\\n\\t\\t\\tname: \\\"" + name + "\\\"\\n\\t\\t\\tserverSlug: \\\"" + world + "\\\"\\n\\t\\t\\tserverRegion: \\\"NA\\\"\\n\\t\\t) {\\n\\t\\t\\tCurrent_EW: zoneRankings(zoneID: 45)\\n\\t\\t\\tLegacy_EW: zoneRankings(zoneID: 43)\\n\\t\\t\\tCurrent_ShB: zoneRankings(zoneID: 32)\\n\\t\\t\\tLegacy_ShB: zoneRankings(zoneID: 30)\\n\\t\\t\\t\\n\\t\\t}\\n\\t}\\n}\\n\",\"variables\":{\"name\":\"Emilia Makise\",\"serverSlug\":\"Halicarnassus\",\"serverRegion\":\"NA\"}}"
    headers = {
        "Content-Type": "application/json",
        "Authorization": "Bearer " + bearer_token 
    }

    response = requests.request("POST", url, data=payload, headers=headers)


    contents = response.json()
    character = contents['data']['characterData']['character']
    message = {}
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
    ret = ""
    for fight, kill in message.items():
        ret += f"{fight} {kill} times\n"


    return ret
        



        
        
    





bot.run(bot_token)

