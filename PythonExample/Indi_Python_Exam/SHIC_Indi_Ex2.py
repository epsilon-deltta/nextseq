import sys
from PyQt5.QtGui import *
from PyQt5.QtCore import *
from PyQt5.QAxContainer import *
from PyQt5.QtWidgets import QApplication
from PyQt5.QtWidgets import QMainWindow
from PyQt5.QtWidgets import QPushButton
from PyQt5.QtWidgets import QLineEdit
from pandas import Series, DataFrame
import pandas as pd
import numpy as np

'''
    신한아이 인디 해외주식 예제입니다:
    코드를 입력하시고 Search 버튼을 누르시면
    종목코드에 해당하는 일별 차트 데이터 100개와
    종목 가격정보를 조회하여 출력합니다.
'''

class IndiWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("IndiExample")

        #Indi OCX Loading
        self.IndiTR = QAxWidget("GIEXPERTCONTROL.GiExpertControlCtrl.1")
        self.IndiTR.ReceiveData.connect(self.ReceiveData)
        self.IndiTR.ReceiveSysMsg.connect(self.ReceiveSysMsg)

        # Indi OCX Loading
        self.IndiReal = QAxWidget("GIEXPERTCONTROL.GiExpertControlCtrl.1")
        self.IndiReal.ReceiveRTData.connect(self.ReceiveRTData)

        self.rqidD = {}
        PriceInfodt = np.dtype([('Symbol', 'S10'), ('Name', 'S40'), ('Close', 'f'), ('Open', 'f'), ('High', 'f'), ('Low', 'f'),
                       ('UpLimit', 'f'), ('DownLimit', 'f'), ('PrevClose', 'f'), ('Ask1', 'f'), ('Bid1', 'f'),
                       ('Time', 'S6'), ('Vol', 'u4'), ('ContQty', 'u4'), ('Ask1Qty', 'u4'), ('Bid1Qty', 'u4')])
        self.PriceInfo = np.empty([1], dtype=PriceInfodt)

        Historicaldt = np.dtype([('Date', 'S8'), ('Time', 'S6'), ('Open', 'f'), ('High', 'f'), ('Low', 'f'), ('Close', 'f'), ('Vol', 'u4')])
        self.Historical = np.empty([100], dtype=Historicaldt)

        '''
            해외주식의 경우 국가코드(3)+현지코드로 구성됩니다.
            미국 : USAMSFT
            홍콩 : CHN0001
            이런 코드를 문서상 GIC 코드라고 하며 실시간 조회시 Key가 됩니다.
       '''
        self.MainSymbol = ""
        self.edSymbol = QLineEdit(self)
        self.edSymbol.setGeometry(20, 20, 65, 20)
        self.edSymbol.setText("")

        btnResearch = QPushButton("Search", self)
        btnResearch.setGeometry(90, 20, 50, 20)
        btnResearch.clicked.connect(self.btn_Search)

    def btn_Search(self):
        Symbol = self.edSymbol.text()

        # 기존 실시간 해제
        if self.MainSymbol != "":
            self.IndiReal.dynamicCall("UnRequestRTReg(QString, QString)", "RB", self.MainSymbol)
            self.IndiReal.dynamicCall("UnRequestRTReg(QString, QString)", "RC", self.MainSymbol)
            self.IndiReal.dynamicCall("UnRequestRTReg(QString, QString)", "RH", self.MainSymbol)

        self.MainSymbol = Symbol
        Symbol = self.MainSymbol[3:]
        Country = self.MainSymbol[0:3]

        # 차트 조회
        ret = self.IndiTR.dynamicCall("SetQueryName(QString)", "TR_RCHART")

        # 해외주식 조회에 관한 해외거래소 조건에 따라 사용자 ID를 입력하세요.
        ret = self.IndiTR.dynamicCall("SetSingleData(int, QString)", 0, "YourID")
        # 해외주식 실시간 신청고객인 경우
        ret = self.IndiTR.dynamicCall("SetSingleData(int, QString)", 1, "RRRRRRRRRRR")

        ret = self.IndiTR.dynamicCall("SetSingleData(int, QString)", 2, Country)
        ret = self.IndiTR.dynamicCall("SetSingleData(int, QString)", 3, Symbol)
        ret = self.IndiTR.dynamicCall("SetSingleData(int, QString)", 4, "D")
        ret = self.IndiTR.dynamicCall("SetSingleData(int, QString)", 5, "1")
        ret = self.IndiTR.dynamicCall("SetSingleData(int, QString)", 6, "00000000")
        ret = self.IndiTR.dynamicCall("SetSingleData(int, QString)", 7, "99999999")
        ret = self.IndiTR.dynamicCall("SetSingleData(int, QString)", 8, "100")
        ret = self.IndiTR.dynamicCall("SetSingleData(int, QString)", 9, self.MainSymbol)
        rqid = self.IndiTR.dynamicCall("RequestData()")

        self.rqidD[rqid] =  "TR_RCHART"

        # 해외주식 기본정보 조회
        ret = self.IndiTR.dynamicCall("SetQueryName(QString)", "RB")
        ret = self.IndiTR.dynamicCall("SetSingleData(int, QString)", 0, self.MainSymbol)
        rqid = self.IndiTR.dynamicCall("RequestData()")

        self.rqidD[rqid] = "RB"

        # 해외주식 현재가 조회
        ret = self.IndiTR.dynamicCall("SetQueryName(QString)", "RC")
        ret = self.IndiTR.dynamicCall("SetSingleData(int, QString)", 0, self.MainSymbol)
        rqid = self.IndiTR.dynamicCall("RequestData()")

        self.rqidD[rqid] = "RC"

        # 해외주식 호가 조회
        ret = self.IndiTR.dynamicCall("SetQueryName(QString)", "RH")
        ret = self.IndiTR.dynamicCall("SetSingleData(int, QString)", 0, self.MainSymbol)
        rqid = self.IndiTR.dynamicCall("RequestData()")

        self.rqidD[rqid] = "RH"

    def ReceiveData(self, rqid):

        TRName = self.rqidD[rqid]
        if TRName == "TR_RCHART" :
            nCnt = self.IndiTR.dynamicCall("GetMultiRowCount()")
            np.reshape(self.Historical, nCnt)
            for i in range(0, nCnt):
                self.Historical[i]['Date'] = self.IndiTR.dynamicCall("GetMultiData(int, int)", i, 0)
                self.Historical[i]['Time'] = self.IndiTR.dynamicCall("GetMultiData(int, int)", i, 1)
                self.Historical[i]['Open'] = self.IndiTR.dynamicCall("GetMultiData(int, int)", i, 2)
                self.Historical[i]['High'] = self.IndiTR.dynamicCall("GetMultiData(int, int)", i, 3)
                self.Historical[i]['Low'] = self.IndiTR.dynamicCall("GetMultiData(int, int)", i, 4)
                self.Historical[i]['Close'] = self.IndiTR.dynamicCall("GetMultiData(int, int)", i, 5)
                self.Historical[i]['Vol'] = self.IndiTR.dynamicCall("GetMultiData(int, int)", i, 6)

            print(self.Historical)

        elif TRName == "RB":
            self.PriceInfo[0]['Name'] = self.IndiTR.dynamicCall("GetSingleData(int)", 5)
            self.PriceInfo[0]['PrevClose'] = self.IndiTR.dynamicCall("GetSingleData(int)", 11)
            self.PriceInfo[0]['UpLimit'] = self.IndiTR.dynamicCall("GetSingleData(int)", 16)
            self.PriceInfo[0]['DownLimit'] = self.IndiTR.dynamicCall("GetSingleData(int)", 17)

            # 해외주식 실시간 등록
            ret = self.IndiReal.dynamicCall("RequestRTReg(QString, QString)", "SB", self.MainSymbol)
        elif TRName == "RC":
            self.PriceInfo[0]['Symbol'] = self.IndiTR.dynamicCall("GetSingleData(int)", 2)
            self.PriceInfo[0]['Time'] = self.IndiTR.dynamicCall("GetSingleData(int)", 5)
            self.PriceInfo[0]['Close'] = self.IndiTR.dynamicCall("GetSingleData(int)", 7)
            self.PriceInfo[0]['Vol'] = self.IndiTR.dynamicCall("GetSingleData(int)", 11)
            self.PriceInfo[0]['ContQty'] = self.IndiTR.dynamicCall("GetSingleData(int)", 13)
            self.PriceInfo[0]['Open'] = self.IndiTR.dynamicCall("GetSingleData(int)", 14)
            self.PriceInfo[0]['High'] = self.IndiTR.dynamicCall("GetSingleData(int)", 15)
            self.PriceInfo[0]['Low'] = self.IndiTR.dynamicCall("GetSingleData(int)", 16)

            # 해외주식 실시간 등록
            ret = self.IndiReal.dynamicCall("RequestRTReg(QString, QString)", "SC", self.MainSymbol)
        elif TRName == "RH":
            self.PriceInfo[0]['Ask1'] = self.IndiTR.dynamicCall("GetSingleData(int)", 8)
            self.PriceInfo[0]['Bid1'] = self.IndiTR.dynamicCall("GetSingleData(int)", 9)
            self.PriceInfo[0]['Ask1Qty'] = self.IndiTR.dynamicCall("GetSingleData(int)", 10)
            self.PriceInfo[0]['Bid1Qty'] = self.IndiTR.dynamicCall("GetSingleData(int)", 11)

            # 해외주식 실시간 등록
            ret = self.IndiReal.dynamicCall("RequestRTReg(QString, QString)", "SH", self.MainSymbol)

        self.rqidD.__delitem__(rqid)
    def ReceiveRTData(self, RealType):
        # 해외주식 실시간 처리
        if RealType == "RC":
            self.PriceInfo[0]['Symbol'] = self.IndiReal.dynamicCall("GetSingleData(int)", 2)
            self.PriceInfo[0]['Time'] = self.IndiReal.dynamicCall("GetSingleData(int)", 5)
            self.PriceInfo[0]['Close'] = self.IndiReal.dynamicCall("GetSingleData(int)", 7)
            self.PriceInfo[0]['Vol'] = self.IndiReal.dynamicCall("GetSingleData(int)", 11)
            self.PriceInfo[0]['ContQty'] = self.IndiReal.dynamicCall("GetSingleData(int)", 13)
            self.PriceInfo[0]['Open'] = self.IndiReal.dynamicCall("GetSingleData(int)", 14)
            self.PriceInfo[0]['High'] = self.IndiReal.dynamicCall("GetSingleData(int)", 15)
            self.PriceInfo[0]['Low'] = self.IndiReal.dynamicCall("GetSingleData(int)", 16)

        elif RealType == "RB":
            self.PriceInfo[0]['Name'] = self.IndiReal.dynamicCall("GetSingleData(int)", 5)
            self.PriceInfo[0]['PrevClose'] = self.IndiReal.dynamicCall("GetSingleData(int)", 11)
            self.PriceInfo[0]['UpLimit'] = self.IndiReal.dynamicCall("GetSingleData(int)", 16)
            self.PriceInfo[0]['DownLimit'] = self.IndiReal.dynamicCall("GetSingleData(int)", 17)
        elif RealType == "RH":
            self.PriceInfo[0]['Ask1'] = self.IndiReal.dynamicCall("GetSingleData(int)", 8)
            self.PriceInfo[0]['Bid1'] = self.IndiReal.dynamicCall("GetSingleData(int)", 9)
            self.PriceInfo[0]['Ask1Qty'] = self.IndiReal.dynamicCall("GetSingleData(int)", 10)
            self.PriceInfo[0]['Bid1Qty'] = self.IndiReal.dynamicCall("GetSingleData(int)", 11)

        print(self.PriceInfo[0])

    def ReceiveSysMsg(self, MsgID):
        print("System Message Received = ", MsgID)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    IndiWindow = IndiWindow()
    IndiWindow.show()
    app.exec_()

