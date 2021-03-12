
import log
import discord
import temp
import os
import os.path
import glob
import random
import hate
from google_images_download import google_images_download  

# by Jakub Grzana

pic_post_dir = "picture_posting"
google_images = google_images_download.googleimagesdownload()  
count = 100 # library supports up to 100
MAX_PIC_POSTERS = 10
MAX_SEARCH_WORDS = 10

################################ DOWNLOAD IMAGE ################################

def downloadImages(query, path):
    global count
    arguments = {"keywords": query, 
                 "format": "jpg", 
                 "limit": count, 
                 #"print_urls":True,
                 "size": "medium",
                 "output_directory": path
                 }
    try: 
        google_images.download(arguments)
    except Exception as e:
        print(e)

################################################################################


################################### INTERNAL ###################################
def GetPicPath():
    path = temp.GetTempDirPath() + pic_post_dir
    if not os.path.isdir(path):
        os.mkdir(path)
    path = path + '/'
    return path
    
def RequestPictures(search_words):
    path = GetPicPath()
    files = []
    for word in search_words:
        if os.path.isdir(path+word):
            if len(glob.glob(path+word+'/*')) < 3:
                downloadImages(word, path)
        else:
            downloadImages(word, path)
        files = files + glob.glob(path+word+'/*')
    return files

###########################################################################


################################ INTERFACE ################################

def AddPicPoster(bot,local_env,guild, pic_poster_name, timer, channel_id, search_word):
    if len(local_env['pic_post']) >= MAX_PIC_POSTERS:
        return (False, "Too many pic-posters on this server")
    results = hate.Detect(search_word)
    if hate.BoolParse( hate.ParseWeight(results) ):
            return (False, "Keyword contains hate speech or offensive language")
    else:
        local_env['pic_post'][pic_poster_name] = {
            'timer' : timer,
            'channel_id' : channel_id,
            'search_words' : [search_word]  }
        return (True, None)

def AddSearchWord(bot, local_env, guild, pic_poster_name, search_word):
    if pic_poster_name in local_env['pic_post']:
        if hate.BoolDetect(search_word):
            return (False, "Keyword contains hate speech or offensive language")
        if len(local_env['pic_post'][pic_poster_name]['search_words']) >= MAX_SEARCH_WORDS:
            return (False, "This pic-poster has too many keywords to search for")
        else:
            local_env['pic_post'][pic_poster_name]['search_words'].append(search_word)
            return (True, None)
    else:
        return (False, "Pic-poster not found")

def RemovePicPoster(bot, local_env, guild, pic_poster_name):
    if pic_poster_name in local_env['pic_post']:
        del local_env['pic_post'][pic_poster_name]
        return (True, None)
    return (False, "Pic-poster not found")
    
def RemoveSearchWord(bot, local_env, guild, pic_poster_name, search_word):
    if pic_poster_name in local_env['pic_post']:
        try:
            local_env['pic_post'][pic_poster_name]['search_words'].remove(search_word)
            return (True, None)
        except:
            return (False,"Pic-poster doesn't have this keyword")
    return (False, "Pic-poster not found")

###########################################################################


################################## LOOP ###################################

async def Pass(bot, local_env, guild, minute):
    for pic_poster_name in local_env['pic_post']:
        timer = local_env['pic_post'][pic_poster_name]['timer']
        if minute % timer != 0:
            continue
        channel_id = local_env['pic_post'][pic_poster_name]['channel_id']
        if channel_id == None:
            continue
        try:
            search_words = local_env['pic_post'][pic_poster_name]['search_words']
            pictures = RequestPictures(search_words)
            random.shuffle(pictures)
            channel = bot.get_channel(channel_id)
            if len(pictures) < 3:
                return
            samples = random.sample(pictures, random.randint(1,3))
            # creating object ot be send to discord
            files_to_send = [ discord.File(sample) for sample in samples ]
            await channel.send(files=files_to_send)
        except Exception as e:
            await log.Error(bot,e,guild, local_env, {})