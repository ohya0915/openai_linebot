from typing import List, Optional

from fastapi import APIRouter, HTTPException, Header, Request
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import TextMessage, MessageEvent, TextSendMessage, StickerMessage, \
    StickerSendMessage
from pydantic import BaseModel
from instance.config import Config
import openai

line_bot_api = LineBotApi(Config.CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(Config.CHANNEL_SECRET)
openai.api_key = Config.OPENAI_API_KEY

router = APIRouter(
    prefix="/ohya",
    tags=["chatbot"],
    responses={404: {"description": "Not found"}},
)


class Line(BaseModel):
    destination: str
    events: List[Optional[None]]


@router.post("/callback")
async def callback(request: Request, x_line_signature: str = Header(None)):
    body = await request.body()
    try:
        handler.handle(body.decode("utf-8"), x_line_signature)
    except InvalidSignatureError:
        raise HTTPException(status_code=400, detail="chatbot handle body error.")
    return 'OK'


@handler.add(MessageEvent, message=TextMessage)
def message_text(event):
    result = openai_resp(event.message.text)
    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=result["model_response"])
    )


@handler.add(MessageEvent, message=StickerMessage)
def sticker_text(event):
    line_bot_api.reply_message(
        event.reply_token,
        StickerSendMessage(package_id='11538', sticker_id='51626494')
    )
    
    
def openai_resp(msg_text: str) -> dict:
    """
    response user message
    :param : message
    :return: result
    """
    completion = openai.ChatCompletion.create(
    model="gpt-3.5-turbo",
    messages=[
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": msg_text}
    ]
    )
    result=completion.choices[0].message['content']

    return {"model_response": result}
    