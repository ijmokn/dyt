package com.ajis.aisad.client;

import com.ajis.general.common.Customize;
import com.ajis.general.common.AISTool;
import com.ajis.general.common.Customize;
import com.ajis.general.common.ComMacro;
import com.ajis.general.data.DataBase;
import com.ajis.general.data.DataUsrfil;
import com.ajis.general.manager.MiddlewareManager;
import com.ajis.general.model.ModeBuilder;
import com.ajis.middleware.adbcinterface.BarcodeSetConfig;
import com.ajis.middleware.adbcinterface.IBarcodeOperation;
import com.ajis.middleware.adiointerface.IIOOperation;

public class Customize60236 extends Customize {
    @Override
        public void setScannerType() {
            IBarcodeOperation barcode = null;
            barcode = MiddlewareManager.getSingleton(sContext).getBarcodeOperationInterface();
            DataBase database = null;
            database = ModeBuilder.getInstance().getModeData();

            int codeType = 0;
            boolean skuAddon = true;
            String temp = "";
            int eanFlg = DataUsrfil.getInstance().getEanFlg();
            int nw7Flg = DataUsrfil.getInstance().getNw7Flg();
            int cod39Flg = DataUsrfil.getInstance().getCode39Flg();
            int unLimitFlg = DataUsrfil.getInstance().getUnlmtCode();
            int scannerType = barcode.adbcGetScannerType();

            BarcodeSetConfig bcrConfig = new BarcodeSetConfig(scannerType);

            if(eanFlg == 0 && nw7Flg == 0 && cod39Flg == 0 && unLimitFlg == 0) {
                codeType = IBarcodeOperation.ADBC_CODETYPE_EAN
                        | IBarcodeOperation.ADBC_CODETYPE_CODE39
                        | IBarcodeOperation.ADBC_CODETYPE_NW7
                        | IBarcodeOperation.ADBC_CODETYPE_CODE128
                        | IBarcodeOperation.ADBC_CODETYPE_EAN128
                        | IBarcodeOperation.ADBC_CODETYPE_Industrial2of5
                        | IBarcodeOperation.ADBC_CODETYPE_CODE93
                        | IBarcodeOperation.ADBC_CODETYPE_ITF
                        | IBarcodeOperation.ADBC_CODETYPE_PDF
                        | IBarcodeOperation.ADBC_CODETYPE_QR
                        | IBarcodeOperation.ADBC_CODETYPE_DATAMATRIX
                        | IBarcodeOperation.ADBC_CODETYPE_DATABAR
                        | IBarcodeOperation.ADBC_CODETYPE_COMPOSITE;
            } else {
                if (unLimitFlg == 1) {
                    codeType = IBarcodeOperation.ADBC_CODETYPE_EAN
                            | IBarcodeOperation.ADBC_CODETYPE_CODE39
                            | IBarcodeOperation.ADBC_CODETYPE_NW7
                            | IBarcodeOperation.ADBC_CODETYPE_CODE128
                            | IBarcodeOperation.ADBC_CODETYPE_EAN128
                            | IBarcodeOperation.ADBC_CODETYPE_Industrial2of5
                            | IBarcodeOperation.ADBC_CODETYPE_CODE93
                            | IBarcodeOperation.ADBC_CODETYPE_ITF;
                } else {
                    if (eanFlg == 1) {
                        codeType = codeType | IBarcodeOperation.ADBC_CODETYPE_EAN
                                 | IBarcodeOperation.ADBC_CODETYPE_ITF;
                    }

                    if (nw7Flg == 1) {
                        codeType = codeType | IBarcodeOperation.ADBC_CODETYPE_NW7;
                    }

                    if (cod39Flg == 1) {
                        codeType = codeType | IBarcodeOperation.ADBC_CODETYPE_CODE39;
                    }
                }

                codeType = codeType | IBarcodeOperation.ADBC_CODETYPE_QR;

                if (DataUsrfil.getInstance().getwkmode() == ComMacro.MODE_SKU) {
                    skuAddon = false;
                    temp = DataUsrfil.getInstance().getSku1Num();

                    if (temp.length() == 16) {
                        int len = 0;
                        for (int i = 0; i < 8; i++) {
                            len = AISTool.stringToInt(temp.substring(i * 2, i * 2 + 2));

                            if (len == 18) {
                                skuAddon = true;
                                break;
                            }
                        }
                    }
                }

                if(scannerType == IBarcodeOperation.ADBC_SCANNER_HONEY) {
                    if (database.getCurScanMode() == IBarcodeOperation.ADBC_READMODE_MULTI
                            || database.getCurScanMode() == IBarcodeOperation.ADBC_READMODE_MIXED) {
                        skuAddon = false;
                    }
                }

                if (!skuAddon) {
                    bcrConfig.mBcrConfigEAN.mBcrConfigEAN13.mAddonNum = 0;
                    bcrConfig.mBcrConfigEAN.mBcrConfigEAN8.mAddonNum = 0;
                    bcrConfig.mBcrConfigEAN.mBcrConfigUPCA.mAddonNum = 0;
                    bcrConfig.mBcrConfigEAN.mBcrConfigUPCE0.mAddonNum = 0;
                } else {
                    bcrConfig.mBcrConfigEAN.mBcrConfigEAN13.mAddonNum = BarcodeSetConfig.ADBC_BCRSET_ANNON_2
                            | BarcodeSetConfig.ADBC_BCRSET_ANNON_5;
                    bcrConfig.mBcrConfigEAN.mBcrConfigEAN8.mAddonNum = BarcodeSetConfig.ADBC_BCRSET_ANNON_2
                            | BarcodeSetConfig.ADBC_BCRSET_ANNON_5;
                    bcrConfig.mBcrConfigEAN.mBcrConfigUPCA.mAddonNum = BarcodeSetConfig.ADBC_BCRSET_ANNON_2
                            | BarcodeSetConfig.ADBC_BCRSET_ANNON_5;
                    bcrConfig.mBcrConfigEAN.mBcrConfigUPCE0.mAddonNum = BarcodeSetConfig.ADBC_BCRSET_ANNON_2
                            | BarcodeSetConfig.ADBC_BCRSET_ANNON_5;
                }

                bcrConfig.mBcrConfigEAN.mBcrConfigUPCA.mPrefixTransmit = true;
                bcrConfig.mBcrConfigEAN.mBcrConfigUPCE0.mPrefixTransmit = false;

                bcrConfig.mBcrConfigCode39.mStartStopFlag = false;
                bcrConfig.mBcrConfigCode39.mCDCheck = false;
                bcrConfig.mBcrConfigCode39.mCDTransmit = false;

                bcrConfig.mBcrConfigNW7.mStartStopFlag = false;
                bcrConfig.mBcrConfigNW7.mCDCheck = false;
                bcrConfig.mBcrConfigNW7.mCDTransmit = false;

                bcrConfig.mBcrConfigITF.mCDCheck = false;
                bcrConfig.mBcrConfigITF.mCDTransmit = false;

                bcrConfig.mBcrConfigCode93.mCDCheck = true;
                bcrConfig.mBcrConfigCode93.mCDTransmit = false;

                bcrConfig.mBcrConfigCode128.mCDCheck = false;
                bcrConfig.mBcrConfigCode128.mCDTransmit = false;

                bcrConfig.mBcrConfigEAN128.mCDCheck = false;
                bcrConfig.mBcrConfigEAN128.mCDTransmit = false;

                if(!database.getITF()) {
                    bcrConfig.mBcrConfigITF.mMinLength = 5;
                    bcrConfig.mBcrConfig2of5.mMinLength = 5;
                }
            }

            if(scannerType == IBarcodeOperation.ADBC_SCANNER_HONEY) {
                try {
                    IIOOperation ioOperation = MiddlewareManager.getSingleton(sContext).getIOOperationInterface();
                    String centerPosition = ioOperation.adioGetHoneyCenterValue();
                    barcode.adbcSetScannerCenterWindow(centerPosition);
                } catch (Exception e) {

                }
            }

            barcode.adbcSetBarcodeSetConfig(bcrConfig);
            barcode.adbcSetScannerType(codeType);
            barcode.adbcSetScannerTimerOut(5000);
            barcode.adbcSetScannerMode(database.getInitScanMode());

            setMultiPrefix();
        }
}
