#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Simple Bot to reply to Telegram messages.

This program is dedicated to the public domain under the CC0 license.

This Bot uses the Updater class to handle the bot.

First, a few handler functions are defined. Then, those functions are passed to
the Dispatcher and registered at their respective places.
Then, the bot is started and runs until we press Ctrl-C on the command line.

Usage:
Basic Echobot example, repeats messages.
Press Ctrl-C on the command line or send a signal to the process to stop the
bot.
"""

from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
import logging
import uuid
import os
from urllib.parse import urlparse
from meb_checkimage import classify_image
from telegram import (ReplyKeyboardMarkup, ReplyKeyboardRemove)

last_photo = {}
# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)

logger = logging.getLogger(__name__)


# Define a few command handlers. These usually take the two arguments bot and
# update. Error handlers also receive the raised TelegramError object in error.
def start(bot, update):
    """Send a message when the command /start is issued."""
    update.message.reply_text('Hi!')


def help(bot, update):
    """Send a message when the command /help is issued."""
    update.message.reply_text('Help!')


def echo(bot, update):
    """Echo the user message."""
    update.message.reply_text(update.message.text)


def error(bot, update, error):
    """Log Errors caused by Updates."""
    logger.warning('Update "%s" caused error "%s"', update, error)

def getphoto(bot, update):
    global last_photo
    file_id = update.message.photo[-1].file_id
    print('fileID = ',file_id)
    file_info = bot.getFile(file_id)
    print('file.file_path =', file_info.file_path)
    path = urlparse(file_info.file_path).path
    ext = os.path.splitext(path)[1]
    filename=str(uuid.uuid4())+ext
    filepath="data/"+str(update.message.from_user.id)+"/unknown/"+filename
    directory = os.path.dirname(filepath)
    if not os.path.exists(directory):
        os.makedirs(directory)
    file_info.download(custom_path=filepath)
#    update.message.reply_text("Recieved photo "+filename)
    (top_k,labels,results)=classify_image(filepath)
    z="Recieved photo "+filename+"\n---------------"
    for i in top_k:
        z=z+"\n"+labels[i]+":"+str(results[i])
    z=z+"\n--------------------\nPlease set category (true alert or false alert) or just skip"
    reply_keyboard = [['/true_alert', '/false_alert', '/skip_alert']]
    last_photo[update.message.from_user.id]=filepath
    update.message.reply_text(z,reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True))


def true_alert(bot, update):
    global last_photo
    if update.message.from_user.id in last_photo:
        fp=last_photo[update.message.from_user.id]
        fp_new=fp.replace("/unknown/","/true/")
        directory = os.path.dirname(fp_new)
        if not os.path.exists(directory):
            os.makedirs(directory)
        os.rename(fp,fp_new)
        last_photo.pop(update.message.from_user.id,None)
        update.message.reply_text("Successfully marked as true_alert")
    else:
        update.message.reply_text("Something goes wrong - photo don't found")


def false_alert(bot, update):
    global last_photo
    if update.message.from_user.id in last_photo:
        fp=last_photo[update.message.from_user.id]
        fp_new=fp.replace("/unknown/","/false/")
        directory = os.path.dirname(fp_new)
        if not os.path.exists(directory):
            os.makedirs(directory)
        os.rename(fp,fp_new)
        last_photo.pop(update.message.from_user.id,None)
        update.message.reply_text("Successfully marked as false_alert")
    else:
        update.message.reply_text("Something goes wrong - photo don't found")


def skip_alert(bot, update):
    global last_photo
    if update.message.from_user.id in last_photo:
        last_photo.pop(update.message.from_user.id,None)
        update.message.reply_text("Ok. You boss")
    else:
        update.message.reply_text("Something goes wrong - photo don't found")


def main():
    """Start the bot."""
    # Create the EventHandler and pass it your bot's token.
    updater = Updater("")

    # Get the dispatcher to register handlers
    dp = updater.dispatcher

    # on different commands - answer in Telegram
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("help", help))
    dp.add_handler(CommandHandler("true_alert", true_alert))
    dp.add_handler(CommandHandler("false_alert", false_alert))
    dp.add_handler(CommandHandler("skip_alert", skip_alert))

    dp.add_handler(MessageHandler(Filters.photo & (~ Filters.forwarded), getphoto))

    # on noncommand i.e message - echo the message on Telegram
    dp.add_handler(MessageHandler(Filters.text, echo))

    # log all errors
    dp.add_error_handler(error)

    # Start the Bot
    updater.start_polling()

    # Run the bot until you press Ctrl-C or the process receives SIGINT,
    # SIGTERM or SIGABRT. This should be used most of the time, since
    # start_polling() is non-blocking and will stop the bot gracefully.
    updater.idle()


if __name__ == '__main__':
    main()
