package android.hardware.usb.ext;

import android.hardware.usb.ext.IPortSecurityStateCallback;
import android.hardware.usb.ext.PortSecurityState;

@VintfStability
oneway interface IUsbExt {
    const int NO_ERROR = 0;
    const int ERROR_NO_I2C_PATH = 1;
    const int ERROR_FILE_WRITE = 2;
    const int ERROR_DENY_NEW_USB_WRITE = 3;

    void setPortSecurityState(String portName, PortSecurityState state, IPortSecurityStateCallback callback);
}
