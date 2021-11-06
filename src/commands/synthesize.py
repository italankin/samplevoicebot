import logging
import re

from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.constants import CHATACTION_RECORD_AUDIO
from telegram.ext import CallbackContext, Dispatcher, MessageHandler, Filters, CallbackQueryHandler

from commands.command import Command
from synthesizerfacade import SynthesizerFacade

logger = logging.getLogger(__name__)

KEY_TEXT = 'text'


class SynthesizeCommand(Command):
    def __init__(self, synthesizer_facade: SynthesizerFacade):
        self._synthesizer_facade = synthesizer_facade

    def register(self, dispatcher: Dispatcher):
        dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, self._command))
        dispatcher.add_handler(CallbackQueryHandler(self._inline_callback, pattern=re.compile("voice=[A-z]+")))

    def _command(self, update: Update, context: CallbackContext):
        if update.message:
            query = update.message.text
        else:
            query = update.edited_message.text
        language, text, is_valid = self._synthesizer_facade.parse_query(query)
        if not is_valid:
            logger.debug(f"Invalid query='{query}', language='{language}' sanitized='{text}'")
            return
        context.user_data[KEY_TEXT] = text
        buttons = []
        voices = self._synthesizer_facade.voices(text, language).all_voices
        for voice in voices:
            buttons.append([InlineKeyboardButton(text=voice, callback_data=f"voice={voice}")])
        reply_markup = InlineKeyboardMarkup(buttons)
        update.effective_chat.send_message(text='Select voice:', reply_markup=reply_markup)

    def _inline_callback(self, update: Update, context: CallbackContext):
        update.callback_query.answer()
        update.callback_query.message.delete()
        if KEY_TEXT not in context.user_data:
            return
        update.effective_chat.send_chat_action(action=CHATACTION_RECORD_AUDIO)
        text = context.user_data[KEY_TEXT]
        context.user_data.clear()
        voice = update.callback_query.data.split('=')[1]
        voice_bytes = self._synthesizer_facade.synthesize_bytes(voice, text)
        if voice_bytes:
            update.effective_chat.send_voice(voice=voice_bytes)
