---
# DiscordBot

Simple discord bot made to learn Discord API.  
Most scripts are library scripts. Callable scripts are called "executable_*"  
executable_main.py - main script of Discord Bot  
executable_train_hate_classifier.py - train classifier to be used by Discord bot to scan for Hate Speech

To run programs, type in command line  
python executable_train_hate_classifier.py  
python executable_main.py  

---
# REQUIREMENTS. Created using programs & libraries:

Python 3.9.0  
nltk 3.5  
Discord API for python 1.6.0 (REQUIRES DISCORD_TOKEN)  
python-dotenv 0.15.0  
deep-translator 1.4.1  
detectlanguage 1.4.0 (REQUIRES DETECT_LANGUAGE_TOKEN)  
profanity-check 1.0.3  
Joeclinton1's fork of google-images-download  

Tokens must be included in ".env" file in working directory, containing:  
DISCORD_TOKEN="your token here"  
DETECT_LANGUAGE_TOKEN="your token here"  

---
# Licence & stuff:

This program is free for private usage, as well as educational usage.  
Credit is always required: Jakub Grzana, https://github.com/AzethMeron  
Commercial usage of any part of this program requires special permission from creator.  
I do NOT claim rights to any of libraries mentioned in REQUIREMENTS.  
No warranty given. I don't hold any reponsibilities for malicious/illegal usage of built-in tools.

---
# Disclaimer: UwU translator

uwu_translator.py is extracted from repository of WahidBawa - https://github.com/WahidBawa/UwU-Translator  
All rights on this script goes to WahidBawa

---
# Safety warning

This bot gathers some informations about users of Discord server and servers themself, for example number of messages posted by each user. Data is then saved without encryption. Instead, it uses Python built-in function hash() to replace ID of server and user with its' hash. 
