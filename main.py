import discord
from discord import app_commands
from discord.ext import commands, tasks
import random
import re
import json
import os
import time
import translatelib

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix="t+", intents=intents) # TODO make t+ commands work

# constants

DATA_FILE = "uwu_data.json"
data = {}
ROLE_NAME = "uwu mod"
URL_REGEX = re.compile(r"https?://\S+|www\.\S+")
OWNER_USER_ID = 1123319890753896498

# persistence

def load_data():
    global data
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            data = json.load(f)
    else:
        data = {}

def save_data():
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=2)

def get_guild(guild_id: int):
    gid = str(guild_id)
    if gid not in data:
        data[gid] = {
            "users": {},
            "channels": {},
            "webhooks": {}
        }
    return data[gid]

# uwuify

def uwuify(text: str) -> str:
    words = text.split()
    new_words = []

    for word in words:
        # don't touch links
        if URL_REGEX.fullmatch(word):
            new_words.append(word)
            continue

        # uwu transformations
        word = re.sub(r"[rl]", "w", word)
        word = re.sub(r"[RL]", "W", word)
        word = re.sub(r"n([aeiou])", r"ny\1", word)
        word = re.sub(r"N([aeiou])", r"Ny\1", word)

        # stutter
        if random.random() < 0.13 and len(word) > 1:
            word = f"{word[0]}-{word}"

        new_words.append(word)

    text = " ".join(new_words)

    if random.random() < 0.8:
        text += " " + random.choice([
            "uwu",
            "owo",
            "nyaa~",
            ":3",
            "*purrs*"
        ])

    return text

def absolute_catgirl(text: str) -> str:
    rp_actions = [
        "*twitches ears*",
        "*knocks something over accidentally*",
        "*stares at you intensely*",
        "*paws at air*",
        "*rolls on floor*",
        "*tail swishes aggressively*",
        "*boops your screen*",
        "*hides under blanket*",
        "*pounces your sentence*"
    ]

    words = text.split()
    new_words = []

    for word in words:
        is_url = URL_REGEX.fullmatch(word)

        # don't touch links
        if not is_url:
            # uwu transformation
            word = re.sub(r"[rl]", "w", word)
            word = re.sub(r"[RL]", "W", word)
            word = re.sub(r"n([aeiou])", r"ny\1", word)
            word = re.sub(r"N([aeiou])", r"Ny\1", word)

            if len(word) > 2:
                if random.random() < 0.18:
                    word = f"{word[0]}-{word}"

                if random.random() < 0.10:
                    word += random.choice([
                        "~",
                        "!!",
                        "…",
                        "nya"
                    ])

        new_words.append(word)

        # don't inject RP actions after links
        if not is_url and random.random() < 0.12:
            new_words.append(random.choice(rp_actions))

    text = " ".join(new_words)

    # punctuation
    # avoid modifying urls accidentally
    parts = text.split()

    for i, part in enumerate(parts):
        if URL_REGEX.fullmatch(part):
            continue

        if random.random() < 0.5:
            part = part.replace("!", "!!!")

        if random.random() < 0.5:
            part = part.replace(".", "…")

        parts[i] = part

    text = " ".join(parts)

    prefixes = [
        "*ears perk up* ",
        "*suddenly appears* ",
        "*kneads reality itself* ",
        "nyaa!! ",
        "*zoomies activated* "
    ]

    suffixes = [
        " nya~",
        " meow :3",
        " *purrs*",
        " nyaaa >w<",
        " 𝓷𝔂𝓪~"
    ]

    if random.random() < 0.6:
        text = random.choice(prefixes) + text

    if random.random() < 0.9:
        text += random.choice(suffixes)

    return text

# modes

def uwu_mode(text: str) -> str:
    return uwuify(text)

def reverse_mode(text: str) -> str:
    return text[::-1]

def mock_mode(text: str) -> str:
    return "".join(
        c.upper() if i % 2 == 0 else c.lower()
        for i, c in enumerate(text)
    )

def badwifi_mode(text: str) -> str:
    return "".join(c if random.random() > 0.5 else "" for i, c in enumerate(text))

def stopyelling(text: str) -> str:
    return "\n".join("-# " + line for line in text.lower().split("\n"))

def stfu(text: str) -> str:
    return ""

def uwu_reverse(text):
    return reverse_mode(uwu_mode(text))

