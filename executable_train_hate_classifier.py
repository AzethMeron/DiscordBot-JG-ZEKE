
import lib_hate
import nltk
import file
import data

# by Jakub Grzana
# program to train classifier to classify text using Bag-of-Words approach

# train/test sets are lists of dictionaries, such as:
# train_set = [
#	{'text': 'Why hello there', 'type': 'none'}, 
#	{'text': 'Your momma is terrible', 'type': 'hate'}
# ]

#####################################
WordLimit = 1500 # upper limit of words to be used
name_train_set=lib_hate.GetClassifierDir()+".train_set"
name_test_set=lib_hate.GetClassifierDir()+".test_set"
#####################################

# Loading sets
train_set = file.Load(name_train_set)
test_set = file.Load(name_test_set)

# Preprocessing sets, gathering all words
important_words = []
for row in train_set:
    row['text'] = lib_hate.PreprocessMessage(row['text'])
    important_words.extend(row['text'].split())
important_words = list(nltk.FreqDist(important_words).keys())[0:WordLimit]

# Training Classifier
train_vector = ( (lib_hate.feature_extractor(row['text'],important_words),row['type']) for row in train_set )
classifier = nltk.NaiveBayesClassifier.train( train_vector )

# Testing
test_vector = [ (lib_hate.feature_extractor(lib_hate.PreprocessMessage(row['text']),important_words), row['type']) for row in test_set ]
print("Score: "+ str(nltk.classify.accuracy(classifier, test_vector)))

# Saving classifier to be used by discord bot
file.Save(lib_hate.GetClassifierDir()+lib_hate.name_classifier,classifier)
file.Save(lib_hate.GetClassifierDir()+lib_hate.name_important_words,important_words)