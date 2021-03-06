import discord
from discord.ext import commands
from utils import response_building_util
from helpers import programmes_helper
from services import dm_service
import constants


class SendaccepteddmCommand(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def sendaccepteddm(self, ctx, uni_name: str, dry_run: str = None):

        if ctx.message.author.id != constants.administrator_user_id or not ctx.guild:
            await ctx.send(ctx.message.author.mention + ' You don\'t have permission to execute this command')
            return

        if uni_name == 'all':
            for uni in ('TUD', 'TUE'):
                await ctx.send(ctx.message.author.mention + f' Processing {uni}')
                await self.sendaccepteddm(ctx, uni, dry_run)
            return

        async with self.bot.db_conn.acquire() as connection:
            dm = dm_service.DMService(connection)

            if uni_name not in dm.University.__members__:
                raise commands.UserInputError

            send_messages = True

            if dry_run is not None:
                if dry_run == 'dry-run':
                    send_messages = False
                    await ctx.send(ctx.message.author.mention + f' dry run: not sending DMs')
                else:
                    raise commands.UserInputError

            university = dm.University[uni_name]

            channel_id = constants.accepted_channel_id
            message_id = constants.accepted_message_id

            channel = self.bot.get_channel(channel_id)
            message = await channel.fetch_message(message_id)

            if university == dm.University.TUD:
                target_emoji_name = 'TUD'
            elif university == dm.University.TUE:
                target_emoji_name = 'TuE'
            else:
                raise commands.UserInputError

            reaction = None
            for curr_reaction in message.reactions:
                if curr_reaction.custom_emoji and curr_reaction.emoji.name == target_emoji_name:
                    reaction = curr_reaction
                    break

            users = await reaction.users().flatten()

            await ctx.send(ctx.message.author.mention + f' Sending DMs to {len(users)} users...')

            results = {
                'success': [],
                'not-server-member': [],
                'unhandled-exception': [],
                'unknown-programme': [],
                'rank-already-set': [],
                'dm-status-not-null': [],
                'cannot-send-dm': [],
            }

            for member in users:
                if not isinstance(member, discord.Member):
                    results['not-server-member'].append(member)
                    continue

                programme_id = await dm.get_member_programme(member, university)

                if not programme_id:
                    results['unknown-programme'].append(member)
                    continue

                try:
                    key = await dm.send_programme_rank_dm(
                        member, programmes_helper.programmes[programme_id], send_messages, results)

                    if key:
                        results['success'].append(member)
                except Exception as e:
                    print(f'an error occurred while sending message to {member.name}: {str(e)}')
                    results['unhandled-exception'].append(member)

        await ctx.send(ctx.message.author.mention + f' Done sending DMs, '
                                                    f'{len(users) - len(results["success"])} skipped')

        if not results['success']:
            return

        results_embed = discord.Embed(title=f".sendaccepteddm results: {uni_name}", color=0x36bee6)

        user_groups = dict()

        for key in results.keys():
            user_groups[key] = list(map(lambda u: f'`{u.name}{f" ({u.id})" if key == "not-server-member" else ""}`',
                                        results[key]))

        response_building_util.build_embed_groups(results_embed, user_groups)

        if dry_run:
            results_embed.set_footer(text='dry run: not sending DMs')

        dm_channel = await ctx.message.author.create_dm()
        await dm_channel.send(embed=results_embed)

    @sendaccepteddm.error
    async def info_error(self, ctx, error):
        user = ctx.message.author
        if isinstance(error, commands.UserInputError):
            await ctx.send(user.mention + ' Invalid arguments. Usage: `.sendaccepteddm <all/TUD/TUE> [dry-run]`')
        else:
            await ctx.send(user.mention + ' An unexpected error occurred')
            raise


def setup(bot):
    bot.add_cog(SendaccepteddmCommand(bot))
