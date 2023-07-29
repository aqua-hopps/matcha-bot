from interactions import Client, Intents, listen
from interactions import slash_command, SlashContext
from interactions import OptionType, slash_option
from interactions import Embed, EmbedField
from interactions.api.events import CommandError

from dotenv import load_dotenv
from datetime import datetime
from bookings import book, unbook, wait_for_sdr, delete_booking_entry

from google.cloud import compute_v1

import os
import traceback
import asyncio
import concurrent.futures


# Colors
green = "#4c7c2c"
blue  = "#2c4c7c"
red   = "#7c2c4c"


# Load environment variables
load_dotenv()

token = os.getenv("DISCORD_BOT_TOKEN")
project_id = os.getenv("PROJECT_NAME")

# Authenticate with GCP
instance_client = compute_v1.InstancesClient()

# intents are what events we want to receive from discord, `DEFAULT` is usually fine
bot = Client(intents=Intents.DEFAULT)


@listen()  # this decorator tells snek that it needs to listen for the corresponding event, and run this coroutine
async def on_ready():
    # This event is called when the bot is ready to respond to commands
    print("Bot is online")


@listen(CommandError, disable_default_listeners=True)  # tell the dispatcher that this replaces the default listener
async def on_command_error(event: CommandError):
    traceback.print_exception(event.error)
    if not event.ctx.responded:
        await event.ctx.send("Something went wrong.")


@slash_command(name="hello", description="Za Warudo")
async def hello_command(ctx: SlashContext):
    await ctx.send("Hello World!")


@slash_command(name="book", description="Book a server in your desired region.")
@slash_option(
    name="region",
    description="country",
    required=True,
    opt_type=OptionType.STRING
)
async def book_command(ctx: SlashContext, region: str):
    # Ignore DM messages
    if ctx.guild is None:
        return
    
    # User info
    userid = int(ctx.author.id)
    username = ctx.author.username
    country = region.lower()

    # Book the server
    status, instance_name, instance_zone = await book(userid, username, country)

    if status == "failed":
        embed = Embed(
            timestamp   = datetime.now(),
            color       = red,
            title       = "**Bookings**",
            description = "Your book request has failed. (database_error)\nPlease report this issue to @aqua_hopps",
            footer      = "Apologies"
        )
    if status == "user_limit":
        embed = Embed(
            timestamp   = datetime.now(),
            color       = red,
            title       = "**Bookings**",
            description = "You have already booked a server.\nPlease unbook the server before booking a new one.",
            footer      = "Regards"
        )
    if status == "capacity_limit":
        embed = Embed(
            timestamp   = datetime.now(),
            color       = red,
            title       = "**Bookings**",
            description = "There are no available servers at the moment.\nPlease try again later.",
            footer      = "Regards"
        )
    if status == "success":
        embed = Embed(
            timestamp   = datetime.now(),
            color       = blue,
            title       = "**Bookings**",
            description = "Your server is being booked, this may take some time.\nDetails will be sent via private message when the server is ready.",
            footer      = "Have fun"
        )

    # Send slash command reply
    msg = await ctx.send(ctx.author.mention, embed=embed)

    # Return if book failed
    if status != "success":
        return

    async def send_details(ip):
        status, booking = await wait_for_sdr(ip, instance_name)

        if status == "failed":
            embed = Embed(
                timestamp   = datetime.now(),
                color       = red,
                title       = "**Bookings**",
                description = "Your book request has failed. (database_error)\nPlease report this issue to @aqua_hopps",
                footer      = "Apologies"
            )
        if status == "timeout":
            embed = Embed(
                timestamp   = datetime.now(),
                color       = red,
                title       = "**Bookings**",
                description = "Your book request has failed. (server_timeout)\nPlease report this issue to @aqua_hopps",
                footer      = "Apologies"
            )

        # Define variables
        sdr_ip              = booking[0]
        sdr_port            = booking[1]
        sv_password         = booking[2]
        connect_string      = f"connect {ip}:27015; password {sv_password}"
        connect_string_sdr  = f"connect {sdr_ip}:{sdr_port}; password {sv_password}"
        stv_string          = f"connect {ip}:27020"
        stv_string_sdr      = f"connect {sdr_ip}:{sdr_port + 1}"
        
        embed_dm = Embed(
            timestamp   = datetime.now(),
            color       = green,
            title       = "**Bookings**",
            description = "Your server is ready!",
            footer      = "Have fun",
            fields      = [
                EmbedField(
                    name    = "Default Connect",
                    value   = f"```{connect_string}```",
                    inline  = False
                ),
                EmbedField(
                    name    = "SDR Connect",
                    value   = f"```{connect_string_sdr}```",
                    inline  = False
                ),
                EmbedField(
                    name    = "STV Details",
                    value   = f"```{stv_string}```",
                    inline  = False
                ),
                EmbedField(
                    name    = "SDR STV Details",
                    value   = f"```{stv_string_sdr}```",
                    inline  = False
                ),
                EmbedField(
                    name    = "Server",
                    value   = f"`{instance_name}`",
                    inline  = True
                ),
                EmbedField(
                    name    = "Region",
                    value   = f"`{country}`",
                    inline  = True
                ),
                EmbedField(
                    name    = "Reminder",
                    value   = "Use `!votemenu` to change configs and maps.",
                    inline  = False
                )
            ]
        )

        embed = Embed(
            timestamp   = datetime.now(),
            color       = green,
            title       = "**Bookings**",
            description = "Server details have been sent to you via private message.",
            footer      = "Have fun"
        )

        await ctx.author.user.send(embed=embed_dm)
        await ctx.edit(msg.id, content=ctx.author.mention, embed=embed)

    def get_external_ip(future):
        response = instance_client.get(project=project_id, instance=instance_name, zone=instance_zone, timeout=10)
        ip = response.network_interfaces[0].access_configs[0].nat_i_p
        asyncio.create_task(send_details(ip))

    # Start the instance
    try:
        operation = instance_client.start(project=project_id, instance=instance_name, zone=instance_zone, timeout=90)
        operation.add_done_callback(get_external_ip)

    except concurrent.futures.TimeoutError:
        embed = Embed(
            timestamp   = datetime.now(),
            color       = red,
            title       = "**Bookings**",
            description = "Your book request has failed. (google_cloud_timeout)\nPlease report this issue to @aqua_hopps",
            footer      = "Apologies"
        )
        await ctx.edit(msg.id, content=ctx.author.mention, embed=embed)
    except Exception as e:
        embed = Embed(
            timestamp   = datetime.now(),
            color       = red,
            title       = "**Bookings**",
            description = "Your book request has failed. (google_cloud_error)\nPlease report this issue to @aqua_hopps",
            footer      = "Apologies"
        )
        await ctx.edit(msg.id, content=ctx.author.mention, embed=embed)


