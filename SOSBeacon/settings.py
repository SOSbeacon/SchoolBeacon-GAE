TWILIO_ACCOUNT = ''
TWILIO_TOKEN = ''

SENDGRID_ACCOUNT = ''
SENDGRID_PASSWORD = ''

try:
    import settingslocal
except ImportError:
    settingslocal = None

if settingslocal:
    for setting in dir(settingslocal):
        globals()[setting.upper()] = getattr(settingslocal, setting)
