import discord
from discord.ext import commands
from discord import app_commands
import json
import os
from datetime import datetime

TOKEN = "YOUR_TOKEN_HERE"

intents = discord.Intents.all()
bot = commands.Bot(command_prefix='!', intents=intents)

WARNS_FILE = "warns.json"

def load_warns():
    if os.path.exists(WARNS_FILE):
        with open(WARNS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

def save_warns(warns):
    with open(WARNS_FILE, 'w', encoding='utf-8') as f:
        json.dump(warns, f, indent=2, ensure_ascii=False)

def get_warns_data(guild_id, user_id):
    warns = load_warns()
    if guild_id in warns and user_id in warns[guild_id]:
        return warns[guild_id][user_id]
    return {"count": 0, "history": []}

def set_warns_data(guild_id, user_id, data):
    warns = load_warns()
    if guild_id not in warns:
        warns[guild_id] = {}
    warns[guild_id][user_id] = data
    save_warns(warns)

@bot.event
async def on_member_join(member):
    role = discord.utils.get(member.guild.roles, name="TikToker")
    if role:
        await member.add_roles(role)

@bot.tree.command(name="warn", description="Warn a user")
@app_commands.describe(user="Who", reason="Why")
@app_commands.choices(amount=[
    app_commands.Choice(name="0.5", value=0.5),
    app_commands.Choice(name="1", value=1.0)
])
async def warn(interaction: discord.Interaction, user: discord.Member, amount: float = 1.0, reason: str = "None"):
    data = get_warns_data(str(interaction.guild.id), str(user.id))
    data["count"] += amount
    data["history"].append({"type":"warn","amount":amount,"reason":reason,"moderator":interaction.user.name,"date":datetime.now().strftime("%d.%m.%Y %H:%M")})
    set_warns_data(str(interaction.guild.id), str(user.id), data)
    embed = discord.Embed(title="WARN", color=0xFFA500)
    embed.add_field(name="User", value=user.mention)
    embed.add_field(name="Total", value=f"**{data['count']}/5**")
    embed.add_field(name="Reason", value=reason)
    embed.set_footer(text=f"Mod: {interaction.user.name}")
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="warns", description="Check warns")
@app_commands.describe(user="Who")
async def warns(interaction: discord.Interaction, user: discord.Member = None):
    if not user: user = interaction.user
    data = get_warns_data(str(interaction.guild.id), str(user.id))
    if data["count"] > 0:
        embed = discord.Embed(title=f"Warns: {user.name}", color=0xFF0000)
        embed.add_field(name="Total", value=f"**{data['count']}/5**", inline=False)
        for i, h in enumerate(data["history"], 1):
            icon = "[-]" if h['type']=='warn' else "[+]"
            embed.add_field(name=f"{icon} {i} ({h['amount']})", value=f"{h.get('reason','')}\n{h['moderator']}\n{h['date']}", inline=False)
        await interaction.response.send_message(embed=embed)
    else:
        await interaction.response.send_message(f"No warns", ephemeral=True)

@bot.tree.command(name="unwarn", description="Remove warns")
@app_commands.describe(user="Who", amount="How many")
@app_commands.choices(amount=[
    app_commands.Choice(name="0.5", value=0.5),
    app_commands.Choice(name="1", value=1.0),
    app_commands.Choice(name="2", value=2.0),
    app_commands.Choice(name="3", value=3.0),
    app_commands.Choice(name="4", value=4.0),
    app_commands.Choice(name="5", value=5.0)
])
async def unwarn(interaction: discord.Interaction, user: discord.Member, amount: float):
    data = get_warns_data(str(interaction.guild.id), str(user.id))
    if data["count"] <= 0:
        await interaction.response.send_message("No warns", ephemeral=True)
        return
    data["count"] = max(0, data["count"] - amount)
    data["history"].append({"type":"unwarn","amount":amount,"moderator":interaction.user.name,"date":datetime.now().strftime("%d.%m.%Y %H:%M")})
    set_warns_data(str(interaction.guild.id), str(user.id), data)
    embed = discord.Embed(title="UNWARN", color=0x00FF00)
    embed.add_field(name="Removed", value=f"**-{amount}**")
    embed.add_field(name="Left", value=f"**{data['count']}/5**")
    embed.set_footer(text=f"Mod: {interaction.user.name}")
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="clearwarns", description="Clear all warns")
@app_commands.describe(user="Who")
async def clearwarns(interaction: discord.Interaction, user: discord.Member):
    data = get_warns_data(str(interaction.guild.id), str(user.id))
    data["count"] = 0
    data["history"].append({"type":"unwarn","amount":"all","moderator":interaction.user.name,"date":datetime.now().strftime("%d.%m.%Y %H:%M")})
    set_warns_data(str(interaction.guild.id), str(user.id), data)
    embed = discord.Embed(title="CLEARED", description=f"All warns removed for {user.mention}", color=0x00FF00)
    embed.set_footer(text=f"Mod: {interaction.user.name}")
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="say", description="Send message as bot")
@app_commands.describe(channel="Where", text="What")
async def say(interaction: discord.Interaction, channel: discord.TextChannel, text: str):
    await channel.send(text)
    await interaction.response.send_message("Done!", ephemeral=True)

@bot.event
async def on_ready():
    print(f"Bot: {bot.user}")
    for guild in bot.guilds:
        await bot.tree.sync(guild=guild)
        print(f"Synced: {guild.name}")
    print("Ready!")

bot.run(TOKEN)