MODES = {
    "UwU": uwu_mode,
    "Absolute catgirl": absolute_catgirl,
    "Reverse": reverse_mode,
    "Mock": mock_mode,
    "Bad Wifi": badwifi_mode,
    "stop yelling im scared :3": stopyelling,
    "stfu": stfu,
    "JACKPOT": uwu_reverse,
}

# webhook

async def get_webhook(channel: discord.TextChannel):
    guild_data = get_guild(channel.guild.id)
    webhooks = guild_data["webhooks"]

    if str(channel.id) in webhooks:
        return discord.Webhook.from_url(webhooks[str(channel.id)], client=bot)

    existing = await channel.webhooks()
    webhook = None

    for w in existing:
        if w.name == "uwu-bot":
            webhook = w
            break

    if webhook is None:
        webhook = await channel.create_webhook(name="uwu-bot")

    webhooks[str(channel.id)] = webhook.url
    save_data()

    return webhook

# cleanup expired

@tasks.loop(seconds=5)
async def cleanup_expired():
    now = time.time()
    changed = False

    for guild_id in data:
        users = data[guild_id]["users"]

        to_remove = [
            uid for uid, info in users.items()
            if info["expiry"] <= now
        ]

        for uid in to_remove:
            del users[uid]
            changed = True

    if changed:
        save_data()

@cleanup_expired.before_loop
async def before_cleanup():
    await bot.wait_until_ready()

# events

@bot.event
async def on_ready():
    load_data()
    cleanup_expired.start()
    await bot.tree.sync()
    print(f"Logged in as {bot.user}")

@bot.event
async def on_message(message: discord.Message):
    if not message.guild:
        return

    # ignore this bot's own webhook to prevent infinite loops
    if message.webhook_id:
        webhooks = await message.channel.webhooks()

        for w in webhooks:
            if (
                w.id == message.webhook_id and
                w.name == "uwu-bot"
            ):
                return

    global duration
    guild_data = get_guild(message.guild.id)

    uid = str(message.author.id)
    cid = str(message.channel.id)
    now = time.time()

    users = guild_data["users"]
    channels = guild_data["channels"]

    mode = None

    if uid in users and users[uid]["expiry"] > now:
        mode = users[uid].get("mode", "uwu")
    elif cid in channels:
        mode = channels[cid]
    elif any(role.name.lower() == "uwued" for role in message.author.roles):
        mode = "UwU"

    if not mode:
        await bot.process_commands(message)
        return

    webhook = await get_webhook(message.channel)

    transform = MODES.get(mode, uwu_mode)
    content = transform(message.content)

    files = []

    for attachment in message.attachments:
        files.append(await attachment.to_file())

    await webhook.send(
        content=content,
        username=message.author.display_name,
        avatar_url=message.author.display_avatar.url,
        files=files,
        embeds=message.embeds
    )

    try:
        await message.delete()
    except discord.Forbidden:
        return

    await bot.process_commands(message)

# perms

def is_admin(interaction: discord.Interaction) -> bool:
    user = interaction.user
    has_uwu_mod = any(role.name.lower() == "uwu mod" for role in user.roles)
    return (
        user.guild_permissions.administrator
        or user.id == OWNER_USER_ID
        or has_uwu_mod
    )

# commands

def mode_choices():
    return [
        app_commands.Choice(name=m, value=m)
        for m in MODES.keys()
    ]

@bot.tree.command(
    name="guilds",
    description="List guilds or generate an invite for a guild"
)
async def guilds(
    interaction: discord.Interaction,
    guild_id: str | None = None
):
    if interaction.user.id != YOUR_USER_ID:
        await interaction.response.send_message(
            "You are not allowed to use this command.",
            ephemeral=True
        )
        return

    # no id passed -> list guilds
    if guild_id is None:
        guild_list = "\n".join(
            f"{guild.name} ({guild.id})"
            for guild in bot.guilds
        )

        if not guild_list:
            guild_list = "The bot is not in any guilds."

        # 2000 char limit
        if len(guild_list) > 1900:
            guild_list = guild_list[:1900] + "\n..."

        await interaction.response.send_message(
            f"```{guild_list}```\nIn {len(bot.guilds)} guild(s)"
        )
        return

    # id passed -> generate invite
    try:
        guild_id = int(guild_id)
    except ValueError:
        await interaction.response.send_message(
            "Invalid guild ID.",
            ephemeral=True
        )
        return

    guild = bot.get_guild(guild_id)

    if guild is None:
        await interaction.response.send_message(
            "The bot is not in that guild.",
            ephemeral=True
        )
        return

    # find a channel where the bot can create invites
    invite = None

    for channel in guild.text_channels:
        perms = channel.permissions_for(guild.me)

        if perms.create_instant_invite:
            try:
                invite = await channel.create_invite(
                    max_uses=1,
                    unique=True,
                    reason=f"Invite requested by {interaction.user}"
                )
                break
            except Exception:
                pass

    if invite is None:
        await interaction.response.send_message(
            "Could not create an invite for that guild.",
            ephemeral=True
        )
        return

    await interaction.response.send_message(
        f"Invite for **{guild.name}**:\n{invite}",
        ephemeral=True
    )

