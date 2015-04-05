from pytrie import SortedStringTrie as Trie
from dicts.sorteddict import ValueSortedDict
from random import randint
import random
from sets import Set
import requests
import urllib2
import json






#Used in word frequencies to avoid counting the word in the next line as after a particular word as a new line is the equivalent of a new sentence.
nothingPrecedes = '[]'

#A list of words to never end a line with to from a rudimentary level increase grammatical sense
doNotEndWith =  ['a', 'to', "by", 'with', 'and', 'in', 'the', 'but', 'their', 'there', 'or', 'my', 'i',]

#A Few sets used to store properties of various words
unstressed = Set()
stressed = Set()
lineStarters = Set()
rhymingDictionary = {}
#The Big Huge Thesaurus API Key
apiKey = "enter your own key here"

#Word to be entered when prompted for theme to quit the program.
terminateProgram = 'done'

training_text = "shakespeare.txt"




#This method creates two tries by parsing dictionary.txt
#The first (syllableCountTrie) just is a trie where the key is a word and
#the value is the number of syllables that word contains
#The second (syllableGuideTrie) just converts dictionary.txt into a Trie.
#This trie lays out the pronunciation and stresses of words.
def createSyllableMap():
    file = open("dictionary.txt", "r")
    syllableCountTrie = Trie()
    syllableGuideTrie = Trie()
    for line in file:
        indexOfSpace = line.find(" ")
        word = line[:indexOfSpace]
        pronounciation = line[indexOfSpace + 2 :]
        syllableGuideTrie.__setitem__(word, pronounciation)
        syllables = countSyllables(pronounciation)
        syllableCountTrie.__setitem__(word, syllables)
    return syllableCountTrie, syllableGuideTrie

#This method just counts the number of syllables in each word based off of the layout in dictionary.txt
#numbers equate to syllables so it just counts the occurrences of a number in the syllable guide provided
#by the file.
def countSyllables(word):
    numbers = ['0','1','2', '3', '4', '5', '6', '7', '8', '9']
    syllables = 0
    for char in word:
        if char in numbers:
            syllables += 1
    return syllables

#Some words end with 'st or st (such as bestow'st) that in modern English people won't use.
#Because the syllable guide doesn't include it with the "st" this method just strips that out
#so the syllables can be counted.
def subtractOutExtension(word):
    if len(word) > 3:
        if word[-3:] == "\'st":
            word = word[:len(word) - 3]
        elif word[-2:] == 'st':
            word = word[:len(word) - 2]
    return word





#This method does all of the work need to parse the training text.
#It goes line by line building a dictionary of the words used after a particular word and the number of times.
#It also adds all of the words that start a line into the set called lineStarters and categorizes words
#into stressed and unstressed sets by their first syllable.
#Lastly, it creates a rhyming dictionary where by entering the sound of the last syllable as shown in dictionary.txt
#all the words that rhyme with it are given.
def parseTrainingTexts(syllablePronounciation):
    text_file = open (training_text, "r")
    successors = {}
    previous = nothingPrecedes
    for line in text_file:
        if line == "\n":
            previous = nothingPrecedes
        else:
            words = line.split()
            if(len(words) > 0 and subtractOutExtension(words[0].upper()) in syllablePronounciation):
                lineStarters.add(words[0].capitalize())
            for word in words :
                realWord = subtractOutExtension(word).upper()
                if realWord in syllablePronounciation:
                    prounciation = syllablePronounciation[realWord]
                    lastOccurenceSyllableUnstressed = prounciation.rfind("0")
                    lastOccurenceSyllableStressed = prounciation.rfind("1")
                    if lastOccurenceSyllableStressed > lastOccurenceSyllableUnstressed:
                        subPronounciation = prounciation[:lastOccurenceSyllableStressed]
                    else:
                        subPronounciation = prounciation[:lastOccurenceSyllableUnstressed]
                    indexOfSpace = subPronounciation.rfind(" ")
                    lastSyllable = prounciation[indexOfSpace + 1:]
                    if lastSyllable in rhymingDictionary:
                        currentList = rhymingDictionary[lastSyllable]
                        if word not in currentList:
                            currentList.append(word)
                            rhymingDictionary[lastSyllable] = currentList
                    else:
                        rhymingDictionary[lastSyllable] = [word]

                    indexUnstressed = prounciation.find("0")
                    indexStressed = prounciation.find("1")
                    if(indexUnstressed == -1 or indexStressed > indexUnstressed):
                        stressed.add(word)
                    else:
                        unstressed.add(word)
                if previous in successors:
                    entry = successors[previous.lower()]
                    if word in entry :
                        entry[word] += 1
                    else :
                         entry[word] = 1
                elif previous != nothingPrecedes:
                    successors[previous.lower()] = {word:1}
                previous = word

    return successors

