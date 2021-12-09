import inspect
import itertools as it
import random
import re
import time
import tkinter as tk


DEFAULT_CONFIG = {
	'card_color_back': '#303030',
	'card_color_black': '#000000', 
	'card_color_icon': '#FFFFFF',
	'card_color_red': '#FF0000',
	'game_color_bg': '#C0C0C0'
}


class CardGame(tk.Tk):
	"""
	The window for the card game, controls the entire game.
	"""

	def __init__(self):
		super().__init__()
		
		self.score = 0

		self.title('Concentration')
		self.resizable(True, True)

		self.cardgrid = CardGrid(self, bg=config['game_color_bg'])

	def savescore(self):
		with open('score.txt', 'w') as scorefile:
			scorefile.write(f'Your final score was {self.score}')

	def close(self):
		self.savescore()
		print(f'Nice job! Your score was {self.score} (saved to score.txt).')
		time.sleep(3)
		self.destroy()


class CardGrid(tk.Frame):
	"""
	Container for the grid of cards in the game.
	"""

	ROWS = 6
	COLS = 9

	# padding around each card (px)
	PAD = 2

	def __init__(self, master: tk.Misc, *args, **kwargs):
		super().__init__(master, *args, **kwargs)

        # class properties
		self.current_cards: list[Card] = []
		self.matched_cards: set[Card] = set()

		self.master.grid_rowconfigure(0, weight=1)
		self.master.grid_columnconfigure(0, weight=1)
		self.grid(column=0, row=0, sticky=tk.NSEW)

		for i in range(self.ROWS):
			self.grid_rowconfigure(i, weight=1)
		for i in range(self.COLS):
			self.grid_columnconfigure(i, weight=1)

		self.createcards()

	def createcards(self):
		self.cards: list[Card] = []

		suits = Card.SPADES, Card.HEARTS, Card.DIAMONDS, Card.CLUBS
		values = range(1, 14)

		# add standard 52 cards
		self.cards.extend(Card(self, s, v) for s, v in it.product(suits, values))

		# add jokers
		self.cards.append(Card(self, Card.HEARTS, 14))
		self.cards.append(Card(self, Card.DIAMONDS, 14))

		# randomize order of cards
		random.shuffle(self.cards)

		# position cards in grid
		for card, (i, j) in zip(self.cards, it.product(range(CardGrid.ROWS), range(CardGrid.COLS))):
			card.grid(row=i, column=j, padx=CardGrid.PAD, pady=CardGrid.PAD)

	def cardclicked(self, card: 'Card'):
		if card in self.matched_cards: return
		if len(self.current_cards) == 1 and card is self.current_cards[0]: return

		if not card.flipped:
			card.flip()
		self.current_cards.append(card)

		if len(self.current_cards) == 2:
			self.master.score += 1
			
			if self.gameover():
				self.update_idletasks()
				self.master.close()

		if len(self.current_cards) == 3:
			card1, card2, card3 = self.current_cards

			if card1.matches(card2):
				self.matched_cards.add(card1)
				self.matched_cards.add(card2)
			else:
				card1.flip()
				card2.flip()

			# remove first two cards in queue
			self.current_cards = [card3]

			if not card3.flipped:
				card3.flip()

	def gameover(self) -> bool:
		return all(card.flipped for card in self.cards)


