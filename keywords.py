import discord
from discord import Embed
from discord.utils import get
from classes import Player, grind_spots, session, Inventory, Shop, formatNum, colors
import asyncio

client = discord.Client()


def check(author, message):
    def inner_check(message):
        return message.author == author

    return inner_check


async def sendMsg(message, content: str):
    await message.channel.send(content)


async def grind(message, player):
    author = message.author
    await message.channel.send(
        f"{author.mention} For how long do you wish to grind? Type value in seconds."
    )

    for i in range(5):
        try:
            choice = await client.wait_for(
                "message", check=check(author, message), timeout=15
            )
            sec = int(choice.content)
            await player.grind(sec, message)
            break
        except asyncio.exceptions.TimeoutError:
            await message.channel.send(f" {author.mention} Timed out!")
            return
        except ValueError:
            await message.channel.send(
                f" {author.mention} Invalid number. Did you make a typo?"
            )
            continue


async def ginfo(message, player):
    author = message.author
    await player.grind_info(message)


async def stockAdd(message, player):
    author = message.author

    def emoteCheck(emote, user):
        return user == message.author

    if author.id != 683075740790423587:
        return
    for i in range(0, 3):
        try:
            await sendMsg(message, "Name?")
            getName = await client.wait_for(
                "message", check=check(author, message), timeout=30
            )
            name = getName.content
            await sendMsg(message, "Level?")
            getLevel = await client.wait_for(
                "message", check=check(author, message), timeout=30
            )
            level = int(getLevel.content)
            await sendMsg(message, "Price?")
            getPrice = await client.wait_for(
                "message", check=check(author, message), timeout=30
            )
            price = int(getPrice.content)
            await sendMsg(message, "Stackable?")
            getStackable = await client.wait_for(
                "message",
                check=lambda x: x.content.lower() == "true"
                or x.content.lower() == "false"
                and message.author == author,
                timeout=30,
            )
            stackable = getStackable.content
            statCheck = Embed(
                title="Is that correct?",
                description=f"Name: {name} \nLevel: {level} \nPrice: {formatNum(price)} \nStackable: {stackable}",
                color=0x8A2BE2,
            )
            msg = await message.channel.send(embed=statCheck)
            await msg.add_reaction("👍")
            await msg.add_reaction("👎")
            await asyncio.sleep(1)
            reaction, user = await client.wait_for("reaction_add", check=emoteCheck)
            if reaction.emoji not in ["👎", "👍"]:
                return
            if reaction.emoji == "👎":
                await sendMsg(message, "Aborted.")
                break
            elif reaction.emoji == "👍":
                if stackable.lower() == "true":
                    stackable = True
                elif stackable.lower() == "false":
                    stackable = False
                await Shop.add_item(name, level, price, stackable, message)
                await sendMsg(message, f"Added *{name}* to the item shop.")
            else:
                pass
            break
        except ValueError:
            await sendMsg(message, "Value Error.")
            continue


async def stockRm(message, player):
    author = message.author
    if author.id != 683075740790423587:
        return

    await sendMsg(message, "What item would you like to remove?")
    itemName = await client.wait_for(
        "message", check=check(author, message), timeout=20
    )
    stock = session.query(Shop).filter(Shop.name == itemName.content).first()
    if not stock:
        await sendMsg(message, f"No {itemName.content} in the stock!")
        return
    stats = [stock.name, stock.lvl, stock.price, stock.stackable]

    statEmbed = Embed(
        title=f"You are about to remove {stats[0]}. Are you sure? (Y/N)",
        description=f"Name: {stats[0]}\n Level: {stats[1]}\n Price: {stats[2]}\n Stackable: {stats[3]} ",
        color=0x8A2BE2,
    )
    await message.channel.send(embed=statEmbed)
    for i in range(0, 3):
        reply = await client.wait_for(
            "message", check=check(author, message), timeout=10
        )
        if reply.content.lower() == "y":
            s = Shop.remove_item(itemName.content)
            await sendMsg(message, f"Successfully removed {stats[0]}")
            break
        elif reply.content.lower() == "n":
            await sendMsg(message, "Aborted.")
            break
        else:
            continue


async def stock(message, player):
    currentStock = session.query(Shop).all()
    items = ""
    for item in currentStock:
        items += f"+{item.lvl} {item.name} *{formatNum(item.price)}$*\n"
    stockEmbed = Embed(title="Stock", description=items, color=0x00FF00)
    await message.channel.send(embed=stockEmbed)