#If no rhyme can be found this method is called to find a word that rhymes with a
#given word. It calls the rhyme brain API to find a word that is the correct
#number of syllables to end a line and then uses the syllable information
#to make sure it has the proper stress.
#param rhymeWord: the word it needs to rhyme with
#param syllablesNeeded: The number of syllables the word needs to be
#param syllablePronunciation:   The guide of syllables as shown in dictionary.txt
def forceRhymingDictionary(rhymeWord, syllablesNeeded, syllablePronunciation):
    contenders = []
    parameters = {"function" : "getRhymes" , "word" : rhymeWord}
    request = requests.get("http://rhymebrain.com/talk", params=parameters)
    json = request.json()
    if (syllablesNeeded % 2 == 0):
        for item in json:
            word = item["word"]
            syllables = item["syllables"]
            if word.upper() in syllablePronunciation and int(syllables) == syllablesNeeded:
                if syllablePronunciation[word.upper()].find("1") > syllablePronunciation[word.upper()].find("0"):
                    contenders.append(word)
    else:
         for item in json:
            word = item["word"]
            syllables = item["syllables"]
            if word.upper() in syllablePronunciation and int(syllables) == syllablesNeeded:
                if syllablePronunciation[word.upper()].find("1") < syllablePronunciation[word.upper()].find("0"):
                    contenders.append(word)
    return contenders


#If no rhyme naturally comes through a Markov chain (as one of the options) then
#this method is called. It searches all of the words that end with the given sound
#and if they match the syllable requirements (stress and count) puts them in a contenders
#list.
#param syllablesNeeded: The number of syllables the word needs to be
#param syllableCount: A trie containing the number of syllables in each word
#param syllablePronunciation: The guide of syllables as shown in dictionary.txt
#param rhymeSound: The sound the word needs to end with to rhyme with the correct word.
def forcePick(syllablesNeeded, syllableCount, syllablePronunciation, rhymeSound):
    contenders = []
    words = rhymingDictionary[rhymeSound]
    if syllablesNeeded % 2 == 0:
        for word in words:
            wordAlt = subtractOutExtension(word)
            if(wordAlt !=  word):
                wordAlt = wordAlt.upper()
                if syllableCount[wordAlt] + 1 == syllablesNeeded and syllablePronunciation[wordAlt].find("0") > syllablePronunciation[wordAlt].find("1"):
                    contenders.append(word)
            else:
                wordAlt = wordAlt.upper()
                if syllableCount[wordAlt] == syllablesNeeded and syllablePronunciation[wordAlt].find("0") > syllablePronunciation[wordAlt].find("1"):
                    contenders.append(word)

    else:
        for word in words:
            wordAlt = subtractOutExtension(word)
            if(wordAlt !=  word):
                wordAlt = wordAlt.upper()
                if syllableCount[wordAlt] + 1  == syllablesNeeded and syllablePronunciation[wordAlt].find("0") < syllablePronunciation[wordAlt].find("1"):
                    contenders.append(word)
            else:
                wordAlt = wordAlt.upper()
                if syllableCount[wordAlt] == syllablesNeeded and syllablePronunciation[wordAlt].find("0") < syllablePronunciation[wordAlt].find("1"):
                    contenders.append(word)

    return contenders

