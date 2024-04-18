import configparser
import discord
from discord.ext import commands, tasks
from discord import app_commands
import random
from newsapi import NewsApiClient
from youtube_dl import YoutubeDL
import requests
import json
import asyncio

emoji_dict = {
    "musical_note":127925,
    "smiling_face_with_tear":129394,
    "fire":128293,
}

config = configparser.ConfigParser()
config.read('utils/config.ini')

def get_token():
    global config
    token = config.get('discord', 'access_token')
    return token

def get_information():
    global tree, client
    return tree, client

def random_choice():
    keys = list(emoji_dict.keys())
    result = ""
    for i in range(2):
        n = random.randint(0,len(keys) - 1)
        result += "<:{0}:{1}> ".format(
            keys[n],
            emoji_dict[keys[n]]
        )
    return result

def get_news(category:str):
    key = config.get('News_api', 'key')
    result = list()
    rs = requests.get(f'https://newsapi.org/v2/top-headlines?country=tw&category={category}&apiKey={key}')
    news_json = json.loads(rs.text)
    for article in news_json['articles']:
        result.append({
            'title': article['title'],
            'description': article['description'],
            'image': article['urlToImage'],
            'url': article['url'],
        })
    return result

@tasks.loop(seconds=5.0)
async def updateINFO():
    await client.update_members()

def search(query):
    opt = {
        'format': 'bestaudio',
        'yesplaylist': 'True',
    }
    with YoutubeDL(opt) as ydl:
        try:
            requests.get(query)
        except:
            info = ydl.extract_info(f"ytsearch:{query}", download=False)['entries'][0]
        else:
            info = ydl.extract_info(query, download=False)

    return (info, info['formats'][0]['url'], info['title'])

def recommand_kkbox(territory):
    category = -1
    rs = requests.get(f'https://kma.kkbox.com/charts/api/v1/daily/categories?terr=tw&type=newrelease')
    for data in rs.json()['data']:
        if data['category_name'] == territory:
            category = int(data['category_id'])
    rs = requests.get(f'https://kma.kkbox.com/charts/api/v1/daily?category={category}&limit=10&terr=tw&type=newrelease')
    print(rs.status_code)
    result = [(data['song_name'], data['cover_image']['small'], data['artist_name'], data['song_url'], data['release_date']) for data in rs.json()['data']['charts']['newrelease']]
    # print(result)
    return result

# TODO: change to button without reaction
async def pages_task(id, pages):
    channel = client.get_channel(id)
    message = await channel.send(embed=pages[0])

    await message.add_reaction('⏮')
    await message.add_reaction('◀')
    await message.add_reaction('▶')
    await message.add_reaction('⏭')

    index = 0
    emoji = ''
    try:
        while True:
            if emoji == '⏮':
                index = 0
            elif emoji == '◀' and index > 0:
                index -= 1
            elif emoji == '▶' and index < len(pages) - 1:
                index += 1
            elif emoji == '⏭':
                index = len(pages) - 1

            await message.edit(embed = pages[index])
            reaction, user = await client.wait_for('reaction_add', timeout = 180.0)

            if reaction == None or user == None:
                break
            if user != client.user:
                emoji = str(reaction.emoji)
                await message.remove_reaction(reaction.emoji, user)
    except asyncio.exceptions.TimeoutError as Te:
        print(Te)
        return channel, message

class agentClient(discord.Client):
    def __init__(self):
        super().__init__(intents=discord.Intents.all())
        global config
        self.synced = False
        self.members = {}

    @tasks.loop(seconds=5.0)
    async def update_members(self):
        for guild in self.guilds:
            for member in guild.members:
                self.members[member.name] = member

    async def on_ready(self):
        await self.wait_until_ready()
        if not self.synced:
            await tree.sync() #id: 855886229470707772
            self.synced = False
        print("start catch information.")
        self.update_members.start()
        channel_id = int(config.get('discord', 'reply_channel'))
        channel = self.get_channel(channel_id) 
        Online_Message = f'Hi! 我上線了 {self.user}'
        print(channel,  Online_Message)
        await channel.send(Online_Message)

    async def on_presence_update(self, before, after):
        emojis = random_choice()
        self.members[after.name] = after
        channel_id = int(config.get('discord', 'reply_channel'))
        if before.status is discord.Status.offline and after.status is discord.Status.online:
            channel = client.get_channel(channel_id)  # notification
            message = await channel.send(f'{after.name} 現在上線拉!')
            # await message.add_reaction("<:pokemonguakeda:987375184593948692>")
            for emoji in emojis.split(' '):
                if emoji in [' ', '']:
                    continue
                await message.add_reaction(emoji)

        if before.status is discord.Status.online and after.status is discord.Status.offline:
            channel = client.get_channel(channel_id)  # notification channel
            message = await channel.send(f'{after.name} 不~不要走 TAT!')
            await message.add_reaction("<:shark02:892762787066044416>")

    async def on_message(self, message):
        if message.author == self.user:
            return
        self.members[message.author.name] = message.author
        if message.content.startswith('/emoji'):
            sp_msg = message.content.split(' ')
            if len(sp_msg) < 3:
                return
            emoji = "你發的emoji是<:{0}:{1}> <:capoobigface:>".format(sp_msg[2], ord(sp_msg[1]))
            print("emoji number:{0}".format(ord(sp_msg[1])))
            await message.channel.send(emoji)
        if message.content.startswith('/join'):
            await self.join(self.members[message.author.name], message.channel)
        if message.content.startswith('/leave'):
            await self.leave(self.members[message.author.name], message.channel)
        if message.content.startswith('/channel_id'):
            await message.channel.send("頻道 {0} id:{1}".format(message.channel.name, message.channel.id))

    async def join(self, member, textChannel):
        # TODO: 可以改成更好的方式，如使用guild先找尋所有伺服器中有加入語音頻道的voice_clients

        is_connected = True if len(self.voice_clients) > 0 else False
        bot_voice_id = [voice_client.channel.id for voice_client in self.voice_clients]

        if(member.voice and is_connected): # 機器人已經加入伺服器的語音，但不確定是否是發送者的語音頻道
            channel = member.voice.channel
            # 在相同頻道
            if(member.voice.channel.id in bot_voice_id):
                await textChannel.send("Hi 我已經在這個頻道裡面了喔!")
                return
            # 加入發送者的語音頻道
            await textChannel.send("等我一下 馬上過去!<:horse:128052><:fire:128293><:fire:128293>")
            for voice_client in self.voice_clients:
                if voice_client.guild.id == member.guild.id:
                    await voice_client.move_to(channel)
                    break
        elif(member.voice and not is_connected): # 機器人還沒有加入伺服器的語音，而且發送者有加入頻道
            channel = member.voice.channel
            await channel.connect()
            await textChannel.send("Hi 你今天想聽甚麼?")
        else:
            await textChannel.send("你又沒加入語音頻道，我要去哪裡放歌給你聽呢? a(^Owo^)b")

    async def leave(self, member, textChannel):
        is_connected = True if len(self.voice_clients) > 0 else False
        bot_guild_id = [voice_client.guild.id for voice_client in self.voice_clients]

        if(is_connected and member.guild.id in bot_guild_id):
            await self.voice_clients[bot_guild_id.index(member.guild.id)].disconnect()
            await textChannel.send("我離開拉, 有需要再叫我!")
        else:
            await textChannel.send("Umm... 我沒加入過任何頻道ㄟ")

    def get_member(self, name):
        if name not in self.members.keys():
            return None
        return self.members[name]

client = agentClient()
tree = app_commands.CommandTree(client)
