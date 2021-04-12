
import translator
import profanity_check
import data
import log
import uuid
import datetime
from datetime import date

import file
import nltk
import lib_hate

####################################################################################################################################################
# by Jakub Grzana
# I'm very proud of this system. Though syntax for commands is trash
#
# Major features:
#     automated hate speech detection - programmed in BoolDetect and Detect functions. Uses profanity_check library, and my own implementation of Bag-of-Words model. 
#                                       For now, automated HS detection isn't precise at all. Training set for BoW was poor, and profanity_check is less than ideal for this purpose
#                                       But the system is here, and by using Tests list you can easily manage tests performed
#     reports on specific channel, to be reviewed - once bot detect HS, it creates a report which is then sent to local_env['moderation']['channel_unsolved_cases']
#                                       Then administrator can review this report, and decide whether it deserves a warning or not.
#     managing warnings - even with automated hate speech detection disabled, administration can manually add warnings to users
#                                       Then this system will automatically store them in memory, save, and remove after specific number of days.
#                                       All warnings are for programmed (fixed) time, and there's no distinction in weight. It's feature, not a bug.
#                                       Program will search for users exceeding number of allowed warnings, and will nag administration to take action
#                                       Timer for that is very long tho. 
#                                       Administration can requrest raport at any moment 
# Note this bot will NOT take any real actions. It is programmed to be support for administration, not to do their job. It would be kinda dangerous
# to give too many permission to bot. Thus, JG Zeke is purely advisor bot 
#
#
# Edit: Meh, user reports are kinda "hacked into" this bot, thus code got complicated :/
####################################################################################################################################################

###################################################################################
# profanity_check

def profanity_internal(text):
    if profanity_check.predict([text]) == [1]:
        return True
    return False

###################################################################################
# Bag-of-Words hate speech detection

def BagOfWordsClassifier(text, classifier, important_words):
    # preprocess message
    text = lib_hate.PreprocessMessage(text)
    # for performance gain: skip messages that are nearly empty after preprocessing
    if len(text) < 3: 
        return False
    # get features
    features = lib_hate.feature_extractor(text,important_words)
    # classify
    if classifier.classify(features) == 'hate':
        return True
    return False

###################################################################################

general_cl = file.Load(lib_hate.GetClassifierDir()+"general_classifier")
general_iw = file.Load(lib_hate.GetClassifierDir()+"general_important_words")

def GeneralBoW(text):
    return BagOfWordsClassifier(text, general_cl, general_iw)

###################################################################################


####################### HATE SPEECH DETECTION - HEADQUARTER #######################

# (name, bool_func(text), weight) weights are unused now
Tests = [ ("Profanity Check", profanity_internal, 50),
("General Hate Speech", GeneralBoW, 50) ]

def BoolParse(weight_results):
    return bool(round(weight_results))

def ParseWeight(results):
    weight = 0
    total_weight = 0
    for result in results:
        total_weight += result[2]
        if result[1]:
            weight += result[2]
    return round(weight / total_weight,1)

def BoolDetect(text):
    global Tests
    for test in Tests:
        if test[1](text):
            return True
    return False

def Detect(text):
    global Tests
    output = []
    for test in Tests:
        output.append( (test[0], test[1](text), test[2]) )
    return output
    
###################################################################################
# Internals

def MakeReport(report, display_name, user_name, guild, submitted_by):
    endline = "\n"
    link = f'https://discordapp.com/channels/{guild.id}/{report[1]}/{report[2]}'
    output =  "=============================================\n"
    output = output + f'**Case number** {report[0]}{endline}**Link to message**: {link}{endline}**Suspect**: {user_name} aka {display_name}{endline}{endline}**Content of message**: *"{report[3].replace(endline," ")}"*{endline}{endline}'
    if type(report[4]) == type([]):
        weight = ParseWeight(report[4])
        output = output + "**Hate speech scan results**: weighted " + str(weight) + "\n"
        for test in report[4]:
            output = output + test[0] + ": " + str(test[1]) + "\n"
    else:
        output = output + f'**Reported by user**: {str(submitted_by)} aka {submitted_by.display_name}'
    return output
    
def RequestWarnReport(local_env, guild, number):
    naughty_boy_list = [ (user, data.GetUserEnvironment(local_env,user)['warnings']) \
    for user in guild.members \
    if len(data.GetUserEnvironment(local_env,user)['warnings']) >= number ]
    naughty_boy_list.sort(key = lambda item: len(item[1]) )
    to_send = "**==================================**\n"
    to_send = to_send + f'**Daily report**: {date.today()}' + "\n"
    if len(naughty_boy_list) == 0:
        to_send = to_send + "There're no players exceeding safe number of warnings. Truly wonderful day it is!"
    for item in naughty_boy_list:
        to_send = to_send + str(item[0]) + " aka " + item[0].display_name + f': {len(item[1])} warnings' + "\n"
    return (to_send, len(naughty_boy_list))
    
