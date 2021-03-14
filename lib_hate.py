import twitter
import pandas 
import random
import nltk
import re
import os
import os.path

# by Jakub Grzana

################################### PARAMETERS ####################################
# stopwords - set of words to be removed
stopwords = nltk.corpus.stopwords.words('english')
stopwords.remove("not")
# forbidden characters - characters that are removed from every word in text
characters_to_be_removed  = [ ',', '.', ':', '`', '\'', '\\' ] 
# lemmatizer - function(word)
lemmatize = nltk.WordNetLemmatizer().lemmatize
###################################################################################

###################################################################################
classifier_dir = "classifier"
###################################################################################

# function to perform lemmatization of word
# input: word - string, one word
# output: string, lemmatized word
# Uses lemmatizer declared in parameters above
# Doesn't lemmatize mentions of users: @username
def Lemmatize(word):
	if(word[:1] == '@'):
		return word
	else:
		return lemmatize(word)

# function to perform preprocessing of particular word
# input: word - string, one word
# output: string, one preprocessed word
# converts word to lowercase, removes characters declared in parameters,
# if it's username, changed to @user
def PreprocessWord(word):
    word = word.lower()
    word = "".join( [ char for char in word if char not in characters_to_be_removed ] )
    if word[:1] == '@' or word[1:2] == '@':
        word = "@user"
        return word
    return lemmatize(word)

# function to perform preprocessing of text
# input: sent - string, containing whole text
# output: string, containing preprocessed text
# changes all URLs in text into "tokenurl"
# removes stopwords declared in parameters
# call Word() function for every word in text
def PreprocessMessage(sent):
	regex = r"(?i)\b((?:https?://|www\d{0,3}[.]|[a-z0-9.\-]+[.][a-z]{2,4}/)(?:[^\s()<>]+|\(([^\s()<>]+|(\([^\s()<>]+\)))*\))+(?:\(([^\s()<>]+|(\([^\s()<>]+\)))*\)|[^\s`!()\[\]{};:'\".,<>?«»“”‘’]))"
	urls = re.findall(regex,sent)
	for url in urls:
		sent = sent.replace(url[0], "tokenurl")
	sent = sent.split()
	sent = [ PreprocessWord(word) for word in sent if word.lower() not in stopwords ]
	return " ".join(sent)

def feature_extractor(text, important_words):
    text_ngrams = set( text.split() )
    
    features = {}
    for ngram in important_words:
        feature_name = "%s" % ' '.join(map(str, ngram))
        features[feature_name] = (ngram in text_ngrams)
    return features
    
def GetClassifierDir():
    if not os.path.isdir(classifier_dir):
        os.mkdir(classifier_dir)
    return classifier_dir+"/"