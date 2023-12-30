import aiosqlite
import os.path
import discord
import sqlite3
import json
import logging

# region Basics
async def connect():
    current_dir = os.path.dirname(__file__)
    path = current_dir + "/../files/"
    db = await aiosqlite.connect(path + "data.db")
    c = await db.cursor()
    await db.commit()  # Ensures that the database doesn't get locked.
    return db, c

async def create_account(ctx):
    db, c = await connect()
    await c.execute(f"SELECT userid FROM bank WHERE userid = {ctx.author.id}")
    result = await c.fetchone()
    if result is None:
        sql = "INSERT INTO bank(userid, money) VALUES (?, ?)"
        val = (ctx.author.id, 0)
        await db.execute(sql, val)
        await db.commit()
        print("Opened account for", ctx.author.id)
        await ctx.respond("Your bank account has been successfuly created.")
    else:
        await ctx.respond("You already have an open bank account.")

async def check_account(member, ctx):
    if not ctx.guild:
        # Commands are disabled in DMs.
        return True
    db, c = await connect()
    await c.execute(f"SELECT userid FROM bank WHERE userid = {member.id}")
    result = await c.fetchone()
    if result is None:
        if ctx is not None:
            pronoun = 'You' if member is ctx.author else 'They'
            await ctx.respond(f"{pronoun} do not have a bank account. " +
                              f"{pronoun} can open one with </register:1154556280376131604>.")
        return True

async def get_money(user):
    db, c = await connect()
    await c.execute(f"SELECT money FROM bank WHERE userid = {user.id}")
    result = await c.fetchone()
    return result[0]

async def change_money(user, amount):
    db, c = await connect()
    await c.execute(f"SELECT money FROM bank WHERE userid = {user.id}")
    money = await c.fetchone()
    new = money[0] + amount
    await c.execute("UPDATE bank SET money = ? WHERE userid = ?", (new, user.id))
    await db.commit()
    return new

# Used by the leaderboard.
async def db_fetch(sql):
    dc, c = await connect()
    await c.execute(sql)
    return await c.fetchall()

async def get_guides():
    with open('../files/guides.json') as f:
        data = json.load(f)
        f.close()
    return data

async def log(msg: str, ctx: discord.ApplicationContext):
    logging.info(f"[COMMAND] {msg} - {ctx.user.id} ({ctx.user.name}), #{ctx.channel_id}, {ctx.guild_id}")
    return

# endregion

# region Items
async def get_item_info(item, option):
    db, c = await connect()
    await c.execute(f"SELECT {option} FROM items WHERE name = \"{item}\"")
    result = await c.fetchone()
    if result is None:
        return None
    return result[0]

async def get_inv(user, item=None):
    db, c = await connect()
    if item is None:
        await c.execute(f"SELECT item, amount FROM inventory WHERE userid = {user.id}")
        result = await c.fetchall()
        return result
    else:
        try:
            await c.execute(f"SELECT amount FROM inventory WHERE userid = {user.id} AND item = \"{item}\"")
            result = (await c.fetchone())[0]
            return result
        except TypeError:
            return 0

async def add_inv(user, item, amount=1):
    db, c = await connect()
    await c.execute(f"SELECT amount FROM inventory WHERE userid = {user.id} AND item = \"{item}\"")
    result = await c.fetchone()
    if result is None:
        await c.execute(f"INSERT INTO inventory(userid, item, amount) VALUES (?, ?, ?)", (user.id, item, amount))
    else:
        result = result[0] + amount
        await c.execute("UPDATE inventory SET amount = ? WHERE userid = ? AND item = ?", (result, user.id, item))
    await db.commit()

async def remove_inv(user, item, amount=1):
    db, c = await connect()
    await c.execute(f"SELECT amount FROM inventory WHERE userid = {user.id} AND item = \"{item}\"")
    result = await c.fetchone()
    if result is None:
        return "noitem"
    result = result[0]
    if amount > result:
        return "notenough"
    result -= amount
    if result == 0:
        await c.execute("DELETE FROM inventory WHERE userid = ? AND item = ?", (user.id, item))
    else:
        await c.execute("UPDATE inventory SET amount = ? WHERE userid = ? AND item = ?", (result, user.id, item))
    await db.commit()

