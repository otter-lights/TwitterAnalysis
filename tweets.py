#!/usr/bin/env python
# encoding: utf-8

from tweepy import OAuthHandler
from tweepy import API
from tweepy import Cursor
from datetime import datetime, date, time, timedelta
from collections import Counter
import sys
import random
import math

#Twitter API credentials
consumer_key = "r15DimhEiq3xAVRTqE1UYr1hH"
consumer_secret = "eJXox9RWdULFeXax86Voqa7Q71ahtHG49lvoqTWePxLKBADCg9"
access_key = "702680361411743744-ZgoTkWiYV1a9hFYVEwvr2ZqRLDK8BVa"
access_secret = "fU8pXkLVNmleWfcFlinEFIZ0ZZgnnUQZfpV1yMREckY4m"

# has two loops that go over every tweet, O(2n) = O(n)
def get_all_tweets(screen_name):
    #Limitations with the twitter API only allow access to the most reacent 3240 tweets, 200 at a time
    
    #authorization and initialization of tweepy
    auth = OAuthHandler(consumer_key, consumer_secret)
    auth.set_access_token(access_key, access_secret)
    api = API(auth)
    
    item = api.get_user(screen_name)
    totalTweets = item.statuses_count
    
    #this is done to avoid weird outputs when showing percentage completed because the max amount of tweets is 3240
    if totalTweets > 3240:
        totalTweets = 3240
    
    #make an empty list of all tweets as Tweepy objects
    alltweets = []  
    
    #make initial request for most recent tweets (200 is the maximum allowed count)
    new_tweets = api.user_timeline(screen_name = screen_name,count=200)
    
    #save most recent tweets
    alltweets.extend(new_tweets)
    
    #save the id of the oldest tweet less one
    oldest = alltweets[-1].id - 1
    
    #keep grabbing tweets until there are no tweets left to grab
    while len(new_tweets) > 0:        
        #all subsiquent requests use the max_id param to prevent duplicates
        new_tweets = api.user_timeline(screen_name = screen_name,count=200,max_id=oldest)
        
        #add recent tweets to alltweets
        alltweets.extend(new_tweets)
        
        #update the oldest tweet id
        oldest = alltweets[-1].id - 1
        
        print(f"{math.floor(100 * len(alltweets)/totalTweets)}% of tweets from @{screen_name} downloaded so far")
    
    print("Finished retrieving " + str(len(alltweets)) + " tweets from @" + screen_name)
    # initatalize a dictionary of only the information that i use
    tweets = {}
    
    # fill the above dictionary with the text and time stamp of the tweet
    for i in range(len(alltweets)-1):
        tweet = alltweets[i]
        tweets[i] = {"text": tweet.text, "time": tweet.created_at}
    
    return tweets
    
# Constant runtime
def time_since(time):
    # get the current date and tweet date as a datetime object
    today = date.today()
    tweetdate = date(int(time[0]), int(time[1]), int(time[2]))
    
    #finds the difference between the dates, returns the delta in number of days
    delta = today - tweetdate
    return delta.days

# Constant runtime    
def relevency(tweet):
    #calls the time_since function to determine delta days between the current date and the tweet
    days = time_since(str(tweet["time"])[:11].split("-"))
    #finds the rough number of months since twitter was created, not exact
    start = math.ceil(math.ceil(time_since(["2006", "3", "21"])/7)/4)
    #finds the rough number of months since the tweet
    months = math.ceil(math.ceil(days/7)/4)
    
    #based this eqn off of a graph made on desmos that looked like i wanted it to
    relevent = (start - months)^2
    return relevent

# Constant runtime of the number of words in the file
def read_txtfile(filename):
    #opens the given file and reads the words into a dictionary
    #file formatting must have one word on each line 
    f = open(filename, "r")
    
    words = {}
    line = f.readline().strip()
    while line != "":
        words[line] = True
        line = f.readline().strip()
    f.close()
    return words 

# Constant worst-case runtime of 280 (bc tweets are max 280 characters)    
def remove_stopwords(text, stops):
    #this is a twitter specific stopword, rt = retweet and it shows up at the beginning of non-original tweets
    stops["rt"] = True
    #lowers all of the text to decrease words that mean the same thing but have different capitalization
    text = text.lower()
    
    #turns the text into a list of words, and returns a list with any "stop words" removed
    words = text.split()
    non_stop = []
    for word in words:
        if word not in stops:
            non_stop.append(word)
    return non_stop 

