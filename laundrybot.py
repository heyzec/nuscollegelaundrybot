# -*- coding: utf-8 -*-
"""
Created on Wed Oct 24 22:05:36 2018
@author: PengFei
"""
# LaundryMachineBot implementation using python telegram bot library 

#import time
#import datetime
import logging
import os
from telegram import InlineKeyboardMarkup, InlineKeyboardButton, ParseMode
from telegram.ext import Updater, CommandHandler, ConversationHandler, CallbackQueryHandler
from emoji import emojize

#Set up telegram token 
TELEGRAM_TOKEN = os.environ['RC4LAUNDRYBOT_TOKEN'] 

# Set up logging
logging.basicConfig(
    format='%(asctime)s.%(msecs)03d - %(name)s - %(levelname)s - %(message)s',
    datefmt="%Y-%m-%d %H:%M:%S",
    level = logging.INFO)

logger = logging.getLogger(__name__)


# Building menu for every occasion 
def build_menu(buttons, n_cols, header_buttons = None, footer_buttons = None):
    menu = [buttons[i:i + n_cols] for i in range(0, len(buttons), n_cols)]
    if header_buttons:
        menu.insert(0, header_buttons)
    if footer_buttons:
        menu.append(footer_buttons)
    return menu

# building emojis for every occasion
#ethumb = emojize(":thumbsup: ", use_aliases=True)
#eblacksquare = emojize(":black_small_square: ", use_aliases=True)
#earrowfwd = emojize(":arrow_forward: ", use_aliases=True)
#ebangbang = emojize(":bangbang: ", use_aliases=True)
#eheart = emojize(":heart: ", use_aliases=True)
#enumber1 = emojize(":one: ", use_aliases=True)
#enumber2 = emojize(":two: ", use_aliases=True)
#enumber3 = emojize(":three: ", use_aliases=True)
#ebluediamond = emojize(":small_blue_diamond: ", use_aliases=True)
etick = emojize(":white_check_mark: ", use_aliases=True)
ecross = emojize(":x: ", use_aliases=True)

"""
check status
- select laundry machine level (pinned laundry room) --> get status of 4 machines 
- select current level --> matches closest laundry room + get status of 2 levels of machines

settings 
- on off notification for pinned laundry room 
- change pinned laundry room 

help
- simple guide 

future functions
- queuing and QR code? 

"""
# set up INFO_STORE for userdata  
INFO_STORE = {}

# set up DATA_STORE for laundry machine status 
DATA_STORE = {}

# define states 
(AFTER_START, MENU, AFTER_METHOD, SELECT_LEVEL, NEAREST) = range(5)

def start(bot, update):
    button_list = [InlineKeyboardButton(text='Check Machine Status', callback_data = 'checkstart'),
                   InlineKeyboardButton(text='Settings', callback_data = 'settings'),
                   InlineKeyboardButton(text='Help', callback_data = 'help')]
    menu = build_menu(button_list, n_cols = 1)
    mainmenutext = "<b>Hello!</b>\n\n"
    mainmenutext += "I am RC4's Laundry Machine Bot. Check status, adjust notifications, and more!"
    
    try:
        user = update.message.from_user
        logger.info(update.message.text.strip())
        INFO_STORE[user.id] = {}
        INFO_STORE[user.id]["level"] = {}
        INFO_STORE[user.id]["settings"] = {}
        INFO_STORE[user.id]["settings"]['notification'] = {}
        logger.info("User {} just started conversation.".format(user.username if user.username else user.first_name))
        
        bot.sendMessage(text = mainmenutext, 
                        chat_id = update.message.chat.id,
                        reply_markup = InlineKeyboardMarkup(menu),
                        parse_mode=ParseMode.HTML)
        
    except AttributeError:
        query = update.callback_query
        user = query.from_user
        logger.info("User {} clicked back to main menu".format(user.username if user.username else user.first_name))

        bot.editMessageText(text = mainmenutext, 
                        chat_id =  query.message.chat.id,
                        message_id=query.message.message_id,
                        reply_markup = InlineKeyboardMarkup(menu),
                        parse_mode=ParseMode.HTML)
    
    return AFTER_START

def select_method(bot, update):
    query = update.callback_query
    user = query.from_user
    logger.info("User {} is selecting method.".format(user.username if user.username else user.first_name))

    button_list = [InlineKeyboardButton(text="By my house's laundry room!", callback_data = 'pinnedlevelmethod'),
                   InlineKeyboardButton(text="Show me all the nearest laundry machines!", callback_data = 'nearestlevelmethod'),
                   InlineKeyboardButton(text='Back', callback_data = 'back')]
    menu = build_menu(button_list, n_cols = 1)
    
    reply_text = "<b>Which method do you want me to get laundry machine statuses?</b>"
        
    bot.editMessageText(text = reply_text,
                        reply_markup = InlineKeyboardMarkup(menu),
                        chat_id=query.message.chat_id,
                        message_id=query.message.message_id,
                        parse_mode=ParseMode.HTML)    
    return AFTER_METHOD

