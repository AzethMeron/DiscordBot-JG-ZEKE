
import os
from dotenv import load_dotenv # ENV vars
from deep_translator import GoogleTranslator
import detectlanguage 
import log
import uwu_translator

# by Jakub Grzana

################################### INTERNAL ###################################

detectlanguage.configuration.api_key = os.getenv('DETECT_LANGUAGE_TOKEN')

def MakeMessage(text, reaction, user, src_lang, tgt_lang):
    mess = f"\
    {text}\n\
    {src_lang} -> {tgt_lang}\n\
    Requested by: {user.display_name}"
    return mess

def CheckForCustom(tgt_lang):
    global CustomLangs
    if tgt_lang in CustomLangs:
        return CustomLangs[tgt_lang][0] 
    return tgt_lang

def uwu_postprocess(translated_text):
    return uwu_translator.convert(translated_text.split())

# custom lang: (working_lang, func(text))
CustomLangs = { 'uwu' : ('en', uwu_postprocess) }

def DetectLanguage(text):
    return detectlanguage.simple_detect(text)

def RawTranslate(src_lang, tgt_lang, text):
    return GoogleTranslator(source=src_lang, target=tgt_lang).translate(text)

def Translate(tgt_lang, text):
    global CustomLangs
    src_lang = 'auto'
    translator_tgt = CheckForCustom(tgt_lang) 
    translated = text
    try:
        src_lang = DetectLanguage(text)
    except Exception as e:
        src_lang = 'auto'
        print(e)
    if src_lang != translator_tgt:
        translated = RawTranslate(src_lang,translator_tgt,text)
    if translator_tgt != tgt_lang:
        translated = CustomLangs[tgt_lang][1](translated)
    return (src_lang, tgt_lang, translated)
    
def EnsureEnglish(text):
    src = DetectLanguage(text) #skipping language detection will cause exceptions, but no fatal ones so i consider it
    if src != 'en':
        text = RawTranslate(src,'en',text)
    return text


###########################################################################


################################ INTERFACE ################################

def AddEmojiTranslation(bot, local_env, emoji, language):
    global CustomLangs
    lang_dict = GoogleTranslator.get_supported_languages(as_dict=True)
    for key in lang_dict:
        if language == key or language == lang_dict[key] or language in CustomLangs:
            local_env['supported_languages'][emoji] = language
            return (True, None)
    return (False, "Unsupported language")
    
def RemoveEmojiTranslation(bot, local_env, emoji):
    if emoji in local_env['supported_languages']:
        del local_env['supported_languages'][emoji]
        return (True, None)
    return (False, "This emoji isn't used by translator")

###########################################################################


################################## LOOP ###################################

async def Pass(bot, local_env, reaction, user):
    if reaction.message.author.bot:
        return
    if len(reaction.message.content) < 5:
        return 
    try:
        if reaction.count > 1: 
            return
        supported_languages = local_env['supported_languages']
        emoji = str(reaction.emoji)
        if emoji in supported_languages:
            (src_lang, tgt_lang, translated) = Translate(supported_languages[emoji],reaction.message.content)
            reply = MakeMessage(translated, reaction, user, src_lang, tgt_lang)
            await reaction.message.add_reaction(emoji)
            await reaction.message.reply(reply)
    except Exception as e:
        await log.Error(bot, e, reaction.message.guild, local_env, { 'reaction' : str(reaction.emoji), 'content': reaction.message.content } ) 