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
    신한아이 인디 국내주식 예제입니다:
    코드를 입력하시고 Search 버튼을 누르시면
    종목코드에 해당하는 일별 차트 데이터 100개와
    종목 가격정보를 조회하여 출력합니다.
'''

class IndiWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("IndiExample")

        self.IndiTR = QAxWidget("GIEXPERTCONTROL.GiExpertControlCtrl.1")
        self.IndiTR.ReceiveData.connect(self.ReceiveData)
        self.IndiTR.ReceiveSysMsg.connect(self.ReceiveSysMsg)

        self.IndiReal = QAxWidget("GIEXPERTCONTROL.GiExpertControlCtrl.1")
        self.IndiReal.ReceiveRTData.connect(self.ReceiveRTData)

        self.rqidD = {}
        PriceInfodt = np.dtype([('Symbol', 'S10'), ('Name', 'S40'), ('Close', 'f'), ('Open', 'f'), ('High', 'f'), ('Low', 'f'),
                       ('UpLimit', 'f'), ('DownLimit', 'f'), ('PrevClose', 'f'), ('Ask1', 'f'), ('Bid1', 'f'),
                       ('Time', 'S6'), ('Vol', 'u4'), ('ContQty', 'u4'), ('Ask1Qty', 'u4'), ('Bid1Qty', 'u4')])
        self.PriceInfo = np.empty([1], dtype=PriceInfodt)

        Historicaldt = np.dtype([('Date', 'S8'), ('Time', 'S6'), ('Open', 'f'), ('High', 'f'), ('Low', 'f'), ('Close', 'f'), ('Vol', 'u4')])
        self.Historical = np.empty([100], dtype=Historicaldt)

        self.MainSymbol = ""
        self.edSymbol = QLineEdit(self)
        self.edSymbol.setGeometry(20, 20, 60, 20)
        self.edSymbol.setText("")

        btnResearch = QPushButton("Search", self)
        btnResearch.setGeometry(85, 20, 50, 20)
        btnResearch.clicked.connect(self.btn_Search)


    def btn_Search(self):
        Symbol = self.edSymbol.text()

        # 기존종목 실시간 해제
        if self.MainSymbol != "":
            self.IndiReal.dynamicCall("UnRequestRTReg(QString, QString)", "SB", self.MainSymbol)
            self.IndiReal.dynamicCall("UnRequestRTReg(QString, QString)", "SC", self.MainSymbol)
            self.IndiReal.dynamicCall("UnRequestRTReg(QString, QString)", "SH", self.MainSymbol)

        self.MainSymbol = Symbol

        # 차트조회
        ret = self.IndiTR.dynamicCall("SetQueryName(QString)", "TR_SCHART")
        ret = self.IndiTR.dynamicCall("SetSingleData(int, QString)", 0, self.MainSymbol)
        ret = self.IndiTR.dynamicCall("SetSingleData(int, QString)", 1, "D")
        ret = self.IndiTR.dynamicCall("SetSingleData(int, QString)", 2, "1")
        ret = self.IndiTR.dynamicCall("SetSingleData(int, QString)", 3, "00000000")
        ret = self.IndiTR.dynamicCall("SetSingleData(int, QString)", 4, "99999999")
        ret = self.IndiTR.dynamicCall("SetSingleData(int, QString)", 5, "100")
        rqid = self.IndiTR.dynamicCall("RequestData()")

        self.rqidD[rqid] =  "TR_SCHART"

        # 종목 기본정보 조회
        ret = self.IndiTR.dynamicCall("SetQueryName(QString)", "SB")
        ret = self.IndiTR.dynamicCall("SetSingleData(int, QString)", 0, self.MainSymbol)
        rqid = self.IndiTR.dynamicCall("RequestData()")

        self.rqidD[rqid] = "SB"

        # 종목 현재가 조회
        ret = self.IndiTR.dynamicCall("SetQueryName(QString)", "SC")
        ret = self.IndiTR.dynamicCall("SetSingleData(int, QString)", 0, self.MainSymbol)
        rqid = self.IndiTR.dynamicCall("RequestData()")

        self.rqidD[rqid] = "SC"

        # 종목 호가 조회
        ret = self.IndiTR.dynamicCall("SetQueryName(QString)", "SH")
        ret = self.IndiTR.dynamicCall("SetSingleData(int, QString)", 0, self.MainSymbol)
        rqid = self.IndiTR.dynamicCall("RequestData()")

        self.rqidD[rqid] = "SH"

    def ReceiveData(self, rqid):

        TRName = self.rqidD[rqid]
        if TRName == "TR_SCHART" :
            nCnt = self.IndiTR.dynamicCall("GetMultiRowCount()")
            np.reshape(self.Historical, nCnt)
            for i in range(0, nCnt):
                self.Historical[i]['Date'] = self.IndiTR.dynamicCall("GetMultiData(int, int)", i, 0)
                self.Historical[i]['Time'] = self.IndiTR.dynamicCall("GetMultiData(int, int)", i, 1)
                self.Historical[i]['Open'] = self.IndiTR.dynamicCall("GetMultiData(int, int)", i, 2)
                self.Historical[i]['High'] = self.IndiTR.dynamicCall("GetMultiData(int, int)", i, 3)
                self.Historical[i]['Low'] = self.IndiTR.dynamicCall("GetMultiData(int, int)", i, 4)
                self.Historical[i]['Close'] = self.IndiTR.dynamicCall("GetMultiData(int, int)", i, 5)
                self.Historical[i]['Vol'] = self.IndiTR.dynamicCall("GetMultiData(int, int)", i, 9)

            print(self.Historical)

        elif TRName == "SB":
            self.PriceInfo[0]['Name'] = self.IndiTR.dynamicCall("GetSingleData(int)", 6)
            self.PriceInfo[0]['PrevClose'] = self.IndiTR.dynamicCall("GetSingleData(int)", 23)
            self.PriceInfo[0]['UpLimit'] = self.IndiTR.dynamicCall("GetSingleData(int)", 27)
            self.PriceInfo[0]['DownLimit'] = self.IndiTR.dynamicCall("GetSingleData(int)", 28)

            # 실시간 등록
            ret = self.IndiReal.dynamicCall("RequestRTReg(QString, QString)", "SB", self.MainSymbol)
        elif TRName == "SC":
            self.PriceInfo[0]['Symbol'] = self.IndiTR.dynamicCall("GetSingleData(int)", 1)
            self.PriceInfo[0]['Time'] = self.IndiTR.dynamicCall("GetSingleData(int)", 2)
            self.PriceInfo[0]['Close'] = self.IndiTR.dynamicCall("GetSingleData(int)", 3)
            self.PriceInfo[0]['Vol'] = self.IndiTR.dynamicCall("GetSingleData(int)", 7)
            self.PriceInfo[0]['ContQty'] = self.IndiTR.dynamicCall("GetSingleData(int)", 9)
            self.PriceInfo[0]['Open'] = self.IndiTR.dynamicCall("GetSingleData(int)", 10)
            self.PriceInfo[0]['High'] = self.IndiTR.dynamicCall("GetSingleData(int)", 11)
            self.PriceInfo[0]['Low'] = self.IndiTR.dynamicCall("GetSingleData(int)", 12)

            # 실시간 등록
            ret = self.IndiReal.dynamicCall("RequestRTReg(QString, QString)", "SC", self.MainSymbol)
        elif TRName == "SH":
            self.PriceInfo[0]['Ask1'] = self.IndiTR.dynamicCall("GetSingleData(int)", 4)
            self.PriceInfo[0]['Bid1'] = self.IndiTR.dynamicCall("GetSingleData(int)", 5)
            self.PriceInfo[0]['Ask1Qty'] = self.IndiTR.dynamicCall("GetSingleData(int)", 6)
            self.PriceInfo[0]['Bid1Qty'] = self.IndiTR.dynamicCall("GetSingleData(int)", 7)

            # 실시간 등록
            ret = self.IndiReal.dynamicCall("RequestRTReg(QString, QString)", "SH", self.MainSymbol)

        self.rqidD.__delitem__(rqid)
    def ReceiveRTData(self, RealType):

        if RealType == "SC":
            self.PriceInfo[0]['Symbol'] = self.IndiReal.dynamicCall("GetSingleData(int)", 1)
            self.PriceInfo[0]['Time'] = self.IndiReal.dynamicCall("GetSingleData(int)", 2)
            self.PriceInfo[0]['Close'] = self.IndiReal.dynamicCall("GetSingleData(int)", 3)
            self.PriceInfo[0]['Vol'] = self.IndiReal.dynamicCall("GetSingleData(int)", 7)
            self.PriceInfo[0]['ContQty'] = self.IndiReal.dynamicCall("GetSingleData(int)", 9)
            self.PriceInfo[0]['Open'] = self.IndiReal.dynamicCall("GetSingleData(int)", 10)
            self.PriceInfo[0]['High'] = self.IndiReal.dynamicCall("GetSingleData(int)", 11)
            self.PriceInfo[0]['Low'] = self.IndiReal.dynamicCall("GetSingleData(int)", 12)

        elif RealType == "SB":
            self.PriceInfo[0]['Name'] = self.IndiReal.dynamicCall("GetSingleData(int)", 5)
            self.PriceInfo[0]['PrevClose'] = self.IndiReal.dynamicCall("GetSingleData(int)", 23)
            self.PriceInfo[0]['UpLimit'] = self.IndiReal.dynamicCall("GetSingleData(int)", 27)
            self.PriceInfo[0]['DownLimit'] = self.IndiReal.dynamicCall("GetSingleData(int)", 28)
        elif RealType == "SH":
            self.PriceInfo[0]['Ask1'] = self.IndiReal.dynamicCall("GetSingleData(int)", 4)
            self.PriceInfo[0]['Bid1'] = self.IndiReal.dynamicCall("GetSingleData(int)", 5)
            self.PriceInfo[0]['Ask1Qty'] = self.IndiReal.dynamicCall("GetSingleData(int)", 6)
            self.PriceInfo[0]['Bid1Qty'] = self.IndiReal.dynamicCall("GetSingleData(int)", 7)

        print(self.PriceInfo[0])

    def ReceiveSysMsg(self, MsgID):
        print("System Message Received = ", MsgID)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    IndiWindow = IndiWindow()
    IndiWindow.show()
    app.exec_()

