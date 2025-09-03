import discord
from discord.ext import commands
import sqlite3

intents = discord.Intents.default()
intents.members = True  # serve per lavorare con membri
bot = commands.Bot(command_prefix='/', intents=intents)

conn = sqlite3.connect('patenti.db')
c = conn.cursor()

# Creazione tabella se non esiste
c.execute('''CREATE TABLE IF NOT EXISTS patenti (
    discord_name TEXT PRIMARY KEY,
    nome TEXT,
    cognome TEXT,
    data_nascita TEXT,
    punti INTEGER,
    valida INTEGER
)''')
conn.commit()

# Funzioni controllo ruoli
def has_role(user, role_name):
    return any(role.name == role_name for role in user.roles)

def is_cittadino(user):
    return has_role(user, "🏙️ | Cittadino Di Italian Paradais")

def is_polizia(user):
    return has_role(user, "🚓 | Dipartimento Di Polizia")

def is_staff(user):
    return has_role(user, ".")

# --- COMANDO 1: CREA PATENTE ---
@bot.command()
async def patente(ctx, nome: str, cognome: str, data_nascita: str, utente: discord.Member):
    if not is_cittadino(ctx.author):
        await ctx.send("❌ Solo i cittadini possono creare una patente.")
        return

    discord_name = str(utente)
    c.execute("SELECT * FROM patenti WHERE discord_name = ?", (discord_name,))
    if c.fetchone():
        await ctx.send("❌ Questo utente ha già una patente registrata.")
        return

    c.execute("INSERT INTO patenti VALUES (?, ?, ?, ?, ?, ?)",
              (discord_name, nome, cognome, data_nascita, 20, 1))
    conn.commit()
    await ctx.send(f"✅ Patente creata per **{nome} {cognome}** a {utente.mention} con **20 punti**.")

# --- COMANDO 2: GUARDA PATENTE ---
@bot.command()
async def guarda(ctx, utente: discord.Member):
    if not is_polizia(ctx.author):
        await ctx.send("❌ Solo la polizia può controllare le patenti.")
        return

    discord_name = str(utente)
    c.execute("SELECT nome, cognome, data_nascita, punti, valida FROM patenti WHERE discord_name = ?", (discord_name,))
    row = c.fetchone()
    if not row:
        await ctx.send(f"❌ Nessuna patente trovata per {utente.mention}.")
        return

    nome, cognome, data_nascita, punti, valida = row
    stato = "Valida" if valida else "Non valida"
    embed = discord.Embed(title=f"📄 Patente di {nome} {cognome}", color=0x00ff00)
    embed.add_field(name="Nome", value=nome, inline=True)
    embed.add_field(name="Cognome", value=cognome, inline=True)
    embed.add_field(name="Data di nascita", value=data_nascita, inline=False)
    embed.add_field(name="Punti", value=str(punti), inline=True)
    embed.add_field(name="Stato", value=stato, inline=True)
    await ctx.send(embed=embed)

# --- COMANDO 3: TOGLI PUNTI ---
@bot.command()
async def togli_punti(ctx, utente: discord.Member, punti_da_togliere: int):
    if not is_polizia(ctx.author):
        await ctx.send("❌ Solo la polizia può togliere punti.")
        return

    discord_name = str(utente)
    c.execute("SELECT punti FROM patenti WHERE discord_name = ?", (discord_name,))
    row = c.fetchone()
    if not row:
        await ctx.send(f"❌ Nessuna patente trovata per {utente.mention}.")
        return

    punti = row[0]
    nuovi_punti = punti - punti_da_togliere
    if nuovi_punti < 0:
        nuovi_punti = 0

    valida = 1 if nuovi_punti > 0 else 0

    c.execute("UPDATE patenti SET punti = ?, valida = ? WHERE discord_name = ?", (nuovi_punti, valida, discord_name))
    conn.commit()

    stato = "valida" if valida else "non valida"
    await ctx.send(f"😄 Punti rimossi da {utente.mention}. Nuovi punti: {nuovi_punti}. Patente ora {stato}.")

# --- COMANDO 4: AGGIUNGI PUNTI ---
@bot.command()
async def aggiungi_punti(ctx, utente: discord.Member, punti_da_aggiungere: int):
    if not is_staff(ctx.author):
        await ctx.send("❌ Non hai i permessi per aggiungere punti.")
        return

    discord_name = str(utente)
    c.execute("SELECT punti FROM patenti WHERE discord_name = ?", (discord_name,))
    row = c.fetchone()
    if not row:
        await ctx.send(f"❌ Nessuna patente trovata per {utente.mention}.")
        return

    punti = row[0]
    nuovi_punti = punti + punti_da_aggiungere
    if nuovi_punti > 20:
        nuovi_punti = 20

    c.execute("UPDATE patenti SET punti = ?, valida = 1 WHERE discord_name = ?", (nuovi_punti, discord_name))
    conn.commit()

    await ctx.send(f"✅ Punti aggiunti a {utente.mention}. Punti ora: {nuovi_punti}.")

# --- COMANDO 5: RESET PUNTI ---
@bot.command()
async def reset_punti(ctx, utente: discord.Member):
    if not is_staff(ctx.author):
        await ctx.send("❌ Non hai i permessi per resettare i punti.")
        return

    discord_name = str(utente)
    c.execute("SELECT * FROM patenti WHERE discord_name = ?", (discord_name,))
    if not c.fetchone():
        await ctx.send(f"❌ Nessuna patente trovata per {utente.mention}.")
        return

    c.execute("UPDATE patenti SET punti = 20, valida = 1 WHERE discord_name = ?", (discord_name,))
    conn.commit()

    await ctx.send(f"✅ Punti resettati a 20 e patente resa valida per {utente.mention}.")

# --- COMANDO 6: ELIMINA PATENTE ---
@bot.command()
async def elimina_patente(ctx, utente: discord.Member):
    if not is_staff(ctx.author):
        await ctx.send("❌ Non hai i permessi per eliminare patenti.")
        return

    discord_name = str(utente)
    c.execute("SELECT * FROM patenti WHERE discord_name = ?", (discord_name,))
    if not c.fetchone():
        await ctx.send(f"❌ Nessuna patente trovata per {utente.mention}.")
        return

    c.execute("DELETE FROM patenti WHERE discord_name = ?", (discord_name,))
    conn.commit()

    await ctx.send(f"✅ Patente eliminata per {utente.mention}.")

# --- COMANDO 7: LISTA PATENTI ---
@bot.command()
async def lista_patenti(ctx):
    if not is_staff(ctx.author):
        await ctx.send("❌ Non hai i permessi per vedere la lista delle patenti.")
        return

    c.execute("SELECT nome, cognome, punti, valida FROM patenti")
    rows = c.fetchall()
    if not rows:
        await ctx.send("❌ Nessuna patente registrata.")
        return

    msg = "**Lista Patenti:**\n"
    for nome, cognome, punti, valida in rows:
        stato = "Valida" if valida else "Non valida"
        msg += f"- {nome} {cognome} | Punti: {punti} | Stato: {stato}\n"

    await ctx.send(msg)

# Avvio bot
bot.run()
