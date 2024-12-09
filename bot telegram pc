import logging
import os
import pyautogui
import subprocess
import yfinance as yf
from pycoingecko import CoinGeckoAPI
from dotenv import load_dotenv
from telegram import ForceReply, Update
from telegram.ext import Application, CommandHandler, ContextTypes
import time
import requests

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
        gold_data = yf.Ticker("GLD")  # ETF que segue o preço do ouro
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
        oil_data = yf.Ticker("CL=F")  # Petróleo Bruto (WTI)
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

async def send_startup_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /start is issued."""
    user = update.effective_user
    welcome_message = (
        rf"Olá, {user.mention_html()}! Bem-vindo ao seu bot pessoal.\n"
        "Aqui estão os comandos disponíveis:\n"
        "/start - Inicia o bot\n"
        "/help - Mostra esta mensagem de ajuda\n"
        "/screenshot - Captura a tela e envia para você\n"
        "/shutdown - Desliga o PC\n"
        "/weather - Mostra o clima de uma cidade"
    )
    await update.message.reply_html(welcome_message, reply_markup=ForceReply(selective=True))

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /help is issued."""
    help_text = (
        "🤖 Available Commands:\n\n"
        "/start - Start the bot and get a welcome message\n"
        "/help - Show this help message\n"
        "/screenshot - Take a screenshot of the computer screen\n"
        "/shutdown - Shut down the computer\n"
        "/weather [city] - Get current weather for a specific city\n"
        "/dolar - Get current USD to Brazilian Real (BRL) exchange rate\n\n"
        "💡 Need more help? Contact the bot administrator."
    )
    await update.message.reply_text(help_text)

async def screenshot_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Capture the screen and send it to the user."""
    screenshot = pyautogui.screenshot()
    screenshot_path = "screenshot.png"
    screenshot.save(screenshot_path)

    with open(screenshot_path, 'rb') as file:
        await update.message.reply_photo(photo=file)

    logger.info("Screenshot taken and sent to Telegram.")

async def shutdown_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Shut down the PC."""
    await update.message.reply_text("Desligando o PC...")
    subprocess.run(["shutdown", "-s", "-t", "0"])

async def send_welcome_message(application: Application) -> None:
    """Send a welcome message to all chat members when the bot starts."""
    chat_id = os.getenv("TELEGRAM_CHAT_ID")
    welcome_message = (
        "Olá! Estou ativo agora. Aqui estão os comandos disponíveis:\n"
        "/start - Inicia o bot\n"
        "/help - Mostra esta mensagem de ajuda\n"
        "/screenshot - Captura a tela e envia para você\n"
        "/shutdown - Desliga o PC\n"
        "/weather [são paulo]"
    )
    try:
        await application.bot.send_message(chat_id=chat_id, text=welcome_message)
    except Exception as e:
        logger.error(f"Error sending welcome message: {e}")

async def on_start(context: ContextTypes.DEFAULT_TYPE) -> None:
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
        financial_data = await get_financial_data()  # Use await aqui
        await context.bot.send_message(chat_id=chat_id, text=financial_data)
        logger.info("Financial data sent to Telegram.")
        
        # Fetch and send weather for São Paulo
        weather_api_key = os.getenv("OPENWEATHERMAP_API_KEY")
        if weather_api_key and weather_api_key != "0368db67fed70ece05eed66bb711f77d":
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
        
    except Exception as e:
        logger.error(f"Error in on_start: {e}")

