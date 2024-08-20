# This example requires the 'message_content' intent.
import asyncio
import cogs.head_to_head
import cogs.dynasty
import dotenv
import discord
import os


try:
    # Attempt to load the .env file
    if not dotenv.load_dotenv(dotenv.find_dotenv(), override=True):
        print(".env file not found, proceeding with environment variables")
except Exception as e:
    print(f"Error loading .env file: {e}")

# Use the environment variables
token = os.getenv('DISCORD_TOKEN')

if token:
    print("Discord token loaded successfully.")
else:
    print("Discord token not found.")


intents = discord.Intents.default()
intents.message_content = True

# bot = discord.ext.commands.Bot(intents=intents)
bot = discord.Bot(intents=intents)

@bot.event
async def on_ready():
    print(f'We have logged in as {bot.user}')
    print(f'List of commands: {bot.commands}')


@bot.event
async def on_message(message):
    if message.author == bot.user:
        return
    if message.content.startswith('$hello'):
        await message.channel.send('Hello!')


@bot.slash_command(description="Sends the bot's latency.") # this decorator makes a slash command
async def ping(ctx): # a slash command will be created with the name "ping"
    await ctx.respond(f"Pong! Latency is {bot.latency}")



# Load the cog
def load_cogs():
    # await bot.load_extension("cogs.head_to_head")
    bot.load_extension("cogs.dynasty")


# Main function to run the bot
async def main():
    load_cogs()
    await bot.start(token)

asyncio.run(main())

# bot.run(token)