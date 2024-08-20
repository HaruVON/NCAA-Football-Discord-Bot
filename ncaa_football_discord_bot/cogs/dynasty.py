import asyncio
import discord
from discord.ext import commands
import json
import os

# Setup function to add this cog to the bot
def setup(bot):
    bot.add_cog(DynastySetupCog(bot))

class DynastySetupCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.data_dir = "data"
        self.invite_file = os.path.join(self.data_dir, "invite_role_data.json")
        self.invite_data = self.load_invite_data()

    def load_invite_data(self):
        """Load invite data from a JSON file, or create the file if it doesn't exist."""

        if not os.path.exists(self.data_dir):
            os.makedirs(self.data_dir)

        if not os.path.exists(self.invite_file):
            # Create the file with an empty dictionary if it doesn't exist
            with open(self.invite_file, "w") as file:
                json.dump({}, file, indent=4)

        # Load the data from the file
        with open(self.invite_file, "r") as file:
            return json.load(file)


    def save_invite_data(self):
        """Save invite data to a JSON file."""
        with open(self.invite_file, "w") as file:
            json.dump(self.invite_data, file, indent=4)

    @commands.has_permissions(manage_channels=True)
    @commands.guild_only()
    @commands.slash_command(name="create_dynasty", description="Create a category with predefined channels and restricted access.")
    async def create_dynasty(self, ctx, category_name: str):
        """Creates a category with predefined channels, restricted access, and an invite link."""

        await ctx.defer()  # Use ctx.defer() for slash command

        guild = ctx.guild

        # Add crown emojis to the category name
        formatted_category_name = f"👑{category_name}👑"

        # Create the role with the same name as the category
        role_name = category_name
        role = await guild.create_role(name=role_name)
        await ctx.send(f"Created role: {role.name}")

        # Set up permission overwrites for the category
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(view_channel=False),
            role: discord.PermissionOverwrite(view_channel=True)
        }

        # Create the category
        category = await guild.create_category(name=formatted_category_name, overwrites=overwrites)
        await ctx.send(f"Created category: {category.name}")

        # Determine the prefix for channel names
        category_name_words = category_name.split()
        if len(category_name_words) > 1:
            # Create an acronym for multi-word category names
            prefix = ''.join(word[0] for word in category_name_words).lower()
        else:
            # Use the full category name for single-word category names
            prefix = category_name.lower()

        # List of channels to create within the category
        channels = [
            {"name": "readme", "type": discord.ChannelType.text},
            {"name": "announcements", "type": discord.ChannelType.text},
            {"name": "rules", "type": discord.ChannelType.text},
            {"name": "vote", "type": discord.ChannelType.text},
            {"name": "general", "type": discord.ChannelType.text},
            {"name": "threads", "type": discord.ChannelType.text},
            {"name": "teams", "type": discord.ChannelType.text},
            {"name": "voice", "type": discord.ChannelType.voice},
        ]

        created_channels = {}

        # Create the channels within the category, prepending category name
        for channel_info in channels:
            channel_name = f"{prefix} {channel_info['name']}"
            channel_type = channel_info["type"]

            try:
                if channel_type == discord.ChannelType.text:
                    channel = await guild.create_text_channel(name=channel_name, category=category)
                elif channel_type == discord.ChannelType.voice:
                    channel = await guild.create_voice_channel(name=channel_name, category=category)

                created_channels[channel_info["name"]] = channel
                await ctx.send(f"Created {channel_type.name} channel: {channel_name}")

                # Adding a slight delay to avoid overwhelming Discord API
                await asyncio.sleep(1)
            except Exception as e:
                await ctx.send(f"Failed to create channel {channel_name}: {str(e)}")
                return  # Stop further execution if an error occurs

        # Generate an invite link for the category's general channel
        try:
            invite = await created_channels["general"].create_invite(max_uses=0, unique=True)
            self.invite_data[invite.code] = {
                "role_id": role.id,
                "role_name": role.name,
                "category_name": category.name,
                "guild_id": guild.id,
                "invite_id": invite.id  # Store invite ID
            }
            self.save_invite_data()

            await ctx.send(f"Created invite link: {invite.url}")
            await ctx.respond(f"Category '{formatted_category_name}' with channels has been set up with restricted access to the role '{role_name}'.")
        except KeyError:
            await ctx.send("Failed to create an invite for the GENERAL channel. Make sure it was created successfully.")

    @commands.Cog.listener()
    async def on_member_join(self, member):
        # Ideally, you'd store and compare invites before and after the join
        invites_before_join = await member.guild.invites()
        used_invite = None
        for invite in invites_before_join:
            if invite.uses == 1:
                used_invite = invite
                break

        if not used_invite:
            return

        # Check if the invite is associated with a role
        invite_info = self.invite_data.get(used_invite.code)
        if invite_info and invite_info["guild_id"] == member.guild.id:
            role = discord.utils.get(member.guild.roles, id=invite_info["role_id"])
            if role:
                await member.add_roles(role)
                await member.guild.system_channel.send(f"{member.mention} joined using {used_invite.url} and has been given the {role.name} role.")
                
                # Send a welcome message in the GENERAL channel of the category
                general_channel = discord.utils.get(member.guild.channels, name=f"{role.name} | GENERAL")
                if general_channel:
                    await general_channel.send(f"Welcome {member.mention} to {general_channel.category.name}!")

    @commands.has_permissions(manage_channels=True)
    @commands.guild_only()
    @commands.slash_command(name="delete_dynasty", description="Delete a category, all its channels, and the associated role.")
    async def delete_dynasty(self, ctx, category_name: str):
        """Deletes a dynasty, all its channels, and the associated role."""
        await ctx.defer()  # Use ctx.defer() for slash command
        guild = ctx.guild
        category = discord.utils.get(guild.categories, name=category_name)

        if not category:
            await ctx.respond(f"No category found with the name: {category_name}")
            return

        role_id = None
        invite_id = None

        # Iterate over the overwrites to find the role with view_channel permission
        for role, overwrites in category.overwrites.items():
            if isinstance(role, discord.Role) and overwrites.view_channel:
                role_id = role.id
                break

         # Get the invite ID from the stored data
        for invite_code, invite_info in self.invite_data.items():
            if invite_info["category_name"] == category_name and invite_info["guild_id"] == guild.id:
                invite_id = invite_info.get("invite_id")
                break

        errors = []
        for channel in category.channels:
            try:
                await channel.delete()
                await asyncio.sleep(1)  # Add a delay to prevent "Unknown Integration" errors
            except discord.DiscordException as e:
                errors.append(f"Failed to delete channel {channel.name}: {str(e)}")

        try:
            await category.delete()
        except discord.DiscordException as e:
            errors.append(f"Failed to delete category {category.name}: {str(e)}")

        if role_id:
            role = discord.utils.get(guild.roles, id=role_id)
            if role:
                try:
                    await role.delete()
                except discord.DiscordException as e:
                    errors.append(f"Failed to delete role {role.name}: {str(e)}")

        if invite_id:
            invite = discord.utils.get(await guild.invites(), id=invite_id)

        if invite:
            try:
                await invite.delete()
                del self.invite_data[invite.code]  # Remove from invite data
                self.save_invite_data()
            except discord.DiscordException as e:
                errors.append(f"Failed to revoke invite {invite.url}: {str(e)}")

        if errors:
            await ctx.respond(f"Encountered errors while deleting category, channels, and role: {'; '.join(errors)}")
        else:
            await ctx.respond(f"Successfully deleted category, all channels, and the associated role: {category_name}")
