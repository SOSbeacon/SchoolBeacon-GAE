TWILIO_ACCOUNT = ''
TWILIO_TOKEN = ''
TWILIO_FROM = ''

SENDGRID_ACCOUNT = ''
SENDGRID_PASSWORD = ''
SENDGRID_SENDER = ''

try:
    import settingslocal
except ImportError:
    settingslocal = None

if settingslocal:
    for setting in dir(settingslocal):
        globals()[setting.upper()] = getattr(settingslocal, setting)