# Constant worst-case runtime of O(2 * 280) = O(560)
def clean(tweet):
    #performs cleaning on the text (removing emojis and punctuation)
    
    #gets a list of each character in the tweet
    text = list(tweet["text"].lower())
    #list of punctuation types to remove
    punct = [".", ",", "!", ":", ";", "'", "*", "\"", "?", "...", "--", "(", ")", "[", "]", "{", "}"]
    final = ""
    #iterates through the characters of a tweet and removes punctuation
    for char in text:
        #added afterwards to separate two words connected w a slash or dash
        if char == "/" or char == "-":
            final += " "
        elif char not in punct:
            final += char

    #encodes and decodes into ascii, used to ignore non ascii characters
    final = final.encode("ascii", errors="ignore").decode()    
    
    #splits into the separate words of the tweet to remove any links
    words = final.split()
    final = ""
    for word in words:
        if not word.startswith("http"):
            final += word + " "
    
    return final

# Constant worst-case runtime of O(280)
def get_sentiment(words, pos, neg):
    #start with a sentiment of 0
    sent = 0
    
    #for each word, if it is positive, increase sentiment. if it is negative, decrease sentiment
    for word in words:
        if word in pos:
            sent += 1
        if word in neg:
            sent -= 1
    
    #return pos or neg, depending on sentiment value
    if sent > 0:
        return "pos"
    elif sent < 0:
        return "neg"
    else:
        return "neut"

# Constant worse-case runtime of approx. O(1,000,000) --> the corpus has 500 samples of about 2000 words
def read_corpus():
    # doesn't use the read_txtfile function bc the corpus is formatted differently
    # formatting will be {"word":"tag", "word2":"tag2"}
    brown_corpus = {}
    
    #opens the corpus and iterates through each sample until the last one
    f = open("browntag_nolines.txt", "r")
    sample = f.readline()
    
    while sample != "":
        #split each tagged sample into format "word_tag"
        words = sample.split()
        #for each word, split into a list of the word and the tag, then add into the corpus if not present
        for word in words:
            corp = word.split("_")
            if corp[0] not in brown_corpus:
                brown_corpus[corp[0]] = corp[1] 
        sample = f.readline()
    f.close()
    return brown_corpus

# Modified the merge sort algorithim to sort using a list and two dictionaries
# Still has a runtime complexity of O(p log p) where p is the length of the users combined likes
def merge_sort(alist, dic1, dic2):
    if len(alist) <= 1:
        return alist
    
    list1 = merge_sort(alist[:int(len(alist)/2)], dic1, dic2)
    list2 = merge_sort(alist[int(len(alist)/2):], dic1, dic2)
        
    return merge(list1, list2, dic1, dic2)

def merge(list1, list2, dic1, dic2):
	result = []
	in1 = 0
	in2 = 0
	while len(result) < len(list1) + len(list2):
		if len(list1) <= in1:
			result.append(list2[in2])
			in2 += 1
		elif len(list2) <= in2:
			result.append(list1[in1])
			in1 += 1
		elif dic1[list1[in1]] + dic2[list1[in1]] < dic1[list2[in2]] + dic2[list2[in2]] :
			result.append(list1[in1])
			in1 += 1
		else:
			result.append(list2[in2])
			in2 += 1
	return result
			
