from discord.ext import commands, tasks
from discord import app_commands
from discord.utils import get
from discord import FFmpegPCMAudio
import discord
import asyncio

import time
from utils.utils import *

token = get_token()

tree, client = get_information()

description = {
    "help": ([],"顯示所有功能"),
    "reply": (["nick_name"], "跟輸入的名字say hi"),
    "member_status": (["member"], "顯示查詢的成員狀態"),
    "serveremoji": ([], "顯示伺服器擁有的emoji名稱以及id"),
    "news": (["choices"], "隨機10條查詢最近新聞，請輸入: "),
    "play": (["query"], "播放歌曲, query輸入要搜尋的歌曲, 將會在youtube幫您搜尋並且播放"),
    "stop": ([], "終止播放歌曲"),
    "pause": ([], "暫停播放歌曲"),
    "resume": ([], "繼續播放歌曲"),
    "next": ([], "播放下一首歌曲"),
    "list": ([], "顯示目前所有歌曲"),
    "leave": ([], "請機器人人離開 <:smiling_face_with_tear:129394>"),
    "recommand": ([], "<:musical_note:127925>推薦歌單"),
}

@tree.command(name="help", description=description["help"][1])
async def self(interaction:discord.Interaction):
    emoji_fire = "<:fire:128293>"
    embed = discord.Embed(
        title="help",
        color=discord.Color.blurple(),
        description='以下是所有功能的指令方法以及說明文字 {0}'.format(emoji_fire)
    )

    for key in description.keys():
        args = " ".join(["`[{0}]`".format(arg) for arg in description[key][0]])
        description_context = description[key][1]
        embed.add_field(name="\/{0} {1}".format(key, args), value="{0}".format(description_context), inline=False)
    await interaction.response.send_message(embed=embed)

@tree.command(name="reply", description=description["reply"][1]) 
async def self(interaction: discord.Interaction, nick_name:str):
    print("interaction.response:{}".format(interaction.response))
    await interaction.response.send_message("Hi {0}!".format(nick_name))

@tree.command(name="member_status", description=description["member_status"][1]) 
async def self(interaction: discord.Interaction, member:discord.Member):
    member_real = client.get_member(member.name)
    reply_msg = "姓名:{0} 目前狀態: {1}".format(
        member_real.name,
        member_real.raw_status,
    )
    await interaction.response.send_message(reply_msg)

@tree.command(name="serveremoji", description=description["serveremoji"][1])
async def self(interaction: discord.Interaction):
    reply_msg = ""
    counter = 1
    for emoji in interaction.guild.emojis:
        reply_msg += "<:{0}:{1}>|".format(emoji.name, emoji.id)
        if counter % 5 == 0:
            reply_msg += '\n'
        counter += 1
        print(emoji.name, emoji.id)
    await interaction.response.send_message(reply_msg)

options = {
    "商業":"business",
    "娛樂":"entertainment",
    "一般":"general",
    "健康":"health",
    "科學":"science",
    "體育":"sports",
    "科技":"technology",
}

@tree.command(name="news", description=description["news"][1] + " {}".format("/".join([key for key in options.keys()])))
@app_commands.choices(choices=[
        app_commands.Choice(name="商業", value="business"),
        app_commands.Choice(name="娛樂", value="entertainment"),
        app_commands.Choice(name="一般", value="general"),
        app_commands.Choice(name="健康", value="health"),
        app_commands.Choice(name="科學", value="science"),
        app_commands.Choice(name="體育", value="sports"),
        app_commands.Choice(name="科技", value="technology"),
        ])
async def self(interaction: discord.Interaction, choices: app_commands.Choice[str]):
    global client
    category = choices.value
    news_res = get_news(category)
    # print(interaction.response)
    last_embed = discord.Embed(
        title="本次搜尋結果",
        color=discord.Color.blurple(),
        description="以下顯示本次所有的新聞標題及連結",
    )
    pages = []
    for news_report in news_res:
        embed = discord.Embed(
            title=news_report['title'],
            url=news_report['url'],
            color=discord.Color.blurple(),
            description=news_report['description'],
        )
        embed.set_image(url=news_report['image'])
        embed.set_footer(text="pages:{0}/{1}".format(news_res.index(news_report) + 1, len(news_res)))

        last_embed.add_field(
            name="{0}.{1}".format(news_res.index(news_report) + 1, news_report['title']),
            value="[前往新聞網頁]({0})".format(news_report['url']),
            inline=False
        )
        pages.append(embed)

    if len(pages) == 0:
        await interaction.response.send_message("目前與伺服器暫無回應")
        return
    await interaction.response.send_message("您選擇的項目是:{0}".format(choices.name))
    channel, message = await pages_task(interaction.channel_id, pages)
    await channel.send(embed=last_embed)
    await message.clear_reactions()

music_flag = {}
now_playing = ""
music_list = {}
tasks_table = {}

@tasks.loop(seconds=5.0)
async def music_loop():
    # TODO: 還沒做出多伺服器版本, 包含get_channel的選擇
    global now_playing
    FFMPEG_OPTS = {
        'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
        'options': '-vn'
    }
    textChannel = client.get_channel("Please replace this space to your message channel id (digital)")

    for voice in client.voice_clients:
        if len(music_list[str(voice.guild.id)]) > 0 and not voice.is_playing():
            info, source, title = music_list[str(voice.guild.id)].pop(0)
            now_playing = title
            print(now_playing)
            voice.play(FFmpegPCMAudio(source=source, **FFMPEG_OPTS), after=lambda e: print())
            music_flag[voice.guild.id] = True
            await textChannel.send("接下來為您播放的是:{0}".format(title))


