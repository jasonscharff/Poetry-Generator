from pytrie import SortedStringTrie as Trie
from dicts.sorteddict import ValueSortedDict
from random import randint

partsOfSpeech = {'n' : 'noun', 't' : 'transitive', 'i' : 'intransitive', 'r' : 'pronoun', 'a' : 'adjective', 'v' : 'adverb',
               'c' :  'conjunction'}

nothingPrecedes = '[]'



def wordFrequencies():
    text_file = open ("shakespeare.txt", "r")
    successors = {}
    previous = nothingPrecedes
    for line in text_file:
        if line == "\n":
            previous = nothingPrecedes
        else:
            words = line.split()
            for word in words:
                if previous in successors:
                    entry = successors[previous]
                    if word in entry :
                        entry[word] += 1
                    else :
                        entry[word] = 1
                elif previous != nothingPrecedes :
                    successors[previous] = {word:1}
                previous = word
    return successors




def getNextWord(word, largeDictionary):
    subDict = largeDictionary[word]
    asList = toWeightedList(subDict, largeDictionary)
    if(len(asList) == 0):
        pass #In reality, we need to fix this.
    else:
        nextChoice = asList[randint(0, len(asList) - 1)]
    return nextChoice


def toWeightedList(smallDictionary, largeDictionary):
    list = []
    for key in smallDictionary:
        if key in largeDictionary:
            numElements = smallDictionary[key]
            for i in range (0, numElements):
                list.append(key)
    return list


def generateWords(numberWords, seed):
    poem = seed + " "
    lastWord = seed
    largeDictionary = wordFrequencies()
    for i in range (0, numberWords):
        word = getNextWord(lastWord, largeDictionary)
        poem += word + " "
        lastWord = word
    return poem


for i in range (0, 14):
    print(generateWords(4, "thou"))








#http://pythonhosted.org//PyTrie/
def generatePronounciationTrie():
    pronounciation = Trie()
    print("Generating Database...")
    try:
        text_file = open("dictionary.txt", "r")
        for line in text_file:

            firstSpace = line.find(" ")
            key = line[:firstSpace]
            value = line[firstSpace+2:]
            pronounciation.__setitem__(key, value)
    except IOError:
        print("An IOError has occurred.")
    print("Generating Your Poem...")
    return pronounciation




def countSyllables(guide):
    total = 0
    for char in guide:
        total += 1
    return total

# class word ():
#     def __init__(self, word):
#         pass
#     def isolateSyllables (word):
#         for char in word:
#             if



