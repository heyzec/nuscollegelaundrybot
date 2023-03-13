# Laundry Bot for RC4, current telegram handle: @RC4LaundryBot

import os
import re
import logging
from typing import Optional
import requests
from datetime import datetime
import time
import traceback

from emoji import emojize
from dotenv import load_dotenv, find_dotenv
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, Defaults
from telegram.constants import ParseMode

# Use .env file
load_dotenv(find_dotenv())

# Set up logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize global variables
RC_URL = os.environ['RC_URL']
LAUNDRY_LEVELS = [5, 8, 11, 14, 17]
MACHINES_INFO = {
    'washer1': 'Washer 1',
    'washer2': 'Washer 2',
    'dryer1': 'Dryer 1',
    'dryer2': 'Dryer 2'
}

# Building emojis for every occasion
EMOJI_DIAMOND = emojize(":small_blue_diamond: ", language='alias')
EMOJI_TICK = emojize(":white_check_mark: ", language='alias')
EMOJI_CROSS = emojize(":x: ", language='alias')
EMOJI_SOON = emojize(":soon: ", language='alias')


def build_menu(buttons: list[InlineKeyboardButton],
               n_cols: int,
               header_buttons: Optional[list[InlineKeyboardButton]] = None,
               footer_buttons: Optional[list[InlineKeyboardButton]] = None):
    """Build a menu for every occasion."""
    menu = [buttons[i:i + n_cols] for i in range(0, len(buttons), n_cols)]
    if header_buttons:
        menu.insert(0, header_buttons)
    if footer_buttons:
        menu.append(footer_buttons)
    return InlineKeyboardMarkup(menu)


def make_status_menu(level_number: int):
    """Create status menu which contains help command, a pinned level number, and refresh button."""
    level_buttons = []

    for level in LAUNDRY_LEVELS:
        label = f'L{level}'
        data = f'check_L{level}'
        if level == level_number:
        #    label = u'\u2022 ' + label + u' \u2022'
            label = EMOJI_DIAMOND + label
        
        button = InlineKeyboardButton(text=label, callback_data=data)
        level_buttons.append(button)

    refresh_button = [InlineKeyboardButton(
        text='Refresh',
        callback_data=f'check_L{level_number}'
    )]

    help_button = [InlineKeyboardButton(
        text='Help',
        callback_data='help'
    )]

    return build_menu(level_buttons, 5, footer_buttons=refresh_button, header_buttons=help_button)


def make_status_text(level_number: int):
    """Carve status text for each level."""
    laundry_data = ''
    floor_url = RC_URL + str(level_number)

    # Get Request to the database backend
    machine_status = requests.get(floor_url).json()
    # machine_status = {
    #     'washer1': 0,
    #     'washer2': 0,
    #     'dryer1': 0,
    #     'dryer2': 0,
    # }

    for machine_id in MACHINES_INFO:
        if machine_status[machine_id] == 0:
            status_emoji = EMOJI_TICK
        elif machine_status[machine_id] == 1:
            status_emoji = EMOJI_CROSS
        else:
            status_emoji = EMOJI_SOON
        machine_name = MACHINES_INFO[machine_id]
        laundry_data += f'{status_emoji} {machine_name}\n'

    # TODO: This should be the backend server time instead
    current_time = datetime.fromtimestamp(time.time() + 8*3600).strftime('%d %B %Y %H:%M:%S')

    return f"<b>Showing statuses for Level {level_number}</b>:\n\n" \
           f"{laundry_data}\n" \
           f"Last updated: {current_time}\n"


# start command initializes: 
async def handle_start(update, context):
    user_data = context.user_data
    assert user_data is not None
    if 'pinned_level' in user_data:
        await level_status(update, context,
                     from_pinned_level=True, new_message=True)
    else:
        await ask_level(update)


async def ask_level(update):  
    level_text = "Heyyo! I am RC4's Laundry Bot. <i>As I am currently in [BETA] mode, I can only show details for Ursa floor.</i>\n\n<b>Which laundry level do you wish to check?</b>"
    level_buttons = []
    for level in LAUNDRY_LEVELS:
        label = f'Level {level}'
        data = f'set_L{level}'
        buttons = InlineKeyboardButton(text=label, callback_data=data) # data callback to set_pinned_level
        level_buttons.append(buttons)
    await update.message.reply_text(text=level_text,
                              reply_markup=build_menu(level_buttons, 1))


async def set_pinned_level(update, context):
    user_data = context.user_data
    query = update.callback_query
    level = int(re.match('^set_L(5|8|11|14|17)$', query.data).group(1))
    user_data['pinned_level'] = level

    await level_status(update, context, from_pinned_level=True)


async def level_status(update, context, from_pinned_level=False, new_message=False):
    user_data = context.user_data
    query = update.callback_query
    if from_pinned_level:
        level = user_data['pinned_level']
    else:
        level = int(re.match('^check_L(5|8|11|14|17)$', query.data).group(1))
    
    user_data['check_level'] = level

    if new_message:
        await update.message.reply_text(text=make_status_text(level),
                                  reply_markup=make_status_menu(level))
    else:
        await query.message.edit_text(text=make_status_text(level),
                              reply_markup=make_status_menu(level))


async def help_menu(update, context):
    user_data = context.user_data
    query = update.callback_query
    help_text = "<b>Help</b>\n\n" + "Washer 1 and Dryer 2 accept coins\n" + EMOJI_TICK + "= Available / Job done\n" + EMOJI_SOON + "= Job finishing soon\n" + EMOJI_CROSS + "= In use\n"
    help_text += "\nInformation not accurate or faced a problem? Please message @PakornUe or @Cpf05, thank you!"
    help_text += "\n\nThis is a project by RC4Space's Laundry Bot Team. We appreciate your feedback as we are currently still beta-testing in Ursa before launching the college-wide implementation! :)"
    
    level = user_data['check_level']

    help_menu_button = [InlineKeyboardButton(
        text='Back',
        callback_data=f'check_L{level}'
    )]

    await query.message.edit_text(text=help_text,
                            reply_markup=build_menu(help_menu_button, 1))


async def error(update, error):
    logger.warning('Update "%s" caused error "%s"', update, error)
    traceback.print_exc()


def main():
    BOT_TOKEN = os.environ['BOT_TOKEN']
    defaults = Defaults(parse_mode=ParseMode.HTML)
    app = ApplicationBuilder().token(BOT_TOKEN).defaults(defaults).build()
    #NAME = 'nuscollegelaundrybot'
    #PORT = os.environ.get('PORT')
    

    app.add_handler(CommandHandler('start', handle_start))
    app.add_handler(CallbackQueryHandler(set_pinned_level,
                                        pattern='^set_L(5|8|11|14|17)$'))
    app.add_handler(CallbackQueryHandler(level_status,
                                        pattern='^check_L(5|8|11|14|17)$'))
    app.add_handler(CallbackQueryHandler(help_menu,
                                        pattern='help'))
    app.add_error_handler(error)

    #updater.start_webhook(listen="0.0.0.0", port=int(PORT), url_path=TOKEN)
    #updater.bot.setWebhook("https://{}.herokuapp.com/{}".format(NAME, TOKEN))
    app.run_polling()

if __name__ == '__main__':
    main()