def after(voice:discord.VoiceClient):
    global music_flag
    music_flag[voice.guild.id] = False
    print("done.{0}".format(music_flag[voice.guild.id]))

@tree.command(name="play", description=description["play"][1])
async def self(interaction: discord.Interaction, query:str):
    global music_flag, now_playing
    msg_info = {
        'channel_id': interaction.channel_id,
        'user': interaction.user.name,
        'guild': interaction.guild_id,
    }
    FFMPEG_OPTS = {
        'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
        'options': '-vn'
    }

    await interaction.response.send_message("處理中...")
    member = client.get_member(msg_info['user'])
    textChannel = client.get_channel(msg_info['channel_id'])

    await client.join(member, textChannel)

    info, source, title = search(query)
    voice = [voice_client if voice_client.guild.id == msg_info['guild'] else None for voice_client in client.voice_clients][0]

    if str(voice.guild.id) not in music_list.keys():
        music_list[str(voice.guild.id)] = []

    if voice.is_playing():
        music_list[str(voice.guild.id)].append((info, source, title))
        await textChannel.send("已經開始播放歌曲了! 先將你的歌曲 {0} 儲存到點播歌單囉!<:fire:128293>".format(title))
        return

    music_flag[str(voice.guild.id)] = True
    now_playing = title
    voice.play(FFmpegPCMAudio(source=source, **FFMPEG_OPTS), after=after(voice))
    if not music_loop.is_running():
        music_loop.start()
    # print("voice flag:", voice.is_playing())
    await textChannel.send("接下來為您播放的是:{0}".format(title))

@tree.command(name="stop", description=description["stop"][1])
async def self(interaction: discord.Interaction):
    voice = [voice_client if voice_client.guild.id == interaction.guild_id else None for voice_client in client.voice_clients][0]
    if music_loop.is_running():
        music_loop.cancel()
    voice.stop()
    await interaction.response.send_message(f"已停止播放{now_playing}")

@tree.command(name="pause", description=description["pause"][1])
async def self(interaction: discord.Interaction):
    voice = [voice_client if voice_client.guild.id == interaction.guild_id else None for voice_client in client.voice_clients][0]
    if music_loop.is_running():
        music_loop.cancel()
    voice.pause()
    await interaction.response.send_message(f"已暫停播放{now_playing}")

@tree.command(name="resume", description=description["resume"][1])
async def self(interaction: discord.Interaction):
    voice = [voice_client if voice_client.guild.id == interaction.guild_id else None for voice_client in client.voice_clients][0]
    voice.resume()
    if not music_loop.is_running():
        music_loop.start()
    await interaction.response.send_message(f"繼續撥放{now_playing}")

@tree.command(name="next", description=description["next"][1])
async def self(interaction: discord.Interaction):
    await interaction.response.send_message("還在測試中")

@tree.command(name="list", description=description["list"][1])
async def self(interaction: discord.Interaction):
    emoji_fire = "<:fire:128293>"
    emoji_music = "<:musical_note:127925>"
    embed = discord.Embed(
        title="歌曲列表",
        color=discord.Color.blurple(),
        description='以下是點播歌單 {0}{0}{0}'.format(emoji_fire)
    )

    for info, source, title in music_list[str(interaction.guild_id)]:
        embed.add_field(name="{0}.".format(music_list[str(interaction.guild_id)].index((info, source, title)) + 1), value=title, inline=False)
    await interaction.response.send_message(embed=embed)

@tree.command(name="leave", description=description["leave"][1])
async def self(interaction: discord.Interaction):
    await interaction.response.send_message("呼叫機器人人...")
    member = client.get_member(interaction.user.name)
    channel = client.get_channel(interaction.channel_id)
    await client.leave(member, channel)

@tree.command(name="recommand", description=description["recommand"][1])
@app_commands.choices(choices=[
        app_commands.Choice(name="華語", value="華語"),
        app_commands.Choice(name="西洋", value="西洋"),
        app_commands.Choice(name="日語", value="日語"),
        app_commands.Choice(name="韓語", value="韓語"),
        app_commands.Choice(name="台語", value="台語"),
        app_commands.Choice(name="粵語", value="粵語"),
        ])
async def self(interaction: discord.Interaction, choices: app_commands.Choice[str]):
    territory = choices.value
    await interaction.response.send_message("查詢中...")
    logo = {
        'kkbox': 'https://ssl.kkbox.com/tw/images/kklogo/kkbox.png',
        'naver': 'https://keedan.com/track/files/2021/12/122.jpeg',
    }
    channel = client.get_channel(interaction.channel_id)

    result = recommand_kkbox(territory)
    embed = discord.Embed(
        title="{0}歌曲推薦".format(choices.name),
        url="https://kma.kkbox.com/charts/",
        color=discord.Color.blurple(),
        description="以下是來自kkbox的本日推薦{0}歌單".format(choices.name),
    )
    embed.set_thumbnail(url=logo['kkbox'])
    for track_title, image, artist, song_url, release_date in result:
        id = result.index((track_title, image, artist, song_url, release_date)) + 1
        embed.add_field(
            name="{0}.{1} - {2}".format(
                id,
                track_title,
                artist
            ),
            value="[專輯封面]({0})".format(image),
            inline=False
        )
    await channel.send(embed=embed)

client.run(token)
