# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2023 Hitalo M. <https://github.com/HitaloM>

from typing import Union

from aiogram import F, Router
from aiogram.enums import ChatType
from aiogram.filters import Command
from aiogram.types import CallbackQuery, Message
from aiogram.utils.i18n import gettext as _
from aiogram.utils.keyboard import InlineKeyboardBuilder
from babel import Locale

from gojira import i18n
from gojira.database.models import Chats, Users
from gojira.utils.callback_data import LanguageCallback, StartCallback

router = Router(name="language")


@router.message(Command("language"))
@router.callback_query(StartCallback.filter(F.menu == "language"))
async def select_language(union: Union[Message, CallbackQuery]):
    keyboard = InlineKeyboardBuilder()
    is_callback = isinstance(union, CallbackQuery)
    message = union.message if is_callback else union
    if message is None or union.from_user is None:
        return None

    if message.chat.type == ChatType.PRIVATE:
        lang = await Users.get(id=union.from_user.id)
        chat_type = "private"
    else:
        lang = await Chats.get(id=message.chat.id)
        chat_type = "group"

    lang = str(Locale.parse(lang.language_code).display_name).capitalize()
    if message.chat.type == ChatType.PRIVATE:
        text = _("Your language: {lang}").format(lang=lang)
    else:
        text = _("Chat language: {lang}").format(lang=lang)

    for lang in i18n.available_locales:
        lang = str(Locale.parse(lang).display_name).capitalize()
        keyboard.button(text=lang, callback_data=LanguageCallback(lang=lang, chat=chat_type))

    keyboard.button(
        text=str(Locale.parse("en").display_name).capitalize(),
        callback_data=LanguageCallback(lang="en", chat=chat_type),
    )

    keyboard.adjust(4)
    if is_callback:
        await message.edit_text(text, reply_markup=keyboard.as_markup())
    else:
        await message.reply(text, reply_markup=keyboard.as_markup())


@router.callback_query(LanguageCallback.filter())
async def language_callback(callback: CallbackQuery, callback_data: LanguageCallback):
    if callback.message is None or callback.from_user is None:
        return None

    if callback_data.chat == "private":
        await Users.filter(id=callback.from_user.id).update(language_code=callback_data.lang)
    if callback_data.chat == "group":
        await Chats.filter(id=callback.message.chat.id).update(language_code=callback_data.lang)

    lang = Locale.parse(callback_data.lang)
    await callback.message.edit_text(
        _("Changed language to {lang}").format(lang=lang.display_name)
    )