async def net_worth(userid): # FIX
    # shopdata = await get_item_info()
    db, c = await connect()
    await c.execute(f"SELECT money FROM bank WHERE userid = {userid}")
    money = (await c.fetchone())[0]
    # await c.execute(f"SELECT inventory FROM bank WHERE userid = {userid}")
    # inv = json.loads((await c.fetchone())[0])
    # for item in inv:
    #     if shopdata[item]["price"] is not None:
    #         money += shopdata[item]["price"] * inv[item]
    return money

async def get_items(ctx: discord.AutocompleteContext):
    member = ctx.interaction.user
    try:
        if ctx.command.name == "buy" and "member" in ctx.options:
            member = ctx.options["member"]
            member = ctx.interaction.guild.get_member(int(member))
        inv = await get_inv(member)
    except TypeError:
        return []
    result = []
    for item in inv:
        item = item[0]
        if ctx.command.name == "use":
            if await get_item_info(item, "use") is not None:
                result.append(item)
        else:
            if await get_item_info(item, "sellable") == 1:
                result.append(item)
    return result

async def get_all_items():
    db, c = await connect()
    await c.execute(f"SELECT name FROM items")
    return await c.fetchall()
# endregion

# region Companies
async def add_company(name, owner):
    db, c = await connect()
    await c.execute(f"INSERT INTO companies(name, owner, money) VALUES (?, ?, ?)", (name, owner, 0))
    await db.commit()

async def get_company(name, value):
    db, c = await connect()
    await c.execute(f"SELECT {value} FROM companies WHERE name = \"{name}\"")
    result = await c.fetchone()
    if result is None:
        return result
    else:
        return result[0]

async def get_companies():
    db, c = await connect()
    await c.execute(f"SELECT * FROM companies")
    return await c.fetchall()

async def change_money_company(name, amount):
    db, c = await connect()
    await c.execute(f"SELECT money FROM companies WHERE name =\"{name}\"")
    money = await c.fetchone()
    new = money[0] + amount
    await c.execute("UPDATE companies SET money = ? WHERE name = ?", (new, name))
    await db.commit()
    return new

async def change_company(name, option, value):
    db, c = await connect()
    await c.execute(f"UPDATE companies SET {option} = \"{value}\" WHERE name = \"{name}\"")
    await db.commit()

async def delete_company(name):
    db, c = await connect()
    company_id = await get_company(name, 'id')
    await c.execute("SELECT name FROM shops WHERE company = ?", (company_id,))
    shops = [x[0] for x in await c.fetchall()]
    for shop in shops:
        await delete_shop(shop)
    await c.execute("DELETE FROM inventory WHERE company = ?", (company_id,))
    await c.execute("DELETE FROM companies WHERE name = ?", (name,))
    await db.commit()

async def get_company_from_id(company_id):
    db, c = await connect()
    await c.execute(f"SELECT name FROM companies WHERE id = {company_id}")
    result = await c.fetchone()
    return result[0]

async def get_inv_company(company_id, item):
    db, c = await connect()
    if item is None:
        await c.execute(f"SELECT item, amount FROM inventory WHERE company = {company_id}")
        result = await c.fetchall()
        return result
    else:
        try:
            await c.execute(f"SELECT amount FROM inventory WHERE company = {company_id} AND item = \"{item}\"")
            result = (await c.fetchone())[0]
            return result
        except TypeError:
            return 0

async def add_inv_company(company, item, amount=1):
    db, c = await connect()
    await c.execute(f"SELECT amount FROM inventory WHERE company = {company} AND item = \"{item}\"")
    result = await c.fetchone()
    if result is None:
        await c.execute(f"INSERT INTO inventory(company, item, amount) VALUES (?, ?, ?)", (company, item, amount))
    else:
        result = result[0] + amount
        await c.execute("UPDATE inventory SET amount = ? WHERE company = ? AND item = ?", (result, company, item))
    await db.commit()

async def remove_inv_company(company, item, amount=1):
    db, c = await connect()
    await c.execute(f"SELECT amount FROM inventory WHERE company = {company} AND item = \"{item}\"")
    result = await c.fetchone()
    if result is None:
        return "noitem"
    result = result[0]
    if amount > result:
        return "notenough"
    result -= amount
    if result == 0:
        await c.execute("DELETE FROM inventory WHERE company = ? AND item = ?", (company, item))
    else:
        await c.execute("UPDATE inventory SET amount = ? WHERE company = ? AND item = ?", (result, company, item))
    await db.commit()
