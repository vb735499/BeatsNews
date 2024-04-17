# BeatsNews   
### version 1.0
BeatsNews will provide you music stream on voice channel,  music recommend from kkbox top 10, and news delivery from local news.  

# Command of Services
1. /help : it will list all of command and describtion to message channel.
2. /reply [member]: say hello to the member.
3. /member_status [member]: check the member status. (Online, Offline ... etc.)
4. /serveremoji: list all icons avaliable on the gulid.
5. /news [choices]: Randomly quering recently news articles on the user's selected category.
6. /play [query]: join the voice channel of the user issuing the command and play music based on the keyword or URL input by the user.
7. /stop: elimate all of music in the list and stop the player to playing music.
8. /pause: pasue the currently playing music.
9. /resume: play the currently paused music.
10. /next: play next music in the list.
11. /list: list all music of the user's quering.
12. /leave: let the BeatsNewws leave the currently voice channel.
13. /recommand: recommand music from the KKBOX.


# Requirements
python >= 3.8.12  
## API Keys you need to create
[Discord Developer](https://discord.com/developers/applications?new_application=true): Go to discord developer page and creat a new application for bot. And you need generate `access_token` / `secret` two different token to access the bot application.
[News API](https://newsapi.org/): Go to Newsapi.org website to generate you own api key to access the news delivery service.
[KKBOX OpenAPI](https://developer.kkbox.com/#/signin): Go to developer.kkbox.com to generate a new `Clinet_id` and `Client_secret`.  
*Note: Remember to keep those keys/ids, we will used in later.*