#This method gets the next word of the line. It uses a Markov chain such that it chooses a word
#that was used after the current word in the training text. To pick the next word out of all of the possibilities in the
#Markov chain a weighted probability is done such that words used more often after the current word have a greater chance
#of being chosen as the next word. It also has to deal with rhyme such that if a rhyme isn't naturally occurring when
#necessary then it will forcefully pick a word that rhymes, first from Shakespeare if possible, but if not from a large rhyming dictionary.
#param word: the current word
#param largeDictionary: The dictionary that contains all the words that follow a particular word
#param syllableCount: A trie containing the number of syllables in each word
#param syllablesRemaining: The number of syllables still needed in a line
#param syllablePronunciation: The guide of syllables as shown in dictionary.txt
#param rhymeSound: The sound that the last word of the line must end with to rhyme with another line. Can be None if first in a rhyming pattern.
#param rhymeWord: The word that the last word of the line will need to rhyme with another line. Can be None if first in a rhyming pattern
def getNextWord(word, largeDictionary, syllableCount, syllablesRemaining, syllablePronunciation, rhymeSound, rhymeWord):
    subDict = largeDictionary[word.lower()]
    weightedListTuple = toWeightedList(subDict, largeDictionary, syllableCount, syllablesRemaining, rhymeSound)
    if rhymeSound != None and syllablesRemaining <= 3 and  weightedListTuple[1] == False :
        contenders = forcePick(syllablesRemaining, syllableCount, syllablePronunciation, rhymeSound)
        if len(contenders) >= 1:
            return random.sample(contenders, 1)[0]
        else:
            contenders = forceRhymingDictionary(rhymeWord, syllablesRemaining, syllablePronunciation)
            if (len(contenders) >= 1):
                return random.sample(contenders, 1)[0]
            else:
                raise ImpossibleLineError("Choose a new matching line")
    asList = weightedListTuple[0]
    wordAlt = subtractOutExtension(word)
    if(len(asList) == 0):
        if(syllablePronunciation[wordAlt.upper()].find("1") > syllablePronunciation[wordAlt.upper()].find("0")):
            nextChoice = ""
            nextAlt = subtractOutExtension(nextChoice)
            while nextChoice not in largeDictionary or nextAlt not in syllableCount or syllablesRemaining - syllableCount[nextAlt] < 0:
                nextChoice = (random.sample(unstressed, 1))[0]
                nextAlt = subtractOutExtension(nextChoice).upper()
        else:
            nextChoice = " "
            nextAlt = subtractOutExtension(nextChoice)
            while nextChoice not in largeDictionary or nextAlt not in syllableCount or syllablesRemaining - syllableCount[nextAlt] < 0:
                nextChoice = (random.sample(stressed, 1))[0]
                nextAlt = subtractOutExtension(nextChoice).upper()
    else:
        nextChoice = ""
        x = 0
        while nextChoice not in largeDictionary and x < 25:
            x += 1
            nextChoice = asList[randint(0, len(asList) - 1)]
        if x == 25:
            nextChoice = ""
            while nextChoice not in largeDictionary:
                nextChoice = random.sample(stressed)

    return nextChoice


#This method goes through the possible contenders for the next word and creates a list
#weighing the number of entries in the list by number of occurrences. It also filters out
#certain words that would make less grammatical sense (such as ending a line with the word "a").
#Finally, if a word would complete a line that rhymes with the word it needs to that is sent over
#instead of anything else to encourage natural rhyming through the Markov chain.
#param smallDictionary: the dictionary of each word that comes after the initial word and the number of occurrences. (key=word, value=number of occurrences)
#param largeDictionary: the dictionary containing all the words that follow the given word (the key)
#param syllableCount: A trie containing the number of syllables in each word
#param syllablesRemaining: the number of syllables remaining in the line.
#param rhymeSound: the sound a word would need to end with to rhyme with a previous line. Can be None if start of new rhyming pattern
def toWeightedList(smallDictionary, largeDictionary, syllableCount, syllablesRemaining, rhymeSound):
    list = []
    rhymeList = []
    addOne = False
    for key in smallDictionary:
        realKey = subtractOutExtension(key)
        if realKey != key:
            addOne = True
        else:
            addOne = False

        if realKey.upper() in syllableCount:
             if key.lower() in doNotEndWith and ( (addOne == True and syllablesRemaining - (syllableCount[realKey.upper()] + 1) == 0) or (addOne == False and \
                (syllablesRemaining - syllableCount[realKey.upper()] == 0))):
                    continue

        if rhymeSound != None:
            if  (realKey in rhymingDictionary[rhymeSound] and addOne == True and syllablesRemaining - (syllableCount[realKey.upper()] + 1) == 0 ) or \
            (realKey in rhymingDictionary[rhymeSound] and addOne == False and syllablesRemaining - syllableCount[realKey.upper()] == 0 ):
                rhymeList.append(key)

        try:
            if addOne == False and key in largeDictionary and syllablesRemaining - syllableCount[realKey.upper()] >= 0 or addOne == True and key in largeDictionary and syllablesRemaining - syllableCount[realKey.upper()] + 1 >= 0:
                if addOne == True:
                    key = realKey
                numElements = smallDictionary[key]
                for i in range (0, numElements):
                    list.append(key)
        except KeyError:
            pass
    if (len(rhymeList) > 0):
        return rhymeList, True
    else:
        return list, False