# Runtime Analysis of O(2n + 2k + s + p log p) = O(n + k + s + p log p) 
# n = length of user1_tweets
# k = length of user2_tweets
def method_one(user1, user2):
    # O(n) --> see explanation in function comments
    user1_tweets = get_all_tweets(user1)
    # O(k)
    user2_tweets = get_all_tweets(user2)
    
    stops = read_txtfile("stopwords.txt")
    pos = read_txtfile("positive-words.txt")
    neg = read_txtfile("negative-words.txt")
    
    # creation of both a list and a dictionary for each user, to allow iteration of a list but O(1) searching of a dictionary
    user1_interests = []
    user1_interestDic = {}
    user2_interests = []
    user2_interestDic = {}
    
    # worst case is O(n), iterates through all of user1's tweets
    for i in range(len(user1_tweets)-1):
        # does some cleaning of the text with helper functions (remove emojis etc.) and gets sentiment & relevancy of tweet
        tweet = user1_tweets[i]
        text = clean(tweet)
        words = remove_stopwords(text, stops)
        sent = get_sentiment(words, pos, neg)
        rel = relevency(tweet)
        
        # because words is based on the length of a tweet the worst case runtime will be O(280) as tweets cannot have over 280 characters
        for word in words:
            if word not in user1_interestDic:
                user1_interestDic[word] = 0
            if sent == "pos":
                user1_interestDic[word] += rel
            if sent == "neg":
                user1_interestDic[word] -= rel
            if word not in user1_interests: 
                user1_interests.append(word)
    
    # worst case O(k), same as above but iterating through the second users tweets
    for i in range(len(user2_tweets)-1):
        tweet = user2_tweets[i]
        text = clean(tweet)

        words = remove_stopwords(text, stops)
        sent = get_sentiment(words, pos, neg)
        rel = relevency(tweet)
        
        for word in words:
            if word not in user2_interestDic:
                user2_interestDic[word] = 0
            if sent == "pos":
                user2_interestDic[word] += rel
            if sent == "neg":
                user2_interestDic[word] -= rel
            if word not in user2_interests: 
                user2_interests.append(word)
    common_processing(user1_interests, user1_interestDic, user2_interests, user2_interestDic)

# Runtime Analysis of O(2n + 2k + s + p log p)  
# n = length of user1_tweets
# k = length of user2_tweets
def method_two(user1, user2):
    # O(n)
    user1_tweets = get_all_tweets(user1)
    # O(k)
    user2_tweets = get_all_tweets(user2)
    
    # same reasoning as in first function
    user1_interests = []
    user1_interestDic = {}
    user2_interests = []
    user2_interestDic = {}
    
    corpus = read_corpus()
    
    # these are the adjective POS tags from the brown corpus
    adjectives = ["JJ", "JJR", "JJS", "JJT"]
    stops = read_txtfile("stopwords.txt")
    pos = read_txtfile("positive-words.txt")
    neg = read_txtfile("negative-words.txt")
    
    # O(n)
    for i in range(len(user1_tweets)-1):
        # same cleaning method as the first function, does not include sentiment
        tweet = user1_tweets[i]
        text = clean(tweet)
        words = remove_stopwords(text, stops)
        rel = relevency(tweet)
        
        # store the adjectives (in sents) and the non adjectives in tempInterests until finalized in second internal loop
        sents = []
        tempInterests = []
        
        # in the worst case scenario this loop can only run 280 times as there are 280 characters in a tweet
        for word in words:
            if word in corpus and corpus[word] in adjectives:
                sents.append(word)
            elif word not in user1_interestDic:
                tempInterests.append(word)
        
        # sentiment is now calculated based only on the adjectives of the sentance
        sent = get_sentiment(sents, pos, neg)
        
        # iterates through the non-adjective words and adds them to the full interest list + dictionary
        for word in tempInterests:
            if sent == "neut":
                continue
                
            if word not in user1_interestDic:
                user1_interests.append(word)
                user1_interestDic[word] = 0
            
            if sent == "pos":
                user1_interestDic[word] += rel
            else:
                user1_interestDic[word] -= rel
    
    # O(k), also comments are not repeated in this function as it is the same as above    
    for i in range(len(user2_tweets)-1):
        tweet = user2_tweets[i]
        text = clean(tweet)
        words = remove_stopwords(text, stops)
        rel = relevency(tweet)
        sents = []
        tempInterests = []
        
        for word in words:
            if word in corpus and corpus[word] in adjectives:
                sents.append(word)
            elif word not in user2_interestDic:
                tempInterests.append(word)
        
        sent = get_sentiment(sents, pos, neg)
        

        for word in tempInterests:
            if sent == "neut":
                continue
                
            if word not in user2_interestDic:
                user2_interests.append(word)
                user2_interestDic[word] = 0
            
            if sent == "pos":
                user2_interestDic[word] += rel
            if sent == "neg":
                user2_interestDic[word] -= rel
    
    common_processing(user1_interests, user1_interestDic, user2_interests, user2_interestDic)

