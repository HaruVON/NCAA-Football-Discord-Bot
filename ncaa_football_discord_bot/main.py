from bot import bot
import os

# for filename in os.listdir('./cogs'):
#     if filename.endswith('.py'):
#         bot.load_extension(f'cogs.{filename[:-3]}')

# cogs_list = [
#     'greetings',
#     'moderation',
#     'fun',
#     'owner'
# ]

# for cog in cogs_list:
#     bot.load_extension(f'cogs.{cog}')

if __name__ == "__main__":
    bot.run()