async def CreateCase(local_env, message, test_results, mode_channel, submitted_by=None):
    sent = await mode_channel.send("This should be editted instantly")
    report = (sent.id, message.channel.id, message.id, message.content, test_results)
    await sent.edit( content=MakeReport(report, message.author.display_name, str(message.author), message.guild, submitted_by) )
    local_env['moderation']['unclosed_cases'].append(report)
    
def FindCaseOfMessage(local_env, channel_id, message_id):
    for item in local_env['moderation']['unclosed_cases']:
        if item[1] == channel_id:
            if item[2] == message_id:
                return item
    return None
    
###################################################################################

def SetModChannel(local_env, channel):
    if local_env['moderation']['channel_unsolved_cases'] != None:
        if len(local_env['moderation']['unclosed_cases']) > 0:
            return (False, "There's already active moderation channel with unclosed cases in it. Please solve them or purge before changing moderation channel")
    local_env['moderation']['channel_unsolved_cases'] = channel.id
    return (True, None)
    
def SetArchiveChannel(local_env, channel):
    local_env['moderation']['channel_archive'] = channel.id
    return (True, None)
   
def SetNaggingChannel(local_env, channel):
    local_env['moderation']['channel_autoreports'] = channel.id
    return (True, None)
    
def SetUserReportsChannel(local_env, channel):
    local_env['moderation']['channel_user_reports'] = channel.id
    return (True, None)

def PurgeUnclosedCases(local_env):
    local_env['moderation']['unclosed_cases'] = []
    return (True, None)
    
def DisableModeration(local_env):
    if local_env['moderation']['channel_unsolved_cases'] == None:
        return (False, "Moderation isn't enabled anyway")
    local_env['moderation']['channel_unsolved_cases'] = None
    local_env['moderation']['channel_autoreports'] = None
    local_env['moderation']['unclosed_cases'] = []
    local_env['moderation']['channel_archive'] = None
    return (True,None)
    
async def AddWarning(local_env, user, reason):
    warnings_to_nag = local_env['moderation']['warnings_to_nag']
    dte = date.today()
    user_env = data.GetUserEnvironment(local_env, user)
    user_env['warnings'].append( (dte,reason) )
    if local_env['moderation']['verbose_warnings']:
        if not user.dm_channel:
            await user.create_dm()
        num = len(user_env['warnings'])
        to_send = f'**Dear {user.display_name}**' + "\n" +\
        "I'm sad to report you got warning." + "\n" +\
        f'Reason: *"{reason}"*' + "\n" +\
        f'This is yours {num} warning ' 
        if num >= warnings_to_nag:
            to_send = to_send + "which means I will nag administration to deal with your case"
        to_send = to_send + "\n" + "No hard feelings"
        await user.send(to_send)
    return (True, None)
    
async def CaseSolve(bot, local_env, case_id, confirmation):
    # searching for case in unclosed_cases
    case = None
    for c in local_env['moderation']['unclosed_cases']:
        if c[0] == case_id:
            case = c
            break
    if case == None:
        return (False, "Case not found")
    # getting message in mode channel
    mode_channel_id = local_env['moderation']['channel_unsolved_cases']
    mode_channel = bot.get_channel(mode_channel_id)
    mode_message = await mode_channel.fetch_message(case[0])
    backup_content = mode_message.content
    # back-up in archive
    archive_id = local_env['moderation']['channel_archive']
    if archive_id != None:
        archive = bot.get_channel(archive_id)
        await archive.send(backup_content+"\n**Verdict**: "+str(confirmation))
    # removing case from unclosed_cases 
    if confirmation:
        # getting message that caused the problem
        hate_channel_id = case[1]
        hate_message_id = case[2]
        reason = "Hate speech detected in " + f'"{case[3]}"'
        try:
            hate_channel = bot.get_channel(hate_channel_id)
            hate_message = await hate_channel.fetch_message(hate_message_id)
        except:
            local_env['moderation']['unclosed_cases'].remove(c)
            return (False, "Failed to get message that violated rules. It's likely removed.\nWarning wasn't issued. Sadly you must deal with it on your own")
        # add warning to given user
        user = hate_message.author
        await AddWarning(local_env, user, reason )
        # attempt to remove hate message
        try:
            await hate_message.delete()
        except:
            pass
    await mode_message.edit(content="Case solved")
    local_env['moderation']['unclosed_cases'].remove(c)
    return (True, None)

