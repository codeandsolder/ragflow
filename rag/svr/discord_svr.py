#
#  Copyright 2024 The InfiniFlow Authors. All Rights Reserved.
#
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.
#
"""
Discord bot server for RAGFlow integration.

This module provides a Discord bot that connects to RAGFlow's completion API
to provide AI-powered responses in Discord channels.
"""
import logging
import os
from typing import Any

import aiohttp
import discord

# Configuration constants - should be set via environment variables in production
# These have no defaults and must be configured before running
RAGFLOW_API_URL: str | None = os.environ.get("RAGFLOW_API_URL")
DISCORD_BOT_KEY: str | None = os.environ.get("DISCORD_BOT_KEY")

# Default response template
DEFAULT_GREETING: str = "Hi~ How can I help you? "

# Response type constants
RESPONSE_TYPE_TEXT: int = 1
RESPONSE_TYPE_IMAGE: int = 3

# Temp image filename
TEMP_IMAGE_FILENAME: str = "tmp_image.png"


def create_discord_client() -> discord.Client:
    """Create and configure a Discord client with required intents."""
    intents = discord.Intents.default()
    intents.message_content = True
    return discord.Client(intents=intents)


async def fetch_ragflow_response(user_question: str, conversation_id: str, auth_token: str) -> list[dict[str, Any]]:
    """
    Fetch response from RAGFlow API.

    Args:
        user_question: The question to ask RAGFlow
        conversation_id: The conversation ID to use
        auth_token: The authorization token for RAGFlow API

    Returns:
        List of response data dictionaries from RAGFlow

    Raises:
        aiohttp.ClientError: If the HTTP request fails
        ValueError: If the API response is invalid
    """
    if not RAGFLOW_API_URL:
        raise ValueError("RAGFLOW_API_URL environment variable is not set")

    payload = {
        "conversation_id": conversation_id,
        "Authorization": auth_token,
        "word": user_question,
    }

    async with aiohttp.ClientSession() as session:
        async with session.post(RAGFLOW_API_URL, json=payload) as response:
            response.raise_for_status()
            data = await response.json()
            return data.get("data", [])


async def send_response(channel: discord.TextChannel, user: discord.User, text: str, image_file: discord.File | None = None) -> None:
    """
    Send a response to a Discord channel.

    Args:
        channel: The Discord channel to send to
        user: The user to mention in the response
        text: The text response to send
        image_file: Optional image file to attach
    """
    await channel.send(f"{user.mention}{text}")
    if image_file:
        await channel.send(file=image_file)


client = create_discord_client()


@client.event
async def on_ready() -> None:
    """Event handler for when the bot is ready."""
    logging.info("Discord bot logged in as %s", client.user)


@client.event
async def on_message(message: discord.Message) -> None:
    """
    Event handler for incoming messages.

    Processes mentions and forwards questions to RAGFlow API.
    """
    if message.author == client.user:
        return

    if not client.user.mentioned_in(message):
        return

    # Extract user question from message
    content_parts = message.content.split("> ")
    if len(content_parts) == 1:
        await message.channel.send(DEFAULT_GREETING)
        return

    user_question = content_parts[1]

    # Get credentials from environment or message context
    conversation_id = os.environ.get("RAGFLOW_CONVERSATION_ID", "")
    auth_token = os.environ.get("RAGFLOW_AUTH_TOKEN", "")

    if not conversation_id or not auth_token:
        logging.error("Missing RAGFlow credentials - check environment variables")
        await message.channel.send("Bot configuration error: missing credentials")
        return

    try:
        response_data = await fetch_ragflow_response(user_question, conversation_id, auth_token)
    except Exception as e:
        logging.exception("Failed to fetch response from RAGFlow: %s", e)
        await message.channel.send("Sorry, I encountered an error processing your request.")
        return

    # Process response data
    text_response: str = ""
    image_file: discord.File | None = None

    for item in response_data:
        item_type = item.get("type")
        if item_type == RESPONSE_TYPE_TEXT:
            text_response = item.get("content", "")
        elif item_type == RESPONSE_TYPE_IMAGE:
            # Handle image response
            image_url = item.get("url")
            if image_url:
                try:
                    import base64
                    import aiohttp

                    async with aiohttp.ClientSession() as session:
                        async with session.get(image_url) as resp:
                            if resp.status == 200:
                                image_data = await resp.read()
                                with open(TEMP_IMAGE_FILENAME, "wb") as f:
                                    f.write(image_data)
                                image_file = discord.File(TEMP_IMAGE_FILENAME)
                except Exception as img_err:
                    logging.warning("Failed to fetch image: %s", img_err)

    # Send the response
    try:
        await send_response(message.channel, message.author, text_response, image_file)
    except Exception as e:
        logging.exception("Failed to send Discord response: %s", e)


def run_bot() -> None:
    """Run the Discord bot with proper event loop handling."""
    if not DISCORD_BOT_KEY:
        error_msg = "DISCORD_BOT_KEY environment variable is not set"
        logging.error(error_msg)
        raise ValueError(error_msg)

    import asyncio

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    try:
        loop.run_until_complete(client.start(DISCORD_BOT_KEY))
    except KeyboardInterrupt:
        loop.run_until_complete(client.close())
    finally:
        loop.close()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    run_bot()
