import random
import discord
from global_items import global_items
from asyncio import sleep

client = discord.Client()

class Item:
    def __init__(self, name: str) -> None:  
        self.name = name

def to_dict(x):
    return x.__dict__

class Shop:
    def __init__(self, stock: dict = None) -> None:
        if stock is None:
            self.stock = {}
        else:
            self.stock = stock

    def add_item(self, item: dict, price):
        
        if item.get("name") not in self.stock:
            self.stock[item.get("name")] = price
        elif item.get("name") in self.stock:
            print("item already in stock")
        else:
            print("Item does not exist.")
            
class Inventory:
    def __init__(self, items :list = None, money: int = 100) -> None:
        if items is None:
            self.items = []
        else:
            self.items = items
        self.slots = 100
        self.money = money
        self.slot = []

class Player:
    def __init__(self, lvl: int, name:str,fs: int = 0,  inventory = Inventory()) -> None:
        self.lvl = lvl
        self.name = name
        self.inventory = inventory
        self.fs = fs
        self.is_grinding = False
    
    def buy_item(self, name, shop):
        self.inventory.slots = 100
        if name in shop.stock:
            price = shop.stock[name]
            if self.inventory.money >= price:
                self.inventory.money -= price
                self.inventory.items.append([name, 0])
                print(self.inventory.items)
            else:
                print("you dont have enough money")
        else:
            print("item does not exist")

    def enhance(self, name, times):
        for i in range(0, times):
            try:
                item = list(filter(lambda item: item[0] == name, self.inventory.items))
                #item[0][1] = item[0][1]
                if item[0][1] == 20:
                    return
                search_g = list(filter(lambda global_item: global_item[0] ==  name and global_item[1] == item[0][1], global_items))
                chance = search_g[0][2]
                sc = search_g[0][3]
                pre_sc = search_g[0][4]
                post_sc = search_g[0][5]
                fs = self.fs
                print("fs: " + str(fs))
                x = random.randint(0, 100)

                if fs < sc:
                    chance += fs*pre_sc
                elif fs >= post_sc:
                    chance += sc*pre_sc
                    chance += (fs - sc)*post_sc
                
                if chance > 90:
                    chance = 90
                
                if item[0][1] <= 7:
                    chance = 100
                elif item[0][1] == 8:
                    chance = 90

                if x <= chance:
                    if item[0][1] > 8:
                        self.fs = 0
                    print("enchancment succeded " + str(item[0][0]) + " +" + str(item[0][1]))
                    item[0][1] += 1
                else:
                    print("enhancment failed " + str(item[0][0]) + " +" + str(item[0][1]))
                    self.fs += 1
                    if item[0][1] > 16:
                        item[0][1] -= 1
            except:
                print("Item is not in the inventory")
        
    async def grind(self, s):
        if self.is_grinding is True:
            return
        self.is_grinding = True
        money_sec = 200000000 / 3600
        earned_money = money_sec * s
        await sleep(s)
        self.inventory.money += round(earned_money)
        self.is_grinding == False
        print(self.inventory.money)


class Game:
    def __init__(self, players: list = None) -> None:
        if players is None:
            self.players =  []
        else:
            self.players = players

p = Player(0, "Terry", 10)
s = Shop()
s.add_item(to_dict(Item("Kzarka Longbow")), 20)
@client.event
async def on_message(message):
    global s
    if message.author == client.user:
        return

    if message.content.startswith('$grind'):
        sec = message.content[7:]
        await p.grind(int(sec))
    
    if message.content.startswith("$buy"):
        item = message.content[5:]
        p.buy_item(item, s)
    
    if message.content.startswith("$enhance"):
        item = message.content[9:]
        p.enhance(item, 1)


client.run("ODMyNTgyODczNzA1ODczNDI5.YHl5OQ.ndiEdf5QOgqKrtXgLRmeX6bFo8w")