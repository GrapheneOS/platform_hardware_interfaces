package android.hardware.usb.ext;

import android.hardware.usb.ext.PortSecurityState;

@VintfStability
oneway interface IUsbExt {
    const int ERROR_NO_I2C_PATH = 1;
    const int ERROR_FILE_WRITE = 2;

    void setPortSecurityState(String portName, PortSecurityState state);
}
