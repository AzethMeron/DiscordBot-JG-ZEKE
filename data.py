
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
    output['moderation']['nagging'] = None
    output['moderation']['unclosed_cases'] = []
    output['moderation']['archive'] = None
    output['moderation']['verbose_warnings'] = True
    output['moderation']['WARNING_LENGTH_IN_DAYS'] = 28
    output['moderation']['WARNINGS_TO_NAG'] = 3
    output['users'] = dict()
    output['pic_post'] = dict()
    output['supported_languages'] = { '🇵🇱' : 'pl', 
     '🇬🇧' : 'en', 
     '🇺🇸' : 'en'
    }
    return output
    
def RecursiveDictUpdate(dict_data, dict_temp):
    for key in dict_temp:
        if type(dict_temp[key]) == type(dict()):
            if key not in dict_data:
                dict_data[key] = dict()
            RecursiveDictUpdate(dict_data[key], dict_temp[key])
        else:
            if key not in dict_data:
                dict_data[key] = dict_temp[key]

def LoadGuildEnvironment(guild):
    if not os.path.isdir(guilddir):
        os.mkdir(guilddir)
    filepath = guilddir + "/" + str(hash(guild.id)) + ".bse"
    if not os.path.isfile(filepath):
        guild_envs[guild.id] = NewGuildEnvironment()
    else:
        guild_envs[guild.id] = file.Load(filepath)
        RecursiveDictUpdate(guild_envs[guild.id], NewGuildEnvironment())
        
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
        RecursiveDictUpdate(user_env, NewUserData()) # Well actually it is required, cause LoadGuildEnvironment won't update user data :/ Looks like it is one of weakpoints of this bot
        return user_env
    else:
        local_env['users'][hash(user.id)] = NewUserData()
        return local_env['users'][hash(user.id)]

def StripUsersData(local_env, members):
    local_env['users'] = { hash(member.id) : GetUserEnvironment(local_env, member) for member in members }