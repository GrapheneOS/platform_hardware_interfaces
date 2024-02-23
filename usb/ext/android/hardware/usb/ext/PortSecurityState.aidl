package android.hardware.usb.ext;

@Backing(type="int")
@VintfStability
enum PortSecurityState {
    DISABLED = 0,
    // immediately disables USB data path and disables alt modes on subsequent connections
    CHARGING_ONLY_IMMEDIATE = 10,
    // applies after port disconnect if it's currently connected
    CHARGING_ONLY = 15,
    ENABLED = 50,
}
