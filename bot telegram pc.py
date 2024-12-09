import logging
import os
import pyautogui
import subprocess
import yfinance as yf
from pycoingecko import CoinGeckoAPI
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import (
    ApplicationBuilder, CommandHandler, ContextTypes, ChatMemberHandler
)
import time
import requests
from datetime import datetime

# Load environment variables from .env file
load_dotenv()

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logging.getLogger("httpx").setLevel(logging.WARNING)

logger = logging.getLogger(__name__)

# Initialize CoinGecko API client
cg = CoinGeckoAPI()

# Function to get gold price using Yahoo Finance
async def get_gold_price():
    try:
        gold_data = yf.Ticker("GC=F")  # COMEX Gold futures
        gold_history = gold_data.history(period="1d")
        if gold_history.empty:
            logger.error("No data found for gold.")
            return "No data found for gold."
        gold_price = gold_history['Close'].iloc[0]
        return gold_price
    except Exception as e:
        logger.error(f"Error fetching gold price: {e}")
        return "Error fetching gold price."

# Function to get Brent Crude Oil price using Yahoo Finance
async def get_oil_price():
    try:
        oil_data = yf.Ticker("BZ=F")  # Brent Crude Oil
        oil_history = oil_data.history(period="1d")
        if oil_history.empty:
            logger.error("No data found for Brent Crude Oil.")
            return "No data found for Brent Crude Oil."
        oil_price = oil_history['Close'].iloc[0]
        return oil_price
    except Exception as e:
        logger.error(f"Error fetching Brent Crude Oil price: {e}")
        return "Error fetching Brent Crude Oil price."

# Function to get Bitcoin price using CoinGecko
async def get_bitcoin_price():
    try:
        bitcoin_data = cg.get_price(ids='bitcoin', vs_currencies='usd')
        bitcoin_price = bitcoin_data['bitcoin']['usd']
        return bitcoin_price
    except Exception as e:
        logger.error(f"Error fetching Bitcoin price: {e}")
        return "Error fetching Bitcoin price."

# Function to fetch and format all financial data
async def get_financial_data() -> str:
    """Fetch financial data from various sources."""
    try:
        # Fetch various financial data
        bitcoin_price = await get_bitcoin_price()
        gold_price = await get_gold_price()
        oil_price = await get_oil_price()
        
        # Fetch USD to BRL exchange rate
        try:
            usd_brl_rate = cg.get_price(ids='usd', vs_currencies='brl')['usd']['brl']
        except Exception as e:
            logger.error(f"Error fetching USD to BRL rate: {e}")
            usd_brl_rate = "N/A"
        
        # Helper function to format numeric values safely
        def format_numeric(value, default="N/A"):
            try:
                # Convert to float if it's a string that looks like a number
                if isinstance(value, str):
                    value = float(value.replace('$', '').replace(',', ''))
                return f"{value:.2f}" if isinstance(value, (int, float)) else default
            except (ValueError, TypeError):
                return default
        
        # Format financial data message
        financial_message = (
            f"💰 Financial Data Update:\n"
            f"💹 Bitcoin: ${format_numeric(bitcoin_price)}\n"
            f"🥇 Gold: ${format_numeric(gold_price)}\n"
            f"🛢️ Oil: ${format_numeric(oil_price)}\n"
            f"💱 USD to BRL: R$ {format_numeric(usd_brl_rate)}"
        )
        
        return financial_message
    except Exception as e:
        logger.error(f"Error in get_financial_data: {e}")
        return "Unable to fetch financial data."

# Send welcome message to the user who sent /start
async def send_welcome_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send welcome message when the /start command is issued."""
    try:
        # Mensagem de boas-vindas
        welcome_message = (
            "Olá! Bem-vindo ao chat.\n\n"
            "Aqui estão alguns comandos que você pode usar:\n"
            "📸 /screenshot - Captura a tela e envia para você\n"
            "🖥️ /shutdown - Desliga o PC\n"
            "🌦️ /weather [cidade] - Mostra o clima\n"
            "💱 /dolar - Mostra a cotação do dólar"
            f"Iniciado em: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        )

        # Enviar mensagem de boas-vindas
        await context.bot.send_message(chat_id=update.effective_chat.id, text=welcome_message)
        logger.info("Boas-vindas enviadas ao chat.")
    except Exception as e:
        logger.error(f"Erro ao enviar mensagem de boas-vindas: {e}")

# Handle new chat members
async def new_member_welcome(chat_member_update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send welcome message when a new user joins the chat."""
    try:
        new_member = chat_member_update.chat_member.new_chat_member
        welcome_message = f"Olá, {new_member.user.first_name}! Seja bem-vindo ao nosso chat."
        await context.bot.send_message(chat_id=chat_member_update.chat_member.chat.id, text=welcome_message)
    except Exception as e:
        logger.error(f"Erro ao enviar mensagem de boas-vindas a novo membro: {e}")