# endregion

# region Shops
async def add_shop(name, company):
    db, c = await connect()
    await c.execute(f"INSERT INTO shops(company, name, description, open) VALUES (?, ?, ?, ?)",
                    (company, name, "Description not set", 0))
    await db.commit()

async def get_shops():
    db, c = await connect()
    await c.execute(f"SELECT * FROM shops")
    return await c.fetchall()

async def get_shop(name, value):
    db, c = await connect()
    await c.execute(f"SELECT {value} FROM shops WHERE name = \"{name}\"")
    result = await c.fetchone()
    if result is None:
        return result
    else:
        return result[0]

async def change_shop(name, option, value):
    db, c = await connect()
    await c.execute(f"UPDATE shops SET {option} = \"{value}\" WHERE name = \"{name}\"")
    await db.commit()

async def delete_shop(name):
    db, c = await connect()
    shop_id = await get_shop(name, 'id')
    await c.execute("DELETE FROM shop_offers WHERE shop = ?", (shop_id,))
    await c.execute("DELETE FROM shops WHERE name = ?", (name,))
    await db.commit()

async def add_offer(shop, item, offer, direction, price, target, elasticity, min_price, max_price, rank):
    db, c = await connect()
    await c.execute(f"SELECT name FROM shop_offers WHERE shop = {shop} AND name = \"{offer}\"")
    if await c.fetchone() is not None:
        return "alreadyexists"
    await c.execute(f"SELECT rank FROM shop_offers WHERE shop = {shop}")
    ranks = [x[0] for x in await c.fetchall()]
    try:
        if rank > max(ranks) or rank == 0:
            rank = max(ranks) + 1
    except ValueError:
        rank = 1
    await c.execute(f"UPDATE shop_offers SET rank = rank + 1 WHERE shop = {shop} and rank >= {rank}")
    sql = "INSERT INTO shop_offers(shop, rank, name, item, direction, price, target, elasticity, min, max)" \
        + "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)"
    val = (shop, rank, offer, item, direction, price, target, elasticity, min_price, max_price)
    await c.execute(sql, val)
    await db.commit()
    return rank

async def delete_offer(shop, name):
    db, c = await connect()
    await c.execute("SELECT rank FROM shop_offers WHERE shop = ? AND name = ?", (shop, name))
    rank = (await c.fetchone())[0]
    await c.execute("DELETE FROM shop_offers WHERE shop = ? AND name = ?", (shop, name))
    await c.execute(f"UPDATE shop_offers SET rank = rank - 1 WHERE shop = {shop} and rank > {rank}")
    await db.commit()

#BROKEN
async def change_offer(shop, offer, name, item, direction, price, target, elasticity, min_price, max_price, rank,
                       old_rank):
    print(shop, offer, name, item, direction, price, target, elasticity, min_price, max_price, rank, old_rank)
    db, c = await connect()
    if rank > old_rank:
        await c.execute(f"SELECT rank FROM shop_offers WHERE shop = {shop}")
        ranks = [x[0] for x in await c.fetchall()]
        if rank > max(ranks):
            rank = max(ranks) + 1
        await c.execute(f"UPDATE shop_offers SET rank = rank - 1 WHERE shop = {shop}" +
                        f" AND rank > {old_rank} rank <= {rank}")
    if rank < old_rank:
        await c.execute(f"UPDATE shop_offers SET rank = rank + 1 WHERE shop = {shop}" +
                        f" AND rank >= {rank} rank < {old_rank}")
    set_value = f"name = \"{name}\", item = \"{item}\", direction = {direction}, price = {price}, " + \
                f"target = {target}, elasticity = {elasticity}, min = {min_price}, max = {max_price}, rank = {rank}"
    await c.execute(f"UPDATE shop_offers SET {set_value} WHERE shop = {shop} AND name = \"{offer}\"")
    await db.commit()
    return rank

async def get_offers(shop):
    shop_id = await get_shop(shop, 'id')
    db, c = await connect()
    try:
        await c.execute(f"SELECT * FROM shop_offers WHERE shop = {shop_id} ORDER BY rank")
        return await c.fetchall()
    except sqlite3.OperationalError:
        return []