async def buy(message, player):
    author = message.author
    await sendMsg(message, f"{author.mention} What item do you want to buy?")
    for i in range(5):
        try:
            item_choice = await client.wait_for(
                "message", check=check(author, message), timeout=15
            )
            if item_choice.content == "$stock":
                continue
            stock = session.query(Shop).filter(
                Shop.name == item_choice.content).first()
            if stock:
                await sendMsg(
                    message, f"{author.mention} How many of them do you want to buy?"
                )
                for i in range(3):
                    try:
                        getQuantity = await client.wait_for(
                            "message", check=check(author, message), timeout=15
                        )
                        quantity = int(getQuantity.content)
                        if stock.stackable is False and quantity > 5:
                            await sendMsg(
                                message,
                                "Can't buy more than 5 of this item. Maximum quantity is 5.",
                            )
                            continue
                        if quantity <= 0:
                            await sendMsg(message, "Can't buy less than 1.")
                            continue
                        await player.buy_item(item_choice.content, quantity, message)
                        break
                    except ValueError:
                        await sendMsg(message, "Wrong quantity number.")
                        continue
                    except asyncio.exceptions.TimeoutError:
                        await sendMsg(message, f"{author.mention} Timed out!")
                        break
            else:
                await sendMsg(
                    message,
                    "Did you make a typo? Type $stock for list of available items.",
                )
            break

        except ValueError:
            await sendMsg(
                message, "Did you make a typo? Type $stock for list of available items."
            )
            continue
        except asyncio.exceptions.TimeoutError:
            await sendMsg(message, f"{author.mention} Timed out!")
            break


async def sell(message, player):
    author = message.author

    async def sell(chosenItem):
        for i in range(0, 2):
            try:
                stock = (
                    session.query(Shop).filter(
                        Shop.name == item_name.content).first()
                )
                if not stock:
                    await message.channel.send("Item is not sellable.")
                    break
                chosenItemEmbed = Embed(
                    title="Are you sure you want to sell this item? (Y/n)",
                    description=f"Name: {chosenItem.name}\n Lvl: {chosenItem.lvl}\n Durability: {chosenItem.durability}\n Stackable: {chosenItem.stackable}\n Sell Price: *{stock.price * 0.75} $*",
                    color=colors["purple"],
                )
                await message.channel.send(embed=chosenItemEmbed)
                answer = await client.wait_for(
                    "message", check=check(author, message), timeout=20
                )
                for i in range(0, 2):
                    try:
                        if (
                            answer.content.lower() == "yes"
                            or answer.content.lower() == "y"
                        ):
                            await player.sell_item(
                                item_name.content, chosenItem._id, message
                            )
                            break
                        elif (
                            answer.content.lower() == "no"
                            or answer.content.lower() == "n"
                        ):
                            await sendMsg(message, "Aborting.")
                            break
                        else:
                            continue
                    except asyncio.exceptions.TimeoutError:
                        await sendMsg(message, f"{author.mention} Timed out!")
                        break
                break
            except asyncio.exceptions.TimeoutError:
                await sendMsg(message, f"{author.mention} Timed out!")
                break

    await sendMsg(message, f"{author.mention} What item do you want to sell?")
    for i in range(3):
        try:
            item_name = await client.wait_for(
                "message", check=check(author, message), timeout=20
            )
            item_check = (
                session.query(Inventory)
                .filter(Inventory.name == item_name.content)
                .all()
            )
            if len(item_check) == 0:
                await sendMsg(
                    message,
                    f"{author.mention} {item_name.content} is not in your inventory.",
                )
                break
            elif len(item_check) > 1:
                strOfItems = ""
                slotNum = 1
                for item in item_check:
                    strOfItems += f"{slotNum}. +{item.lvl} {item.name}\n"
                    slotNum += 1
                item_list = Embed(
                    title="Multiple of the same item. Choose one to sell.",
                    description=strOfItems,
                    color=colors["purple"],
                )
                await message.channel.send(embed=item_list)
                slotToSell = await client.wait_for(
                    "message", check=check(author, message), timeout=20
                )
                chosenItem = item_check[int(slotToSell.content)]
                await sell(chosenItem)

            elif len(item_check) == 1:
                item = item_check[0]
                await sell(item)
        except asyncio.exceptions.TimeoutError:
            await sendMsg(message, f"{author.mention} Timed out!")
            break
        break


async def money(message, player):
    author = message.author
    await sendMsg(message, f"{author.mention} Purse: {formatNum(player.money)}$")


async def inventory(message, player):
    items = []
    inv = session.query(Inventory).filter(
        Inventory.owner_id == player._id).all()
    for item in inv:
        items.append(
            f"+{item.lvl} {item.name} Durability: *{item.durability}*")
    joined = "\n".join(items)
    items_embed = discord.Embed(
        title="Inventory", description=joined, color=0x2B908F)
    await message.channel.send(embed=items_embed)


