import json
import discord
import os
import time
import tinytuya
from enum import Enum
from datetime import datetime
from discord.ext import tasks

class People(Enum):
    ETHAN = 818878534541115401
    AMIEL = 416852923369127957
    IGGY = 3129176466959892484

ID_TO_NAME = {
    818878534541115401: (People.ETHAN, 0b01),
    416852923369127957: (People.AMIEL, 0b10),
    312917646695989248: (People.IGGY, 0b100)
}

d = tinytuya.Device(
    os.environ['TUYA_DEVID'],
    os.environ['TUYA_IPADDR'],
    local_key=os.environ['TUYA_LOCALKEY'],
    version=3.5
)

# Print once on startup to verify ON status
print(d.status())

# Simple logging
def log(msg, l=1):
    now = datetime.now()
    formatted = now.strftime("%m-%d %H:%M")
    print(f"[{formatted}{'  '*(l-1)}] {msg}")

# Helper class for JSON db
class AirconInfo:
    def __init__(self, current_users, last_off, current_raw, on_time, off_time):
        self.current_users = current_users
        self.last_off = last_off
        self.current_users_raw = current_raw
        self.on_time = on_time
        self.off_time = off_time

    @staticmethod
    def get_ac_info():
        with open("aircon_info.json", "r") as f:
            info = json.load(f)
            last_off = info["last_off"]
            current_users = []

            if info["current_users"] & 0b01:
                current_users.append(People.ETHAN)
            if info["current_users"] & 0b10:
                current_users.append(People.AMIEL)
            if info["current_users"] & 0b100:
                current_users.append(People.IGGY)

            return AirconInfo(current_users, last_off, info["current_users"], info["on_time"], info["off_time"])

    @staticmethod
    def save_ac_info(current_users: int, last_off, on_time, off_time):
        with open("aircon_info.json", "w") as f:
            json.dump({"current_users": current_users, "last_off": last_off, "on_time": on_time, "off_time": off_time}, f)

bot = discord.Bot()
WAIT_TIME_MINS = 2

class MyView(discord.ui.View):

    @discord.ui.button(
        label="Turn AC on",
        style=discord.ButtonStyle.success
    )
    async def ac_on_callback(self, button, interaction: discord.Interaction):
        log("AC requested to be turned on", l=2)

        ac_info = AirconInfo.get_ac_info()
        delta_t = time.time() - ac_info.last_off

        ac_channel = bot.get_channel(1418199915154378803)

        if interaction.user.id not in ID_TO_NAME.keys():
            log("Unauthorized user. Ignoring.", l=2)
            await interaction.response.edit_message(content="You're not authorized to turn on/off the AC.")
            return

        # If enough time has passed (prevents AC on/off spam which could damage the AC)
        if delta_t > (60 * WAIT_TIME_MINS):
            log("Enough time passed. Proceeding...", l=2)

            # AC already turned on by user
            if ac_info.current_users_raw & ID_TO_NAME[interaction.user.id][1]:
                log("AC already turned on previously by user. Ignoring.", l=2)
                await interaction.response.send_message(
                    content="You already turned on the AC!",
                    ephemeral=True,
                    delete_after=15
                )
                return

            current_users = ac_info.current_users_raw | ID_TO_NAME[interaction.user.id][1]

            log("Aircon turned on.", l=2)
            d.set_status(True, 16)

            # no one has turned on the ac
            if not ac_info.current_users_raw:
                log("Single user turned on AC.", l=2)

                # if the aircon is turned on within shared time (e.g., 8pm-6am),
                # all users will share the bill
                if now_within_aircon_range(ac_info):
                    log("Since within shared time, all users are shared", l=2)
                    desc = f"By <@{interaction.user.id}> at <t:{int(time.time())}:f>. All users are counted since turned on within shared time."
                    current_users = 7 # all users
                else:
                    desc = f"By <@{interaction.user.id}> at <t:{int(time.time())}:f>."

                embed = discord.Embed(
                    title="Aircon turned ON",
                    description = desc,
                    color = discord.Color.green()
                )
            else:
                log("Multiple user turned on AC.", l=2)

                users_ids = ", ".join([f"<@{a.value}>" for a in ac_info.current_users])
                embed = discord.Embed(
                    title=f"<@{interaction.user.id}> joined {users_ids} in turning the AC on!",
                    description=f"At <t:{int(time.time())}:f>.",
                    color=discord.Color.green()
                )

            AirconInfo.save_ac_info(current_users, ac_info.last_off, ac_info.on_time, ac_info.off_time)

            await ac_channel.send(embed=embed)
            await interaction.response.send_message(content="AC turned on! Check <#1418199915154378803> for the log.", ephemeral=True, delete_after=15)
            return
        else:
            log("Not enough time since AC turned off. Ignoring.", l=2)
            await interaction.response.send_message(
                content=f"Less than {WAIT_TIME_MINS} minutes since last turned on (<t:{int(ac_info.last_off)}:t>). Please try again <t:{int(ac_info.last_off) + 60 * WAIT_TIME_MINS}:R>.",
                delete_after=15,
                ephemeral=True
            )
            return

    @discord.ui.button(
        label="Turn AC off",
        style=discord.ButtonStyle.danger
    )
    async def ac_off_callback(self, button, interaction):
        log("AC requested to be turned off")

        ac_info = AirconInfo.get_ac_info()

        if not ac_info.current_users:
            log("AC already off, requested.", l=2)
            await interaction.response.send_message(
                content="AC is already off!",
                ephemeral=True,
                delete_after=15
            )
            return

        AirconInfo.save_ac_info(0x00, time.time(), ac_info.on_time, ac_info.off_time)
        ac_channel = bot.get_channel(1418199915154378803)

        embed = discord.Embed(
            title="Aircon turned OFF",
            description=f"By <@{interaction.user.id}> at <t:{int(time.time())}:f>.",
            color=discord.Color.red()
        )

        log("AC turned OFF", l=2)
        d.set_status(False, 16)

        await ac_channel.send(embed=embed)
        await interaction.response.send_message(
            content=f"AC turned off! Check <#1418199915154378803> for the log.",
            ephemeral=True,
            delete_after=15
        )