@slash_command(name="unbook", description="Unbook your server.")
async def unbook_command(ctx: SlashContext):
    # Ignore DM messages
    if ctx.guild is None:
        return

    # User info
    userid   = int(ctx.author.id)
    username = ctx.author.username

    status, instance_name, instance_zone = await unbook(userid, username)

    if status == "failed":
        embed = Embed(
            timestamp   = datetime.now(),
            color       = red,
            title       = "**Bookings**",
            description = "Your unbook request has failed. (database_error)\nPlease report this issue to @aqua_hopps",
            footer      = "Apologies"
        )
    if status == "none":
        embed = Embed(
            timestamp   = datetime.now(),
            color       = red,
            title       = "**Bookings**",
            description = "You haven't booked a server yet.\nPlease book a server first.",
            footer      = "Regards"
        )
    if status == "success":
        embed = Embed(
            timestamp   = datetime.now(),
            color       = blue,
            title       = "**Bookings**",
            description = "Your server is being closed, this may take some time.",
            footer      = "Regards"
        )
    
    # Send slash command reply
    msg = await ctx.send(ctx.author.mention, embed=embed)

    if status != "success":
        return
    
    async def release_instance():
        status = await delete_booking_entry(instance_name)
        if status == "failed":
            embed = Embed(
                timestamp   = datetime.now(),
                color       = red,
                title       = "**Bookings**",
                description = "Your unbook request has failed. (database_error)\nPlease report this issue to @aqua_hopps",
                footer      = "Apologies"
            )
        if status == "success":
            embed = Embed(
                timestamp   = datetime.now(),
                color       = green,
                title       = "**Bookings**",
                description = "Your server has been closed.\nThank you for using our service.",
                footer      = "Have a nice day"
            )
        await ctx.edit(msg.id, content=ctx.author.mention, embed=embed)

    def stopped(future):
        asyncio.create_task(release_instance())

    # Stop the instance
    try:
        operation = instance_client.stop(project=project_id, instance=instance_name, zone=instance_zone, timeout=90)
        operation.add_done_callback(stopped)
    except concurrent.futures.TimeoutError:
        embed = Embed(
            timestamp   = datetime.now(),
            color       = red,
            title       = "**Bookings**",
            description = "Your unbook request has failed. (google_cloud_timeout)\nPlease report this issue to @aqua_hopps",
            footer      = "Apologies"
        )
        await ctx.edit(msg.id, content=ctx.author.mention, embed=embed)
    except Exception as e:
        embed = Embed(
            timestamp   = datetime.now(),
            color       = red,
            title       = "**Bookings**",
            description = "Your unbook request has failed. (google_cloud_error)\nPlease report this issue to @aqua_hopps",
            footer      = "Apologies"
        )
        await ctx.edit(msg.id, content=ctx.author.mention, embed=embed)

bot.start(token)