# Runtime Analysis of O(s + p log p)
# s = either length of user1_interests or length of user2_interests, whichever is shorter
# p = the length of the combined_likes    
def common_processing(user1_interests, user1_interestDic, user2_interests, user2_interestDic): 
    combined_likes = []
    combined_dislikes = []
    combined_neutral = []
    disagree = []
    
    # worst case O(s) where s is either the length of user1_interests or length of user2_interests, whichever is shorter
    if user1_interests <= user2_interests:
        # for each interest determine if the values fall into likes, dislikes, neutral, disagree
        # because we only care about those that are in both we don't have to iterate twice
        for word in user1_interests:
            if user1_interestDic[word] < -0.1 and word in user2_interestDic and user2_interestDic[word] < -0.1:
                combined_dislikes.append(word)
            elif user1_interestDic[word] > 0.1 and word in user2_interestDic and user2_interestDic[word] > 0.1:
                combined_likes.append(word)
            elif (user1_interestDic[word] < 0.1 and user1_interestDic[word] > -0.1) and word in user2_interestDic and (user2_interestDic[word] < 0.1 and user2_interestDic[word] > -0.1):
                combined_neutral.append(word)
            elif word in user2_interestDic:
                disagree.append(word)
    else:
        # same as above but iterating through user2_interests instead of user1_interests to save time
        for word in user2_interests:
            if user2_interestDic[word] < -0.1 and word in user1_interestDic and user1_interestDic[word] < -0.1:
                combined_dislikes.append(word)
            elif user2_interestDic[word] > 0.1 and word in user1_interestDic and user1_interestDic[word] > 0.1:
                combined_likes.append(word)
            elif (user2_interestDic[word] < 0.1 and user2_interestDic[word] > -0.1) and word in user1_interestDic and (user1_interestDic[word] < 0.1 and user1_interestDic[word] > -0.1):
                combined_neutral.append(word)
            elif word in user1_interestDic:
                disagree.append(word)
    
    #this makes sure the user has any tweets to analyze to make sure that there is no division by 0
    if len(user1_interests) > 0 and len(user2_interests) > 0:
        # get the percentage that the user agrees/disagrees as divided by the length of their interests - those they are neutral about
        user1_common_percent = 100 * (len(combined_likes) + len(combined_dislikes))/(len(user1_interests) - len(combined_neutral))
        user1_disagree_percent = 100 * len(disagree)/(len(user1_interests) - len(combined_neutral))
        
        user2_common_percent = 100 * (len(combined_likes) + len(combined_dislikes))/(len(user2_interests) - len(combined_neutral))
        user2_disagree_percent = 100 * len(disagree)/(len(user2_interests) - len(combined_neutral))
    else:
        # returns empty if either user has no tweets
        print("Insufficent interests to make observation.")
        print("User 1 has " + str(len(user1_interests)) + " interests", "User 2 has " + str(len(user2_interests)) + " interests")
        return
    num = input("How many of the top interests should be retrieved? ")
    
    print("Top " + num + " Combined Interests: ")
    # O(p log p) where p is the length of combined_likes --> know this as it is using merge sort, covered in class
    print(merge_sort(combined_likes, user1_interestDic, user2_interestDic)[-int(num):])    
    
    # this is flexible and if this program was actually being deployed I would probably fine tune the variables a bit more based on research
    # at the present for two users to match they must both agree on more than they disagree
    if user1_common_percent > user1_disagree_percent and user2_common_percent > user2_disagree_percent:
        print("Users @" + user1 + " and @" + user2 + " should be friends")
    else:
        print("Users @" + user1 + " and @" + user2 + " should not be friends")

# runs until the user decides to quit
while True:
    # get the two users who will be calculated
    user1 = input("Twitter Handle of First User: ")
    user2 = input("Twitter Handle of Second User: ")
    
    print("\n")
    print("Method One of Friendship Analysis \n")
    method_one(user1, user2)

    print("\n")
    print("Method Two (Brown Corpus) of Friendship Analysis \n")
    method_two(user1, user2)
    
    cont = input("Press Q to Quit ")
    if cont.lower() == "q":
        break