def select_level(bot, update):
    query = update.callback_query
    user = query.from_user
    logger.info("User {} has selected pinnedlevelmethod".format(user.username if user.username else user.first_name))
    
    button_list = [InlineKeyboardButton(text='Level 5', callback_data = 'L05'),
                   InlineKeyboardButton(text='Level 8', callback_data = 'L08'),
                   InlineKeyboardButton(text='Level 11', callback_data = 'L11'),
                   InlineKeyboardButton(text='Level 14', callback_data = 'L14'),
                   InlineKeyboardButton(text='Level 17', callback_data = 'L17'),
                   InlineKeyboardButton(text='Back', callback_data = 'Back')]
    
    menu = build_menu(button_list, n_cols = 2)
    reply_text = "<b>Please select your House's laundry room level:</b>"
        
    bot.editMessageText(text = reply_text,
                        reply_markup = InlineKeyboardMarkup(menu),
                        chat_id=query.message.chat_id,
                        message_id=query.message.message_id,
                        parse_mode=ParseMode.HTML)
    return SELECT_LEVEL

def pinned_level(bot, update):
    query = update.callback_query
    user = query.from_user
    logger.info("Returning 4 pinned laundry machine statuses to: User {}".format(user.username if user.username else user.first_name))
    
    pinned_level = int(query.data[1:])
    statuses = [1, 1, 0, 1]
    machines = ['Washer 1', 'Washer 2', 'Dryer 1', 'Dryer 2']

    reply_text = "On Level {}, here are the statuses of the 4 laundry machines:".format(str(pinned_level))
    for i in range(len(statuses)):
        if statuses[i] == 1:
            reply_text += "\n\n" + etick + machines[i]
        elif statuses[i] == 0:
            reply_text += "\n\n" + ecross + machines[i]
    reply_text += "\n\nPress /start if you wish to restart the whole process anytime!"
        
    bot.editMessageText(text = reply_text,
                        chat_id=query.message.chat_id,
                        message_id=query.message.message_id,
                        parse_mode=ParseMode.HTML)
    
    return ConversationHandler.END


def select_nearest(bot, update):
    query = update.callback_query
    user = query.from_user
    logger.info("User {} has selected nearestlevelmethod".format(user.username if user.username else user.first_name))

    button_list = [InlineKeyboardButton(text='Level 1', callback_data = 'L01'),
                   InlineKeyboardButton(text='Level 2', callback_data = 'L02'),
                   InlineKeyboardButton(text='Level 3', callback_data = 'L03'),
                   InlineKeyboardButton(text='Level 4', callback_data = 'L04'),
                   InlineKeyboardButton(text='Level 5', callback_data = 'L05'),
                   InlineKeyboardButton(text='Level 6', callback_data = 'L06'),
                   InlineKeyboardButton(text='Level 7', callback_data = 'L07'),
                   InlineKeyboardButton(text='Level 8', callback_data = 'L08'),
                   InlineKeyboardButton(text='Level 9', callback_data = 'L09'),
                   InlineKeyboardButton(text='Level 10', callback_data = 'L10'),
                   InlineKeyboardButton(text='Level 11', callback_data = 'L11'),
                   InlineKeyboardButton(text='Level 12', callback_data = 'L12'),
                   InlineKeyboardButton(text='Level 13', callback_data = 'L13'),
                   InlineKeyboardButton(text='Level 14', callback_data = 'L14'),
                   InlineKeyboardButton(text='Level 15', callback_data = 'L15'),
                   InlineKeyboardButton(text='Level 16', callback_data = 'L16'),
                   InlineKeyboardButton(text='Level 17', callback_data = 'L17'),
                   InlineKeyboardButton(text='Back', callback_data = 'Back')]
    menu = build_menu(button_list, n_cols = 3)
    
    reply_text = "<b>Please select your current level:</b>"
        
    bot.editMessageText(text = reply_text,
                        reply_markup = InlineKeyboardMarkup(menu),
                        chat_id=query.message.chat_id,
                        message_id=query.message.message_id,
                        parse_mode=ParseMode.HTML)
    return NEAREST

