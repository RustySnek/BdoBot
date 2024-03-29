from typing import Counter, ItemsView
from sqlalchemy import (
    create_engine,
    Column,
    String,
    Integer,
    DateTime,
    Boolean,
    ForeignKey,
)
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
# lvl/Mph/EXPph
grind_spots = {"Goblins": [0, 10000, 3000]}

colors = {
    "purple": 0x8A2BE2,
    "red": 0xFF0000,
    "green": 0x00FF00,
    "black": 0x0F0F0F,
    "white": 0xF0F0F0,
    "grey": 0x525252,
}


def formatNum(number):
    return "{:,}".format(number)


class Shop(Base):
    __tablename__ = "shop"

    _id = Column(Integer, primary_key=True)
    name = Column(String)
    lvl = Column(Integer)
    price = Column(Integer)
    stackable = Column(Boolean)

    @classmethod
    async def add_item(cls, name: str, lvl: int, price: int, stackable, message):
        s = session.query(Shop).filter(Shop.name == name).all()
        if not s:
            s = Shop(name=name, lvl=int(lvl), price=int(
                price), stackable=stackable)
            session.add(s)
            session.commit()
        else:
            await message.channel.send("Item already exists")
            return

    @classmethod
    def remove_item(cls, name: str):
        s = session.query(Shop).filter(Shop.name == name).first()
        if s:
            session.delete(s)
            session.commit()


class Naderr(Base):
    __tablename__ = "naderr"

    _id = Column(Integer, primary_key=True)
    fs = Column(Integer)
    owner_id = Column(Integer, ForeignKey("player._id"))


class Inventory(Base):
    __tablename__ = "inventory"

    _id = Column(Integer, primary_key=True)
    name = Column(String)
    lvl = Column(Integer)
    durability = Column(Integer)
    stackable = Column(Boolean)
    quantity = Column(Integer)
    owner_id = Column(Integer, ForeignKey("player._id"))


