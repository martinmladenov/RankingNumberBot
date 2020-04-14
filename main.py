import discord
import datetime
import os

client = discord.Client()


@client.event
async def on_message(message):
    content = message.content.lower()

    if ('when' in content or 'where' in content or 'time' in content) and \
            ('rank' in content or 'result' in content or 'score' in content):

        if message.author == client.user:
            return

        print(message.channel.name + ' | ' + message.author.name + ': ' + message.content)
        print('sending!')

        # now = datetime.datetime.now(tz=datetime.timezone.utc)
        #
        # release = datetime.datetime(2020, 4, 14, hour=22, tzinfo=datetime.timezone.utc)
        #
        # seconds = (release - now).total_seconds()

        await message.channel.send(message.author.mention +
                                   ' The ranking numbers for the Numerus clausus programmes will be released on '
                                   '15 April at around **0:00 CEST** on Studielink!\n' +
                                   f'Time remaining: **RESULTS OUT NOW! CHECK STUDIELINK!**')


client.run(os.environ['DISCORD_SECRET'])