# Perform startup tasks when the bot starts
async def startup_tasks(context: ContextTypes.DEFAULT_TYPE) -> None:
    """Perform startup tasks when the bot starts."""
    try:
        # Take and send startup screenshot
        screenshot_path = os.path.join(os.getenv("TEMP", "/tmp"), "startup_screenshot.png")
        screenshot = pyautogui.screenshot()
        screenshot.save(screenshot_path)
        
        chat_id = os.getenv("TELEGRAM_CHAT_ID")
        
        if screenshot_path:
            with open(screenshot_path, 'rb') as screenshot_file:
                await context.bot.send_photo(chat_id=chat_id, photo=screenshot_file, caption="Startup Screenshot")
            logger.info("Startup screenshot taken and sent to Telegram.")
        
        # Send financial data
        financial_data = await get_financial_data()
        await context.bot.send_message(chat_id=chat_id, text=financial_data)
        logger.info("Financial data sent to Telegram.")
        
        # Send welcome message for startup tasks
        welcome_message = (
            "Olá! Bem-vindo ao chat.\n\n"
            "Aqui estão alguns comandos que você pode usar:\n"
            "📸 /screenshot - Captura a tela e envia para você\n"
            "🖥️ /shutdown - Desliga o PC\n"
            
            f"Iniciado em: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        )
        await context.bot.send_message(chat_id=chat_id, text=welcome_message)
        logger.info("Welcome message sent for startup tasks.")
        
        # Fetch and send weather for São Paulo
        weather_api_key = os.getenv("OPENWEATHERMAP_API_KEY")
        if weather_api_key:
            try:
                url = f"http://api.openweathermap.org/data/2.5/weather?q=Sao%20Paulo,BR&appid={weather_api_key}&units=metric"
                response = requests.get(url, timeout=10)
                response.raise_for_status()
                data = response.json()

                # Extract relevant weather information
                temp = data['main']['temp']
                feels_like = data['main']['feels_like']
                humidity = data['main']['humidity']
                description = data['weather'][0]['description']
                wind_speed = data['wind']['speed']

                # Emoji selection based on weather description
                def get_weather_emoji(description):
                    description = description.lower()
                    if 'clear' in description:
                        return '☀️'
                    elif 'cloud' in description:
                        return '☁️'
                    elif 'rain' in description:
                        return '🌧️'
                    elif 'storm' in description:
                        return '⛈️'
                    elif 'snow' in description:
                        return '❄️'
                    else:
                        return '🌈'

                weather_emoji = get_weather_emoji(description)

                # Format weather message
                weather_message = (
                    f"{weather_emoji} Weather in Sao Paulo:\n"
                    f"🌡️ Temperature: {temp:.1f}°C\n"
                    f"🌡️ Feels like: {feels_like:.1f}°C\n"
                    f"💧 Humidity: {humidity}%\n"
                    f"📝 Conditions: {description.capitalize()}\n"
                    f"💨 Wind Speed: {wind_speed} m/s"
                )

                await context.bot.send_message(chat_id=chat_id, text=weather_message)
                logger.info("Weather for São Paulo sent successfully.")
            
            except Exception as weather_error:
                logger.error(f"Error fetching weather for São Paulo: {weather_error}")
                await context.bot.send_message(chat_id=chat_id, text="❌ Could not fetch weather information for São Paulo.")
        else:
            # Log that weather API key is not set
            logger.warning("Weather API key is not set or is a placeholder.")
            await context.bot.send_message(chat_id=chat_id, text="❌ Weather API key is not configured.")
        
    except Exception as e:
        logger.error(f"Error in startup_tasks: {e}")

async def screenshot_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Take and send a screenshot via Telegram."""
    try:
        # Take screenshot
        screenshot_path = os.path.join(os.getenv("TEMP", "/tmp"), "telegram_screenshot.png")
        screenshot = pyautogui.screenshot()
        screenshot.save(screenshot_path)
        
        # Send screenshot
        with open(screenshot_path, 'rb') as screenshot_file:
            await update.message.reply_photo(photo=screenshot_file, caption="Screenshot capturado!")
        
        logger.info("Screenshot command executed successfully.")
    except Exception as e:
        await update.message.reply_text(f"Erro ao capturar screenshot: {e}")
        logger.error(f"Screenshot command error: {e}")

async def shutdown_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Shutdown the computer."""
    try:
        await update.message.reply_text("Desligando o computador em 10 segundos...")
        subprocess.run(["shutdown", "/s", "/t", "10"], shell=True)
        logger.info("Shutdown command initiated.")
    except Exception as e:
        await update.message.reply_text(f"Erro ao desligar: {e}")
        logger.error(f"Shutdown command error: {e}")

async def dolar_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Fetch and send current dollar exchange rate."""
    try:
        # Use yfinance to get USD/BRL exchange rate
        usd_brl = yf.Ticker("USDBRL=X")
        
        # Add more robust error checking
        if not hasattr(usd_brl, 'info'):
            raise ValueError("Unable to retrieve ticker information")
        
        # Try multiple ways to get the price
        current_price = (
            usd_brl.info.get('regularMarketPrice') or 
            usd_brl.info.get('currentPrice') or 
            usd_brl.info.get('price')
        )
        
        if current_price is None:
            raise ValueError("No price information available")
        
        message = f"💱 Cotação atual do Dólar:\n1 USD = R$ {float(current_price):.2f}"
        await update.message.reply_text(message)
        logger.info("Dollar exchange rate fetched successfully.")
    except Exception as e:
        await update.message.reply_text("Não foi possível obter a cotação do dólar.")
        logger.error(f"Dolar command error: {e}")
        # Optional: Add a fallback method or alternative data source here

async def weather_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Fetch and send weather for a specified city."""
    try:
        # Check if city is provided
        if not context.args:
            await update.message.reply_text("Por favor, especifique uma cidade. Exemplo: /weather São Paulo")
            return
        
        city = " ".join(context.args)
        weather_api_key = os.getenv("OPENWEATHERMAP_API_KEY")
        
        if not weather_api_key:
            await update.message.reply_text("Chave de API de clima não configurada.")
            return
        
        url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={weather_api_key}&units=metric"
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()

        # Extract relevant weather information
        temp = data['main']['temp']
        feels_like = data['main']['feels_like']
        humidity = data['main']['humidity']
        description = data['weather'][0]['description']
        wind_speed = data['wind']['speed']

        # Emoji selection based on weather description
        def get_weather_emoji(description):
            description = description.lower()
            if 'clear' in description:
                return '☀️'
            elif 'cloud' in description:
                return '☁️'
            elif 'rain' in description:
                return '🌧️'
            elif 'storm' in description:
                return '⛈️'
            elif 'snow' in description:
                return '❄️'
            else:
                return '🌈'

        weather_emoji = get_weather_emoji(description)

        # Format weather message
        weather_message = (
            f"{weather_emoji} Clima em {city}:\n"
            f"🌡️ Temperatura: {temp:.1f}°C\n"
            f"🌡️ Sensação térmica: {feels_like:.1f}°C\n"
            f"💧 Umidade: {humidity}%\n"
            f"📝 Condições: {description.capitalize()}\n"
            f"💨 Velocidade do vento: {wind_speed} m/s"
        )

        await update.message.reply_text(weather_message)
        logger.info(f"Weather for {city} fetched successfully.")
    
    except requests.exceptions.RequestException as e:
        await update.message.reply_text(f"Erro ao buscar informações de clima para {city}.")
        logger.error(f"Weather command error: {e}")
    except Exception as e:
        await update.message.reply_text("Ocorreu um erro inesperado.")
        logger.error(f"Unexpected weather command error: {e}")

def main():
    application = ApplicationBuilder().token(os.getenv("TELEGRAM_BOT_TOKEN")).build()

    # Handlers
    application.add_handler(CommandHandler("start", send_welcome_message))
    application.add_handler(CommandHandler("screenshot", screenshot_command))
    application.add_handler(CommandHandler("shutdown", shutdown_command))
    application.add_handler(CommandHandler("dolar", dolar_command))
    application.add_handler(CommandHandler("weather", weather_command))
    application.add_handler(ChatMemberHandler(new_member_welcome, ChatMemberHandler.CHAT_MEMBER))
    
    # Schedule startup tasks using JobQueue
    application.job_queue.run_once(startup_tasks, when=0)

    # Run the bot
    application.run_polling()

if __name__ == "__main__":
    main()
