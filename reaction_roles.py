
import log

def SetMessage(local_env, message):
    local_env['reaction_roles']['message'] = (message.channel.id, message.id)
    return (True, None)

def AddRole(local_env, emoji, role_mention_id):
    local_env['reaction_roles']['main'][emoji] = role_mention_id
    return (True, None)

def RemoveRole(local_env, emoji):
    if emoji in local_env['reaction_roles']['main']:
        del local_env['reaction_roles']['main'][emoji]
        return (True, None)
    else:
        return (False, "No reaction role found")

async def AddEmoji(bot, local_env, reaction, user):
    if reaction.message.author.bot:
        return
    try:
        reaction_channel_id = local_env['reaction_roles']['message'][0]
        reaction_message_id = local_env['reaction_roles']['message'][1]
        if reaction.message.channel.id == reaction_channel_id:
            if reaction.message.id == reaction_message_id:
                if reaction.emoji in local_env['reaction_roles']['main']:
                    role_id = local_env['reaction_roles']['main'][reaction.emoji]
                    guild = reaction.message.guild
                    role = guild.get_role(role_id)
                    await user.add_roles( role )
    except Exception as e:
        await log.Error(bot, e, reaction.message.guild, local_env, { 'reaction' : str(reaction.emoji), 'content': reaction.message.content } ) 

async def RemoveEmoji(bot, local_env, reaction, user):
    if reaction.message.author.bot:
        return
    try:
        reaction_channel_id = local_env['reaction_roles']['message'][0]
        reaction_message_id = local_env['reaction_roles']['message'][1]
        if reaction.message.channel.id == reaction_channel_id:
            if reaction.message.id == reaction_message_id:
                if reaction.emoji in local_env['reaction_roles']['main']:
                    role_id = local_env['reaction_roles']['main'][reaction.emoji]
                    guild = reaction.message.guild
                    role = guild.get_role(role_id)
                    await user.remove_roles( role )
    except Exception as e:
        await log.Error(bot, e, reaction.message.guild, local_env, { 'reaction' : str(reaction.emoji), 'content': reaction.message.content } ) 
