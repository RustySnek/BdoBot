import discord
from classes import Player, session, Inventory, Shop, formatNum

client = discord.Client()


@client.event
async def on_message(message):
    p_name = str(message.author.name)
    dc_id = int(message.author.id)
    
    if message.author == client.user:

        return
    if message.content.startswith("$grind"):
        player = Player.create(dc_id, p_name)
        sec = message.content[7:]
        await player.grind(int(sec), message)
    
    if message.content.startswith("$ginfo"):
        player = Player.create(dc_id, p_name)
        await player.grind_info(message)

        
    
    if message.content.startswith("$buy"):
        player = Player.create(dc_id, p_name)
        item = message.content[5:]
        await player.buy_item(item, message)    
    
    if message.content.startswith("$sell"):
        player = Player.create(dc_id, p_name)
        item = message.content[6:]
        try:
            name, num = item.split("-")
        except:
            name = message.content[6:]
            num = None
        await player.sell_item(name, num, message)
    
    if message.content.startswith("$enhance"):
        player = Player.create(dc_id, p_name)
        item = message.content[9:]
        try:
            name, num = item.split("-")
        except:
            name = message.content[9:]
            num = None
        await player.enhance(name, message, num)
    
    if message.content.startswith("$inventory"):
        items = []
        player = Player.create(dc_id, p_name)
        inv = session.query(Inventory).filter(Inventory.owner_id == player._id).all()
        for item in inv:
            items.append("+" + str(item.lvl) + " " + str(item.name))
        
        joined = ", ".join(items)
        items_embed = discord.Embed(title = "Inventory", description = joined, color = 0x2B908F)
        await message.channel.send(embed = items_embed)
        
    if message.content.startswith("$money"):
        player = Player.create(dc_id, p_name)
        await message.channel.send("money: " + str(formatNum(player.money)))
    
    if message.content.startswith("$sadd"):
        content = message.content[6:]
        try:
            name, lvl, price = content.split("-")
        except ValueError:
            await message.channel.send("Wrong syntax do name-lvl-price")
            return
        if dc_id == 683075740790423587:
            shop = Shop.add_item(name, lvl, price)
        else:
            await message.channel.send("You don't have permission to do that.")
    
    if message.content.startswith("$stopgrind"):
        player = Player.create(dc_id, p_name)
        await player.stop_grind(message)


    if message.content.startswith("$srm"):
        name = message.content[5:]
        if dc_id == 683075740790423587:
            try:
                shop = Shop.remove_item(name)
            except:
                await message.channel.send("Item does not exist in the database.")
        else:
            await message.channel.send("You don't have permission to do that.")
        
client.run("ODMyNTgyODczNzA1ODczNDI5.YHl5OQ.yXDJ1XCZWDQMkc0kDI6sI6x7wGw")
