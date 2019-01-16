import os
import re
import logging
import requests
from datetime import datetime
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
# ethumb = emojize(":thumbsup: ", use_aliases=True)
# eblacksquare = emojize(":black_small_square: ", use_aliases=True)
# earrowfwd = emojize(":arrow_forward: ", use_aliases=True)
# ebangbang = emojize(":bangbang: ", use_aliases=True)
# eheart = emojize(":heart: ", use_aliases=True)
# enumber1 = emojize(":one: ", use_aliases=True)
# enumber2 = emojize(":two: ", use_aliases=True)
# enumber3 = emojize(":three: ", use_aliases=True)
ebluediamond = emojize(":small_blue_diamond: ", use_aliases=True)
etick = emojize(":white_check_mark: ", use_aliases=True)
ecross = emojize(":x: ", use_aliases=True)

# start command initializes: 
def check_handler(bot, update, user_data):
    logger.info("User: {} has started conversation with bot.".format(update.message.from_user.username else update.message.from_user.first_name))
    if 'pinned_level' in user_data:
        level_status(bot, update, user_data,
                     from_pinned_level=True, new_message=True)
    else:
        ask_level(bot, update)

def ask_level(bot, update):  
    level_text = "Which laundry level do you wish to check?"
    level_buttons = []
    for level in LAUNDRY_LEVELS:
        label = 'Level {}'.format(level)
        data = 'set_L{}'.format(level)
        buttons = InlineKeyboardButton(text=label, callback_data=data) # data callback to set_pinned_level
        level_buttons.append(buttons)
    update.message.reply_text(text=level_text,
                              reply_markup=build_menu(level_buttons, 1))

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
        status_emoji = etick if machine_status[machine_id] else ecross
        machine_name = MACHINES_INFO[machine_id]
        laundry_data += '{} {}\n'.format(status_emoji, machine_name)
    current_time = datetime.now().strftime('%d %B %Y %H:%M:%S')

    return "<b>Showing Statuses for Level {}</b>:\n\n" \
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

    return build_menu(level_buttons, 5, footer_buttons=refresh_button)

def level_status(bot, update, user_data, from_pinned_level=False, new_message=False):
    query = update.callback_query

    if from_pinned_level:
        level = user_data['pinned_level']
    else:
        level = int(re.match('^check_L(5|8|11|14|17)$', query.data).group(1))
    
    user_data['check_level'] = level

    if new_message:
        update.message.reply_text(text=make_status_text(level),
                                  reply_markup=make_status_menu(level))
    else:
        bot.edit_message_text(text=make_status_text(level),
                              chat_id=query.message.chat_id,
                              message_id=query.message.message_id,
                              reply_markup=make_status_menu(level))

    logger.info("Level status text is edited for user: {}".format(query.from_user.username else query.from_user.first_name))

def error(bot, update, error):
    logger.warning('Update "%s" caused error "%s"', update, error)

def main():
    TOKEN = os.environ['RC4LAUNDRYBOT_TOKEN']
    #NAME = 'laundry-bot-beta'
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
    dp.add_error_handler(error)

    #updater.start_webhook(listen="0.0.0.0", port=int(PORT), url_path=TOKEN)
    #updater.bot.setWebhook("https://{}.herokuapp.com/{}".format(NAME, TOKEN))
    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()