class Player(Base):
    __tablename__ = "player"

    _id = Column(Integer, primary_key=True)
    discord_id = Column(Integer)
    name = Column(String)
    fs = Column(Integer)
    money = Column(Integer)
    is_grinding = Column(Boolean)
    grind_end = Column(DateTime)
    earned_money = Column(Integer)
    last_enhanced_id = Column(Integer)
    inventory = relationship("Inventory", backref="owner")
    naderr = relationship("Naderr", backref="owner")

    async def buy_item(self, name, quantity, message):
        stock = session.query(Shop).filter(Shop.name == name).first()
        if stock and self.money >= stock.price * quantity:
            if stock.stackable is False:
                self.money -= stock.price * quantity
                for i in range(0, quantity):
                    inventory = Inventory(
                        name=name, lvl=stock.lvl, durability=100, owner=self
                    )
                    session.add(inventory)
                    session.commit()
                buy_embed = Embed(
                    title=f"Bought {quantity} item/s for {formatNum(stock.price * quantity)}",
                    description=f"{name}",
                    color=colors["green"],
                )
                buy_embed.add_field(name="User", value=self.name, inline=False)
                await message.channel.send(embed=buy_embed)
            elif stock.stackable is True:

                self.money -= stock.price * quantity
                inventory = Inventory(name=name, quantity=quantity, owner=self)
                buy_embed = Embed(
                    title=f"Bought {quantity} items for {formatNum(stock.price * quantity)}",
                    description=f"{name}",
                    color=colors["green"],
                )
                buy_embed.add_field(name="User", value=self.name, inline=False)
                await message.channel.send(embed=buy_embed)

        else:
            no_money = Embed(
                title=f"You don't have enough money to pay for the item. You need {formatNum(stock.price * quantity - self.money)} more.",
                color=colors["red"],
            )
            await message.channel.send(embed=no_money)

    async def sell_item(self, name: str, _id: int, message):
        stock = session.query(Shop).filter(Shop.name == name).first()
        item = list(filter(lambda x: x._id == _id, self.inventory))[0]
        sell_price = int(stock.price * 0.75)
        self.money += sell_price
        sell_embed = Embed(
            title=f"Sold item for *{formatNum(sell_price)} $*",
            description=f"+{item.lvl} {name}",
            color=colors["green"],
        )
        sell_embed.add_field(name="User", value=f"{message.author.mention}")
        await message.channel.send(embed=sell_embed)
        session.delete(item)
        session.commit()

    async def repair(self, _id: int, value: int, message):

        item = list(filter(lambda x: x._id == _id, self.inventory))[0]
        if item.durability == 100:
            await message.channel.send("Item is already at full durability.")
            return

        if item.durability + value > 100:
            await message.channel.send(
                f"Maximum durability can't exceed 100. Changed value to {100-item.durability}."
            )
            value = 100 - item.durability

        item.durability += value
        repair_embed = Embed(
            title="Repair",
            description=f"Repaired {item.name}. Current durability is {item.durability}.",
            color=colors["green"],
        )
        await message.channel.send(embed=repair_embed)

    @classmethod
    def create(cls, discord_id: int, name: str, money: int = 200):
        player = session.query(Player).filter(
            Player.discord_id == discord_id).first()
        if not player:
            player = cls(discord_id=discord_id, name=name, money=money, fs=0)
            for i in range(0, 5):
                naderr = Naderr(fs=i, owner=player)
                session.add(naderr)
                session.commit()
            session.add(player)
            session.commit()
        return player

    async def naderr_change(self, message, player, client):
        author = message.author

        def check(msg):
            return msg.author == message.author

        slots = list(filter(lambda x: x.owner_id == player._id, self.naderr))
        stackStr = f"**Current fs: {player.fs}**\n \n"
        counter = 1
        for i in slots:
            stackStr += f"{str(counter)}. **{i.fs} fs** \n"
            counter += 1
        naderr_embed = Embed(
            title="Naderr's band", description=f"{stackStr}", color=colors["purple"]
        )
        await message.channel.send(embed=naderr_embed)
        msg = await client.wait_for("message", check=check)
        try:
            playerFs = player.fs
            player.fs = slots[int(msg.content) - 1].fs
            slots[int(msg.content) - 1].fs = playerFs
            session.commit()
        except ValueError:
            await message.channel.send("Wrong slot.")
            await player.naderr_change(message, player, client)

    async def grind(self, s, message):
        if self.is_grinding is True:
            await message.channel.send("Already grinding.")
            return
        await message.channel.send(
            f"{message.author.mention} Started grinding for {s / 60} minutes!"
        )
        self.is_grinding = True
        money_sec = 200000000 / 3600
        earned_money = money_sec * s
        self.earned_money = round(earned_money)
        now = datetime.now()
        tdelta = timedelta(seconds=s)
        self.grind_end = now + tdelta
        session.commit()

    async def grind_info(self, message):
        now = datetime.now()
        try:
            if now >= self.grind_end:
                self.money += self.earned_money
                self.is_grinding = False
                self.grind_end = None
                ended = Embed(
                    title=f"Finished grinding.",
                    description=f"{message.author.mention} You've earned {formatNum(self.earned_money)} in total. Your current money amount is {formatNum(self.money)}",
                    color=colors["green"],
                )
                self.earned_money = None
                await message.channel.send(embed=ended)
                session.commit()
            else:
                await message.channel.send(
                    f"{self.grind_end - now} left till the end of your grind."
                )
        except TypeError:
            await message.channel.send(
                "You are not grinding. Type $grind (seconds) to start"
            )

    async def stop_grind(self, message):
        self.is_grinding = False
        self.grind_end = None
        self.earned_money = None
        session.commit()
        await message.channel.send("Succesfuly stopped grind.")

    async def enhance(self, _id: int, message, client):
        def check(author):
            return message.author == author.author

        def emoteCheck(reaction, author):
            return author == message.author and reaction.emoji in ["📖", "👎", "👍", "🗡"]

        while True:
            try:
                item = list(filter(lambda x: x._id == _id, self.inventory))[0]
            except IndexError:
                await message.channel.send(
                    f"{message.author.mention} Item no longer exists."
                )
                return
            if (
                item.lvl <= 15
                and item.durability < 20
                or item.lvl > 15
                and item.durability < 10
            ):
                await message.channel.send(
                    f"Durability to low for enhancment. Type $repair to repair the item."
                )
                return
            lvl = item.lvl
            if lvl == 20:
                return
            split_name = item.name.split(" ", 1)[0]
            try:
                tag = global_tags[split_name]
            except KeyError:
                await message.channel.send(f"{item.name} Can't be enhanced.")
                return
            search_g = list(
                filter(
                    lambda global_item: global_item[0] == tag and global_item[1] == lvl,
                    global_items,
                )
            )[0]
            if search_g[0] == "Acc" and lvl == 4:
                return
            chance, soft_cap, pre_soft_cap, post_soft_cap = (
                search_g[2],
                search_g[3],
                search_g[4],
                search_g[5],
            )
            fs = self.fs
            x = random.randint(0, 100)

            if fs < soft_cap:
                chance += fs * pre_soft_cap
            elif fs >= post_soft_cap:
                chance += soft_cap * pre_soft_cap
                chance += (fs - soft_cap) * post_soft_cap

            if chance > 90:
                chance = 90
            if search_g[0] != "Acc":
                self.last_enhanced_id = _id
                if lvl <= 7:
                    chance = 100

            if x <= chance:
                if lvl > 8:
                    self.fs = 0
                item.lvl = 1 + item.lvl
                session.commit()
                result = Embed(
                    title="Enhancment Succeded!",
                    description=f"You've succeded on enhancing +{item.lvl} {item.name} at {chance}%",
                    color=colors["green"],
                )
            else:
                result = Embed(
                    title="Enhancment Failed!",
                    description=f"You've failed on enhancing +{item.lvl + 1} {item.name} at {chance}%",
                    color=colors["red"],
                )
                self.fs += 1
                if search_g[0] == "Acc":
                    session.delete(item[0])
                    session.commit()
                if lvl > 16:
                    item.lvl = lvl - 1
                    item.durability -= 10
                    session.commit()
                    result.add_field(
                        name="Item level dropped!",
                        value=f"{item.name} level dropped due to enhancment failure.",
                    )
                elif lvl <= 15:
                    item.durability -= 5

            result.add_field(
                name="Continue?",
                value=f"You are at {self.fs} failstacks do you want to enhance again?",
            )
            msg = await message.channel.send(embed=result)
            await msg.add_reaction("👍")
            await msg.add_reaction("👎")
            await msg.add_reaction("🗡")
            await msg.add_reaction("📖")
            reaction, author = await client.wait_for("reaction_add", check=emoteCheck)
            if reaction.emoji == "👍":
                continue
            elif reaction.emoji == "👎":
                await message.channel.send("Stopped.")
                break
            elif reaction.emoji == "🗡":
                await message.channel.send("What weapon do you want to enhance next?")
                search = await client.wait_for("message", check=check)
                itemInv = list(
                    filter(lambda x: x.name == search.content, self.inventory)
                )
                if not itemInv:
                    return
                itemStr = ""
                itemCounter = 1
                for item in itemInv:
                    itemStr += f"{itemCounter}. {item.name} \n"
                    itemCounter += 1
                itemsEmbed = Embed(
                    title="Choose one to enhance.", description=itemStr)
                await message.channel.send(embed=itemsEmbed)
                position = await client.wait_for("message", check=check)
                try:
                    _id = itemInv[int(position.content) - 1]._id
                    continue
                except IndexError:
                    await message.channel.send("Item doesn't exist.")
            elif reaction.emoji == "📖":
                await self.naderr_change(message, self, client)


Base.metadata.create_all(engine)