def nearest_levels(bot, update):
    query = update.callback_query
    user = query.from_user
    logger.info("Returning 8 nearest laundry machine statuses to: User {}".format(user.username if user.username else user.first_name))
    
    current_level = int(query.data[1:])
    laundry_levels = [5, 8, 11, 14, 17]
    nearest_level = min(laundry_levels, key=lambda x:abs(x-current_level))

    pinned_level = int(query.data[1:])
    statuses = [1, 1, 0, 1]
    machines = ['Washer 1', 'Washer 2', 'Dryer 1', 'Dryer 2']
    
    reply_text = "Here are the respective statuses of laundry machines nearest to your level ({}):".format(str(current_level))
    reply_text = "\n\nOn Level {}, here are the statuses of the 4 laundry machines:".format(str(nearest_level))
    for i in range(len(statuses)):
        if statuses[i] == 1:
            reply_text += "\n\n" + etick + machines[i]
        elif statuses[i] == 0:
            reply_text += "\n\n" + ecross + machines[i]
    reply_text += "\n\nPress /start if you wish to restart the whole process anytime!"
        
    bot.editMessageText(text = reply_text,
                        chat_id=query.message.chat_id,
                        message_id=query.message.message_id,
                        parse_mode=ParseMode.HTML)
    
    return ConversationHandler.END


def settings(bot, update):
    query = update.callback_query
    user = query.from_user
    logger.info("User {} has selected settings.".format(user.username if user.username else user.first_name))

    button_list = [InlineKeyboardButton(text='Back to Main Menu', callback_data = 'back')]
    menu = build_menu(button_list, n_cols = 1)
    
    reply_text = "<b>FILL IN SETTINGS TEXT.</b>"
        
    bot.editMessageText(text = reply_text,
                        reply_markup = InlineKeyboardMarkup(menu),
                        chat_id=query.message.chat_id,
                        message_id=query.message.message_id,
                        parse_mode=ParseMode.HTML)
    return MENU


def helpfaq(bot, update):
    query = update.callback_query
    user = query.from_user
    logger.info("User {} has selected help/faq.".format(user.username if user.username else user.first_name))

    button_list = [InlineKeyboardButton(text='Back to Main Menu', callback_data = 'back')]
    menu = build_menu(button_list, n_cols = 1)
    
    reply_text = "<b>FILL IN FAQ TEXT.</b>"
        
    bot.editMessageText(text = reply_text,
                        reply_markup = InlineKeyboardMarkup(menu),
                        chat_id=query.message.chat_id,
                        message_id=query.message.message_id,
                        parse_mode=ParseMode.HTML)
    return MENU

def cancel(bot, update):
    user = update.message.from_user
    chatid = update.message.chat.id
    logger.info("User {} has cancelled the conversation.".format(user.username if user.username else user.first_name))
        
    bot.send_message(text = "Bye! See you soon! Press /start to restart.",
                     chat_id=chatid,
                     parse_mode=ParseMode.HTML)
    return ConversationHandler.END


#def autonotify(bot):
#    # auto notify queue 
#    return 


def main(): 
    updater = Updater(TELEGRAM_TOKEN)    
    # get job queue
    #job_queue = updater.job_queue    
    
    # keep notifying queue on 
    #job_queue.run_repeating(autonotify, interval=60, first=60) 
      
    # dispatcher to register handlers
    dispatcher = updater.dispatcher
    
    #NAME = 'laundry-bot-beta'
    #PORT = os.environ.get('PORT')
    
    conv_handler = ConversationHandler(
            entry_points = [CommandHandler('start', start)],
            
            states = {
                    AFTER_START: [CallbackQueryHandler(callback = select_method, pattern = '^(checkstart)$'),
                                  CallbackQueryHandler(callback = settings, pattern = '^(settings)$'),
                                  CallbackQueryHandler(callback = helpfaq, pattern = '^(help)$')],
                                  
                    MENU: [CallbackQueryHandler(callback = start, pattern = '^(back)$')],
                                  
                    AFTER_METHOD: [CallbackQueryHandler(callback = select_level, pattern = '^(pinnedlevelmethod)$'),
                                   CallbackQueryHandler(callback = select_nearest, pattern = '^(nearestlevelmethod)$'),
                                   CallbackQueryHandler(callback = start, pattern = '^(back)$')],
                    
                    SELECT_LEVEL: [CallbackQueryHandler(callback = pinned_level, pattern = '^((?!back).)*$'),
                                   CallbackQueryHandler(callback = select_method, pattern = '^(back)$')],
                                   
                    NEAREST: [CallbackQueryHandler(callback = nearest_levels, pattern = '^((?!back).)*$'),
                              CallbackQueryHandler(callback = select_method, pattern = '^(back)$')]},
                              
            fallbacks = [CommandHandler('cancel', cancel)],
            
            allow_reentry = True
        )
    
    dispatcher.add_handler(conv_handler)
        
    #updater.start_webhook(listen="0.0.0.0",
    #                      port = int(PORT),
    #                      url_path = TOKEN)
    #updater.bot.setWebhook("https://{}.herokuapp.com/{}".format(NAME, TOKEN))
    
    updater.start_polling()
    updater.idle()
    return 


if __name__ == '__main__':     
    main()