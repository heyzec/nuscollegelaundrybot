import os
import re
import logging
import requests
from datetime import datetime
import time
from emoji import emojize
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ParseMode
from telegram.ext import Updater, CommandHandler, CallbackQueryHandler

# Set up logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize global variables
RC_URL = "https://us-central1-rc4laundrybot.cloudfunctions.net/readData/RC4-"
LAUNDRY_LEVELS = [5, 8, 11, 14, 17]
MACHINES_INFO = {
    'washer1': 'Washer 1',
    'washer2': 'Washer 2',
    'dryer1': 'Dryer 1',
    'dryer2': 'Dryer 2'
}

# Building menu for every occasion
def build_menu(buttons, n_cols, header_buttons=None, footer_buttons=None):
    menu = [buttons[i:i + n_cols] for i in range(0, len(buttons), n_cols)]
    if header_buttons:
        menu.insert(0, header_buttons)
    if footer_buttons:
        menu.append(footer_buttons)
    return InlineKeyboardMarkup(menu)

# Building emojis for every occasion
ebluediamond = emojize(":small_blue_diamond: ", use_aliases=True)
etick = emojize(":white_check_mark: ", use_aliases=True)
ecross = emojize(":x: ", use_aliases=True)
esoon = emojize(":soon: ", use_aliases=True)

# start command initializes: 
def check_handler(bot, update, user_data):
    user = update.message.from_user
    logger.info("User: {} has started conversation with bot.".format(user.username if user.username else user.first_name))
    if 'pinned_level' in user_data:
        level_status(bot, update, user_data,
                     from_pinned_level=True, new_message=True)
    else:
        ask_level(bot, update)

def ask_level(bot, update):  
    level_text = "Heyyo! I am RC4's Laundry Bot. <i>As I am currently in [BETA] mode, I can only show details for Ursa floor.</i>\n\n<b>Which laundry level do you wish to check?</b>"
    level_buttons = []
    for level in LAUNDRY_LEVELS:
        label = 'Level {}'.format(level)
        data = 'set_L{}'.format(level)
        buttons = InlineKeyboardButton(text=label, callback_data=data) # data callback to set_pinned_level
        level_buttons.append(buttons)
    update.message.reply_text(text=level_text,
                              reply_markup=build_menu(level_buttons, 1),
                              parse_mode=ParseMode.HTML)

def set_pinned_level(bot, update, user_data):
    query = update.callback_query
    level = int(re.match('^set_L(5|8|11|14|17)$', query.data).group(1))
    user_data['pinned_level'] = level

    level_status(bot, update, user_data, from_pinned_level=True)

def make_status_text(level_number):
    laundry_data = ''
    floor_url = RC_URL + str(level_number)
    machine_status = requests.get(floor_url).json()
    for machine_id in MACHINES_INFO:
        if machine_status[machine_id] == 0:
            status_emoji = etick
        elif machine_status[machine_id] == 1:
            status_emoji = ecross
        else:
            status_emoji = esoon
        machine_name = MACHINES_INFO[machine_id]
        laundry_data += '{} {}\n'.format(status_emoji, machine_name)

    current_time = datetime.fromtimestamp(time.time() + 8*3600).strftime('%d %B %Y %H:%M:%S')

    return "<b>Showing statuses for Level {}</b>:\n\n" \
           "{}\n" \
           "Last updated: {}\n".format(level_number, laundry_data, current_time)

def make_status_menu(level_number):
    level_buttons = []

    for level in LAUNDRY_LEVELS:
        label = 'L{}'.format(level)
        data = 'check_L{}'.format(level)
        if level == level_number:
        #    label = u'\u2022 ' + label + u' \u2022'
            label = ebluediamond + label
        
        button = InlineKeyboardButton(text=label, callback_data=data)
        level_buttons.append(button)

    refresh_button = [InlineKeyboardButton(
        text='Refresh',
        callback_data='check_L{}'.format(level_number)
    )]

    help_button = [InlineKeyboardButton(
        text='Help',
        callback_data='Help'
    )]

    return build_menu(level_buttons, 5, footer_buttons=refresh_button, header_buttons=help_button)

def level_status(bot, update, user_data, from_pinned_level=False, new_message=False):
    query = update.callback_query
    if from_pinned_level:
        level = user_data['pinned_level']
    else:
        level = int(re.match('^check_L(5|8|11|14|17)$', query.data).group(1))
    
    user_data['check_level'] = level

    if new_message:
        update.message.reply_text(text=make_status_text(level),
                                  reply_markup=make_status_menu(level),
                                  parse_mode=ParseMode.HTML)
    else:
        bot.edit_message_text(text=make_status_text(level),
                              chat_id=query.message.chat_id,
                              message_id=query.message.message_id,
                              reply_markup=make_status_menu(level),
                              parse_mode=ParseMode.HTML)  


def help_menu(bot, update, user_data, from_pinned_level=False, new_message=False):
    query = update.callback_query
    help_text = "<b>Help</b>\n\n" + "Washer 1 and Dryer 2 accept coins\n" + etick + "= Available / Job done\n" + esoon + "= Job finishing soon\n" + ecross + "= In use\n"
    help_text += "\nInformation not accurate or faced a problem? Please contact @PakornUe or @Cpf05, thank you!\n"
    help_text += "\n\nThis is a project by RC4Space's Laundry Bot Team. We appreciate your feedback as we are currently still beta-testing in Ursa before launching the college-wide implementation! :)"
    
    level = user_data['check_level']

    help_menu_button = [InlineKeyboardButton(
        text='Back',
        callback_data='check_L{}'.format(level)
    )]

    bot.edit_message_text(text=help_text,
                            chat_id=query.message.chat_id,
                            message_id=query.message.message_id,
                            reply_markup=build_menu(help_menu_button, 1),
                            parse_mode=ParseMode.HTML)  


def error(bot, update, error):
    logger.warning('Update "%s" caused error "%s"', update, error)

def main():
    TOKEN = os.environ['RC4LAUNDRYBOT_TOKEN']
    #NAME = 'nuscollegelaundrybot'
    #PORT = os.environ.get('PORT')

    updater = Updater(TOKEN)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler('start', check_handler, pass_user_data=True))
    dp.add_handler(CallbackQueryHandler(set_pinned_level,
                                        pattern='^set_L(5|8|11|14|17)$',
                                        pass_user_data=True))
    dp.add_handler(CallbackQueryHandler(level_status,
                                        pattern='^check_L(5|8|11|14|17)$',
                                        pass_user_data=True))
    dp.add_handler(CallbackQueryHandler(help_menu,
                                        pattern='Help',
                                        pass_user_data=True))
    dp.add_error_handler(error)

    #updater.start_webhook(listen="0.0.0.0", port=int(PORT), url_path=TOKEN)
    #updater.bot.setWebhook("https://{}.herokuapp.com/{}".format(NAME, TOKEN))
    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
