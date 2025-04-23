import discord
from discord.ext import commands, tasks
from discord.ui import Button, View
from datetime import datetime, timedelta
import json
import asyncio
import requests

# ------------------ Intents Setup ------------------
intents = discord.Intents.default()
intents.members = True
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

# ------------------ Configuration ------------------
UPLOAD_FORM_URL = "https://yourappurl.com"  # Flask app URL
UPLOAD_CHANNEL_NAME = "upload"  # Private channel for webhook messages

# ------------------ Data Storage ------------------
# Store user-channel mapping for !upload requests
upload_requests = {}

# ------------------ Events ------------------
@bot.event
async def on_ready():
    print(f"✅ Logged in as {bot.user}")

@bot.event
async def on_message(message):
    if message.author.bot:
        return

    await bot.process_commands(message)   

@bot.event
async def on_member_join(member):

    # Get you channel name here
    welcome_channel = discord.utils.get(member.guild.text_channels, name="My-server")
    member_role = discord.utils.get(member.guild.roles, name="Member")
    
    if member_role:
        await member.add_roles(member_role)
        print(f"✅ Assigned 'Member' role to {member.display_name}")

    if welcome_channel:
        await welcome_channel.send(
            f"👋 Welcome {member.mention} to **{member.guild.name}**! Please check <#rules>. You have been assigned the 'Member' role."
        )

@bot.event
async def on_message(message):
    # Listen to webhook messages in the 'upload' channel and forward to the user's channel
    if message.channel.name == UPLOAD_CHANNEL_NAME and message.webhook_id:
        content = message.content
        data = json.loads(content) if content.startswith("{") else None

        if data:
            uploader_id = data.get("uploader_id")
            channel_id = data.get("channel_id")
            file_name = data.get("file_name")
            file_link = data.get("file_link")

            # Use channel_id directly from webhook payload
            target_channel = bot.get_channel(int(channel_id))
            if target_channel:
                # Find the original command message
                async for msg in target_channel.history(limit=10):
                    if msg.author.id == int(uploader_id) and msg.content.startswith("!upload"):
                        await msg.reply(
                            f"📄 **File Uploaded**\n👤 Uploaded by: <@{uploader_id}>\n📄 File: `{file_name}`\n🔗 [View File]({file_link})",
                            ephemeral=True
                        )
                        break
            else:
                print(f"⚠️ Channel with ID {channel_id} not found.")

        return

    await bot.process_commands(message)

# ------------------ Upload Command ------------------
@bot.command()
async def upload(ctx):
    """Send an upload button that opens the Flask form with uploader info."""
    uploader_id = ctx.author.id
    channel_id = ctx.channel.id

    # Save the channel where user requested upload
    upload_requests[str(uploader_id)] = channel_id

    class UploadView(View):
        def __init__(self, uploader_id, channel_id):
            super().__init__(timeout=60)
            upload_url = f"{UPLOAD_FORM_URL}?uploader_id={uploader_id}&channel_id={channel_id}"
            self.add_item(Button(label="📤 Upload File", style=discord.ButtonStyle.link, url=upload_url))

    # Delete the command message and send ephemeral response
    await ctx.message.delete()
    await ctx.send(
        f"{ctx.author.mention} Click the button below to upload a file:",
        view=UploadView(uploader_id, channel_id),
        ephemeral=True
    )

# ------------------ Webhook Handler ------------------
def send_file_notification(file_name, uploader, file_link):
    payload = {
        "content": f"📥 **New File Uploaded**\n👤 Uploaded by: {uploader}\n📄 File: {file_name}\n🔗 [View File]({file_link})"
    }
    response = requests.post(DISCORD_WEBHOOK_URL, json=payload)
    if response.status_code == 204:
        print("✅ File notification sent to Discord.")
    else:
        print(f"❌ Failed to send notification: {response.status_code}")

