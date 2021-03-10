
import data
import log

# by Jakub Grzana

async def Pass(bot, local_env, message):
    try:
        user_env = data.GetUserEnvironment(local_env, message.author)
        user_env['messages'] = user_env['messages'] + 1
    except Exception as e:
        await log.Error(bot, e, message.guild, local_env, { 'message' : message } )