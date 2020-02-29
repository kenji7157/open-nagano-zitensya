from django.shortcuts import render
from django.http import HttpResponseForbidden, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from linebot import (LineBotApi, WebhookHandler)
from linebot.models import (
    MessageEvent, TextMessage, LocationMessage, QuickReplyButton, MessageAction, QuickReply, TextSendMessage, TemplateSendMessage, ButtonsTemplate, LocationAction)
from linebot.exceptions import (InvalidSignatureError)
from zitensya.models import LineUser, Record
import datetime
import os
from naganoZitensya.settings import BASE_DIR
import pandas as pd
import numpy as np
import scipy as sc
from scipy import linalg
YOUR_CHANNEL_ACCESS_TOKEN = os.environ["YOUR_CHANNEL_ACCESS_TOKEN"]
YOUR_CHANNEL_SECRET = os.environ["YOUR_CHANNEL_SECRET"]


line_bot_api = LineBotApi(YOUR_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(YOUR_CHANNEL_SECRET)

age_list = ["10歳代", "20歳代", "30歳代", "40歳代", "50歳代", "60歳代", "70歳代"]
age_items = [QuickReplyButton(action=MessageAction(label=f"{age}", text=f"{age}")) for age in age_list]
occupation_list = ["小学生", "中学生", "高校生", "大学生", "その他"]
occupation_items = [QuickReplyButton(action=MessageAction(label=f"{occupation}", text=f"{occupation}")) for occupation in occupation_list]            
mode_list = ["設定を変更する", "安全スコア判定を行う"]
mode_items = [QuickReplyButton(action=MessageAction(label=f"{mode}", text=f"{mode}")) for mode in mode_list]
rock_list = ["施錠した", "施錠していない"]
rock_items = [QuickReplyButton(action=MessageAction(label=f"{rock}", text=f"{rock}")) for rock in rock_list]             
locale_list = ["位置情報の送信"]
local_items = [QuickReplyButton(action=LocationAction(label=f"{local}", text=f"{local}")) for local in locale_list]    

def index(request):
    """トップページ"""
    return render(request,
                  'zitensya/index.html',
                  {})

@csrf_exempt
def callback(request):
    signature = request.META['HTTP_X_LINE_SIGNATURE']
    body = request.body.decode('utf-8')
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        HttpResponseForbidden()
    return HttpResponse('OK', status=200)

# TextMessage を受信した場合
@handler.add(MessageEvent, message=TextMessage)
def handle_text_message(event):
    lineUserText = event.message.text
    profile = line_bot_api.get_profile(event.source.user_id)
    lineUserObj = LineUser.objects.filter(user_id=profile.user_id).first()
    if not lineUserObj:
        lineUser = LineUser(user_id=profile.user_id,
                    display_name=profile.display_name)
        lineUser.save()
        messages = [
            TextSendMessage(text="ユーザ情報の設定を行います"),
            TextSendMessage(text="年齢を選択してください",
                quick_reply=QuickReply(items=age_items))
            ]
    elif lineUserObj.pattern == -1:
        messages = errorMessage(lineUserText, age_list, lineUserObj.pattern)
        if len(messages) == 0:
            lineUserObj.age = lineUserText[:2]
            lineUserObj.pattern = 0
            lineUserObj.save()
            messages = TextSendMessage(text="職業を選択してください",
                                quick_reply=QuickReply(items=occupation_items))
    elif lineUserObj.pattern == 0:
        messages = errorMessage(lineUserText, occupation_list, lineUserObj.pattern)
        if len(messages) == 0:
            if lineUserText == "小学生":
                lineUserObj.occupation = 0
            elif lineUserText == "中学生":
                lineUserObj.occupation = 1
            elif lineUserText == "高校生":
                lineUserObj.occupation = 2
            elif lineUserText == "大学生":
                lineUserObj.occupation = 3
            elif lineUserText == "その他":
                lineUserObj.occupation = 4            
            lineUserObj.pattern = 1
            lineUserObj.save()
            messages = TextSendMessage(text="設定(年齢と職業の設定)が完了しました",
                                quick_reply=QuickReply(items=mode_items))
    elif lineUserObj.pattern == 1:
        messages = errorMessage(lineUserText, mode_list, lineUserObj.pattern)
        if len(messages) == 0:
            if lineUserText == "設定を変更する":
                messages = [
                    TextSendMessage(text="ユーザ情報を再設定します"),
                    TextSendMessage(text="年齢を選択してください",
                    quick_reply=QuickReply(items=age_items))
                    ]
                lineUserObj.pattern = -1
                lineUserObj.save()
            elif lineUserText == "安全スコア判定を行う":
                messages = TextSendMessage(text="施錠状態を選択してください",
                               quick_reply=QuickReply(items=rock_items))
                lineUserObj.pattern = 2
                lineUserObj.save()
    elif lineUserObj.pattern == 2:
        messages = errorMessage(lineUserText, rock_list, lineUserObj.pattern)
        if len(messages) == 0:
            if lineUserText == "施錠した":
                lineUserObj.is_rock = 1
            elif lineUserText == "施錠していない":
                lineUserObj.is_rock = 0
            lineUserObj.pattern = 3
            lineUserObj.save()
            messages = TextSendMessage(text="位置情報を送信してください",
                            quick_reply=QuickReply(items=local_items))
    elif lineUserObj.pattern == 3:
        messages = TextSendMessage(text="位置情報を送信してください",
                            quick_reply=QuickReply(items=local_items))
    line_bot_api.reply_message(event.reply_token, messages=messages)

# LocationMessage を受信した場合
@handler.add(MessageEvent, message=LocationMessage)
def handle_location_message(event):
    profile = line_bot_api.get_profile(event.source.user_id)
    lineUserObj = LineUser.objects.filter(user_id=profile.user_id).first()
    if lineUserObj.pattern == 3:
        profile = line_bot_api.get_profile(event.source.user_id)
        lineUserObj = LineUser.objects.filter(user_id=profile.user_id).first()
        lineUserObj.latitude = event.message.latitude
        lineUserObj.longitude = event.message.longitude
        lineUserObj.pattern = 1
        lineUserObj.save()
        # 安全スコア判定を行う
        score = calculateScore(lineUserObj)
        state = '安全'
        if score < 10:
            state = '危険'
        elif score < 15:
            state = 'やや危険'
        elif score < 20:
            state = '普通'
        else:
            state = '安全'
        messages = [
            TextSendMessage(text="安全スコアは【" + str(score) + "】です。"),
            TextSendMessage(text="あなたの自転車は【" + state + "】な状態です。",
                            quick_reply=QuickReply(items=mode_items))
            ]
    line_bot_api.reply_message(event.reply_token, messages=messages)

def calculateScore(lineUserObj):
    ROW = 7
    COLUMN = 1489 + 1
    csv = pd.read_csv(BASE_DIR + '/zitensya/CSV/bohan.csv')
    # ヘッダー列を削除
    del csv['Unnamed: 0']
    lineUserObj = setConvertLocation(lineUserObj, csv)
    today = datetime.date.today()
    now = datetime.datetime.now()
    csv['1489'] = [
        today.month,
        now.hour,
        lineUserObj.age,
        lineUserObj.occupation,
        lineUserObj.is_rock,
        lineUserObj.conLatitude,
        lineUserObj.conLongitude
        ]
    # row:行,column:列,ave:平均,vcm:分散共分散行列
    row = []
    column = []
    ave = [0.0 for i in range(ROW)]
    vcm = np.zeros((COLUMN, ROW, ROW))
    diff = np.zeros((1, ROW))
    mahal = np.zeros(COLUMN)
    tmp = np.zeros(ROW)
    # data欠損値の削除
    # axis = 1 で，欠損値のある列を削除
    trans_data = csv.dropna(axis=1)
    # rowにtrans_dataの要素をリストの形式で連結
    for i in range(ROW):
        row.append(list(trans_data.ix[i]))
    # 列を連結
    for i in range(0, COLUMN):
        column.append(list(trans_data.ix[:, i]))
    # 平均値の計算
    for i in range(ROW):
        # スライスという技法
        ave[i] = np.average(row[i][1:len(row[i])])
    # Numpyのメソッドを使うので，array()でリストを変換した．
    column = np.array([column])
    ave = np.array(ave)
    # 分散共分散行列を求める
    # np.swapaxes()で軸を変換することができる．
    for i in range(COLUMN):
        diff = (column[0][i] - ave)
        diff = np.array([diff])
        vcm[i] = (diff * np.swapaxes(diff, 0, 1)) / COLUMN
    # mahalnobis distanceを求める
    for i in range(COLUMN):
        # 一般逆行列を生成し，計算の都合上転値をかける
        vcm[i] = sc.linalg.pinv(vcm[i])
        vcm[i] = vcm[i].transpose()
        vcm[i] = np.identity(ROW)
        # 差分ベクトルの生成
        diff = (column[0][i] - ave)
        for j in range(ROW):
            tmp[j] = np.dot(diff, vcm[i][j])
        mahal[i] = np.dot(tmp, diff)
    mahal = np.sqrt(mahal)
    # Recordに記録する
    setRecord(lineUserObj, mahal[-1])
    return mahal[-1]

def errorMessage(lineUserMessage, messageList, pattern):
    messages = []
    if not lineUserMessage in messageList:
        messages.append(TextSendMessage(text="画面下のボタンから入力を選択して下さい"))
        if pattern == -1:
            messages.append(TextSendMessage(text="年齢を選択してください", quick_reply=QuickReply(items=age_items)))
        if pattern == 0:
            messages.append(TextSendMessage(text="職業を選択してください", quick_reply=QuickReply(items=occupation_items)))
        if pattern == 1:
            messages.append(TextSendMessage(text="操作を選んでください", quick_reply=QuickReply(items=mode_items)))
        if pattern == 2:
            messages.append(TextSendMessage(text="施錠状態を選択してください", quick_reply=QuickReply(items=rock_items)))
        if pattern == 3:
            messages.append(TextSendMessage(text="位置情報を送信してください", quick_reply=QuickReply(items=local_items)))
    return messages

# 変換後の緯度経度をlineUserObjに保存
def setConvertLocation(lineUserObj, csv):
    dMin = 10**9
    tempLocation = []
    for latitude, longitude in zip (csv.iloc[5], csv.iloc[6]):
        lineUserLocation = np.array([lineUserObj.latitude, lineUserObj.longitude])
        csvLocation = np.array([latitude, longitude])
        locationData = np.linalg.norm(csvLocation - lineUserLocation)
        if dMin >= locationData:
            dMin = locationData
            tempLocation = csvLocation
    # lineUserObj = LineUser.objects.filter(lineUserObj=lineUserObj.user_id).first()
    lineUserObj.conLatitude = tempLocation[0]
    lineUserObj.conLongitude = tempLocation[1]
    lineUserObj.save()
    return lineUserObj

def setRecord(lineUserObj, score):
    today = datetime.date.today()
    now = datetime.datetime.now()
    recordObj = Record(user_id=lineUserObj.user_id,
            display_name=lineUserObj.display_name,
            age=lineUserObj.age,
            occupation=lineUserObj.occupation,
            is_rock=lineUserObj.is_rock,
            latitude=lineUserObj.latitude,
            longitude=lineUserObj.longitude,
            conLatitude=lineUserObj.conLatitude,
            conLongitude=lineUserObj.conLongitude,
            month=today.month,
            time=now.hour,
            score=score
            )
    recordObj.save()
