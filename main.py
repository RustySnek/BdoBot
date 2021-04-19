import discord
from classes import Player, session, Inventory, Shop

client = discord.Client()


@client.event
async def on_message(message):
    name = str(message.author.name)
    dc_id = int(message.author.id)
    
    if message.author == client.user:
        return
    if message.content.startswith("$grind"):
        player = Player.create(dc_id, name)
        sec = message.content[7:]
        await player.grind(int(sec))
    
    if message.content.startswith("$buy"):
        player = Player.create(dc_id, name)
        item = message.content[5:]
        player.buy_item(item)
    
    if message.content.startswith("$enhance"):
        player = Player.create(dc_id, name)
        item = message.content[9:]
        await player.enhance(item, 1, message)
    
    if message.content.startswith("$inventory"):
        player = Player.create(dc_id, name)
        inv = session.query(Inventory).filter(Inventory.owner_id == player._id).all()
        for item in inv:
            await message.channel.send(item)
        
    if message.content.startswith("$money"):
        player = Player.create(dc_id, name)
        await message.channel.send("money: " + str(player.money))
    
    if message.content.startswith("$sadd"):
        content = message.content[6:]
        name, lvl, price = content.split("-")
        if dc_id == 683075740790423587:
            shop = Shop.add_item(name, lvl, price)
    
    if message.content.startswith("$srm"):
        name = message.content[5:]
        if dc_id == 683075740790423587:
            shop = Shop.remove_item(name)
        
client.run("ODMyNTgyODczNzA1ODczNDI5.YHl5OQ.8VjlEir2EFS8xiiUDBb4buiS_XA")