class Card(tk.Canvas):
	"""
	A playing card for the concentration game.
	"""

	WIDTH = 60
	HEIGHT = int(WIDTH * 1.4)
	FONT = 'Arial 80'

	# unicode character for the card backs
	CARD_BACK = chr(0x1F0A0)

	# colors
	RED = 0
	BLACK = 1

	# suits
	SPADES = 0xA0
	HEARTS = 0xB0
	DIAMONDS = 0xC0
	CLUBS = 0xD0

	def __init__(self, master: tk.Misc, suit: int, value: int, *args, **kwargs):
		super().__init__(master, *args, width=Card.WIDTH, height=Card.HEIGHT, **kwargs)

		if value == 14:
			assert suit == Card.HEARTS or suit == Card.DIAMONDS, \
				'suit of jokers must be either hearts or diamonds'

		self.suit = suit
		self.value = value

		# whether or not the card is flipped over
		self.flipped = False

		# unicode character for the card's face
		self.char = self.getchar()

		# card color (RED or BLACK, not necessarily the actual color that is shown on screen)
		self.color = self.getcolor()

		textpos = (Card.WIDTH // 2) + 1, (Card.HEIGHT // 2) - 5
		self.icon = self.create_text(textpos, text=Card.CARD_BACK,
			font=Card.FONT, fill=config['card_color_icon'])

		# set background color
		self.update_displaycolor()

		self.bind('<Button-1>', self.mouseclicked)

	def getcolor(self) -> int:
		if self.suit == Card.HEARTS or self.suit == Card.DIAMONDS:
			return Card.RED
		return Card.BLACK

	def getchar(self) -> str:
		# jacks always use same character
		if self.value == 14:
			return chr(0x1F0DF)

		char_val = 0x1F000 | self.suit

		# if value is above jack, characters skip one value
		if self.value > 11:
			return chr(char_val | self.value + 1)

		return chr(char_val | self.value)

	def flip(self):
		self.flipped = not self.flipped
		
		# change card icon
		newtext = self.char if self.flipped else Card.CARD_BACK
		self.itemconfig(self.icon, text=newtext)

		# change card color
		self.update_displaycolor()

	def update_displaycolor(self):
		if self.flipped:
			color = config['card_color_red'] if self.color == Card.RED else config['card_color_black']
		else:
			color = config['card_color_back']
		self.config(bg=color)

	def mouseclicked(self, evt: tk.Event):
		self.master.cardclicked(self)

	def matches(self, other: 'Card') -> bool:
		return self.color == other.color and self.value == other.value

	def __eq__(self, other: object) -> bool:
		assert isinstance(other, Card)
		return self.suit == other.suit and self.value == other.value

	def __hash__(self) -> int:
		return hash((self.suit, self.value))

	def __str__(self) -> str:
		if self.value == 14:
			return '<joker>'

		suitname = {
			Card.CLUBS: 'clubs',
			Card.SPADES: 'spades',
			Card.DIAMONDS: 'diamonds',
			Card.HEARTS: 'hearts'
		}[self.suit]

		if 1 < self.value < 11:
			return f'<{self.value} of {suitname}>'

		valname = {
			1: 'ace',
			11: 'jack',
			12: 'queen',
			13: 'king'
		}[self.value]
		
		return f'<{valname} of {suitname}>'

	def __repr__(self) -> str:
		return f'Card(suit={self.suit}, value={self.value})'


def input_settings():
	"""
	Inputs config settings from settings.txt, creating the file if it doesn't exist.
	"""

	global config
	
	try:
		config = {}
		with open("settings.txt") as file:
			for line in file:
				setting, value = re.split(r':\s*', line.strip())

				# if setting or value is invalid
				if setting not in DEFAULT_CONFIG or not re.fullmatch(r'#(?:\d{3}|\d{6})', value): 
					raise ValueError

				config[setting] = value

	except (FileNotFoundError, ValueError):
		with open("settings.txt", 'w') as file:
			for key, value in DEFAULT_CONFIG.items():
				file.write(f'{key}: {value}\n')

		config = DEFAULT_CONFIG
			
	
def main():
	input_settings()

	print(inspect.cleandoc('''
		----- Concentration -----

		Rules:
		  1. Flip over two cards by clicking on them; your objective is to find
		     a matching pair (same color and value)
		  2. If the cards match, they will stay facing up; otherwise, both
		     cards will flip back over
		  3. Keep flipping over cards and finding matches until all cards are
		     facing up
		  4. Everytime you flip a pair over, your score will increase by 1; try
		     to get as low of a score as possible

		Extra information:
		  * After your first game, you can edit the values in `settings.txt` to
		    customize the appearance of successive games
		  * Your final score for each game will be saved in `score.txt` for you
		    to view
	'''))
	print()

	# wait for enter to start game
	input('Press <enter> to start...')
	print()
	
	cardgame = CardGame()
	
	# start event loop
	cardgame.mainloop()


if __name__ == '__main__':
	main()