@bot.tree.command(name="free", description="Remove uwu effect from a user")
@app_commands.describe(member="User to free")
async def free(interaction: discord.Interaction, member: discord.Member):
    if not is_admin(interaction):
        return await interaction.response.send_message("No permission.", ephemeral=True)

    guild_data = get_guild(interaction.guild.id)
    uid = str(member.id)

    deleted = False

    # remove uwu effect data
    if uid in guild_data["users"]:
        del guild_data["users"][uid]
        save_data()
        deleted = True

    # remove all roles named "uwued"
    removed_roles = []
    for role in member.roles:
        if role.name.lower() == "uwued":
            await member.remove_roles(role)
            removed_roles.append(role.name)

    if deleted or removed_roles:
        await interaction.response.send_message(
            f"{member.display_name} has been freed ✨"
        )
    else:
        await interaction.response.send_message(
            f"{member.display_name} is not affected."
        )

@bot.tree.command(name="uwulock", description="Toggle permanent mode for a user")
@app_commands.describe(member="User to toggle", mode="Transformation mode")
@app_commands.choices(mode=mode_choices())
async def uwulock(interaction: discord.Interaction, member: discord.Member, mode: str = "uwu"):
    if not is_admin(interaction):
        return await interaction.response.send_message("No permission.", ephemeral=True)

    guild_data = get_guild(interaction.guild.id)
    uid = str(member.id)
    users = guild_data["users"]

    if uid in users:
        del users[uid]
        msg = f"Unlocked {member.display_name}"
    else:
        users[uid] = {"expiry": float("inf"), "mode": mode}
        msg = f"Locked {member.display_name} with mode '{mode}'"

    save_data()
    await interaction.response.send_message(msg)

@bot.tree.command(name="uwuout", description="Temporarily apply a mode to a user")
@app_commands.describe(member="User", duration="Seconds", reason="Why", mode="Transformation mode")
@app_commands.choices(mode=mode_choices())
async def uwuout(interaction: discord.Interaction, member: discord.Member, duration: int, reason: str, mode: str = "uwu"):
    print(interaction.user.id)
    print(member.id)
    print(is_admin(interaction))
    print(type(member))
    if (not is_admin(interaction)) and interaction.user.id != member.id:
        return await interaction.response.send_message("No permission.", ephemeral=True)

    guild_data = get_guild(interaction.guild.id)
    uid = str(member.id)

    if interaction.user.id == member.id:
        try: guild_data["users"][str(member.id)]
        except: pass
        else: return await interaction.response.send_message("Don't try to bypass your current uwuout, silly!")

    guild_data["users"][uid] = {
        "expiry": time.time() + duration,
        "mode": mode
    }

    save_data()

    await interaction.response.send_message(
        f"{member.mention} affected for {duration}s (mode: {mode})\nReason: {reason}"
    )

@bot.tree.command(name="channeluwu", description="Toggle mode for a channel")
@app_commands.describe(channel="Channel", mode="Transformation mode")
@app_commands.choices(mode=mode_choices())
async def channeluwu(interaction: discord.Interaction, channel: discord.TextChannel, mode: str = "uwu"):
    if not is_admin(interaction):
        return await interaction.response.send_message("No permission.", ephemeral=True)

    guild_data = get_guild(interaction.guild.id)
    cid = str(channel.id)
    channels = guild_data["channels"]

    if cid in channels:
        del channels[cid]
        msg = f"Disabled in {channel.mention}"
    else:
        channels[cid] = mode
        msg = f"Enabled in {channel.mention} with mode '{mode}'"

    save_data()
    await interaction.response.send_message(msg)

