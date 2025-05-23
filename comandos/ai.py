import discord
from discord.ext import commands
import requests
import os
import json
from dotenv import load_dotenv

load_dotenv()

LOCAL_URL = os.getenv("LOCAL_URL")
if not LOCAL_URL:
    raise ValueError("❌ ERRO: LOCAL_URL não está definido no .env")

# Carregar prompt e parâmetros do ficheiro externo
try:
    with open("prompt.json", encoding="utf-8") as f:
        cfg = json.load(f)
except Exception as e:
    raise RuntimeError(f"❌ Erro ao carregar prompt.json: {e}")

# Extrai parâmetros individuais
MODEL       = cfg["model"]
LANG        = cfg["lang"]
TONE        = cfg["tone"]
FORMAT      = cfg["format"]
PERSONA     = cfg["persona"]
INSTRUCAO   = cfg["system"]
TEMPERATURE = cfg["temperature"]
MAX_TOKENS  = cfg["max_tokens"]
STREAM      = cfg["stream"]

# Constrói o system prompt completo
SYSTEM = (
    f"Linguagem: {LANG}\n"
    f"Tom: {TONE}\n"
    f"Formato: {FORMAT}\n"
    f"Persona: {PERSONA}\n"
    f"{INSTRUCAO}"
)

class AI(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author == self.bot.user:
            return

        if (
            self.bot.user in message.mentions and
            not message.mention_everyone and
            not message.content.startswith("!")
        ):
            pergunta = (
                message.content
                .replace(f"<@{self.bot.user.id}>", "")
                .replace("@everyone", "")
                .replace("@here", "")
                .strip()
            )

            ctx = await self.bot.get_context(message)
            await self.enviar_para_ollama(ctx, pergunta, message.author.mention)

    async def enviar_para_ollama(self, ctx, pergunta, autor_mention):
        if not pergunta:
            return await ctx.send(f"{autor_mention} ❌ ERRO: Nenhuma pergunta detectada.")

        pensando = await ctx.send("🧠 A pensar...")

        payload = {
            "model":       MODEL,
            "system":      SYSTEM,
            "prompt":      pergunta,
            "temperature": TEMPERATURE,
            "max_tokens":  MAX_TOKENS,
            "stream":      STREAM
        }

        # DEBUG
        # print(">>> Payload enviado:", json.dumps(payload, ensure_ascii=False, indent=2))

        try:
            resp = requests.post(LOCAL_URL, json=payload, timeout=30)
            resp.raise_for_status()
            data = resp.json()
            resposta = data.get("response", "❌ ERRO: Não consegui gerar uma resposta.")
        except Exception as e:
            resposta = f"Erro ao contactar a AI: `{e}`"

        await pensando.delete()

        if len(resposta) > 2000:
            resposta = "❌ A resposta é demasiado longa para ser enviada aqui. Tente formular uma pergunta mais objetiva ou divida o pedido em partes."


        await ctx.send(f"{resposta}\n||{autor_mention}||")

async def setup(bot):
    await bot.add_cog(AI(bot))
