from sqlalchemy import create_engine, Column, String, Integer, Boolean, Date, Float, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import random
import discord
from global_items import global_items, global_tags
from asyncio import sleep

client = discord.Client()

engine = create_engine("sqlite:///db_test.db")
session = sessionmaker(bind=engine)()
Base = declarative_base()


class Item:
    def __init__(self, name: str) -> None:  
        self.name = name

def to_dict(x):
    return x.__dict__

class Shop:
    def __init__(self, stock: dict = {}) -> None:
        self.stock = stock

    def add_item(self, item: dict, price):
        
        if item.get("name") not in self.stock:
            self.stock[item.get("name")] = price
        elif item.get("name") in self.stock:
            print("item already in stock")
        else:
            print("Item does not exist.")

class Inventory(Base):
    __tablename__ = "inventory"

    _id = Column(Integer, primary_key = True)
    name = Column(String)
    lvl = Column(Integer)
    owner_id = Column(Integer, ForeignKey("player._id"))

    def __repr__(self) -> str:
        return "+" + str(self.lvl) + " " + str(self.name)
    

class Player(Base):
    __tablename__ = "player"

    _id = Column(Integer, primary_key = True)
    discord_id = Column(Integer)
    name = Column(String)
    fs = Column(Integer)
    money = Column(Integer)
    is_grinding = Column(Boolean)
    inventory = relationship("Inventory", backref="owner")

    def buy_item(self, name, s):
        if name in s.stock and self.money >= s.stock[name]:
            print(s.stock[name])
            self.money -= s.stock[name]
            inventory = Inventory(name = name, lvl = 0, owner = self)
            session.add(inventory)
            session.commit()
        else:
            print("error" + str(name))
    
    
    @classmethod
    def create(cls, discord_id: int, name: str, fs: int = 0, money: int = 200):
        player = session.query(Player).filter(Player.discord_id == discord_id).first()
        if not player:
            player = cls(discord_id = discord_id, name = name, fs = fs, money = money)
            session.add(player)
            session.commit()
        return player

    async def grind(self, s):
        if self.is_grinding is True:
            return
        self.is_grinding = True
        money_sec = 200000000 / 3600
        earned_money = money_sec * s
        session.commit()
        await sleep(s)
        self.money += round(earned_money)
        self.is_grinding = False
        session.commit()
        
    async def enhance(self, name, times, message):
        try:
            for i in range(0, times):
                item = session.query(Inventory).filter(Inventory.owner_id == self._id and Inventory.name == name).all()
                lvl = item[0].lvl
                tag = global_tags[name]
                if lvl == 20:
                    return
                search_g = list(filter(lambda global_item: global_item[0] == tag and global_item[1] == lvl, global_items))
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
                
                if lvl <= 7:
                    chance = 100
                elif lvl == 8:
                    chance = 90

                if x <= chance:
                    if lvl > 8:
                        self.fs = 0
                    item[0].lvl = 1 + item[0].lvl
                    session.commit()
                    await message.channel.send("enchancment succeded " + str(name) + " +" + str(item[0].lvl) + " at " + str(chance) + "%")
                else:
                    await message.channel.send("enhancment failed " + str(name) + " +" + str(item[0].lvl + 1) + " at " + str(chance) + "%")
                    self.fs += 1
                    if lvl > 16:
                        item[0].lvl = lvl - 1
                        session.commit()
        except:
            print("Item is not in the inventory")
    

Base.metadata.create_all(engine)
s = Shop()
s.add_item(to_dict(Item("Kzarka Longbow")), 20)
s.add_item(to_dict(Item("Kzarka Sword")), 20)

@client.event
async def on_message(message):
    global s
    name = str(message.author.name)
    dc_id = int(message.author.id)
    
    if message.author == client.user:
        return
    #try:
    if message.content.startswith("$grind"):
        player = Player.create(dc_id, name)
        sec = message.content[7:]
        await player.grind(int(sec))
    
    if message.content.startswith("$buy"):
        player = Player.create(dc_id, name)
        item = message.content[5:]
        print(item)
        player.buy_item(item, s)
    
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
    #except:
     #  await message.channel.send("You are not registered yet. Type $register")

client.run("ODMyNTgyODczNzA1ODczNDI5.YHl5OQ.yZe6XDc9hI_zflsfzbzSHe1nJj8")
#inventory = Inventory(name = "Kzarka Longbow", lvl = 2, owner = player)
#inventory1 = Inventory(name = "Kzarka Longsword", lvl = 1, owner = player)
