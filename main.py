import discord
from discord import app_commands
from discord.ext import commands
import os
from datetime import datetime
import asyncio
import io
import json
from flask import Flask
from threading import Thread

# ──────────────────────────────────────────────
# CONFIGURACIÓN
GUILD_ID = 1470640454600233021
MOD_ROLE_ID = 1470640785337749606
YOUR_USER_ID = 1424834232680976515
LOG_CHANNEL_ID = 1472080391014973603
FOOTER_TEXT = "KOP PRODUCCIONES!"
FOOTER_ICON = "https://i.imgur.com/QDo9vAq.png"

TICKET_CATEGORY_ID = 1472093377142198414  # ← Tu ID de categoría (ya lo tienes correcto)

COUNTERS_FILE = "ticket_counters.json"
# ──────────────────────────────────────────────

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

def load_counters():
    if os.path.exists(COUNTERS_FILE):
        with open(COUNTERS_FILE, 'r') as f:
            return json.load(f)
    return {"soporte": 0, "postulaciones": 0, "vip": 0, "donaciones": 0}

def save_counters(counters):
    with open(COUNTERS_FILE, 'w') as f:
        json.dump(counters, f, indent=4)

class TicketView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="| ꜱᴏᴘᴏʀᴛᴇ", style=discord.ButtonStyle.danger, emoji="🎫", custom_id="ticket_soporte")
    async def soporte_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self._create_ticket(interaction, "soporte", """¡Hola! ✨
Gracias por abrir un ticket de soporte. Estamos aquí para ayudarte.
Cuéntanos tu problema de la forma más clara posible. Si es necesario, adjunta imágenes o pruebas para que podamos entender mejor tu caso.
Lo más pronto posible un administrador o alguien del equipo se pondrá en contacto contigo para ayudarte. Gracias por tu paciencia y comprensión.""")

    @discord.ui.button(label="| ᴘᴏꜱᴛᴜʟᴀᴄɪᴏɴᴇꜱ", style=discord.ButtonStyle.success, emoji="📝", custom_id="ticket_postulaciones")
    async def postulaciones_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self._create_ticket(interaction, "postulaciones", """¡Hola! ✨
Nos alegra verte por aquí. Gracias por tu interés en formar parte del proyecto.
Tómate un momento para responder con calma y cuéntanos un poco sobre ti.
Para empezar tu postulación, envía un solo mensaje con la siguiente información, en este orden:
─ Nombre:
─ Edad:
─ Tiempo disponible: (horas/días que puedes dedicar)
─ ¿Por qué deberíamos elegirte?
─ Experiencia previa: (Desarrollador, en producciones, en eventos, etcétera. Si no tienes, cuéntanos igual)
Cualquier otra pregunta o información adicional que necesitemos te la haremos saber.
Con esta información ya podemos empezar tu postulación. Lo más pronto posible un administrador te responderá. ¡Mucha suerte!""")

    @discord.ui.button(label="| ᴠɪᴘ", style=discord.ButtonStyle.primary, emoji="👑", custom_id="ticket_vip")
    async def vip_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self._create_ticket(interaction, "vip", """¡Hola! ✨
Este espacio es para resolver tus dudas sobre el VIP o para realizar la compra del mismo.
Aquí puedes preguntarnos todo lo que necesites saber antes de decidirte: beneficios incluidos, condiciones o cualquier otra consulta que tengas.
Si ya tienes claro que quieres adquirir el VIP, cuéntanos por aquí y te guiaremos paso a paso en el proceso. También puedes comentarnos si tienes alguna duda específica o algo que te gustaría saber antes de comprar.
En breve, un administrador se pondrá en contacto contigo para responderte y ayudarte con todo.
¡Gracias por tu interés en apoyar el proyecto!""")

    @discord.ui.button(label="| ᴅᴏɴᴀᴄɪᴏɴᴇꜱ", style=discord.ButtonStyle.primary, emoji="💰", custom_id="ticket_donaciones")
    async def donaciones_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self._create_ticket(interaction, "donaciones", """¡Hola! :sparkles:
Agradecemos mucho tu interés en apoyar o aportar a la producción.
Cuéntanos por aquí en qué te gustaría colaborar o cómo te gustaría apoyar al proyecto.
Lo más pronto posible un administrador contacto contigo para responderte.
¡Gracias por el apoyo! :heart:""")

    async def _create_ticket(self, interaction: discord.Interaction, category: str, welcome_msg: str):
        user = interaction.user
        guild = interaction.guild

        counters = load_counters()
        counters[category] = counters.get(category, 0) + 1
        ticket_number = counters[category]
        save_counters(counters)

        formatted_number = f"{ticket_number:03d}"
        ticket_name = f"{category}-{user.name.lower().replace(' ', '-')}-{formatted_number}"

        existing = discord.utils.get(guild.text_channels, name=ticket_name)
        if existing:
            return await interaction.response.send_message(f"Ya tienes un ticket abierto: {existing.mention}", ephemeral=True)

        mod_role = guild.get_role(MOD_ROLE_ID)

        overwrites = {
            guild.default_role: discord.PermissionOverwrite(view_channel=False),
            user: discord.PermissionOverwrite(view_channel=True, send_messages=True, read_message_history=True, attach_files=True, embed_links=True),
            guild.me: discord.PermissionOverwrite(view_channel=True, send_messages=True, read_message_history=True),
        }
        if mod_role:
            overwrites[mod_role] = discord.PermissionOverwrite(view_channel=True, send_messages=True, read_message_history=True, attach_files=True, embed_links=True)

        ticket_category = guild.get_channel(TICKET_CATEGORY_ID)
        if not ticket_category or not isinstance(ticket_category, discord.CategoryChannel):
            return await interaction.response.send_message("Error: La categoría de tickets no existe o el ID es inválido.", ephemeral=True)

        try:
            channel = await guild.create_text_channel(
                name=ticket_name,
                overwrites=overwrites,
                category=ticket_category,
                topic=f"Ticket de {category} #{formatted_number} | Abierto por {user} ({user.id}) | {datetime.now().strftime('%Y-%m-%d %H:%M')}",
                reason=f"Ticket {category} #{formatted_number} por {user}"
            )
        except discord.HTTPException as e:
            print(f"Error creando canal: {e}")
            return await interaction.response.send_message(f"Error creando canal: {e}", ephemeral=True)

        embed = discord.Embed(
            description=welcome_msg,
            color=discord.Color.blue(),
            timestamp=datetime.now()
        )
        embed.set_author(name=f"Ticket de {category.capitalize()} #{formatted_number}", icon_url=user.avatar.url if user.avatar else None)
        embed.set_footer(text=FOOTER_TEXT, icon_url=FOOTER_ICON)

        content = f"{mod_role.mention if mod_role else ''} {user.mention} abrió ticket **{category} #{formatted_number}**."
        await channel.send(content, embed=embed, view=CloseTicketView())

        await interaction.response.send_message(f"¡Ticket creado! → {channel.mention}", ephemeral=True)

