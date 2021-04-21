from typing import Counter, ItemsView
from sqlalchemy import create_engine, Column, String, Integer, DateTime, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import random
from discord import Embed
from global_items import global_items, global_tags
from datetime import timedelta, datetime

engine = create_engine("sqlite:///db_test.db")
session = sessionmaker(bind=engine)()
Base = declarative_base()

def formatNum(number):
    return ("{:,}".format(number))


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
    grind_end = Column(DateTime)
    earned_money = Column(Integer)
    inventory = relationship("Inventory", backref="owner")

    async def buy_item(self, name, message):
        stock = session.query(Shop).filter(Shop.name == name).first()
        if stock and self.money >= stock.price:
            self.money -= stock.price
            inventory = Inventory(name = name, lvl = stock.lvl, owner = self)
            session.add(inventory)
            session.commit()
            buy_embed = Embed(title = f"Bought Item for {formatNum(stock.price)}", description = f"+{stock.lvl} {name}", color = 0x00ff00)
            buy_embed.add_field(name = "User", value = self.name, inline=False)
            await message.channel.send(embed = buy_embed)

        elif stock and self.money <= stock.price:
            no_money = Embed(title = f"You don't have enough money to pay for the item. You need {formatNum(stock.price - self.money)} more.", color = 0xff0000)
            await message.channel.send(embed = no_money)

        else:
            doesnt_exist = Embed(title = f"{name} is not in the stock.", color = 0xff0000)
            await message.channel.send(embed = doesnt_exist)
    
    async def sell_item(self, name, num, message):
        stock = session.query(Shop).filter(Shop.name == name).first()
        item = list(filter(lambda x: x.name == name, self.inventory))

        if len(item) > 1 and num is None:
            too_many = Embed(title = f"{len(item)} of the same item.", description = f"You have more than 1 item please select one from list below and do $sell {name}-from 0 to {len(item) - 1}", color = 0x8A2BE2)
            too_many.add_field(name = "Items", value = f"{item}")
            await message.channel.send(embed = too_many)
            return
        
        if num is None:
            num = 0

        if stock:
            sell_price = int(stock.price * 0.75)
            self.money += sell_price
            sell_embed = Embed(title = f"Sold item for {formatNum(sell_price)}", description = f"+{item[int(num)].lvl} {name}", color = 0x00ff00)
            sell_embed.add_field(name = "User", value = self.name)
            await message.channel.send(embed = sell_embed)
            session.delete(item[int(num)])
            session.commit()
        else:
            notIn_inv = Embed(title = "Not in the inventory.", description = f"{name} is not in your inventory.")
            await message.channel.send(embed = notIn_inv)

    
    
    @classmethod
    def create(cls, discord_id: int, name: str, fs: int = 0, money: int = 200):
        player = session.query(Player).filter(Player.discord_id == discord_id).first()
        if not player:
            player = cls(discord_id = discord_id, name = name, fs = fs, money = money)
            session.add(player)
            session.commit()
        return player

    async def grind(self, s, message):
        if self.is_grinding is True:
            await message.channel.send("Already grinding.")
            return
        self.is_grinding = True
        money_sec = 200000000 / 3600
        earned_money = money_sec * s
        self.earned_money = round(earned_money)
        now = datetime.now()
        tdelta = timedelta(seconds = s)
        self.grind_end = now + tdelta
        session.commit()

    async def grind_info(self, message):
        now = datetime.now()
        try:
            if now >= self.grind_end:
                self.money += self.earned_money
                self.is_grinding = False
                self.grind_end = None
                ended = Embed(title = f"Finished grinding.", description = f"{message.author.mention} You've earned {formatNum(self.earned_money)} in total. Your current money amount is {formatNum(self.money)}", color = 0x00ff00)
                self.earned_money = None
                await message.channel.send(embed = ended)
                session.commit()
            else:
                await message.channel.send(f"{self.grind_end - now} left till the end of your grind.")
        except TypeError:
            await message.channel.send("You are not grinding. Type $grind (seconds) to start")
    async def stop_grind(self, message):
        self.is_grinding = False
        self.grind_end = None
        self.earned_money = None
        session.commit()
        await message.channel.send("Succesfuly stopped grind.")
        
    async def enhance(self, name, message, num):
        try:
            for i in range(0, 1):
                item = list(filter(lambda x: x.name == name, self.inventory))
                if len(item) > 1 and num is None:
                    too_many = Embed(title = f"{len(item)} of the same item.", description = f"You have more than 1 item please select one from list below and do $enhance {name}-from 0 to {len(item) - 1}", color = 0x8A2BE2)
                    too_many.add_field(name = "Items", value = f"{item}")
                    await message.channel.send(embed = too_many)
                    return

                if num is None:
                    num = 0

                lvl = item[int(num)].lvl
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
                    item[int(num)].lvl = 1 + item[int(num)].lvl
                    session.commit()
                    success = Embed(title = "Enhancment Succeded!", description = f"You've succeded on enhancing +{item[int(num)].lvl} {name} at {chance}%", color = 0x00ff00)
                    await message.channel.send(embed = success)
                else:
                    fail = Embed(title = "Enhancment Failed!", description = f"You've failed on enhancing +{item[int(num)].lvl + 1} {name} at {chance}%", color = 0xff0000)
                    self.fs += 1
                    if search_g[0] == "Acc":
                        session.delete(item[0])
                        session.commit()
                    if lvl > 16:
                        item[int(num)].lvl = lvl - 1
                        session.commit()
                        fail.add_field(name = "Item level dropped!", value = f"{name} level dropped due to enhancment failure.")
                        
                    await message.channel.send(embed = fail)
            
        except IndexError:
            await message.channel.send("Item is not in the inventory")
        #except:
         #   await message.channel.send(f"{name} cannot be enhanced")


    
Base.metadata.create_all(engine)