async def send_financial_data(context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send financial data to the chat."""
    chat_id = os.getenv("TELEGRAM_CHAT_ID")
    financial_data = await get_financial_data()
    await context.bot.send_message(chat_id=chat_id, text=financial_data)

async def weather_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Fetch and send current weather information."""
    # Get API key from environment variables
    weather_api_key = os.getenv("OPENWEATHERMAP_API_KEY")
    
    # Check if API key is set
    if not weather_api_key or weather_api_key == "0368db67fed70ece05eed66bb711f77d":
        await update.message.reply_text(
            "❌ OpenWeatherMap API key is not fully configured. Please verify the key."
        )
        return
    
    # Extract city from message or arguments
    city = None
    
    # Check if there are command arguments
    if context.args:
        city = " ".join(context.args)
    
    # If no arguments, check the message text
    if not city:
        message_text = update.message.text.strip()
        # Remove '/weather' and any separators
        city = message_text.replace('/weather', '').replace('-', '').strip()
    
    # Validate and clean city input
    if not city:
        await update.message.reply_text(
            "🌍 Please provide a city name. Usage: /weather [City Name]"
        )
        return

    # Clean up common typos and formatting issues
    def clean_city_name(name):
        # Common replacements
        name = name.replace('soa', 'sao')  # Fix 'soa paulo' typo
        name = name.replace('são', 'sao')  # Normalize São
        name = name.replace('saõ', 'sao')  # Another common typo
        
        # Capitalize first letters
        return ' '.join(word.capitalize() for word in name.split())

    city = clean_city_name(city)

    try:
        # Make API call to OpenWeatherMap
        url = f"http://api.openweathermap.org/data/2.5/weather?q={city},BR&appid={weather_api_key}&units=metric"
        logger.info(f"Fetching weather for {city}")
        response = requests.get(url, timeout=10)
        response.raise_for_status()  # Raise an exception for bad status codes
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
            f"{weather_emoji} Weather in {city}:\n"
            f"🌡️ Temperature: {temp:.1f}°C\n"
            f"🌡️ Feels like: {feels_like:.1f}°C\n"
            f"💧 Humidity: {humidity}%\n"
            f"📝 Conditions: {description.capitalize()}\n"
            f"💨 Wind Speed: {wind_speed} m/s"
        )

        await update.message.reply_text(weather_message)
        logger.info(f"Successfully retrieved weather for {city}")

    except requests.exceptions.Timeout:
        logger.error("Weather API request timed out")
        await update.message.reply_text("⏰ Request timed out. Please try again later.")
    except requests.exceptions.RequestException as e:
        logger.error(f"Weather API request error: {e}")
        await update.message.reply_text("🚫 Unable to fetch weather information. Please try again later.")
    except KeyError as e:
        logger.error(f"Unexpected response format from OpenWeatherMap: {e}")
        await update.message.reply_text("🤖 Unexpected error processing weather data.")

# Function to get USD to BRL exchange rate
async def dollar_real_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Fetch current USD to BRL exchange rate."""
    try:
        # Use CoinGecko API to get exchange rate
        usd_brl_rate = cg.get_price(ids='usd', vs_currencies='brl')['usd']['brl']
        
        # Safely convert to float and format
        try:
            rate = float(usd_brl_rate)
            message = f"💱 Current Exchange Rate:\n1 USD = R$ {rate:.2f}"
        except (ValueError, TypeError):
            message = f"💱 Current Exchange Rate:\n1 USD = {usd_brl_rate}"
        
        await update.message.reply_text(message)
    except Exception as e:
        logger.error(f"Error fetching USD to BRL rate: {e}")
        await update.message.reply_text("Unable to fetch current exchange rate.")

def main() -> None:
    """Start the bot."""
    # Get the bot token from environment variables
    token = os.getenv("TELEGRAM_BOT_TOKEN")

    # Create the Application and pass it your bot's token.
    application = Application.builder().token(token).build()

    # on different commands - answer in Telegram
    application.add_handler(CommandHandler("start", send_startup_message))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("screenshot", screenshot_command))
    application.add_handler(CommandHandler("shutdown", shutdown_command))
    application.add_handler(CommandHandler("weather", weather_command))
    application.add_handler(CommandHandler("dolar", dollar_real_command))  # Add this line

    # Schedule the welcome message, screenshot, and financial data to be sent at startup using JobQueue
    application.job_queue.run_once(on_start, when=2)

    # Start polling
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
