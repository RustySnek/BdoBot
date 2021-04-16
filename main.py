import random
from global_items import global_items
from asyncio import sleep

class Item:
    def __init__(self, name: str) -> None:  
        self.name = name

async def grind(s, p):
    if p.is_grinding is True:
        return

    p.is_grinding == True
    money_sec = 200000000 / 3600
    earned_money = money_sec * s
    sleep(s)
    p.inventory.money += round(earned_money)
    p.is_grinding == False
    print(p.inventory.money)


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
                self.inventory.items.append([name, 1])
                print(self.inventory.items)
            else:
                print("you dont have enough money")
        else:
            print("item does not exist")

    def enhance(self, name):
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
            x = random.randint(0, 100)

            if fs < sc:
                chance += fs*pre_sc
            elif fs >= post_sc:
                chance += sc*pre_sc
                chance += (fs - sc)*post_sc
            
            if chance > 90:
                chance = 90
            
            if item[0][1] < 8:
                chance = 100

            if x <= chance:
                if item[0][1] > 8:
                    self.fs = 0
                item[0][1] += 1
                print("enchancment succeded")
                print(item[0][1])
            else:
                print("enhancment failed")
                self.fs += 1
                if item[0][1] > 16:
                    item[0][1] -= 1
        except:
            print("Item is not in the inventory")

class Game:
    def __init__(self, players: list = None) -> None:
        if players is None:
            self.players =  []
        else:
            self.players = players

p = Player(0, "Terry", 9999)
s = Shop()
s.add_item(to_dict(Item("Rusty Sword")), 20)
s.add_item(to_dict(Item("Rusty Axe")), 10)
s.add_item(to_dict(Item("Kzarka Longbow")), 20)

#p.buy_item("Rusty Sword", s)
p.buy_item("Kzarka Longbow", s)
#p.buy_item("Rusty Axe", s)
#p.buy_item("Rusty Axe", s)

#p.enhance("Rusty Axe")
#p.enhance("Rusty Axe")
#p.enhance("Rusty Sword")
p.enhance("Kzarka Longbow")
grind(2, p)
p.buy_item("Kzarka Longbow", s)
