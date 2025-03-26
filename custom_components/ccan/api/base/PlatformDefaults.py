class PlatformDefaults:
    CCAN_MAJOR_VERSION = 0
    CCAN_MINOR_VERSION = 0
    CCAN_PATCH_VERSION = 26

    UPDATE_SECTION_BOOTLOADER    = 0
    UPDATE_SECTION_FIRMWARE      = 1
    UPDATE_SECTION_CONFIGURATION = 2

    VERSION_MAGIC_COOKIE_START = "CCAN_MAGIC_COOKIE_VERSION_"
    VERSION_MAGIC_COOKIE = VERSION_MAGIC_COOKIE_START + str(CCAN_MAJOR_VERSION) + "." + str(CCAN_MINOR_VERSION) + "." + str(CCAN_PATCH_VERSION)
    SERVER_CCAN_ADDRESS = 1023
    INVALID_SERVER_PORT = -1
    INVALID_CCAN_ADDRESS = 65535
    BROADCAST_CCAN_ADDRESS = 65535-1