# ------------------ Ticketing System ------------------
@bot.command()
async def ticket(ctx):
    # Delete the command message first
    await ctx.message.delete()
    
    button = Button(label="Create Ticket", style=discord.ButtonStyle.green)

    async def button_callback(interaction):
        tickets_category = discord.utils.get(ctx.guild.categories, name="Tickets")
        if not tickets_category:
            tickets_category = await ctx.guild.create_category("Tickets")

        overwrites = {
            ctx.guild.default_role: discord.PermissionOverwrite(read_messages=False),
            interaction.user: discord.PermissionOverwrite(read_messages=True, send_messages=True),
            ctx.guild.me: discord.PermissionOverwrite(read_messages=True)
        }

        ticket_channel = await ctx.guild.create_text_channel(
            name=f"ticket-{interaction.user.name}", category=tickets_category, overwrites=overwrites
        )
        await ticket_channel.send(f"🎫 Hello {interaction.user.mention}, how can we help you?")
        await interaction.response.send_message(f"✅ Ticket created: {ticket_channel.mention}", ephemeral=True)

    button.callback = button_callback
    view = View()
    view.add_item(button)
    
    # Send ephemeral message
    await ctx.send("Click the button below to create a support ticket:", view=view, ephemeral=True)

# ------------------ Role Management ------------------
@bot.command()
async def roles(ctx):
    # Delete the command message first
    await ctx.message.delete()
    
    # Create a new interaction for ephemeral message
    message = await ctx.send(
        "React to request a role:\n🔴 for Developer\n🔵 for Sale\n🟣 for Designer\n🟡 for IT",
        ephemeral=True
    )
    await message.add_reaction("🔴")
    await message.add_reaction("🔵")
    await message.add_reaction("🟣")
    await message.add_reaction("🟡")

@bot.event
async def on_raw_reaction_add(payload):
    if payload.member.bot:
        return

    guild = bot.get_guild(payload.guild_id)
    member = guild.get_member(payload.user_id)
    admin_channel = discord.utils.get(guild.text_channels, name="role-requests")

    if not admin_channel:
        return  # Admin channel not found

    # Map emoji to roles
    emoji_to_role = {"🔴": "Developer", "🔵": "Sale", "🟣": "Designer", "🟡": "IT"}
    requested_role = emoji_to_role.get(payload.emoji.name)

    if not requested_role:
        return

    # Send approval request to admin
    class AdminApprovalView(discord.ui.View):
        def __init__(self, user, role_name):
            super().__init__(timeout=300)
            self.user = user
            self.role_name = role_name

        @discord.ui.button(label="✅ Approve", style=discord.ButtonStyle.success)
        async def approve(self, interaction: discord.Interaction, button: discord.ui.Button):
            if not interaction.user.guild_permissions.manage_roles:
                await interaction.response.send_message("🚫 You don't have permission to approve roles.", ephemeral=True)
                return

            role = discord.utils.get(interaction.guild.roles, name=self.role_name)
            if role:
                await self.user.add_roles(role)
                await interaction.response.send_message(f"✅ Approved! {self.user.mention} now has the '{self.role_name}' role.", ephemeral=True)
                try:
                    await self.user.send(f"🎉 Your request for the '{self.role_name}' role was approved!")
                except:
                    pass
            else:
                await interaction.response.send_message(f"⚠️ Role '{self.role_name}' not found.", ephemeral=True)
            self.stop()

        @discord.ui.button(label="❌ Deny", style=discord.ButtonStyle.danger)
        async def deny(self, interaction: discord.Interaction, button: discord.ui.Button):
            if not interaction.user.guild_permissions.manage_roles:
                await interaction.response.send_message("🚫 You don't have permission to deny roles.", ephemeral=True)
                return

            await interaction.response.send_message(f"❌ Denied {self.user.mention}'s request for '{self.role_name}'.", ephemeral=True)
            try:
                await self.user.send(f"🚫 Your request for the '{self.role_name}' role was denied.")
            except:
                pass
            self.stop()

    # Send the role request to admin channel
    await admin_channel.send(
        f"🔔 **Role Request:** {member.mention} is requesting the **'{requested_role}'** role.",
        view=AdminApprovalView(member, requested_role)
    )

# ------------------ Run Bot ------------------
bot.run('Discordbottokenhere') #add your bot token here