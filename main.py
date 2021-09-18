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


@bot.slash_command()
async def nominate(ctx, meme: str):
    meme = meme
    now = datetime.datetime.today()

    try:
        cursor.execute(f"SELECT * FROM month WHERE month = '{now.month}'")
        result = cursor.fetchall()

        if not result:
            sql = "INSERT INTO month (month, year) VALUES (%s, %s)"
            val = (now.month, now.year)
            cursor.execute(sql, val)
            database.commit()

        sql = "INSERT INTO meme (name, month) VALUES (%s, %s)"
        val = (meme, cursor.lastrowid or result[0][0])
        cursor.execute(sql, val)
        database.commit()
    except mysql.connector.errors.IntegrityError as e:
        print(e)
        await ctx.respond(f"Er is iets fout gegaan tijdens het toevoegen van de meme")

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
        print(result)
        month = int(result[0][0])

        cursor.execute(f"SELECT * FROM user WHERE discord_id = '{user.id}'")
        result = cursor.fetchall()

        if not result:
            sql = "INSERT INTO user (discord_id, username) VALUES (%s, %s)"
            val = (user.id, user.name)
            cursor.execute(sql, val)
            database.commit()

        for meme in memes:
            cursor.execute(f"SELECT * FROM meme WHERE id = '{meme}' AND month = {month}")
            result = cursor.fetchall()

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

    await ctx.respond(f"Je hebt gestemd {user.name}!")


@aiocron.crontab('* * * * *')
async def send_poll():
    channel = bot.get_channel(799298071749328896)
    now = datetime.datetime.today()
    votes = {}

    try:
        cursor.execute(f"SELECT id FROM month WHERE month = '{now.month}' AND year = '{now.year}'")
        result = cursor.fetchall()
        month = int(result[0][0])

        cursor.execute(f"SELECT * FROM meme WHERE month = '{month}'")
        result = cursor.fetchall()
        memes = result

        for meme in memes:
            cursor.execute(f"SELECT * FROM vote WHERE meme = '{meme[0]}'")
            result = cursor.fetchall()

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
    await channel.send("De uitslag van deze maand @here:", file=discord.File('votes.png'))


bot.run(os.getenv("BOT_TOKEN"))
