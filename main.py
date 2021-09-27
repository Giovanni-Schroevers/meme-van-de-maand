import os
import datetime

import aiocron
import discord
import mysql.connector
import matplotlib.pyplot as plt
from dotenv import load_dotenv

from database import setup_database

load_dotenv()
database, cursor = setup_database()

bot = discord.Bot()


def get_month():
    now = datetime.datetime.today()

    cursor.execute(f"SELECT id FROM month WHERE month = '{now.month}' AND year = '{now.year}'")
    result = cursor.fetchall()
    database.commit()
    return int(result[0][0])


@bot.slash_command()
async def nominate(ctx, meme: str, attachment: str = None):
    meme = meme
    now = datetime.datetime.today()

    try:
        cursor.execute(f"SELECT * FROM month WHERE month = '{now.month}' AND year = '{now.year}'")
        result = cursor.fetchall()
        database.commit()

        if not result:
            sql = "INSERT INTO month (month, year) VALUES (%s, %s)"
            val = (now.month, now.year)
            cursor.execute(sql, val)
            database.commit()

        sql = "INSERT INTO meme (name, month, attachment) VALUES (%s, %s, %s)"
        val = (meme, result[0][0] or cursor.lastrowid, attachment)
        cursor.execute(sql, val)
        database.commit()
    except mysql.connector.errors.IntegrityError as e:
        print(e)
        await ctx.respond(f"Er is iets fout gegaan tijdens het toevoegen van de meme")
        return

    await ctx.respond(f"Meme {meme} is toegevoegd aan de poll")


@bot.slash_command()
async def vote(ctx, meme_1: int, meme_2: int, meme_3: int):
    memes = [meme_1, meme_2, meme_3]
    user = bot.user
    now = datetime.datetime.today()

    if now.day != 1:
        await ctx.respond(f"Er kan alleen gestemd worden op de eerste van de maand")
        return
    elif len(memes) != 3:
        await ctx.respond(f"Er moet op 3 memes gestemd worden")
        return

    try:
        cursor.execute(f"SELECT id FROM month WHERE month = '{now.month}' AND year = '{now.year}'")
        result = cursor.fetchall()
        database.commit()
        month = int(result[0][0])

        cursor.execute(f"SELECT * FROM user WHERE discord_id = '{user.id}'")
        result = cursor.fetchall()
        database.commit()

        if not result:
            sql = "INSERT INTO user (discord_id, username) VALUES (%s, %s)"
            val = (user.id, user.name)
            cursor.execute(sql, val)
            database.commit()

        for meme in memes:
            cursor.execute(f"SELECT * FROM meme WHERE id = '{meme}' AND month = {month}")
            result = cursor.fetchall()
            database.commit()

            if not result:
                await ctx.respond("Meme kon niet worden gevonden")
                return

            cursor.execute(f"SELECT * FROM vote WHERE user = '{user.id}' AND meme = {meme}")
            result = cursor.fetchall()

            if result:
                await ctx.respond("Je hebt al gestemd")
                return

            sql = "INSERT INTO vote (user, meme) VALUES (%s, %s)"
            val = (user.id, meme)
            cursor.execute(sql, val)
            database.commit()
    except mysql.connector.errors.IntegrityError as e:
        print(e)
        await ctx.respond(f"Er is iets fout gegaan tijdens het stemmen")
        return

    await ctx.respond(f"Je hebt gestemd {user.name}!")


# @aiocron.crontab('0 12 1 * *')
@aiocron.crontab('* * * * *')
async def start_poll():
    channel = bot.get_channel(799298071749328896)
    month = get_month()
    text = "@kaas er is weer te stemmen voor meme van de maand. De memes van deze week zijn: \n"

    try:
        cursor.execute(f"SELECT * FROM meme WHERE month = '{month}'")
        memes = cursor.fetchall()
        database.commit()
        print(memes)

        for meme in memes:
            print(meme)
            text += f"{meme[0]}. {meme[1]}"
            if meme[2]:
                text += f" ({meme[2]})"
            text += "\n"

    except mysql.connector.errors.IntegrityError as e:
        print(e)
        await channel.send("Er is iets fout gegaan tijdens het maken van de poll")
        return

    text += "Er is op een meme te stemmen met /vote en de bijbehorende nummers van de memes"

    await channel.send(text)


@aiocron.crontab('0 12 2 * *')
async def send_poll_results():
    channel = bot.get_channel(799298071749328896)
    now = datetime.datetime.today()
    votes = {}

    try:
        cursor.execute(f"SELECT id FROM month WHERE month = '{now.month}' AND year = '{now.year}'")
        result = cursor.fetchall()
        month = int(result[0][0])

        cursor.execute(f"SELECT * FROM meme WHERE month = '{month}'")
        result = cursor.fetchall()
        database.commit()
        memes = result

        for meme in memes:
            cursor.execute(f"SELECT * FROM vote WHERE meme = '{meme[0]}'")
            result = cursor.fetchall()
            database.commit()

            votes[meme[1]] = len(result)

    except mysql.connector.errors.IntegrityError as e:
        print(e)
        await channel.send("Er is iets fout gegaan tijdens het maken van de poll")
        return

    memes = []
    meme_votes = []

    for meme, meme_vote in votes.items():
        memes.append(meme)
        meme_votes.append(meme_vote)

    fig, ax = plt.subplots()
    rects = ax.bar(memes, meme_votes)

    for rect, label in zip(rects, meme_votes):
        height = rect.get_height()
        ax.text(rect.get_x() + rect.get_width() / 2, height, label,
                ha='center', va='bottom')
    plt.savefig('votes.png')
    await channel.send("De uitslag van deze maand @kaas:", file=discord.File('votes.png'))


bot.run(os.getenv("BOT_TOKEN"))
