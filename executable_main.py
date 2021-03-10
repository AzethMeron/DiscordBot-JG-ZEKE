
import os 
import discord # Discord API
from discord.ext import tasks
from discord.ext import commands
from dotenv import load_dotenv # ENV vars
from discord.ext.commands import has_permissions, MissingPermissions
import traceback

# by Jakub Grzana

load_dotenv() # load environmental variables from file .env

###################################################################
# REQUIREMENTS. Created using programs & libraries:
# Python 3.9.0
# nltk 3.5
# Discord API for python 1.6.0 (REQUIRES DISCORD_TOKEN)
# python-dotenv 0.15.0
# deep-translator 1.4.1
# detectlanguage 1.4.0 (REQUIRES DETECT_LANGUAGE_TOKEN)
# profanity-check 1.0.3
# Joeclinton1's fork of google-images-download
###################################################################

import data
import log
import hate
import translator
import levels
import pic_poster
import temp
from discord.ext.commands import CommandNotFound

version = "JG Zeke bot\n\
Version 0.0.1"

intents = discord.Intents.default()
intents.members = True
DiscordClient = commands.Bot(command_prefix='jg',intents=intents) # create client of discord-bot

################################### INTERNAL ###################################

@DiscordClient.event
async def on_error(event, *args, **kwargs):
    print("UNHANDLED EXCEPTION")
    print(event)
    print(traceback.format_exc())
    
@DiscordClient.event
async def on_command_error(ctx, error):
    await ctx.message.reply(str(error))
  
def cmd_error(reason):
    return f'Command error occured\n\
    Reason: {reason}'
    
async def cmd_results(ctx,result):
    if result[0]:
        await ctx.message.add_reaction('👍')
    else:
        await ctx.message.reply(cmd_error(result[1]))

################################################################################


#################################### TIMER #####################################

async def save_guild_data(bot, local_env, guild, minute):
    data.SaveGuildEnvironment(guild)

# ( minutes, func(bot, local_env, guild, minute) )
# minutes < 100000
Timers = []
Timers.append( (60, hate.RemoveOutdatedWarnings) )
Timers.append( (1440, hate.NagModerators) )
Timers.append( (60, save_guild_data) )
Timers.append( (1, pic_poster.Pass) )

minute = -1
@tasks.loop(minutes=1)
async def each_minute():
    global minute
    # purge temporary dir, once per day
    if abs(minute) % 1440 == 180:
        print("Purging temporary directory")
        temp.PurgeTempDir()
    # Timers
    for (m,func) in Timers:            
        if abs(minute) % m == 0:
            for guild in DiscordClient.guilds:
                local_env = data.GetGuildEnvironment(guild)
                try:
                    await func(DiscordClient, local_env, guild, minute)
                except Exception as e:
                    await log.Error(DiscordClient, e, guild, local_env, { 'minute': minute } )
                    print("Exception in each_minute: " + str(e))
    minute = minute + 1 % 100000

################################################################################


################################## TRIGGERS ####################################

@DiscordClient.event
async def on_member_join(member):
    local_env = data.GetGuildEnvironment(member.guild)
    if hash(memeber.id) not in local_env['users']:
        local_env['users'][hash(member.id)] = data.NewUserData()

@DiscordClient.event
async def on_message(message):
    if message.author.bot:
        return
    # enforce execution of commands
    await DiscordClient.process_commands(message)
    # guild variable
    local_env = data.GetGuildEnvironment(message.guild)
    try:
        await levels.Pass(DiscordClient,local_env, message)
        await hate.Pass(DiscordClient,local_env,message) # takes a lot of time, should be done last
    except Exception as e:
        await log.Error(DiscordClient, e, message.guild, local_env, { 'message' : message } )
    
@DiscordClient.event
async def on_reaction_add(reaction, user):
    if user.bot:
        return 
    #print(reaction.emoji)
    local_env = data.GetGuildEnvironment(reaction.message.guild)
    try:
        await translator.Pass(DiscordClient, local_env,reaction,user)
    except Exception as e:
        await log.Error(DiscordClient, e, reaction.message.guild, local_env, { 'reaction' : reaction, 'user' : user } )

###########################################################################


################################ GENERIC ##################################

@DiscordClient.command(name='save', help="Save data of this server (setup, userdata, warnings and so on)")
@has_permissions(administrator=True)
async def cmd_save(ctx):
    local_env = data.GetGuildEnvironment(ctx.guild)
    try:
        data.SaveGuildEnvironment(ctx.guild)
        result = (True,None)
        await cmd_results(ctx,result)
    except Exception as e:
        await log.Error(DiscordClient, e, ctx.guild, local_env, {'context' : ctx} )
        
@DiscordClient.command(name='version', help="Display version of bot")
async def cmd_version(ctx):
    try:
        await ctx.message.reply(version)
    except Exception as e:
        await log.Error(DiscordClient, e, ctx.guild, local_env, {'context' : ctx} )

