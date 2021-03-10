
import translator
import profanity_check
import data
import log
import uuid
from datetime import date

import file
import nltk
import lib_hate

# by Jakub Grzana

WARNINGS_TO_NAG = 3
WARNING_LENGTH_IN_DAYS = 1

###################################################################################

def profanity_internal(text):
    if profanity_check.predict([text]) == [1]:
        return True
    return False

###################################################################################

classifier = file.Load(lib_hate.GetClassifierDir()+lib_hate.name_classifier)
important_words = file.Load(lib_hate.GetClassifierDir()+lib_hate.name_important_words)

def BagOfWordsClassifier(text):
    global classifier
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

# (name, bool_func(text), weight) weights are unused now
Tests = [ ("Profanity Check", profanity_internal, 1),
("Hate Speech Classifier", BagOfWordsClassifier, 1) ]

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

def MakeReport(report, display_name, user_name, guild):
    endline = "\n"
    link = f'https://discordapp.com/channels/{guild.id}/{report[1]}/{report[2]}'
    output =  "=============================================\n"
    output = output + f'**Case number** {report[0]}{endline}**Link to message**: {link}{endline}**Nickname of suspect**: {display_name}{endline}**Username of suspect**: {user_name}{endline}{endline}**Content of message**: *"{report[3].replace(endline," ")}"*{endline}{endline}'
    output = output + "**Hate speech scan results**:" + "\n"
    for test in report[4]:
        output = output + test[0] + ": " + str(test[1]) + "\n"
    return output
    
###################################################################################

def SetModChannel(local_env, channel):
    if local_env['moderation']['channel'] != None:
        if len(local_env['moderation']['unclosed_cases']) > 0:
            return (False, "There's already active moderation channel with unclosed cases in it. Please solve them or purge before changing moderation channel")
    local_env['moderation']['channel'] = channel.id
    return (True, None)
    
def SetArchiveChannel(local_env, channel):
    local_env['moderation']['archive'] = channel.id
    return (True, None)

def PurgeUnclosedCases(local_env):
    local_env['moderation']['unclosed_cases'] = []
    return (True, None)
    
def DisableModeration(local_env):
    if local_env['moderation']['channel'] == None:
        return (False, "Moderation isn't enabled anyway")
    local_env['moderation']['channel'] = None
    local_env['moderation']['unclosed_cases'] = []
    local_env['moderation']['archive'] = None
    return (True,None)
    
async def AddWarning(local_env, user, reason):
    dte = date.today()
    user_env = data.GetUserEnvironment(local_env, user)
    user_env['warnings'].append( (dte,reason) )
    if True:
        if not user.dm_channel:
            await user.create_dm()
        num = len(user_env['warnings'])
        to_send = f'**Dear {user.display_name}**' + "\n" +\
        "I'm sad to report you got warning." + "\n" +\
        f'Reason: *"{reason}"*' + "\n" +\
        f'This is yours {num} warning ' 
        if num >= WARNINGS_TO_NAG:
            to_send = to_send + "which means I will nag administration to deal with your case"
        to_send = to_send + "\n" + "No heart feelings"
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
    mode_channel_id = local_env['moderation']['channel']
    mode_channel = bot.get_channel(mode_channel_id)
    mode_message = await mode_channel.fetch_message(case[0])
    backup_content = mode_message.content
    await mode_message.edit(content="Case solved")
    # back-up in archive
    archive_id = local_env['moderation']['archive']
    if archive_id != None:
        archive = bot.get_channel(archive_id)
        await archive.send(backup_content+"\n**Verdict**: "+str(confirmation))
    # removing case from unclosed_cases 
    if confirmation:
        # getting message that caused the problem
        hate_channel_id = case[1]
        hate_message_id = case[2]
        reason = "Hate speech detected in " + f'"{case[3]}"'
        hate_channel = bot.get_channel(hate_channel_id)
        hate_message = await hate_channel.fetch_message(hate_message_id)
        # add warning to given user
        user = hate_message.author
        await AddWarning(local_env, user, reason )
        # try to remove hate message
        try:
            await hate_message.delete()
        except:
            pass
    local_env['moderation']['unclosed_cases'].remove(c)
    return (True, None)

async def GetUserWarnings(local_env, user, message):
    user_env = data.GetUserEnvironment(local_env, user)
    info = f'Informations about user {str(user)} aka {user.display_name}' + "\n"
    info = info + "Warnings: " + str(len(user_env['warnings'])) + "\n"
    for warn in user_env['warnings']:
        info = info + str(warn[0]) + ". Reason " + f'"{warn[1]}"' + "\n"
    await message.reply(info)
    return (True, None)

###################################################################################

# Report structure
# report[0] = id of message in moderation channel
# report[1] = id of channel in which message violated rules
# report[2] = id of message that violated rules
# report[3] = content that violated rules
# report[4] = test results

###################################################################################

async def Pass(bot, local_env, message):
    if len(message.content) < 5:
        return
    try:
        mode_channel_id = local_env['moderation']['channel']
        if mode_channel_id != None:
            text = message.content
            # Ensuring text is in english
            try:
                text = translator.EnsureEnglish(text)
            except Exception as e:
                pass
            # Gathering results
            test_results = Detect(text)
            hate = False
            for check in test_results:
                if check[1]:
                    hate = True
                    break
            # hate detected
            if hate:
                mode_channel = bot.get_channel(mode_channel_id) # connection to 
                sent = await mode_channel.send("This should be editted instantly")
                report = (sent.id, message.channel.id, message.id, message.content, test_results)
                await sent.edit( content=MakeReport(report, message.author.display_name, str(message.author), message.guild) )
                local_env['moderation']['unclosed_cases'].append(report)
        
    except Exception as e:
        await log.Error(bot, e, message.guild, local_env, { 'content' : message.content } )
  
async def RemoveOutdatedWarnings(bot, local_env, guild, minute):
    for member in guild.members:
        return