async def GetUserWarnings(local_env, user, message):
    user_env = data.GetUserEnvironment(local_env, user)
    info = f'Informations about user {str(user)} aka {user.display_name}' + "\n"
    info = info + "Warnings: " + str(len(user_env['warnings'])) + "\n"
    for warn in user_env['warnings']:
        info = info + str(warn[0]) + ". Reason " + f'"{warn[1]}"' + "\n"
    author = message.author
    if author.dm_channel == None:
        await author.create_dm()
    await author.dm_channel.send(info)
    return (True, None)
    
def SetParameters(local_env, num, length, verbose_warnings):
    local_env['moderation']['warnings_to_nag'] = num
    local_env['moderation']['warnings_length_in_days'] = length
    local_env['moderation']['verbose_warnings'] = verbose_warnings
    return (True, None)
    
def SetDaysUntilInactive(local_env, num):
    local_env['moderation']['days_until_inactive'] = num
    return (True, None)
    
async def ReportMessage(bot, local_env, message_reporting, message_reported):
    if FindCaseOfMessage(local_env, message_reported.channel.id, message_reported.id) != None:
        return (True, None)
    mode_channel_id = local_env['moderation']['channel_user_reports']
    if mode_channel_id == None:
        return (False, "Sorry, reports are not enabled on this server")
    mode_channel = bot.get_channel(mode_channel_id) # connection to 
    await CreateCase(local_env, message_reported, None, mode_channel, message_reporting.author)
    return (True, None)

###################################################################################

# Report structure
# report[0] = id of message in moderation channel, which is also ID of case
# report[1] = id of channel in which message violated rules
# report[2] = id of message that violated rules
# report[3] = content that violated rules
# report[4] = test results (if made by bot) or None if submited by user

###################################################################################

async def Pass(bot, local_env, message):
    if len(message.content) < 5:
        return
    try:
        mode_channel_id = local_env['moderation']['channel_unsolved_cases']
        if mode_channel_id != None:
            text = message.content
            # Ensuring text is in english
            try:
                text = translator.EnsureEnglish(text)
            except Exception as e:
                pass
            # Gathering results
            test_results = Detect(text)
            hate = BoolParse( ParseWeight(test_results) )
            # hate detected
            if hate:
                mode_channel = bot.get_channel(mode_channel_id) # connection to 
                await CreateCase(local_env, message, test_results, mode_channel)
        
    except Exception as e:
        await log.Error(bot, e, message.guild, local_env, { 'content' : message.content } )
    
async def RemoveOutdatedWarnings(bot, local_env, guild, minute):
    try:
        warnings_length_in_days = local_env['moderation']['warnings_length_in_days']
        today = date.today()
        for member in guild.members:
            user_env = data.GetUserEnvironment(local_env, member)
            user_env['warnings'][:] = [ warn for warn in user_env['warnings'] if abs( (today - warn[0]).days ) < warnings_length_in_days ]
    except Exception as e:
        await log.Error(bot, e, guild, local_env, { } )

# Loop for nagging moderators
async def NagModerators(bot, local_env, guild, minute):
    try:
        if local_env['moderation']['channel_autoreports'] != None:
            warnings_to_nag = local_env['moderation']['warnings_to_nag']
            nagging_channel_id = local_env['moderation']['channel_autoreports']
            nagging_channel = bot.get_channel(nagging_channel_id)
            (to_send, num) = RequestWarnReport(local_env, guild, warnings_to_nag)
            if num == 0:
                return
            await nagging_channel.send(to_send)
    except Exception as e:
        await log.Error(bot, e, guild, local_env, { } )

async def SearchForInactiveChannels(bot, local_env, guild, minute):
    try:
        bot_member = guild.get_member(bot.user.id)
        if local_env['moderation']['channel_autoreports'] != None:
            #inactive_channels = []
            inactive_channels = "List of inactive_channels:\n"
            for channel in guild.text_channels:
                bot_permission = channel.permissions_for(bot_member)
                if not bot_permission.read_messages or not bot_permission.send_messages or not bot_permission.view_channel:
                    continue
                async for last_message in channel.history(limit=1):
                    last_date = last_message.created_at
                    if last_message.edited_at != None:
                        last_date = last_message.edited_at
                    current_date = datetime.datetime.now()
                    delta = current_date - last_date
                    if delta.days > local_env['moderation']['days_until_inactive']:
                        #inactive_channels.append( (channel.name, delta.days) )
                        inactive_channels = inactive_channels + str(channel.mention) + ": no activity in " + str(delta.days) + " days\n"
            nagging_channel_id = local_env['moderation']['channel_autoreports']
            nagging_channel = bot.get_channel(nagging_channel_id)
            await nagging_channel.send(inactive_channels)
    except Exception as e:
        await log.Error(bot, e, guild, local_env, { } )