###########################################################################


############################### PIC POSTER ################################

@DiscordClient.command(name='pic_post_add', help="Add new pic_poster")
@has_permissions(administrator=True)
async def cmd_pic_post_add(ctx, internal_name, timer: int, keyword):
    local_env = data.GetGuildEnvironment(ctx.guild)
    try:
        result = pic_poster.AddPicPoster(DiscordClient, local_env, ctx.guild, internal_name, timer, ctx.channel.id, keyword.replace("_"," "))
        await cmd_results(ctx,result)
    except Exception as e:
        await log.Error(DiscordClient, e, ctx.guild, local_env, { 'internal_name' : internal_name} )
        
@DiscordClient.command(name='pic_post_remove', help="Remove existing pic_poster")
@has_permissions(administrator=True)
async def cmd_pic_post_remove(ctx, internal_name):
    local_env = data.GetGuildEnvironment(ctx.guild)
    try:
        result = pic_poster.RemovePicPoster(DiscordClient, local_env, ctx.guild, internal_name)
        await cmd_results(ctx,result)
    except Exception as e:
        await log.Error(DiscordClient, e, ctx.guild, local_env, { 'internal_name' : internal_name} )
    
@DiscordClient.command(name='pic_post_keyword_add', help="Add to existing pic_poster keyword to search for")
@has_permissions(administrator=True)
async def cmd_pic_post_keyword_add(ctx, internal_name, keyword):
    local_env = data.GetGuildEnvironment(ctx.guild)
    try:
        result = pic_poster.AddSearchWord(DiscordClient, local_env, ctx.guild, internal_name, keyword.replace("_"," "))
        await cmd_results(ctx,result)
    except Exception as e:
        await log.Error(DiscordClient, e, ctx.guild, local_env, { 'internal_name' : internal_name} )
        
@DiscordClient.command(name='pic_post_keyword_remove', help="Remove keyword from existing pic_poster")
@has_permissions(administrator=True)
async def cmd_pic_post_keyword_remove(ctx, internal_name, keyword):
    local_env = data.GetGuildEnvironment(ctx.guild)
    try:
        result = pic_poster.RemoveSearchWord(DiscordClient, local_env, ctx.guild, internal_name, keyword.replace("_"," "))
        await cmd_results(ctx,result)
    except Exception as e:
        await log.Error(DiscordClient, e, ctx.guild, local_env, { 'internal_name' : internal_name} )
        
################################################################################


################################## MODERATION ##################################

@DiscordClient.command(name='mode_get', help="Get warnings of user")
@has_permissions(administrator=True)
async def cmd_mode_get(ctx, user):
    local_env = data.GetGuildEnvironment(ctx.guild)
    try:
        result = await hate.GetUserWarnings(local_env, ctx.message.mentions[0], ctx.message)
        await cmd_results(ctx,result)
    except Exception as e:
        await log.Error(DiscordClient, e, ctx.guild, local_env, {} )
    
@DiscordClient.command(name='mode_warn', help="Give warning to user")
@has_permissions(administrator=True)
async def cmd_mode_warn(ctx, user_id, reason):
    local_env = data.GetGuildEnvironment(ctx.guild)
    try:
        result = await hate.AddWarning(local_env, ctx.message.mentions[0], reason.replace("_"," "))
        await cmd_results(ctx,result)
    except Exception as e:
        await log.Error(DiscordClient, e, ctx.guild, local_env, {} )
    
@DiscordClient.command(name='mode_channel', help="Set this channel as moderation channel")
@has_permissions(administrator=True)
async def cmd_mode_channel(ctx):
    local_env = data.GetGuildEnvironment(ctx.guild)
    try:
        result = hate.SetModChannel(local_env, ctx.channel)
        await cmd_results(ctx,result)
    except Exception as e:
        await log.Error(DiscordClient, e, ctx.guild, local_env, {} )
    
@DiscordClient.command(name='mode_nagging', help="Set this channel as moderation channel")
@has_permissions(administrator=True)
async def cmd_mode_nagging(ctx):
    local_env = data.GetGuildEnvironment(ctx.guild)
    try:
        result = hate.SetNaggingChannel(local_env, ctx.channel)
        await cmd_results(ctx,result)
    except Exception as e:
        await log.Error(DiscordClient, e, ctx.guild, local_env, {} )
    
@DiscordClient.command(name='mode_archive', help="Set this channel as mod-archive channel")
@has_permissions(administrator=True)
async def cmd_mode_archive(ctx):
    local_env = data.GetGuildEnvironment(ctx.guild)
    try:
        result = hate.SetArchiveChannel(local_env, ctx.channel)
        await cmd_results(ctx,result)
    except Exception as e:
        await log.Error(DiscordClient, e, ctx.guild, local_env, {} )

