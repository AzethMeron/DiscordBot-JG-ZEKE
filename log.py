
import traceback
import file
import os
import os.path

# by Jakub Grzana

logdir = ".logs"

async def Error(bot, exception, guild, local_env, dict_args):
    print(traceback.format_exc())
    if not os.path.isdir(logdir):
        os.mkdir(logdir)
    try:
        filepath = logdir + '/' + str(hash(guild.id)) + '.log'
        # building err_mess
        err_mess = dict()
        err_mess['exception'] = exception
        err_mess['traceback'] = traceback.format_exc()
        for key in dict_args:
            err_mess[key] = dict_args[key]
        # string representation
        str_representation = ""
        for key in err_mess:
            str_representation = str_representation + key + ' : ' + str(err_mess[key]) + '\n'
        # saving
        if os.path.isfile(filepath):
            tmp = file.Load(filepath)
            str_representation = str_representation + '\n\n\n' + tmp
        file.Save(filepath,str_representation)
        # sending debug
        channel_id = local_env['debug_channel']
        if channel_id != None:
            channel = bot.get_channel(channel_id)
            await channel.send(err_mess['traceback'])
    except:
        print("Exception occured during error logging")
        print(traceback.format_exc())