from AWSIoTPythonSDK.MQTTLib import AWSIoTMQTTClient
import time
import json
import socket

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

MQTT_CLIENT = None
JULIUS_SERVER = None

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
    JULIUS_SERVER.connect(JULIUS_HOST, JULIUS_PORT)

def send_message(action):
    if len(action) != 0:
        message = {}
        message['action'] = action

        messageJson = json.dumps(message)

        global MQTT_CLIENT
        MQTT_CLIENT.publish(TOPIC_NAME, messageJson, 1)


init()

julius_action = ""
global JULIUS_SERVER
while True:
    # Juliusサーバからデータを受信
    julius_data = JULIUS_SERVER.recv(JULIUS_DATASIZE).decode('utf-8')

    for line in julius_data.split('\n'):
        # 受信データから、<WORD>の後に書かれている言葉を抽出して変数に格納する。
        # <WORD>の後に、話した言葉が記載されている。
        index = line.find('WORD="')
        if index != -1:
            # julius_actionに話した言葉を格納
            julius_action = julius_action + line[index+6:line.find('"',index+6)]
            
        # 受信データに</RECOGOUT>'があれば、話終わり ⇒ フラグをTrue
        if '</RECOGOUT>' in line:
            fin_flag = True

    if fin_flag == True:
        fin_flag = False
        julius_action = ""

        if 'エンペラー起動' in julius_action:
            send_message('startUp')
        elif 'カメラを起動' in julius_action:
            send_message('cameraStart')
        elif 'カメラを停止' in julius_action:
            send_message('cameraStop')
