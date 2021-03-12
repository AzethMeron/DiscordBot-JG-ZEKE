
import data
import log
import random
import math

# by Jakub Grzana

##########################################################################

def exp_gain():
    return random.randint(10,25)

def exp_to_next_level(level):
    return int(70 * (level+1) * math.log(level+2))
    
##########################################################################

def LevelList(local_env, members):
    output = [ ( member, data.GetUserEnvironment(local_env, member)['lvl_module']['level'] ) for member in members ]
    output.sort(key = lambda item: -item[1] )
    return output
    
def RequestLevelList(local_env, members):
    output = "**Level Leaderboard**" + "\n"
    for item in LevelList(local_env, members):
        if item[1] > 0:
            output = output + str(item[0].display_name) + " - level " + str(item[1]) + "\n"  
        else:
            break
    return output

def SetVerbose(local_env, verbose):
    local_env['lvl_module_verbose'] = verbose
    return (True, None)

##########################################################################

async def Pass(bot, local_env, message):
    try:
        user_env = data.GetUserEnvironment(local_env, message.author)
        user_env['lvl_module']['messages'] += 1
        if not user_env['lvl_module']['send_message_in_this_minute']:
            user_env['lvl_module']['send_message_in_this_minute'] = True
            user_env['lvl_module']['exp'] += exp_gain()
            exp_required = exp_to_next_level(user_env['lvl_module']['level'])
            if (user_env['lvl_module']['exp'] - exp_required) >= 0:
                user_env['lvl_module']['exp'] -= exp_required
                user_env['lvl_module']['level'] += 1
                mention = f'<@{message.author.id}>'
                to_send = "Congratulations " + mention + "! You just advanced to " + str(user_env['lvl_module']['level']) + " level!"
                if local_env['lvl_module_verbose']:
                    await message.reply(to_send)
    except Exception as e:
        await log.Error(bot, e, message.guild, local_env, { 'message' : message } )
        
async def OneMinutePassed(bot, local_env, guild, minute):
    try:
        for member in guild.members:
            user_env = data.GetUserEnvironment(local_env, member)
            user_env['lvl_module']['send_message_in_this_minute'] = False
    except Exception as e:
        await log.Error(bot, e, guild, local_env, { } )