async def naderr_change(message, player):
    await player.naderr_change(message, player, client)


async def enhance(message, player):
    author = message.author
    await sendMsg(message, "What item do you want to enhance?")
    for i in range(0, 2):
        try:
            item_name = await client.wait_for(
                "message", check=check(author, message), timeout=20
            )
            itemInv = list(
                filter(lambda x: x.name == item_name.content, player.inventory)
            )
            if len(itemInv) == 0:
                await sendMsg(
                    message,
                    f"{item_name.content} is not in your inventory. Type again.",
                )
                continue
            elif len(itemInv) == 1:
                await player.enhance(int(itemInv[0]._id), message, client)
                break
            elif len(itemInv) > 1:
                itemstr = ""
                itemslot = 1
                for item in itemInv:
                    itemstr += f"{itemslot}. +{item.lvl} {item.name} Durability: {item.durability}\n"
                    itemslot += 1
                multiple = Embed(
                    title="Multiple of the same item. Choose one to enhance.",
                    description=f"{itemstr}",
                    color=colors["purple"],
                )
                await message.channel.send(embed=multiple)
                for i in range(0, 2):
                    try:
                        slot = await client.wait_for(
                            "message", check=check(author, message), timeout=20
                        )
                        itemId = itemInv[int(slot.content) - 1]._id
                        await player.enhance(int(itemId), message, client)
                        break
                    except asyncio.exceptions.TimeoutError:
                        await sendMsg(message, f"{author.mention} Timed out!")
                        break
                    except IndexError:
                        await sendMsg(message, f"{author.mention} Wrong slot number.")
                        continue
        except asyncio.exceptions.TimeoutError:
            await sendMsg(message, f"{author.mention} Timed out!")
            break
        break


async def enhlast(message, player):
    if player.last_enhanced_id == None:
        await sendMsg(message, "Do $enhance before you can use this command.")
        return
    await player.enhance(player.last_enhanced_id, message, client)


async def repair(message, player):
    author = message.author
    await sendMsg(message, "What item do you want to repair?")
    for i in range(0, 2):
        try:
            item_name = await client.wait_for(
                "message", check=check(author, message), timeout=20
            )
            items = list(
                filter(lambda x: x.name == item_name.content, player.inventory)
            )

            async def getValue(slot):
                await sendMsg(
                    message, "How many points of durability do you want to repair?"
                )
                for i in range(0, 2):
                    value = await client.wait_for(
                        "message", check=check(author, message), timeout=20
                    )
                    try:
                        await player.repair(
                            items[int(slot)]._id, int(value.content), message
                        )
                        break
                    except ValueError:
                        await sendMsg(
                            message,
                            f"{author.mention} Wrong value amount. Did you make a typo?",
                        )
                        continue
                    except asyncio.exceptions.TimeoutError:
                        await sendMsg(message, f"{author.mention} Timed out!")
                        break

            if len(items) == 0:
                await sendMsg(
                    message,
                    f"{author.mention} {item_name.content} is not in your inventory. Did you make a typo?",
                )
                continue
            elif len(items) == 1:
                await getValue(0)
            elif len(items) > 1:
                item_str = ""
                item_slot = 1
                for item in items:
                    item_str += f"{item_slot}. +{item.lvl} {item_name.content} Durability: {item.durability}\n"
                    item_slot += 1
                itemsEmbed = Embed(
                    title="Multiple of the same item. Choose one to repair.",
                    description=f"{item_str}",
                    color=colors["purple"],
                )
                await message.channel.send(embed=itemsEmbed)
                slot = await client.wait_for(
                    "message", check=check(author, message), timeout=20
                )
                await getValue(int(slot.content) - 1)
        except asyncio.exceptions.TimeoutError:
            await sendMsg(message, f"{author.mention} Timed out!")
            break
        break


@client.event
async def on_message(message):
    if message.author == client.user:
        return

    author = message.author
    p_name = str(author.name)
    dc_id = int(author.id)
    player = Player.create(dc_id, p_name)

    keywords = {
        "$grind": grind,
        "$ginfo": ginfo,
        "$stock": stock,
        "$stockadd": stockAdd,
        "$stockrm": stockRm,
        "$inventory": inventory,
        "$buy": buy,
        "$sell": sell,
        "$money": money,
        "$enhance": enhance,
        "$enhlast": enhlast,
        "$repair": repair,
        "$naderr": naderr_change,
    }
    if message.content.lower() in keywords:
        await keywords[message.content.lower()](message, player)

<<<<<<< HEAD
=======
client.run("Your Token")
>>>>>>> f6f85a9187a4bfb8eb6f8672e422866fa2d99e2a

client.run("TOKEN")