class CloseTicketView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Cerrar Ticket", style=discord.ButtonStyle.red, emoji="🔒", custom_id="close_ticket")
    async def close_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("Cerrando ticket en 10 segundos...", ephemeral=True)

        await asyncio.sleep(10)

        log_content = f"Registro de Ticket Cerrado: {interaction.channel.name}\n"
        log_content += f"Cerrado por: {interaction.user.name} ({interaction.user.id})\n"
        log_content += f"Fecha de cierre: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
        log_content += f"Categoría: {interaction.channel.name.split('-')[0]}\n"
        log_content += "─" * 60 + "\n\n"

        async for msg in interaction.channel.history(limit=None, oldest_first=True):
            ts = msg.created_at.strftime('%Y-%m-%d %H:%M:%S')
            author = msg.author.name if msg.author else "Sistema"
            content = msg.content or "[Sin contenido]"
            log_content += f"[{ts}] {author}:\n    {content}\n"

            if msg.attachments:
                log_content += "    Adjuntos:\n"
                for att in msg.attachments:
                    log_content += f"      - {att.filename}: {att.url}\n"

            if msg.embeds:
                log_content += "    Embed presente\n"

            log_content += "\n"

        file_buffer = io.StringIO(log_content)
        file_buffer.seek(0)

        log_channel = interaction.guild.get_channel(LOG_CHANNEL_ID)
        if log_channel:
            await log_channel.send(
                content=f"**Ticket cerrado:** {interaction.channel.name}\nCerrado por: {interaction.user.name}",
                file=discord.File(fp=file_buffer, filename=f"registro-{interaction.channel.name}.txt")
            )
        else:
            print("Canal de logs no encontrado.")

        await interaction.channel.delete(reason="Ticket cerrado con registro adjunto")

@bot.event
async def on_ready():
    print(f"Bot listo: {bot.user} (ID: {bot.user.id})")
    bot.add_view(TicketView())
    bot.add_view(CloseTicketView())
    print("Views persistentes añadidas.")

@bot.tree.command(name="tickets", description="Envía el panel de tickets (solo admins)")
@app_commands.checks.has_permissions(manage_guild=True)
async def send_tickets_panel(interaction: discord.Interaction):
    embed = discord.Embed(
        title="KOP Producciones | Tickets",
        description=" ",
        color=discord.Color.orange()
    )
    embed.add_field(
        name="Selecciona el tipo de ticket que necesitas:",
        value="- 🎫 | Soporte: Ayuda general.\n- 📝 | Postulaciones: Unirte al equipo.\n- 👑 | VIP: Beneficios premium.\n- 💰 | Donaciones: Apoyo a la producción.",
        inline=False
    )
    embed.set_footer(text=FOOTER_TEXT, icon_url=FOOTER_ICON)

    await interaction.channel.send(embed=embed, view=TicketView())
    await interaction.response.send_message("Panel enviado correctamente.", ephemeral=True)

@bot.tree.command(
    name="sync",
    description="Fuerza sincronización de comandos (solo tú)",
    guild=discord.Object(id=GUILD_ID)
)
async def sync_commands(interaction: discord.Interaction):
    if interaction.user.id != YOUR_USER_ID:
        await interaction.response.send_message("No tienes permiso.", ephemeral=True)
        return

    guild = discord.Object(id=GUILD_ID)
    bot.tree.clear_commands(guild=guild)
    bot.tree.copy_global_to(guild=guild)
    synced = await bot.tree.sync(guild=guild)
    await interaction.response.send_message(f"¡Sincronizado! {len(synced)} comandos.", ephemeral=True)

# Flask para UptimeRobot (al final del script, antes de bot.run)
app = Flask(__name__)

@app.route('/')
def home():
    return "Bot KOP Tickets activo 24/7 🚀 - Replit ID: KOP-TICKETS.cosmickiddpriv"

def run_flask():
    try:
        app.run(host='0.0.0.0', port=8080, debug=False, use_reloader=False)
    except Exception as e:
        print(f"Flask error: {e}")

# Inicia Flask
Thread(target=run_flask, daemon=True).start()

# Imprime la URL correcta automáticamente
print("URL para UptimeRobot (copia esta): https://KOP-TICKETS.cosmickiddpriv.repl.co")
print("Si no carga, espera 30 segundos después de Run y refresca.")