#This method generates an entire line of the sonnet starting with the first word (the seed)
#param seed: the first word of the line
#param frequencies: The words that follow a given key. Referred to as largeDictionary in other methods to distinguish it from the subdictionaries it contains
#param syllableCount: A trie containing the number of syllables in each word
#param syllableDirectMap: The guide of syllables as shown in dictionary.txt
#param rhymeSound: The sound the line would need to end with to properly follow sonnet rhyme patterns. Can be None if start of a new rhyme pattern
#param rhymeWord: The word the line would need to end with to properly follow sonnet rhyme patterns. Can be None if start of a new rhyme pattern
def generateLine(seed, frequencies, syllableCount, syllableDirectMap, rhymeSound=None, rhymeWord=None):
    poem = seed
    lastWord = seed
    syllablesRemaining = 10
    seedAlt = subtractOutExtension(seed)
    if seedAlt == seed:
        try:
            syllablesRemaining = syllablesRemaining - syllableCount[seedAlt.upper()]
        except KeyError:
            print(seedAlt.upper())
            print(type(seedAlt.upper()))
    else:
        syllablesRemaining = syllablesRemaining - (syllableCount[seedAlt.upper()] + 1)
    while syllablesRemaining > 0 :
        word = getNextWord(lastWord, frequencies, syllableCount, syllablesRemaining, syllableDirectMap, rhymeSound, rhymeWord)
        lastWord = word
        wordAlt = subtractOutExtension(word)
        if wordAlt == word:
            syllablesRemaining -=  syllableCount[wordAlt.upper()]

        else:
            syllablesRemaining -= (syllableCount[wordAlt.upper()] + 1)
        # print ("Added: " + word + " LEFT WITH: " + str(syllablesRemaining))
        poem += " " + word
    return poem



