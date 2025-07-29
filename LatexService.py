import os
import json

from playwright.sync_api import sync_playwright
import requests

from langchain_openai import ChatOpenAI
from langchain.prompts import PromptTemplate, ChatPromptTemplate

from langchain.chains import LLMChain

#import telebot
#from telebot.types import Message

#Prompt
str_template = """
               You need to return ONLY a valid LaTeX formula for the math formula the user describes or asks for, with no additional text,
               no wrapping in $$ or any other special characters, and no escaping of backslashes.  

                Here is the user's description of a formula: {query}  
               """
#Making Prompt Template from one string with variable placeholder {query}
give_latex_prompt =  PromptTemplate(template=str_template, 
                                    input_variables=['query'])

#LLM
#Let's see how it works in combination with LLM instance
token_path = 'data/new_openai_token.txt'
with open(token_path, 'rt') as f:
    openai_token = f.read()

if "OPENAI_API_KEY" not in os.environ:
    os.environ["OPENAI_API_KEY"] = openai_token
#token is passed via Enviroment variable defined above
llm = ChatOpenAI(model="gpt-4-turbo")

#Chain
llm_chain = LLMChain(llm=llm,
                     prompt=give_latex_prompt)

#Use Playwright (synchronously) to generate image from LaTeX
#<textarea class="form-control" id="latexInputTextArea" placeholder="Enter LaTeX math equation" rows="8"></textarea>
def generate_latex_image(latex_code):
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        print('Made page')
        page.goto("https://latex2image.joeraut.com/")
        print('Went to site')
        #page.fill('textarea[name="latex_code"]', latex_code)
        page.fill('#latexInputTextArea', latex_code)
        print('Filled text area')
        
        page.click('#convertButton')
        print('Pressed the button Convert')

        page.wait_for_selector('#resultImage')
        print('Image appeared')

        img_url = page.get_attribute('#resultImage', 'src')
        print('Got url:', img_url)
        img_path = "data/latex_image.png"
        if img_url:
            response = requests.get(img_url)
            with open(img_path, "wb") as f:
                f.write(response.content)
            print("Image saved as latex_image.png")
        else:
            print("Error: Could not find generated image.")

        browser.close()
        return img_path

llm_chain = LLMChain(llm=llm,
                     prompt=give_latex_prompt)
#result = llm_chain.invoke({'query' : 'Covariance of two samples of random variables X,Y'})
#latex_formula = result['text']
latex_formula = '\mathrm{Cov}(X,Y) = E[(X - E[X])(Y - E[Y])]'
print("Produced formula:", latex_formula)

#print("Launching Playwright...")
#generate_latex_image(latex_formula)

#After this, you can add Telegram Bot Interface and it's gonna be an alright little TG bot.
'''
with open('data/tg_bot_token.txt', 'rt') as f:
    tg_token = f.read()

bot = telebot.TeleBot(tg_token)

class TelegramInterface:
    def __init__(self, tg_bot, chain):
        self.bot = tg_bot
        self.chain = chain

        # Register message handler
        #for start
        @self.bot.message_handler(commands=['start'])
        def send_welcome(message: Message):
            self.bot.reply_to(message, "Welcome! Send me formula description and I will generate an image for you.")
        #for ANY text message
        @self.bot.message_handler(func=lambda message: True)
        def handle_latex_message(message: Message):
            #Get latex formula from LLMChain
            latex_formula = chain.invoke({'query' : message.text.strip()})
            self.bot.send_message(message.chat.id, "Processing your formula... Please wait ⏳")
            #Generate Image via WebService
            image_path = generate_latex_image(latex_formula)
            
            if image_path:
                with open(image_path, "rb") as img:
                    self.bot.send_photo(message.chat.id, img)
                os.remove(image_path)  # Cleanup after sending
            else:
                self.bot.send_message(message.chat.id, "Error generating image. Please check your LaTeX input.")

    def run(self):
        """Start the bot."""
        print("Bot is running...")
        self.bot.polling(none_stop=True)

tg_interface = TelegramInterface(bot, llm_chain)
tg_interface.run()'
'''