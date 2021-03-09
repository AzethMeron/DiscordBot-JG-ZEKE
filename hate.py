
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

###################################################################################

classifier = file.Load(lib_hate.GetClassifierDir()+lib_hate.name_classifier)
important_words = file.Load(lib_hate.GetClassifierDir()+lib_hate.name_important_words)

def BagOfWordsClassifier(text):
    global classifier
    text = lib_hate.PreprocessMessage(text)
    features = lib_hate.feature_extractor(text,important_words)
    if classifier.classify(features) == 'hate':
        return True
    return False

###################################################################################

def BoolDetect(text):
    # Hate detection
    if profanity_check.predict([text]) == [1]:
        return True
    if BagOfWordsClassifier(text):
        return True
    return False

def Detect(text):
    # checks
    [profanity] = profanity_check.predict([text])
    bow = BagOfWordsClassifier(text)
    # return
    return [ ("Profanity Check", profanity),
    ("Hate Speech Classifier", bow) ]
    
###################################################################################

def MakeReport(report, display_name, user_name, guild):
    endline = "\n"
    link = f'https://discordapp.com/channels/{guild.id}/{report[1]}/{report[2]}'
    output = f'**Case number** {report[0]}{endline}**Link to message**: {link}{endline}**Nickname of suspect**: {display_name}{endline}**Username of suspect**: {user_name}{endline}{endline}**Content of message**: *"{report[3].replace(endline," ")}"*{endline}{endline}'
    output = output + "**Hate speech scan results**:" + "\n"
    for test in report[4]:
        output = output + test[0] + ": " + str(test[1]) + "\n"
    return output
    
###################################################################################

def SetModChannel(local_env, channel):
    local_env['moderation']['channel'] = channel.id
    return (True, None)
    
def SetArchiveChannel(local_env, channel):
    local_env['moderation']['archive'] = channel.id
    return (True, None)

def PurgeUnclosedCases(local_env):
    local_env['moderation']['unclosed_cases'] = []
    return (True, None)
    
def AddWarning(local_env, user, reason):
    dte = date.today()
    user_env = data.GetUserEnvironment(local_env, user)
    user_env['warnings'].append( (dte,reason) )
    return (True, None)
    
async def CaseConfirmation(bot, local_env, case_id, confirmation):
    # searching for case in unclosed_cases
    case = None
    for c in local_env['moderation']['unclosed_cases']:
        if c[0] == case_id:
            case = c
            break
    if case == None:
        return (False, "Case not found")
    # getting message in mode channel
    mode_channel_id = case[5]
    mode_channel = bot.get_channel(mode_channel_id)
    mode_message = await mode_channel.fetch_message(case[0])
    backup_content = mode_message.content
    await mode_message.edit(content="Case solved")
    # back-up in archive
    archive_id = local_env['moderation']['archive']
    if archive_id != None:
        archive = bot.get_channel(archive_id)
        await archive.send(backup_content)
    # removing case from unclosed_cases 
    if confirmation:
        hate_channel_id = case[1]
        hate_message_id = case[2]
        reason = "Hate speech detected"
        hate_channel = bot.get_channel(hate_channel_id)
        hate_message = await hate_channel.fetch_message(hate_message_id)
        user = hate_message.author
        AddWarning(local_env, user, reason)
    local_env['moderation']['unclosed_cases'].remove(c)
    return (True, None)

async def GetUserWarnings(local_env, user, message):
    user_env = data.GetUserEnvironment(local_env, user)
    info = f'Informations about user {str(user)} aka {user.display_name}' + "\n"
    info = info + "Warnings: " + str(len(user_env['warnings'])) + "\n"
    for warn in user_env['warnings']:
        info = info + str(warn[0]) + ". Reason" + f'*"{warn[1]}"*' + "\n"
    await message.reply(info)
    return (True, None)

###################################################################################

# Report structure
# report[0] = id of message in moderation channel
# report[1] = id of channel in which message violated rules
# report[2] = id of message that violated rules
# report[3] = content that violated rules
# report[4] = test results
# report[5] = id of moderation channel

###################################################################################

async def Pass(bot, local_env, message):
    if message.author.bot:
        return
    if len(message.content) < 5:
        return
    try:
        channel_id = local_env['moderation']['channel']
        if channel_id != None:
            text = message.content
            # Ensuring text is in english
            try:
                text = translator.EnsureEnglish(text)
            except Exception as e:
                await log.Error(bot, e, message.guild, local_env, { 'content' : message.content } )
            # Gathering results
            test_results = Detect(text)
            hate = False
            for check in test_results:
                if check[1]:
                    hate = True
                    break
            if hate:
                channel = bot.get_channel(channel_id) # connection to 
                sent = await channel.send("This should be editted instantly")
                report = (sent.id, message.channel.id, message.id, message.content, test_results, channel_id)
                await sent.edit( content=MakeReport(report, message.author.display_name, str(message.author), message.guild) )
                local_env['moderation']['unclosed_cases'].append(report)
        
    except Exception as e:
        await log.Error(bot, e, message.guild, local_env, { 'content' : message.content } )
  

