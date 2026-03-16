import discord
from discord.ext import commands, tasks
from discord import app_commands
import requests
from datetime import datetime, timedelta, timezone

import recurring_ical_events
from icalendar import Calendar
import os

TOKEN = os.getenv("TOKEN")

CHANNEL_ID = 1481901142295183380

CALENDAR_URL = "https://calendar.google.com/calendar/ical/e6196c2703be23e87e027067c77f8990c4434a659a08fc9c3612f60c83b42c0e%40group.calendar.google.com/public/basic.ics"

intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)

posted_events = set()


def get_events():

    response = requests.get(CALENDAR_URL)
    calendar = Calendar.from_ical(response.text)

    today = datetime.now(timezone.utc)
    next_week = today + timedelta(days=7)

    events = recurring_ical_events.of(calendar).between(today, next_week)

    result = []

    for event in events:

        name = str(event.get("SUMMARY"))
        start = event.get("DTSTART").dt

        if isinstance(start, datetime):
            date = start.date()
            time = start.strftime("%H:%M")
        else:
            date = start
            time = "All day"

        result.append({
            "name": name,
            "date": date,
            "time": time
        })

    return result


@bot.event
async def on_ready():

    print(f"Bot online come {bot.user}")

    try:
        await bot.tree.sync()
        print("Comandi sincronizzati")
    except Exception as e:
        print(e)

    check_events.start()


# 🔔 controllo automatico eventi
@tasks.loop(minutes=10)
async def check_events():

    channel = bot.get_channel(CHANNEL_ID)

    events = get_events()

    today = datetime.now(timezone.utc).date()

    for event in events:

        if event["date"] == today and event["name"] not in posted_events:

            posted_events.add(event["name"])

            embed = discord.Embed(
                title="📅 Evento Kingshot oggi",
                description=f"⚔️ **{event['name']}**",
                color=0xff9900
            )

            embed.add_field(
                name="🕒 Orario",
                value=event["time"],
                inline=False
            )

            await channel.send(embed=embed)


@bot.tree.command(name="oggi", description="Mostra eventi di oggi")
async def oggi(interaction: discord.Interaction):

    events = get_events()

    today = datetime.now(timezone.utc).date()

    embed = discord.Embed(
        title="📅 Eventi di oggi",
        color=0xff9900
    )

    found = False

    for event in events:

        if event["date"] == today:

            embed.add_field(
                name=event["name"],
                value=f"🕒 {event['time']}",
                inline=False
            )

            found = True

    if not found:
        embed.description = "Nessun evento oggi"

    await interaction.response.send_message(embed=embed)


@bot.tree.command(name="settimana", description="Mostra eventi della settimana")
async def settimana(interaction: discord.Interaction):

    events = get_events()

    embed = discord.Embed(
        title="📅 Eventi della settimana",
        color=0xff9900
    )

    if not events:

        embed.description = "Nessun evento"

    else:

        for event in events:

            embed.add_field(
                name=event["name"],
                value=f"{event['date']} • {event['time']}",
                inline=False
            )

    await interaction.response.send_message(embed=embed)


bot.run(TOKEN)