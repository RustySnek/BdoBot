from sqlalchemy import create_engine, Column, String, Integer, Boolean, ForeignKey
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

class Shop(Base):
    __tablename__ = "shop"
    
    _id = Column(Integer, primary_key= True)
    name = Column(String)
    lvl = Column(Integer)
    price = Column(Integer)

    @classmethod
    def add_item(cls, name: str, lvl: int, price: int):
        s = session.query(Shop).filter(Shop.name == name).first()
        if not s:
            s = Shop(name = name, lvl = lvl, price = price)
            session.add(s)
            session.commit()
        return 
    
    @classmethod
    def remove_item(cls, name: str):
        s = session.query(Shop).filter(Shop.name == name).first()
        if s:
            session.delete(s)
            session.commit()
        


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

    def buy_item(self, name):
        stock = session.query(Shop).filter(Shop.name == name).first()
        if stock and self.money >= stock.price:
            self.money -= stock.price
            inventory = Inventory(name = name, lvl = stock.lvl, owner = self)
            session.add(inventory)
            session.commit()
    
    
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
                item = session.query(Inventory).filter(Inventory.name == name and Inventory.owner_id == self._id).all()
                lvl = item[0].lvl
                if lvl == 20:
                    return
                split_name = name.split(" ", 1)[0]
                tag = global_tags[split_name]
                search_g = list(filter(lambda global_item: global_item[0] == tag and global_item[1] == lvl, global_items))[0]
                if search_g[0] == "Acc" and lvl == 4:
                    return
                chance, soft_cap ,pre_soft_cap, post_soft_cap = search_g[2], search_g[3], search_g[4], search_g[5]
                fs = self.fs
                x = random.randint(0, 100)

                if fs < soft_cap:
                    chance += fs*pre_soft_cap
                elif fs >= post_soft_cap:
                    chance += soft_cap*pre_soft_cap
                    chance += (fs - soft_cap)*post_soft_cap

                if chance > 90:
                    chance = 90
                if search_g[0] != "Acc":
                    if lvl <= 7:
                        chance = 100

                if x <= chance:
                    if lvl > 8:
                        self.fs = 0
                    item[0].lvl = 1 + item[0].lvl
                    session.commit()
                    await message.channel.send("enchancment succeded " + str(name) + " +" + str(item[0].lvl) + " at " + str(chance) + "%")
                else:
                    await message.channel.send("enhancment failed " + str(name) + " +" + str(item[0].lvl + 1) + " at " + str(chance) + "%")
                    self.fs += 1
                    if search_g[0] == "Acc":
                        session.delete(item[0])
                        session.commit()
                    if lvl > 16:
                        item[0].lvl = lvl - 1
                        session.commit()
        except IndexError:
           await message.channel.send("Item is not in the inventory")
    

Base.metadata.create_all(engine)

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
