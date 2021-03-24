import sys
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QAxContainer import *

from pandas import Series, DataFrame
import matplotlib.pyplot as plt
import pandas as pd
import matplotlib.finance as matfin
import matplotlib.ticker as ticker

#import mpl_finance as matfin           설치를 따로 해야 쓸 수 있음


class MyWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("PyStock")
        self.setGeometry(300,300,440,400)
        self.CommTR = QAxWidget("GIEXPERTCONTROL.GiExpertControlCtrl.1")
        self.CommReal = QAxWidget("GIEXPERTCONTROL.GiExpertControlCtrl.1")

        self.CommTR.ReceiveData.connect(self.ReceiveTRData)
        self.CommReal.ReceiveRTData.connect(self.ReceiveRealData)

        self.rqid = {}

        self.listWidget = QListWidget(self)
        self.listWidget.setGeometry(10, 10, 220, 380)
        self.listWidget.itemDoubleClicked.connect(self.RequestTR)

        self.tableWidget = QTableWidget(self)
        self.tableWidget.setGeometry(240, 60, 190, 330)
        self.tableWidget.setRowCount(10)
        self.tableWidget.setColumnCount(1)
        self.setTableWidgetData()

        btn1 = QPushButton("캔들차트", self)
        btn1.setGeometry(240, 10, 90, 45)
        btn1.clicked.connect(self.RequestCandle)

        btn2 = QPushButton("종가선차트", self)
        btn2.setGeometry(340, 10, 90, 45)
        btn2.clicked.connect(self.RequestLine)

    def setTableWidgetData(self):
        row_headers = ['종목명', '단축코드', '체결시간', '현재가', '전일대비구분', '전일대비', '전일대비율', '누적거래량', '누적거래대금', '단위체결량' ]
        column_headers = ['VALUE']
        self.tableWidget.setVerticalHeaderLabels(row_headers)
        self.tableWidget.setHorizontalHeaderLabels(column_headers)

    def RequestStockList(self):
        self.CommTR.dynamicCall("SetQueryName(QString)", "stock_mst")
        nResult = self.CommTR.dynamicCall("RequestData()")
        self.rqid[nResult] = "stock_mst"

    def RequestTR(self):
        self.CommReal.dynamicCall("UnRequestRTRegAll()")
        item = self.listWidget.currentItem()
        if item == None:
            QMessageBox.about(self, "종목코드오류", "종목코드를 선택해주세요.")
            return
        TRName = "SC"
        jongmok = item.text().split(':')
        self.CommTR.dynamicCall("SetQueryName(QString)", TRName)
        self.CommTR.dynamicCall("SetSingleData(int, QString)", 0, jongmok[0])
        nResult = self.CommTR.dynamicCall("RequestData()")
        self.rqid[nResult] = TRName

        self.tableWidget.setItem(0, 0, QTableWidgetItem(jongmok[1]))

    def RequestCandle(self):
        nReturn = self.RequestChart()
        if nReturn != -1:
            self.rqid[nReturn] = "CANDLE"

    def RequestLine(self):
        nReturn = self.RequestChart()
        if nReturn != -1:
            self.rqid[nReturn] = "LINE"

    def RequestChart(self):
        item = self.listWidget.currentItem()
        if item == None:
            QMessageBox.about(self, "종목코드오류", "종목코드를 선택해주세요.")
            return -1
        jongmok = item.text().split(':')
        self.CommTR.dynamicCall("SetQueryName(QString)", "TR_SCHART")
        self.CommTR.dynamicCall("SetSingleData(int, QString)", 0, jongmok[0])
        self.CommTR.dynamicCall("SetSingleData(int, QString)", 1, "D")
        self.CommTR.dynamicCall("SetSingleData(int, QString)", 2, "1")
        self.CommTR.dynamicCall("SetSingleData(int, QString)", 3, "00000000")
        self.CommTR.dynamicCall("SetSingleData(int, QString)", 4, "99999999")
        self.CommTR.dynamicCall("SetSingleData(int, QString)", 5, "50")
        nResult = self.CommTR.dynamicCall("RequestData()")
        return nResult

    def ReceiveTRData(self, nID):
        TRName = self.rqid.get(nID)
        if TRName == "SC":
            self.DrawTable()
        elif TRName == "CANDLE":
            self.DrawCandleChart()
        elif TRName == "LINE":
            self.DrawChart()
        elif TRName == "stock_mst":
            codelist = []
            count = self.CommTR.dynamicCall("GetMultiRowCount()")
            for i in range(0, count):
                gubun = self.CommTR.dynamicCall("GetMultiData(int, QString)", i, 2)
                if gubun == "0":
                    code = self.CommTR.dynamicCall("GetMultiData(int, QString)", i, 1)
                    name = self.CommTR.dynamicCall("GetMultiData(int, QString)", i, 3)
                    codelist.append(code + " : " + name)
            self.listWidget.addItems(codelist)

    def ReceiveRealData(self):
        for i in range (1, 10):
            x = self.CommReal.dynamicCall("GetSingleData(int)", i)
            self.tableWidget.setItem(i, 0, QTableWidgetItem(x))

    def DrawChart(self):
        count = self.CommTR.dynamicCall("GetMultiRowCount()")
        value = {}
        rowvalue = []
        for i in range(0, 6):
            for j in range(0, count):
                x = self.CommTR.dynamicCall("GetMultiData(int, QString)", j, i)
                rowvalue.append(x)
            value[i] = rowvalue
            rowvalue = []

        value[0] = pd.to_datetime(value[0])
        daeshin = {'open': value[2], 'high': value[3], 'low': value[4], 'close': value[5]}
        daeshin_day = DataFrame(daeshin, columns=['open', 'high', 'low', 'close'], index=value[0])

        plt.plot(daeshin_day['close'])
        plt.show()

    def DrawTable(self):
        value = []
        for i in range (1, 10):
            x = self.CommTR.dynamicCall("GetSingleData(int)", i)
            self.tableWidget.setItem(i, 0, QTableWidgetItem(x))

        jongmok = self.tableWidget.item(1, 0).text()
        self.CommReal.dynamicCall("RequestRTReg(QString, QString", "SC", jongmok)

    def DrawCandleChart(self):
        count = self.CommTR.dynamicCall("GetMultiRowCount()")
        value = {}
        rowvalue = []
        for i in range(0, 6):
            for j in range(0, count):
                x = self.CommTR.dynamicCall("GetMultiData(int, QString)", j, i)
                rowvalue.append(x)
            value[i] = rowvalue
            rowvalue = []

        value[0] = pd.to_datetime(value[0])
        daeshin = {'open': value[2], 'high': value[3], 'low': value[4], 'close': value[5]}
        daeshin_day = DataFrame(daeshin, columns=['open', 'high', 'low', 'close'], index=value[0])

        fig = plt.figure(figsize=(12, 8))
        ax = fig.add_subplot(111)

        namelist = []
        daylist = []
        #for day in daeshin_day.index:
        #    namelist.append(day.strftime('%d'))
        #daylist = range(len(daeshin_day))
        for i, day in enumerate(daeshin_day.index):
            if day.dayofweek == 0:
                daylist.append(i)
                namelist.append(day.strftime('%m/%d(Mon)'))

        ax.xaxis.set_major_locator(ticker.FixedLocator(daylist))
        ax.xaxis.set_major_formatter(ticker.FixedFormatter(namelist))

        matfin.candlestick2_ohlc(ax, daeshin_day['open'], daeshin_day['high'], daeshin_day['low'], daeshin_day['close'], width=0.5, colorup='r', colordown='b')
        plt.grid()
        plt.show()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    IndiExam = MyWindow()
    IndiExam.show()
    IndiExam.RequestStockList()
    app.exec_()