async def get_offer(shop, offer):
    shop_id = await get_shop(shop, 'id')
    db, c = await connect()
    try:
        await c.execute(f"SELECT * FROM shop_offers WHERE shop = {shop_id} AND name = \"{offer}\"")
        return (await c.fetchall())[0]  # noqa
    except sqlite3.OperationalError:
        return None
    except IndexError:
        return None

async def calculate_price(shop, offer, amount=1, offset=0):
    shop_id = await get_shop(shop, 'id')
    db, c = await connect()
    await c.execute(f"SELECT item, price, target, elasticity, min, max, direction" +
                    f" FROM shop_offers WHERE shop = {shop_id} AND rank = {offer}")
    results = await c.fetchall()
    results = results[0]  # noqa
    company = await get_company(await get_company_from_id(await get_shop(shop, 'company')), 'id')
    try:
        await c.execute(f"SELECT amount FROM inventory WHERE company = {company} AND item = \"{results[0]}\"")
        stock = (await c.fetchone())[0]
        stock -= offset * results[6]
    except TypeError:
        if results[6] == 1:
            return "N/A"
        else:
            stock = 0
    price = results[1] * (results[2] ** results[3]) / ((stock + (1 if results[6] == -1 else 0)) ** results[3])
    if results[4] is not None:
        if price < results[4]:
            price = results[4]
    if results[5] is not None:
        if price > results[5]:
            price = results[5]
    offset += 1
    price = round(price)
    if amount > offset:
        price += await calculate_price(shop, offer, amount, offset)
    return price
# endregion

# region Governments

async def add_government(server: int, name: str, admin: int):
    db, c = await connect()
    await c.execute(f"INSERT INTO governments(server, name, money, Administrator) VALUES (?, ?, ?, ?)",
                    (server, name, 0, admin))
    await db.commit()

async def get_government(server, value):
    db, c = await connect()
    await c.execute(f"SELECT [{value}] FROM governments WHERE server = {server}")
    result = await c.fetchone()
    if result is None:
        return None
    else:
        return result[0]

async def has_govt_perm(server_id, user, permission: str):
    return user.get_role(await get_government(server_id, "administrator")) is not None \
           or user.get_role(await get_government(server_id, permission)) is not None

async def change_government(server, option: str, value):
    db, c = await connect()
    await c.execute(f"UPDATE governments SET [{option}] = ? WHERE server = {server}", (value,))
    await db.commit()

async def change_money_govt(server, amount):
    db, c = await connect()
    await c.execute(f"SELECT money FROM governments WHERE server = {server}")
    money = await c.fetchone()
    new = money[0] + amount
    await c.execute("UPDATE governments SET money = ? WHERE server = ?", (new, server))
    await db.commit()
    return new

async def get_inv_govt(server, item):
    db, c = await connect()
    if item is None:
        await c.execute(f"SELECT item, amount FROM inventory WHERE government = {server}")
        result = await c.fetchall()
        return result
    else:
        try:
            await c.execute(f"SELECT amount FROM inventory WHERE government = {server} AND item = \"{item}\"")
            result = (await c.fetchone())[0]
            return result
        except TypeError:
            return 0

async def add_inv_govt(server, item, amount=1):
    db, c = await connect()
    await c.execute(f"SELECT amount FROM inventory WHERE government = {server} AND item = \"{item}\"")
    result = await c.fetchone()
    if result is None:
        await c.execute(f"INSERT INTO inventory(government, item, amount) VALUES (?, ?, ?)", (server, item, amount))
    else:
        result = result[0] + amount
        await c.execute("UPDATE inventory SET amount = ? WHERE government = ? AND item = ?", (result, server, item))
    await db.commit()

async def remove_inv_govt(server, item, amount=1):
    db, c = await connect()
    await c.execute(f"SELECT amount FROM inventory WHERE government = {server} AND item = \"{item}\"")
    result = await c.fetchone()
    if result is None:
        return "noitem"
    result = result[0]
    if amount > result:
        return "notenough"
    result -= amount
    if result == 0:
        await c.execute("DELETE FROM inventory WHERE government = ? AND item = ?", (server, item))
    else:
        await c.execute("UPDATE inventory SET amount = ? WHERE government = ? AND item = ?", (result, server, item))
    await db.commit()

# endregion
