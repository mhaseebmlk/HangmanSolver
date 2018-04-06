'''
	Note: I use the several letter frequencies providded by http://letterfrequency.org
'''
import json
import urllib2
import random
import time
import enchant

class HangmanSolver():
	def __init__(self):
		# Game Related properties
		self.API_URL = 'http://gallows.hulu.com/play?code=mhaseeb@purdue.edu'
		self.gameToken = None
		self.postingURL = None
		self.gameStatus = None
		self.gameRemainingGuesses = None
		self.gameState = None

		# Random Guessing related properties
		self.letters = 'abcdefghijklmnopqrstuvwxyz'
		# Guessing based on vowels related properties
		self.vowels = ['a','e','i','o','u','y'] # considering that there are 6 vowels in english (also consider 'y')
		self.guessedVowels = []
		# Guessing based on the letter frequencies in the english langauge
		self.letterFrequency_EnglishLanguage = 'etaoinsrhldcumfpgwybvkxjqz'
		self.guessedLetters_lttrFreq_EngLang = {}
		self.gssdLttrs_lttrFreq_EngLang = 'etaoinsrhldcumfpgwybvkxjqz'
		# Guessing based on brute force related properties
		self.dictionary = enchant.Dict("en_US")

	def startGame(self):
		# get the initial game token, state etc form the API_URL
		data = json.load(urllib2.urlopen(self.API_URL))				
		parsedData = self.__parseData(data)
		self.setGameStatus(parsedData[0])
		self.setGameToken(parsedData[1])
		self.setRemainingGuesses(parsedData[2])
		self.setGameState(parsedData[3])

	# a naive guessing method that tries randomly generated letters
	def makeRandomGuess_v1(self):
		randomGuessLetter = self.letters[random.randint(0,len(self.letters)-1)]
		# now send this random guess to the Hangman API and get the result
		parsedResponse = self.__makeGuessRequest(randomGuessLetter)
		self.setGameStatus(parsedResponse[0])
		self.setRemainingGuesses(parsedResponse[2])
		self.setGameState(parsedResponse[3])

	# a better guessing method that takes into account the fact that most english words/phrases consist of vowels
	def makeRandomGuess_v2(self):
		# first try with all the vowels
		guessLetter = None
		for v in self.vowels:
			if v not in self.guessedVowels:
				self.guessedVowels.append(v)
				guessLetter = v
				break

		# if a guess letter was found, make the request and return
		if guessLetter:
			parsedResponse = self.__makeGuessRequest(guessLetter)
			self.setGameStatus(parsedResponse[0])
			self.setRemainingGuesses(parsedResponse[2])
			self.setGameState(parsedResponse[3])
			return
		# if it was not found then go back to the random way
		self.makeRandomGuess_v1()

	# takes into account the letter frequencies in the english language. (guesses in that order )
	def makeRandomGuess_v3(self):
		# start from the beginning of the letterFrequency_EnglishLanguage and see if this was already guessed
		# if not then use this, else move on
		guessLetter = None
		for l in self.letterFrequency_EnglishLanguage:
			if l not in self.guessedLetters_lttrFreq_EngLang:
				self.guessedLetters_lttrFreq_EngLang[l] = True
				guessLetter = l
				parsedResponse = self.__makeGuessRequest(guessLetter)
				self.setGameStatus(parsedResponse[0])
				self.setRemainingGuesses(parsedResponse[2])
				self.setGameState(parsedResponse[3])
				self.gssdLttrs_lttrFreq_EngLang = self.gssdLttrs_lttrFreq_EngLang.replace(l,'')
				return

	# builds on top of v3 to start chosing the letters randomly when the phrase is guessed ~60%-65%
	def makeRandomGuess_v4(self,percentageMatch):
		if percentageMatch <= 65:
			self.makeRandomGuess_v3()
			return
		randomGuessLetter = self.letters[random.randint(0,len(self.letters)-1)]
		while (randomGuessLetter in self.guessedLetters_lttrFreq_EngLang):
			randomGuessLetter = self.letters[random.randint(0,len(self.letters)-1)]
		parsedResponse = self.__makeGuessRequest(randomGuessLetter)
		self.setGameStatus(parsedResponse[0])
		self.setRemainingGuesses(parsedResponse[2])
		self.setGameState(parsedResponse[3])

	# builds on top of v3 and brute forces after percentageMAtch has reached 68%. Uses online word checker to verify brute force
	def makeRandomGuess_v5(self,percentageMatch, lastGameState):
		if percentageMatch <= 70 or len(lastGameState) <= 20:
			self.makeRandomGuess_v3()
			return
		wordToBruteForce = filter(lambda word: '_' in word,lastGameState.split(' '))[0]
		numMissingLetters = 0
		missingLetterIndeces = []
		for i in xrange(0,len(wordToBruteForce)):
			if wordToBruteForce[i] == '_':
				numMissingLetters = numMissingLetters + 1
				missingLetterIndeces.append(i)
		# more than 3 characters to brute force is a lot! try version 3 for this case
		if numMissingLetters > 3: 
			self.makeRandomGuess_v3()
			return
		newWord = wordToBruteForce
		while not self.dictionary.check(newWord.lower()):
			for i in xrange(0,len(missingLetterIndeces)):
				print 'Brute forcing the word {} ... Checking with word {} ...'.format(wordToBruteForce,newWord.lower())
				randomInt = random.randint(0,len(self.gssdLttrs_lttrFreq_EngLang)-1)
				randChar = (self.gssdLttrs_lttrFreq_EngLang[randomInt])
				newWord = list(newWord)
				newWord[missingLetterIndeces[i]] = randChar
				newWord = "".join(newWord)
		# if (self.dictionary.check(newWord.lower())):
		print 'Matched with the word {}'.format(newWord.lower())
		# send the guessed character for this iteration of the gussing
		parsedResponse = self.__makeGuessRequest(newWord[missingLetterIndeces[0]])
		self.setGameStatus(parsedResponse[0])
		self.setRemainingGuesses(parsedResponse[2])
		self.setGameState(parsedResponse[3])
		# return
		# else:
			

	''' Getters and Setters '''
	def getGameStatus(self):
		return self.gameStatus
	def setGameStatus(self,_status):
		self.gameStatus = _status

	def getGameToken(self):
		return self.gameToken
	def setGameToken(self,_token):
		self.gameToken = _token

	def getRemainingGuesses(self):
		return self.gameRemainingGuesses
	def setRemainingGuesses(self,_remainingGuesses):
		self.gameRemainingGuesses = _remainingGuesses

	def getGameState(self):
		return self.gameState
	def setGameState(self,_state):
		self.gameState = _state

	def getGameURL(self):
		return 'http://gallows.hulu.com/play?code=mhaseeb@purdue.edu&token='+(self.getGameToken())+'&guess='+(self.letters[random.randint(0,len(self.letters)-1)])

	def getGameStats(self,lastGameState):
		# basic stat: return the %age of correct guessed letters from the whole phrase length
		lengthOfPhrase = len(self.getGameState())
		numCorrectGuesses = 0.0
		for l in lastGameState:
			if l != '_':
				numCorrectGuesses = numCorrectGuesses + 1
		return ((numCorrectGuesses/lengthOfPhrase)*100)

	''' "Private" Methods '''
	def __parseData(self,data):
		return (data['status'],data['token'],data['remaining_guesses'],data['state'])

	def __makeGuessRequest(self, guessLetter):
		guessURL = 'http://gallows.hulu.com/play?code=mhaseeb@purdue.edu&token='+(self.getGameToken())+'&guess='+(guessLetter)
		print 'Guess Letter: {} Num Guesses Remaining: {}'.format(guessLetter,self.getRemainingGuesses())
		data = json.load(urllib2.urlopen(guessURL))
		return self.__parseData(data)

def main():
	while True:
		g1 = HangmanSolver()
		g1.startGame()
		lastGameState = g1.getGameState()
		print "================== New Game Started =================="

		while (g1.getGameStatus() == 'ALIVE'):
			lastGameState = g1.getGameState()
			# g1.makeRandomGuess_v1()
			# g1.makeRandomGuess_v2()
			# g1.makeRandomGuess_v3()
			# g1.makeRandomGuess_v4(g1.getGameStats(lastGameState))
			g1.makeRandomGuess_v5(g1.getGameStats(lastGameState),lastGameState)
			

			time.sleep(0.5) # wait for some time before making a new request (taking care of the API)

		if (g1.getGameStatus() == 'FREE'):
			print '\n\n>>>[SUCCESS] We saved the prisnor. Game token #: {}\n\n'.format(g1.getGameToken())
		elif (g1.getGameStatus() == 'DEAD'):
			print '>>> [Result] We could not save the prisnor. Game token #: {}'.format(g1.getGameToken())
			print '\tPhrase to guess: {}'.format(g1.getGameState())
			print '\tOur guess: {}'.format(lastGameState)
			print "\tOur accuracy: {}".format(g1.getGameStats(lastGameState))

if __name__ == '__main__':
	main()
