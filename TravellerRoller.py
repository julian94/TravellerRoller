import discord
import random
import asyncio
import json
import math

class TravellerRoller(discord.Client):
	ExposedFunctions = {
		"roll": roll_dice,
		"shipattack": ship_attack,
	}

	CritLocations = {
		2: "sensors",
		3: "power",
		4: "fuel",
		5: "weapon",
		6: "armour",
		7: "hull",
		8: "m-drive",
		9: "cargo",
		10: "j-drive",
		11: "crew",
		12: "computer",
	}

	CritEffects = {
		"sensors": {
			1: " All checks to use sensors suffer DM-2",
			2: "Sensors inoperative beyond Medium range",
			3: "Sensors inoperative beyond Short range",
			4: "Sensors inoperative beyond Close range",
			5: "Sensors inoperative beyond Adjacent range",
			6: "Sensors disabled",
		},
		"power": {
			1: "Thrust reduced by -1. Power reduced by 10%.",
			2: "Thrust reduced by -1. Power reduced by 10%.",
			3: "Thrust reduced by -1. Power reduced by 50%.",
			4: "Thrust reduced to 0. Power reduced to 0.",
			5: "Thrust reduced to 0. Power reduced to 0. Hull severity increased by +1.",
			6: "Thrust reduced to 0. Power reduced to 0. Hull severity increased by +1D.",
		},
		"fuel": {
			1: "Leak – lose 1D tons of fuel per hour.",
			2: "Leak – lose 1D tons of fuel per round.",
			3: "Leak – lose 1D x10% of fuel.",
			4: "Fuel tank destroyed.",
			5: "Fuel tank destroyed, Hull Severity increased by +1.",
			6: "Fuel tank destroyed, Hull Severity increased by +1D.",
		},
		"weapon": {
			1: "Random weapon suffers Bane when used.",
			2: "Random weapon disabled.",
			3: "Random weapon destroyed.",
			4: "Random weapon explodes, Hull Severity increased by +1.",
			5: "Random weapon explodes, Hull Severity increased by +1.",
			6: "Random weapon explodes, Hull Severity increased by +1.",
		},
		"armour": {
			1: "Armour reduced by -1.",
			2: "Armour reduced by -D3.",
			3: "Armour reduced by -1D.",
			4: "Armour reduced by -1D.",
			5: "Armour reduced by -2D, Hull Severity increased by +1.",
			6: "Armour reduced by -2D, Hull Severity increased by +1.",
		},
		"hull": {
			1: "Spacecraft suffers 1D damage.",
			2: "Spacecraft suffers 2D damage.",
			3: "Spacecraft suffers 3D damage.",
			4: "Spacecraft suffers 4D damage.",
			5: "Spacecraft suffers 5D damage.",
			6: "Spacecraft suffers 6D damage.",
		},
		"m-drive": {
			1: "All checks to control spacecraft suffer DM-1.",
			2: "All checks to control spacecraft suffer DM-2, and Thrust reduced by -1.",
			3: "All checks to control spacecraft suffer DM-3, and Thrust reduced by -1.",
			4: "All checks to control spacecraft suffer DM-4, and Thrust reduced by -1.",
			5: "Thrust reduced to 0.",
			6: "Thrust reduced to zero, Hull Severity increased by +1",
		},
		"cargo": {
			1: "10% of cargo destroyed.",
			2: "1D x 10% of cargo destroyed.",
			3: "2D x 10% of cargo destroyed.",
			4: "All cargo destroyed.",
			5: "All cargo destroyed, Hull Severity increased by +1.",
			6: "All cargo destroyed, Hull Severity increased by +1.",
		},
		"j-drive": {
			1: "All checks to use jump drive suffer DM-2.",
			2: "Jump drive disabled",
			3: "Jump drive destroyed.",
			4: "Jump drive destroyed, Hull Severity increased by +1.",
			5: "Jump drive destroyed, Hull Severity increased by +1.",
			6: "Jump drive destroyed, Hull Severity increased by +1.",
		},
		"crew": {
			1: "Random occupant takes 1D damage.",
			2: "Life support fails within 1D hours.",
			3: "1D occupants take 2D damage.",
			4: "Life support fails within 1D rounds.",
			5: "All occupants take 3D damage.",
			6: "Life support fails.",
		},
		"computer": {
			1: "All checks to use computers suffer DM-2.",
			2: "Computer ratingreduced by -1.",
			3: "Computer ratingreduced by -1.",
			4: "Computer ratingreduced by -1.",
			5: "Computer disabled.",
			6: "Computer destroyed.",
		},
	}

	async def on_ready(self):
		print('Logged in as')
		print(self.user.name)
		print(self.user.id)
		print('------')

	async def d6(self):
		return random.randint(1, 6)
	
	async def twod6(self):
		return d6() + d6()

	async def weapon_d6(self, dice, min = 1):
		sum = 0
		for _ in range(dice):
			sum += random.randint(min, 6)
		return sum
		
	async def d6(self, dice):
		sum = 0
		for _ in range(dice):
			sum += d6()
		return sum
		
	async def d66(self):
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
			await message.channel.send("Unknown command.")
	
	async def roll_dice(self, message, content):
		dice = int(content)
		await message.channel.send(f"Rolled {dice}d6: {d6(dice)}")
	
	async def resolve_crit(self, ship, severity):
		location = self.CritLocations[self.twod6()]
		while ship["critical_locations"][location] is None:
			location = self.CritLocations[self.twod6()]
		if ship["critical_locations"][location] < 0:
			severity += ship["critical_locations"][location]
			if severity < 0: severity = 1
		elif ship["critical_locations"][location] == 6:
			return f"Ship takes {self.d6(6)} extra damage as {location} has already been severely damaged."
		elif ship["critical_locations"][location] > 0:
			severity = max(severity, ship["critical_locations"][location] + 1)
		ship["critical_locations"][location] = severity


	
	async def ship_attack(self, message, content):
		parts = content.split(' ')
		attacker_name = parts[0]
		weapon_name = parts[1]
		target_name = parts[2]

		attacker = ships[attacker_name]
		weapon = attacker["guns"][weapon_name]
		target = ships[target_name]

		effect = self.twod6() + weapon["bonus"]
		if effect < 0:
			await message.channel.send("Hey fucker, you missed!")
			return

		damage_roll = self.weapon_d6(weapon["damage"], weapon["minyield"]) * weapon["multiplier"]
		if weapon["multiplier"] is 1: damage_roll += effect

		damage_inflicted = damage_roll - target["armour"]

		can_crit = True
		if target["displacement"] > 2000 and weapon["type"] in ["turret", "barbette"]:
			can_crit = False
		elif target["displacement"] > 10000 and weapon["type"] not in ["medium_bay", "large_bay"]:
			can_crit = False
		elif target["displacement"] > 100000 and weapon["type"] not in ["large_bay"]:
			can_crit = False

		critical_hit = False
		if can_crit and effect >= 6 and damage_inflicted > 0:
			critical_hit = True
		if damage_inflicted > (target["hpmax"] /10):
			critical_hit = True
		
		if critical_hit:
			crit_severity = 1
			treshold = 10
			if target["displacement"] >= 1000:
				treshold = target["displacement"] / 100
			crit_severity = math.ceil(damage_inflicted / treshold)
			await message.channel.send(self.resolve_crit(target, crit_severity)








with open('./ships.json') as f:
	ships = json.load(f)

with open('./token.json') as f:
	token = json.load(f)["token"]

client = TravellerRoller()
client.run(token)