@DiscordClient.command(name='mode_solve', help="Solve existing case")
@has_permissions(administrator=True)
async def cmd_mode_solve(ctx, case_id: int, confirmation: bool):
    local_env = data.GetGuildEnvironment(ctx.guild)
    try:
        result = await hate.CaseSolve(DiscordClient,local_env, case_id, confirmation)
        await cmd_results(ctx,result)
    except Exception as e:
        await log.Error(DiscordClient, e, ctx.guild, local_env, {} )
        
@DiscordClient.command(name='mode_purge', help="Remove all unclosed cases without solving them")
@has_permissions(administrator=True)
async def cmd_mode_purge(ctx):
    local_env = data.GetGuildEnvironment(ctx.guild)
    try:
        result = hate.PurgeUnclosedCases(local_env)
        await cmd_results(ctx,result)
    except Exception as e:
        await log.Error(DiscordClient, e, ctx.guild, local_env, {} )

@DiscordClient.command(name='mode_show_report', help="Show all users exceeding given number of warnings")
@has_permissions(administrator=True)
async def cmd_show_report(ctx, num: int):
    local_env = data.GetGuildEnvironment(ctx.guild)
    try:
        await ctx.channel.send( hate.RequestWarnReport(local_env, ctx.guild, num))
    except Exception as e:
        await log.Error(DiscordClient, e, ctx.guild, local_env, {} )

@DiscordClient.command(name='mode_disable', help="Purge uncloded cases and remove moderation channels")
@has_permissions(administrator=True)
async def cmd_mode_disable(ctx):
    local_env = data.GetGuildEnvironment(ctx.guild)
    try:
        result = hate.DisableModeration(local_env)
        await cmd_results(ctx,result)
    except Exception as e:
        await log.Error(DiscordClient, e, ctx.guild, local_env, {} )

@DiscordClient.command(name='mode_param_set', help="Set parameters for warning management")
@has_permissions(administrator=True)
async def cmd_mode_param_set(ctx, number_of_warning: int, length_in_days: int):
    local_env = data.GetGuildEnvironment(ctx.guild)
    try:
        result = hate.SetParameters(local_env, number_of_warning, length_in_days)
        await cmd_results(ctx,result)
    except Exception as e:
        await log.Error(DiscordClient, e, ctx.guild, local_env, {} )

################################################################################


################################# DEBUG TOOLS ##################################

@DiscordClient.command(name='debug', help="Debug, will be removed")
@has_permissions(administrator=True)
async def cmd_debug(ctx):
    local_env = data.GetGuildEnvironment(ctx.guild)
    print("Minute: " + str(minute))
    print("Last error: " + str(traceback.format_exc()))
    print(local_env)
        
@DiscordClient.command(name='channel', help="Debug, will be removed")
@has_permissions(administrator=True)
async def cmd_channel(ctx, channel_internal_name):
    local_env = data.GetGuildEnvironment(ctx.guild)
    try:
        local_env[channel_internal_name] = ctx.channel.id
        #print(local_env)
    except Exception as e:
        await log.Error(DiscordClient, e, ctx.guild, local_env, {'context' : ctx} )

################################################################################


################################# TRANSLATION ##################################

@DiscordClient.command(name='lang_add', help="Add emoji-to-translate")
@has_permissions(administrator=True)
async def cmd_lang_add(ctx,emoji,language):
    local_env = data.GetGuildEnvironment(ctx.guild)
    try:
        result = translator.AddEmojiTranslation(DiscordClient,local_env,emoji,language)
        await cmd_results(ctx,result)
    except Exception as e:
        await log.Error(DiscordClient, e, ctx.guild, local_env, { 'emoji' : emoji, 'language': language} )

@DiscordClient.command(name='lang_remove', help="Remove emoji-to-translate")
@has_permissions(administrator=True)
async def cmd_lang_remove(ctx,emoji):
    local_env = data.GetGuildEnvironment(ctx.guild)
    try:
        result = translator.RemoveEmojiTranslation(DiscordClient,local_env,emoji)
        await cmd_results(ctx,result)
    except Exception as e:
        await log.Error(DiscordClient, e, ctx.guild, local_env, { 'emoji' : emoji } )

################################################################################


################################ INITIALISATION ################################

@DiscordClient.event
async def on_ready():
    for guild in DiscordClient.guilds:
        data.LoadGuildEnvironment(guild)
        local_env = data.GetGuildEnvironment(guild)
        for member in guild.members:
            if hash(member.id) not in local_env['users']:
                local_env['users'][hash(member.id)] = data.NewUserData()
        
    each_minute.start()
    print("Initialisation finished")
    print(f'{DiscordClient.user} has connected to Discord!')
    print("Number of servers (guilds) bot is connected to: "+str(len(DiscordClient.guilds)))

DiscordClient.run(os.getenv('DISCORD_TOKEN'))