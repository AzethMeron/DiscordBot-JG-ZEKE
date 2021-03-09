
import os
import os.path
import file

# by Jakub Grzana

guilddir = ".database"

guild_envs = dict()

def NewUserData():
    output = dict()
    output['messages'] = 0
    output['warnings'] = []
    return output

def NewGuildEnvironment():
    output = dict()
    output['debug_channel'] = None
    output['moderation'] = dict()
    output['moderation']['channel'] = None
    output['moderation']['unclosed_cases'] = []
    output['moderation']['archive'] = None
    output['users'] = dict()
    output['pic_post'] = dict()
    output['supported_languages'] = { '🇵🇱' : 'pl', 
     '🇬🇧' : 'en', 
     '🇺🇸' : 'en'
    }
    return output
    
def LoadGuildEnvironment(guild):
    if not os.path.isdir(guilddir):
        os.mkdir(guilddir)
    filepath = guilddir + "/" + str(hash(guild.id)) + ".bse"
    if not os.path.isfile(filepath):
        guild_envs[guild.id] = NewGuildEnvironment()
    else:
        guild_envs[guild.id] = file.Load(filepath)
        tmp = NewGuildEnvironment()
        for key in tmp:
            if key not in guild_envs[guild.id]:
                guild_envs[guild.id][key] = tmp[key]
        
def SaveGuildEnvironment(guild):
    if not os.path.isdir(guilddir):
        os.mkdir(guilddir)
    filepath = guilddir + "/" + str(hash(guild.id)) + ".bse"
    file.Save(filepath,guild_envs[guild.id])

def GetGuildEnvironment(guild):
    if guild.id in guild_envs:
        return guild_envs[guild.id]
    else:
        LoadGuildEnvironment(guild)
        return guild_envs[guild.id]

def GetUserEnvironment(local_env, user):
    if hash(user.id) in local_env['users']:
        user_env = local_env['users'][hash(user.id)]
        # updating old user-data
        tmp = NewUserData()
        for key in tmp:
            if key not in user_env:
                user_env[key] = tmp[key]
        return user_env
    else:
        local_env['users'][hash(user.id)] = NewUserData()
        return local_env['users'][hash(user.id)]