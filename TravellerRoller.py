import discord
import random
import asyncio
import json

class TravellerRoller(discord.Client):
	ExposedFunctions = {
		"roll": roll_dice,
	}

	async def on_ready(self):
		print('Logged in as')
		print(self.user.name)
		print(self.user.id)
		print('------')

	async def d6():
		return random.randint(1,6)
		
	async def d6(dice):
		sum = 0
		for _ in range(dice):
			sum += d6()
		return sum
		
	async def d66():
		return d6() * 10 + d6()

	async def on_message(self, message):
		# Only reply if prefix is used
		if not message.content.startswith('-'):
			return
		# we do not want the bot to reply to itself
		if message.author.id == self.user.id:
			return
		
		# Split into command and content.
		parts = message.split(' ', 1)
		keyword = parts[0][1:]
		content = parts[1]

		if keyword in ExposedFunctions:
			ExposedFunctions[keyword](message, content)
		else:
			await message.channel.send('Unknown command.')
	
	async def roll_dice(message, content):
		dice = int(content)
		await message.channel.send(f"Rolled {dice}d6: ")
	
	







with open('./token.json') as f:
	token = json.load(f)["token"]

client = TravellerRoller()
client.run(token)

