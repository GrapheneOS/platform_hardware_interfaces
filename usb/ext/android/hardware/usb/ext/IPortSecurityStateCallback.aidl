package android.hardware.usb.ext;

import android.hardware.usb.ext.PortSecurityState;

@VintfStability
oneway interface IPortSecurityStateCallback {
    void onSetPortSecurityStateCompleted(int status, int arg1, @utf8InCpp String arg2);
}