@bot.tree.command(name="uwu", description="Apply a mode to text")
@app_commands.describe(text="Text", mode="Transformation mode")
@app_commands.choices(mode=mode_choices())
async def uwu(interaction: discord.Interaction, text: str, mode: str = "uwu"):
    transform = MODES.get(mode, uwu_mode)
    await interaction.response.send_message(transform(text))

@bot.tree.command(name="ping", description="Pong!")
async def ping(interaction: discord.Interaction):
    await interaction.response.send_message("Pong!")

@bot.tree.command(name="translate", description="Translate text to another language")
async def translate(interaction: discord.Interaction, lang: str, text: str):
    try:
        translated = GoogleTranslator(source="auto", target=lang).translate(text)
        await interaction.response.send_message(
            f"Translated to `{lang}`:\n{translated}"
        )
    except Exception as e:
        await interaction.response.send_message(
            f"Translation failed: {e}",
            ephemeral=True
       )

@bot.tree.command(name="translate", description="Translate a message from its Discord link")
async def translate_message(interaction: discord.Interaction, lang: str, message_link: str):
    try:
        # Split link into IDs
        parts = message_link.split("/")
        guild_id = int(parts[-3])
        channel_id = int(parts[-2])
        message_id = int(parts[-1])

        channel = bot.get_channel(channel_id) or await bot.fetch_channel(channel_id)
        message = await channel.fetch_message(message_id)

        translated = translatelib.translate(message.content, "auto", lang)

        await interaction.response.send_message(
            f"Original:\n{message.content}\n\nTranslated to `{lang}`:\n{translated}"
        )

    except Exception as e:
        await interaction.response.send_message(
            f"An error occurred during translation: {e}",
            ephemeral=True
        )

@bot.tree.command(name="hypertranslate", description="'Hypertranslate' a message from its Discord link")
async def hypertranslate_message(interaction: discord.Interaction, lang: str, message_link: str, count: int):
    try:
        # Split link into IDs
        parts = message_link.split("/")
        guild_id = int(parts[-3])
        channel_id = int(parts[-2])
        message_id = int(parts[-1])

        channel = bot.get_channel(channel_id) or await bot.fetch_channel(channel_id)
        message = await channel.fetch_message(message_id)

        translated = translatelib.hypertranslate(message.content, "auto", lang, count)
        path = ""
        for pathitem in translated.path:
            path += pathitem + " -> "
            
        await interaction.response.send_message(
            f"Original:\n{message.content}\n\nHypertranslated (`{path}`):\n{translated.text}"
        )

    except Exception as e:
        await interaction.response.send_message(
            f"An error occurred during translation: {e}",
            ephemeral=True
        )

async def get_or_create_role(guild: discord.Guild) -> discord.Role:
    role = discord.utils.get(guild.roles, name=ROLE_NAME)
    if role:
        return role

    return await guild.create_role(name=ROLE_NAME, reason="Auto-created uwu mod role")


@bot.tree.command(name="trust", description="Give uwu mod role to a user")
async def trust(interaction: discord.Interaction, target: discord.Member):
    if interaction.user.id != OWNER_USER_ID and not interaction.user.guild_permissions.administrator:
        return await interaction.response.send_message("No permission.", ephemeral=True)

    if not interaction.guild:
        return await interaction.response.send_message("Guild only.", ephemeral=True)

    role = await get_or_create_role(interaction.guild)
    await target.add_roles(role, reason=f"Trusted by {interaction.user}")

    await interaction.response.send_message(f"Gave {role.name} to {target.mention}")


@bot.tree.command(name="untrust", description="Remove uwu mod role from a user")
async def untrust(interaction: discord.Interaction, target: discord.Member):
    if interaction.user.id != OWNER_USER_ID and not interaction.user.guild_permissions.administrator:
        return await interaction.response.send_message("No permission.", ephemeral=True)

    if not interaction.guild:
        return await interaction.response.send_message("Guild only.", ephemeral=True)

    role = discord.utils.get(interaction.guild.roles, name=ROLE_NAME)
    if not role:
        return await interaction.response.send_message("Role doesn't exist.", ephemeral=True)

    await target.remove_roles(role, reason=f"Untrusted by {interaction.user}")
    await interaction.response.send_message(f"Removed {role.name} from {target.mention}")

bot.run("token")
