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
			1: "All checks to use sensors suffer DM-2",
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
	
	async def apply_damage_and_sustained_crit(self, ship, new_damage):
		old_treshold = math.floor((ship["hp"]*10)/ship["hpmax"])
		ship["hp"] -= new_damage
		new_treshold = math.floor((ship["hp"]*10)/ship["hpmax"])

		if (new_treshold - old_treshold) == 0: return None
		if ship["hp"] <= 0: return None
		return f"Due to damage a critical hit has happened\n{self.resolve_crit(ship, new_treshold - old_treshold)}"

	
	async def resolve_crit(self, ship, severity, location = self.CritLocations[self.twod6()]):
		crit_message = ""
		while ship["critical_locations"][location] is None:
			location = self.CritLocations[self.twod6()]
		shiplocation = ship["critical_locations"][location]

		severity -= shiplocation["protection"]
		if severity <= 0: return f"A critical hit to {location} was prevented."
		if severity > 6: severity = 6

		# If the location is already max-critted, it can't be critted again.
		if shiplocation["severity"] == 6:
			damage = self.d6(6)
			crit_message += f"Ship takes {damage} extra damage as {location} has already been severely damaged."
			if m := self.apply_damage_and_sustained_crit(ship, damage):
				crit_message += m
			return crit_message
		
		# Apply use whichever severity is highest
		severity = max(severity, shiplocation["severity"] + 1)
		# Note what crit happened
		crit_message += self.CritEffects[location][severity]
		shiplocation["severity"] = severity

		# Apply special effects
		if location is "sensors":
			if severity is 1:
				ship["sensors"] -= 2
			if severity is 6:
				ship["sensors"] = None
		elif location is "weapon":
			if severity is not 1:
				# List guns and destroy/disable one at random
				gun_count = 0
				for gun in ship["guns"]:
					gun_count += gun["count"]
				chosen_gun = random.randint(0, gun_count)
				gun_count = 0
				for gun in ship["guns"]:
					gun_count += gun["count"]
					if gun_count >= chosen_gun:
						if gun["count"] is 1:
							crit_message += f"\n The last {gun['name']} was disabled/destroyed."
							gun = None
						else:
							crit_message += f"\n A {gun['name']} was disabled/destroyed."
							gun["count"] -= 1
						break
		elif location is "armour":
			if severity is 1:
				ship["armour"] -= 1
			elif severity is 2:
				ship["armour"] -= random.randint(1, 3)
			elif severity is 3 or 4:
				ship["armour"] -= self.d6()
			elif  severity is 5:
				ship["armour"] -= self.twod6()
			else:
				ship["armour"] -= self.twod6()
			if ship["armour"] < 0:
				ship["armour"] = 0
		elif  location is "hull":
			damage = self.d6(severity)
			crit_message += f"\nShip takes an additional {damage}"
			if m := self.apply_damage_and_sustained_crit(ship, damage):
				crit_message += m



		# Resolve Hull damage effects.
		if (ship["critical_locations"]["hull"] < 6 and
			(location is "power" and severity == 5
			or location is "fuel" and severity == 5
			or location is "weapon" and severity >= 5
			or location is "armour" and severity >= 4
			or location is "m-drive" and severity == 6
			or location is "cargo" and severity >= 5
			or location is "j-drive" and severity >= 4 )):
			crit_message += self.resolve_crit(ship, 1, "hull")
		elif (ship["critical_locations"]["hull"] < 6 and
			(location is "power" and severity == 6
			or location is "fuel" and severity == 6)):
			crit_message += self.resolve_crit(ship, self.d6(), "hull")

		return crit_message


	
	async def ship_attack(self, message, content):
		parts = content.split(' ')
		attacker_name = parts[0]
		weapon_name = parts[1]
		target_name = parts[2]

		attacker = ships[attacker_name]
		weapon = attacker["guns"][weapon_name]
		target = ships[target_name]

		# Try to hit the target
		effect = self.twod6() + weapon["bonus"]
		if effect < 0:
			await message.channel.send("Hey fucker, you missed!")
			return

		# Deal damage
		damage_roll = self.weapon_d6(weapon["damage"], weapon["minyield"]) * weapon["multiplier"]
		if weapon["multiplier"] is 1: damage_roll += effect

		damage_inflicted = damage_roll - target["armour"]

		# Make a message for the user
		attack_message = f"Resolving attack from {target_name}'s {weapon_name} against {target_name}'\n"
		attack_message += f"{target_name} took {damage_inflicted} bringing it down to {target['hp']}."

		# Critical Hit stuff
		crits = []
		sustained_crits = apply_damage_and_sustained_crit(target, damage_inflicted)
		if sustained_crits > 0: crits.append(sustained_crits)

		can_crit_from_weapon = True
		if target["displacement"] > 2000 and weapon["type"] in ["turret", "barbette"]:
			can_crit_from_weapon = False
		elif target["displacement"] > 10000 and weapon["type"] not in ["medium_bay", "large_bay"]:
			can_crit_from_weapon = False
		elif target["displacement"] > 100000 and weapon["type"] not in ["large_bay"]:
			can_crit_from_weapon = False

		if can_crit_from_weapon and effect >= 6 and damage_inflicted > 0:
			treshold = 10
			if target["displacement"] >= 1000:
				treshold = target["hpmax"] / 100
			crits.append(math.ceil(damage_inflicted / treshold))
		
		if len(crits) > 0:
			attack_message += f"\nIn addition one or more critical hits were dealt:\n"
			crit_result = self.resolve_crit(target, crit_severity)
			attack_message += crit_result
		
		
		# Do this last
		if target["hp"] <= 0:
			attack_message += "\nTarget successfully destroyed!"
		
		await message.channel.send(attack_message)







ships = json.load(open('./ships.json'))
token = json.load(open('./token.json'))["token"]

client = TravellerRoller()
client.run(token)