#This poem generates a poem given a certain theme. It starts by finding all synonyms of
#the given theme. Then any synonym, the original, or related words that Shakespeare
#has used to start a line are used to start lines in this poem. For all of the other
#lines random words that Shakespeare used to start lines are used. If nothing in the
#theme matches the Shakespeare training text then a random poem is generated after
#a warning is printed. After getting the starting word it calls generate line with
#the proper parameters to create a 14 line poem in the specification of a sonnet.
#param theme: the theme of the poem
#param frequencies: The words that follow a given key. Referred to as largeDictionary in other methods to distinguish it from the subdictionaries it contains
#param syllableCount: A trie containing the number of syllables in each word
#param pronunciationGuide: The guide of syllables as shown in dictionary.txt
def generatePoemWithTheme(theme, frequencies, syllableCount, pronunciationGuide):
    starters = []
    url = "http://words.bighugelabs.com/api/2/" + apiKey + "/" + theme + "/json"
    response = urllib2.urlopen(url)
    data = json.load(response)
    key = data.keys()[0]
    keywords = [theme]
    if('rel' in data[key]):
       keywords += data[key]['rel']
    if 'syn' in data[key]:
        keywords += data[key]['syn']
    for word in keywords:
        word = word.encode('ascii', 'ignore')
        capitalized = word.capitalize()
        if capitalized in lineStarters:
            starters.append(capitalized)
    if len(starters) == 0:
        print("Unfortunately that theme won't work. Don't worry though, the computer is pretty creative :) + \n")
    stillNeeded = 14 - len(starters)
    if stillNeeded > 0:
        starters += random.sample(lineStarters, stillNeeded)
    random.shuffle(starters)

    i = 0
    poem = ""
    for i in range (0, 3):
        starter = starters[i]
        lineOne = generateLine(starter, frequencies, syllableCount, pronunciationGuide)
        toRhymeWithA = lineOne.split()[-1]

        i += 1
        starter = starters[i]
        lineTwo = generateLine(starter, frequencies, syllableCount, pronunciationGuide)
        toRhymeWithB = lineTwo.split()[-1]

        i += 1
        starter = starters[i]
        realWord = subtractOutExtension(toRhymeWithA)
        pronouncation = pronunciationGuide[realWord.upper()]
        lastOccurenceSyllableUnstressed = pronouncation.rfind("0")
        lastOccurenceSyllableStressed = pronouncation.rfind("1")
        if lastOccurenceSyllableStressed > lastOccurenceSyllableUnstressed:
            subPronunciation = pronouncation[:lastOccurenceSyllableStressed]
        else:
            subPronunciation = pronouncation[:lastOccurenceSyllableUnstressed]
        indexOfSpace = subPronunciation.rfind(" ")
        lastSyllable = pronouncation[indexOfSpace + 1:]

        lineThree = generateLine(starter, frequencies, syllableCount, pronunciationGuide, lastSyllable, toRhymeWithA)

        realWord = subtractOutExtension(toRhymeWithB)
        pronouncation = pronunciationGuide[realWord.upper()]
        lastOccurenceSyllableUnstressed = pronouncation.rfind("0")
        lastOccurenceSyllableStressed = pronouncation.rfind("1")
        if lastOccurenceSyllableStressed > lastOccurenceSyllableUnstressed:
            subPronunciation = pronouncation[:lastOccurenceSyllableStressed]
        else:
            subPronunciation = pronouncation[:lastOccurenceSyllableUnstressed]
        indexOfSpace = subPronunciation.rfind(" ")
        lastSyllable = pronouncation[indexOfSpace + 1:]
        i += 1
        starter = starters[i]
        lineFour = generateLine(starter, frequencies, syllableCount, pronunciationGuide, lastSyllable, toRhymeWithB)
        poem += lineOne + "\n" + lineTwo + "\n" +  lineThree + "\n" +  lineFour + "\n"

    i += 1
    starter = (random.sample(lineStarters, 1))[0]
    coupletOne = generateLine(starter, frequencies, syllableCount, pronunciationGuide)
    toRhymeWith = coupletOne.split()[-1]

    i += 1
    starter = starters[i]
    realWord = subtractOutExtension(toRhymeWith)
    pronouncation = pronunciationGuide[realWord.upper()]
    lastOccurenceSyllableUnstressed = pronouncation.rfind("0")
    lastOccurenceSyllableStressed = pronouncation.rfind("1")
    if lastOccurenceSyllableStressed > lastOccurenceSyllableUnstressed:
        subPronunciation = pronouncation[:lastOccurenceSyllableStressed]
    else:
        subPronunciation = pronouncation[:lastOccurenceSyllableUnstressed]
        indexOfSpace = subPronunciation.rfind(" ")
        lastSyllable = pronouncation[indexOfSpace + 1:]
    coupletTwo = generateLine(starter, frequencies, syllableCount, pronunciationGuide, lastSyllable, toRhymeWith)

    poem += coupletOne + "\n" + coupletTwo

    return poem




