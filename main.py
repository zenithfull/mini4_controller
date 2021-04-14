from AWSIoTPythonSDK.MQTTLib import AWSIoTMQTTClient
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import FaBo9Axis_MPU9250
import time
import json
import socket
import subprocess

###########################################
# AWS IoT 接続情報
###########################################
# モノの名前
MQTT_CLIENT = 'mini4Controller'
# エンドポイントのURL
ENDPOINT_URL = 'a3042qvtxfzkab-ats.iot.us-east-2.amazonaws.com'
# エンドポイントのポート番号
ENDPOINT_PORT = 8883
# ルート証明書ファイル
ROOT_CA_PATH = 'cert/rootCA.pem'
# 個別秘密鍵ファイル
PRIVATE_KEY_PATH = 'cert/2aa2a47548-private.pem.key'
# 個別証明書ファイル
PRIVATE_CERT_PATH = 'cert/2aa2a47548-certificate.pem.crt'
# トピック名
TOPIC_NAME = 'testTopic'

###########################################
# Julius 接続情報
###########################################
# JuliusサーバのIP
JULIUS_HOST = 'localhost'
# Juliusサーバの接続ポート
JULIUS_PORT = 10500
# Juliusサーバから1回に受け取るデータバイト数
JULIUS_DATASIZE = 1024

###########################################
# ローカルHTMLファイル情報
###########################################
LOCAL_HTML_FILE_PATH = '/home/pi/Documents/workspace/mini4_controller/html/main.html'

## 入力ワード
STARTUP_WORD = "起動"
CAMERA_ON_WORD = "カメラオン"
CAMERA_OFF_WORD = "カメラオフ"
MOVE_WORD = "発進"
STOP_WORD = "停止"
BACK_WORD = "バック"

## 送信コマンド
STARTUP_COMMAND = "startup"
CAMERA_ON_COMMAND = "cameraOn"
CAMERA_OFF_COMMAND = "cameraOff"
MOVE_COMMAND = "move"
STOP_COMMAND = "stop"
BACK_COMMAND = "back"
STRAIGHT_COMMAND = "straight"
LEFT_COMMAND = "left"
RIGHT_COMMAND = "right"

## 左右角度の閾値
LEFT_THRESHOLD = 2.0
RIGHT_THRESHOLD = 10.0
## I/O コントローラ
MQTT_CLIENT = None
JULIUS_SERVER = None
AXIS_READER = None
BROWSER = None

## 内部変数
julius_input_word = ""
julius_input_fin_flag = False
julius_action = STOP_COMMAND
axis_action = STRAIGHT_COMMAND

send_action = ""
send_direction = ""

def init():
    # AWS IoT Connect Info
    global MQTT_CLIENT
    MQTT_CLIENT = AWSIoTMQTTClient(MQTT_CLIENT)
    MQTT_CLIENT.configureEndpoint(ENDPOINT_URL, ENDPOINT_PORT)
    MQTT_CLIENT.configureCredentials(ROOT_CA_PATH, PRIVATE_KEY_PATH, PRIVATE_CERT_PATH)

    # AWS IoT Connect Setting
    MQTT_CLIENT.configureOfflinePublishQueueing(-1)
    MQTT_CLIENT.configureDrainingFrequency(2)
    MQTT_CLIENT.configureConnectDisconnectTimeout(10)
    MQTT_CLIENT.configureMQTTOperationTimeout(5)

    MQTT_CLIENT.connect()

    # Julius Server Connect Info
    global JULIUS_SERVER
    JULIUS_SERVER = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    JULIUS_SERVER.connect((JULIUS_HOST, JULIUS_PORT))
    
    # 9Axis Controller Info
    global AXIS_READER
    AXIS_READER = FaBo9Axis_MPU9250.MPU9250()

    # Browser Info
    global BROWSER
    browser_option = Options()
    browser_option.add_experimental_option("excludeSwitches", ['enable-automation'])
    browser_option.add_argument('--kiosk')

    BROWSER = webdriver.Chrome(executable_path="/usr/lib/chromium-browser/chromedriver", chrome_options=browser_option )

def send_message(action, direction):
    message = {}
    message['action'] = action
    message['direction'] = direction

    messageJson = json.dumps(message)

    global MQTT_CLIENT
    MQTT_CLIENT.publish(TOPIC_NAME, messageJson, 1)


init()

while True:
    # モーションセンサーの値を取得
    accel = AXIS_READER.readAccel()
    print("accel Y: " + str(accel['y']))

    if accel['y'] < LEFT_THRESHOLD:
        axis_action = LEFT_COMMAND
    elif accel['y'] > RIGHT_THRESHOLD:
        axis_action = RIGHT_COMMAND
    else:
        axis_action = STRAIGHT_COMMAND

    if send_direction != axis_action:
        send_message(julius_action, axis_action)
        send_direction = axis_action

    # Juliusサーバからデータを受信
    julius_data = JULIUS_SERVER.recv(JULIUS_DATASIZE).decode('utf-8')

    for line in julius_data.split('\n'):
        # 受信データから、<WORD>の後に書かれている言葉を抽出して変数に格納する。
        # <WORD>の後に、話した言葉が記載されている。
        index = line.find('WORD="')
        if index != -1:
            # julius_input_wordに話した言葉を格納
            julius_input_word = julius_input_word + line[index+6:line.find('"',index+6)]
            
        # 受信データに</RECOGOUT>'があれば、話終わり ⇒ フラグをTrue
        if '</RECOGOUT>' in line:
            julius_input_fin_flag = True
            julius_input_word = julius_input_word.replace('[s]', '')
            julius_input_word = julius_input_word.replace('[/s]', '')
            
    if julius_input_fin_flag == True:
        print(julius_input_word)
        if STARTUP_WORD in julius_input_word:
            # 起動処理
            julius_action = STARTUP_COMMAND
        elif CAMERA_ON_WORD in julius_input_word:
            # カメラ起動処理
            julius_action = CAMERA_ON_COMMAND

            BROWSER.get('file//' + LOCAL_HTML_FILE_PATH)
        elif CAMERA_OFF_WORD in julius_input_word:
            # カメラ終了処理
            julius_action = CAMERA_OFF_COMMAND

            BROWSER.quit()
        elif MOVE_WORD in julius_input_word:
            # 走行処理
            julius_action = STARTUP_COMMAND
        elif STOP_WORD in julius_input_word:
            # 停止処理
            julius_action = STOP_COMMAND
        elif BACK_WORD in julius_input_word:
            # バック走行処理
            julius_action = BACK_COMMAND

        if send_action != julius_action:
            send_message(julius_action, send_direction)
            send_action = julius_action

        julius_input_fin_flag = False
        julius_input_word = ""

