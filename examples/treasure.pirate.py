# tongue: pirate
# Swashbuckling Pirate Example

galleon TreasureChest:
    chart __init__(self, gold_coins):
        self.gold = gold_coins

    chart loot(self, amount):
        perchance amount <= self.gold:
            self.gold -= amount
            booty aye
        otherwise_avast:
            booty nay

chest = TreasureChest(500)
success = chest.loot(150)
ahoy(f"Loot successful: {success}, Remaining gold: {chest.gold}")