#This poem generates a poem without a theme. It randomly selects words to start
#a line from a list of words Shakespeare used (or whatever provides training text) to start a line.
#Then using the specification of a sonnet lines are created using generateLine with the proper parameters to form the sonnet.
#param frequencies: The words that follow a given key. Referred to as largeDictionary in other methods to distinguish it from the subdictionaries it contains
#param syllableCount: A trie containing the number of syllables in each word
#param pronunciationGuide: The guide of syllables as shown in dictionary.txt
def generatePoemWithoutTheme(frequencies, syllableCount, pronunciationGuide):
    poem = ""
    for i in range (0, 3):
        starter = (random.sample(lineStarters, 1))[0]
        lineOne = generateLine(starter, frequencies, syllableCount, pronunciationGuide)
        toRhymeWithA = lineOne.split()[-1]

        starter = (random.sample(lineStarters, 1))[0]
        lineTwo = generateLine(starter, frequencies, syllableCount, pronunciationGuide)
        toRhymeWithB = lineTwo.split()[-1]

        starter = (random.sample(lineStarters, 1))[0]
        realWord = subtractOutExtension(toRhymeWithA)
        pronouncation = pronunciationGuide[realWord.upper()]
        lastOccurenceSyllableUnstressed = pronouncation.rfind("0")
        lastOccurenceSyllableStressed = pronouncation.rfind("1")
        if lastOccurenceSyllableStressed > lastOccurenceSyllableUnstressed:
            subPronunciation = pronouncation[:lastOccurenceSyllableStressed]
        else:
            subPronunciation = pronouncation[:lastOccurenceSyllableUnstressed]
        indexOfSpace = subPronunciation.rfind(" ")
        lastSyllable = pronouncation[indexOfSpace + 1:]

        lineThree = generateLine(starter, frequencies, syllableCount, pronunciationGuide, lastSyllable, toRhymeWithA)

        realWord = subtractOutExtension(toRhymeWithB)
        pronouncation = pronunciationGuide[realWord.upper()]
        lastOccurenceSyllableUnstressed = pronouncation.rfind("0")
        lastOccurenceSyllableStressed = pronouncation.rfind("1")
        if lastOccurenceSyllableStressed > lastOccurenceSyllableUnstressed:
            subPronunciation = pronouncation[:lastOccurenceSyllableStressed]
        else:
            subPronunciation = pronouncation[:lastOccurenceSyllableUnstressed]
        indexOfSpace = subPronunciation.rfind(" ")
        lastSyllable = pronouncation[indexOfSpace + 1:]
        starter = (random.sample(lineStarters, 1))[0]
        lineFour = generateLine(starter, frequencies, syllableCount, pronunciationGuide, lastSyllable, toRhymeWithB)
        poem += lineOne + "\n" + lineTwo + "\n" +  lineThree + "\n" +  lineFour + "\n"

    starter = (random.sample(lineStarters, 1))[0]
    coupletOne = generateLine(starter, frequencies, syllableCount, pronunciationGuide)
    toRhymeWith = coupletOne.split()[-1]

    starter = (random.sample(lineStarters, 1))[0]
    realWord = subtractOutExtension(toRhymeWith)
    pronouncation = pronunciationGuide[realWord.upper()]
    lastOccurenceSyllableUnstressed = pronouncation.rfind("0")
    lastOccurenceSyllableStressed = pronouncation.rfind("1")
    if lastOccurenceSyllableStressed > lastOccurenceSyllableUnstressed:
        subPronunciation = pronouncation[:lastOccurenceSyllableStressed]
    else:
        subPronunciation = pronouncation[:lastOccurenceSyllableUnstressed]
        indexOfSpace = subPronunciation.rfind(" ")
        lastSyllable = pronouncation[indexOfSpace + 1:]
    coupletTwo = generateLine(starter, frequencies, syllableCount, pronunciationGuide, lastSyllable, toRhymeWith)

    poem += coupletOne + "\n" + coupletTwo

    return poem

#This method handles the user input to enter a theme as well as the actual calling of the proper methods to generate a poem.
#It starts by generating the proper database, then prompts the user for a theme, and prints out the generates the poem.
#This method continues until the user enters the keyword (by default "done") to quit.
def main():
    print("The Library is being generated. Please wait a bit.")
    syllableTuple =  createSyllableMap()
    syllableCount = syllableTuple[0]
    pronunciationGuide = syllableTuple[1]
    frequencies = parseTrainingTexts(pronunciationGuide)
    print("Done Generating Library")
    done = False
    while done == False:
        theme = raw_input("If you'd like you can enter a theme here. If you just want the computer to decide just click the enter key. And to quit the program type \'done\' \n")
        if theme == terminateProgram:
            done = True
        elif theme == "" :
            print("Generating..." + "\n")
            tryAgain = True
            while tryAgain == True:
                tryAgain = False
                try:
                    print(generatePoemWithoutTheme(frequencies, syllableCount, pronunciationGuide))
                except (KeyError, ImpossibleLineError):
                    tryAgain = True

        else:
             print("Generating..." + "\n")
             tryAgain = True
             while tryAgain == True:
                tryAgain = False
                try:
                    print(generatePoemWithTheme(theme, frequencies, syllableCount, pronunciationGuide))
                except (KeyError, ImpossibleLineError):
                    tryAgain = True
        print("")

main()







#A custom exception to be thrown when a line is impossible to continue using Markov chains.
class ImpossibleLineError(Exception):
    pass