import os
from dotenv import load_dotenv
import discord
from openai import OpenAI

# Load environment variables from .env file
load_dotenv()
DISCORD_BOT_TOKEN = os.getenv("DISCORD_BOT_TOKEN_MENTOR")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

intents = discord.Intents.default()  # Defaults enable only the non-privileged intents
intents.messages = True  # If you need to listen to messages

system_prompt = 'Personality: insigthful, witty, direct.'
client = OpenAI(api_key=OPENAI_API_KEY)

# Initialize a dictionary to keep track of chat contexts
chat_contexts = {}

async def generate_response(channel_id, message):
    # Ensure the channel has an entry in the chat_contexts dictionary
    if channel_id not in chat_contexts:
        chat_contexts[channel_id] = [{"role": "system", "content": system_prompt}]
    
    # Append the new user message to the history
    chat_contexts[channel_id].append({"role": "user", "content": message})
    
    # Generate response from OpenAI
    response = client.chat.completions.create(
        model=os.getenv("MENTOR_MODEL"),
        messages=chat_contexts[channel_id]
    )
    
    # Append the bot response to the history
    bot_message = response.choices[0].message.content
    chat_contexts[channel_id].append({"role": "assistant", "content": bot_message})
    
    return bot_message

class MyBot(discord.Client):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs, intents=intents)
    
    async def on_ready(self):
        print(f'We have logged in as {self.user}')
    
    async def on_message(self, message):
        # Ignore messages from the bot itself
        if message.author == self.user:
            return
        
        channel_id = message.channel.id
        message_text = message.content

        # Check if the message is "forget"
        if message_text.lower() == "forget":
            # Clear the chat context for this channel
            chat_contexts.pop(channel_id, None)
            await message.channel.send("I've forgotten our previous conversation.")
            return

        if isinstance(message.channel, discord.DMChannel):
            # Generate a response to the incoming message in DMs
            response_message = await generate_response(channel_id, message_text)    
            # Send the response back to the channel
            await message.channel.send(response_message)
        else:
            # Check if the message is in a public channel and the bot is mentioned
            if bot.user.mentioned_in(message):
                # Remove the bot mention from the message content
                message_text = message_text.replace(f'<@!{bot.user.id}>', '').strip()
                # Generate a response to the incoming message
                response_message = await generate_response(channel_id, message_text)
                # Send the response back to the channel
                await message.channel.send(response_message)
        
        return

if __name__ == '__main__':
    bot = MyBot()
    bot.run(DISCORD_BOT_TOKEN)