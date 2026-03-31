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

    now = datetime.now(timezone.utc)
    next_week = now + timedelta(days=7)

    events = recurring_ical_events.of(calendar).between(now, next_week)

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

    print(f"Bot online as {bot.user}")

    try:
        await bot.tree.sync()
        print("Commands synced")
    except Exception as e:
        print(e)

    check_events.start()


# 🔔 AUTO EVENT POST
@tasks.loop(minutes=10)
async def check_events():

    channel = bot.get_channel(CHANNEL_ID)

    events = get_events()

    today = datetime.now(timezone.utc).date()

    for event in events:

        if event["date"] == today and event["name"] not in posted_events:

            posted_events.add(event["name"])

            embed = discord.Embed(
                title="📅 Kingshot Event Today",
                description=f"⚔️ **{event['name']}**",
                color=0xff9900
            )

            embed.add_field(
                name="🕒 Time",
                value=event["time"],
                inline=False
            )

            await channel.send(embed=embed)


# 🔹 TODAY COMMAND
@bot.tree.command(name="today", description="Show today's events")
async def today(interaction: discord.Interaction):

    events = get_events()

    today_date = datetime.now(timezone.utc).date()

    embed = discord.Embed(
        title="📅 Today's Events",
        color=0xff9900
    )

    found = False

    for event in events:

        if event["date"] == today_date:

            embed.add_field(
                name=event["name"],
                value=f"🕒 {event['time']}",
                inline=False
            )

            found = True

    if not found:
        embed.description = "No events today"

    await interaction.response.send_message(embed=embed)


# 🔹 WEEK COMMAND
@bot.tree.command(name="week", description="Show this week's events")
async def week(interaction: discord.Interaction):

    events = get_events()

    embed = discord.Embed(
        title="📅 This Week's Events",
        color=0xff9900
    )

    if not events:
        embed.description = "No events this week"
    else:
        for event in events:
            embed.add_field(
                name=event["name"],
                value=f"{event['date']} • {event['time']}",
                inline=False
            )

    await interaction.response.send_message(embed=embed)


bot.run(TOKEN)