def now_within_aircon_range(ac_info: AirconInfo):
    now = datetime.now().time()
    on_time = datetime.strptime(ac_info.on_time, "%H:%M").time()
    off_time = datetime.strptime(ac_info.off_time, "%H:%M").time()
    return now >= on_time or now <= off_time

async def send_ctrl_view():
    chn = bot.get_channel(1418158999836033027)

    embed = discord.Embed(
        title="Aircon Control",
        description="Turn the aircon on/off using the buttons below.",
        color=discord.Color.blue()
    )

    await chn.send(embed=embed, view=MyView(timeout=None))

@bot.slash_command(
    name="ac",
    description="Send the message to control the AC.",
    guild_ids=[1418158998775140394]
)
async def aircon_cmd(ctx: discord.ApplicationContext):
    await ctx.delete()
    await send_ctrl_view()

# task loop to check power monitor status
# notifies people if it can't connect to the power monitor
@tasks.loop(minutes=1)
async def time_check():
    now = datetime.now()
    time_24h = now.strftime("%H:%M")
    ac_info = AirconInfo.get_ac_info()
    ac_channel = bot.get_channel(1418199915154378803)

    log("Getting power monitor status...")
    s = d.status()
    log(s, l=2)

    if s.get('Error') == 'Network Error: Unable to Connect':
        embed = discord.Embed(
            title=f"Whoever unplugged the power monitor, please plug it back in! ",
            description=f"At <t:{int(time.time())}:f>.",
            color=discord.Color.red()
        )
        await ac_channel.send(
            embed=embed
        )
        return

    if time_24h == ac_info.on_time:
        log("AC automatically turned on.")
        # turn AC on
        d.set_status(True, 16)
        # make everyone a user
        AirconInfo.save_ac_info(7, ac_info.last_off, ac_info.on_time, ac_info.off_time)

        embed = discord.Embed(
            title=f"Aircon turned on automatically!",
            description=f"At <t:{int(time.time())}:f>.",
            color=discord.Color.green()
        )

        await ac_channel.send(embed=embed)
        return

    if time_24h == ac_info.off_time:
        log("AC automatically turned off.")
        # turn AC on
        d.set_status(False, 16)
        # remove everyone as a user
        AirconInfo.save_ac_info(0, ac_info.last_off, ac_info.on_time, ac_info.off_time)

        embed = discord.Embed(
            title=f"Aircon turned off automatically!",
            description=f"At <t:{int(time.time())}:f>.",
            color=discord.Color.red()
        )

        await ac_channel.send(embed=embed)
        return

@bot.event
async def on_ready():
    log(f"Aircon bot is ONLINE as {bot.user}!")
    time_check.start()
    await send_ctrl_view()

bot.run(os.environ['TOKEN'])
