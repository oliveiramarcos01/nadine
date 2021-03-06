import os
import string
import random
import getpass
import socket

from django.conf import settings
from django.contrib.auth.models import User
from django.core.management.base import BaseCommand, CommandError

from pytz import country_names, country_timezones, common_timezones

EXAMPLE_FILE = "nadine/local_settings.example"
SETTINGS_FILE = "nadine/local_settings.py"
PROMPT = '> '

class Command(BaseCommand):
    help = "System Setup"
    requires_system_checks = False

    def handle(self, *args, **options):
        try:
            print
            print("###################################")
            print("Nadine Local Settings Configuration")
            print("###################################")
            print
            self.load_settings_file()
            self.setup_general()
            self.setup_timezone()
            self.setup_email()
            self.setup_database()
            self.write_settings_file()
        except KeyboardInterrupt:
            print
            print("Exiting without saving!")
            print

    def load_settings_file(self):
        # Test to see if SETTINGS_FILE exists and prompt to load it or remove it
        filename = EXAMPLE_FILE
        if os.path.isfile(SETTINGS_FILE):
            print ("File '%s' exists!" % SETTINGS_FILE)
            print ("Do you want to load the existing file? (Y, n)")
            load = raw_input(PROMPT).strip().lower()
            if load == "n":
                print("Current settings in '%s' will be lost!" % SETTINGS_FILE)
            else:
                filename = SETTINGS_FILE
        self.local_settings = LocalSettings(filename)
        print

    def write_settings_file(self):
        print("Write new local_settings file? (y, N)")
        save = raw_input(PROMPT).strip().lower()
        if save == "y":
            print("Writing %s" % SETTINGS_FILE)
            self.local_settings.save(SETTINGS_FILE)

    def prompt_for_value(self, question, key, default=None):
        if not default:
            default = self.local_settings.get_value(key)
        print("%s? (default: '%s')" % (question, default))
        value = raw_input(PROMPT).strip().lower()
        if not value:
            value = default
        self.local_settings.set(key, value)

    def setup_general(self):
        print("### General Settings ###")

        # Secret Key
        secret_key = self.local_settings.get("SECRET_KEY")
        if not secret_key or len(secret_key) < 32:
            print("Generating random SECRET_KEY")
            secret_key = ''.join([random.SystemRandom().choice("{}{}".format(string.ascii_letters, string.digits)) for i in range(63)])
            self.local_settings.set('SECRET_KEY', secret_key, quiet=True)
            print

        # Site Information
        self.prompt_for_value("Site Name", "SITE_NAME")
        current_host = socket.gethostname().lower()
        self.prompt_for_value("Site Domain", "SITE_DOMAIN", default=current_host)
        protocol = "http"
        print("Use SSL? (y, N)")
        ssl = raw_input(PROMPT).strip().lower()
        if ssl == "y":
            protocol = protocol + "s"
        self.local_settings.set('SITE_PROTO', protocol)

        # Site Administrator
        print("Full Name of Administrator")
        admin_name = raw_input(PROMPT).strip().title()
        print("Admin Email Address?")
        admin_email = raw_input(PROMPT).strip().lower()
        self.local_settings.set_admins(admin_name, admin_email)

    def setup_timezone(self):
        print
        print("### Timezone Setup ###")

        # Country
        country = ''
        while country not in country_names:
            print("What country? (blank: list available)")
            country = raw_input(PROMPT).strip().upper()
            if not country:
                print ("Country Codes:")
                print(', '.join(country_names))
                print
        self.local_settings.set('COUNTRY', country)

        # Timezone
        tz = ''
        while tz not in common_timezones:
            print("What timezone? (blank: list available)")
            tz = raw_input(PROMPT).strip()
            if not tz:
                print ("Available Timezones:")
                print(', '.join(country_timezones[country]))
                print
        self.local_settings.set('TIME_ZONE', tz)

    # Database Setup
    def setup_database(self):
        print
        print("### Database Setup ###")
        print("Database Name? (default: nadinedb)")
        db_name = raw_input(PROMPT).strip()
        if not db_name:
            db_name = "nadinedb"
        print("DATABASE_NAME = '%s'" % db_name)
        current_user = getpass.getuser()
        print("Database User? (default: %s)" % current_user)
        db_user = raw_input(PROMPT).strip()
        if not db_user:
            db_user = current_user
        print("DATABASE_USER = '%s'" % db_user)
        print("Database Password? (optional)")
        db_pass = raw_input(PROMPT).strip()
        if db_pass:
            print("DATABASE_PASSWORD = '%s'" % db_pass)
        self.local_settings.set_database(db_name, db_user, db_pass)

    # Mail Server Setup
    def setup_email(self):
        print
        print("### Email Setup ###")
        domain = self.local_settings.get_value("SITE_DOMAIN")
        self.prompt_for_value("Email Host", "EMAIL_HOST")
        self.prompt_for_value("Email Host User", "EMAIL_HOST_USER", default="postmaster@" + domain)
        self.prompt_for_value("Email Host Password", "EMAIL_HOST_PASSWORD")
        # self.prompt_for_value("Email Host Port", "EMAIL_PORT")
        # self.prompt_for_value("User TSL", "EMAIL_USE_TLS")
        self.prompt_for_value("Subject Prefix", "EMAIL_SUBJECT_PREFIX")
        self.prompt_for_value("Sent From Address", "DEFAULT_FROM_EMAIL", default="nadine@" + domain)
        default_from = self.local_settings.get_value("DEFAULT_FROM_EMAIL")
        self.local_settings.set('SERVER_EMAIL', default_from)
        self.prompt_for_value("Staff Address", "STAFF_EMAIL_ADDRESS", default="staff@" + domain)
        self.prompt_for_value("Billing Address", "BILLING_EMAIL_ADDRESS", default="billing@" + domain)
        self.prompt_for_value("Team Address", "TEAM_EMAIL_ADDRESS", default="team@" + domain)


class LocalSettings():

    def __init__(self, filename):
        print("Loading %s" % filename)
        with open(filename) as f:
            self.settings = f.readlines()

        if not self.settings[0].startswith("# Generated using"):
            self.settings.insert(0, "# Generated using ./manage.py setup\n")

    def get_line_number(self, key):
        for i, line in enumerate(self.settings):
            if line.startswith(key):
                return i
        return -1

    def get(self, key):
        line_number = self.get_line_number(key)
        if line_number > 0:
            return self.settings[line_number]
        return None

    def get_value(self, key):
        value = self.get(key)
        if not value:
            return None
        clean_value = value[value.index('=') + 1:].strip()
        if clean_value[0] == "'" or clean_value[0] == '"':
            return clean_value[1:len(clean_value)-1]
        return clean_value

    def set(self, key, value, quiet=False):
        new_line = '%s = "%s"\n' % (key, value)
        if not quiet:
            print(new_line)
        line_number = self.get_line_number(key)
        if line_number >= 0:
            self.settings[line_number] = new_line
        else:
            self.settings.append(new_line)

    def set_admins(self, admin_name, admin_email):
        line_number = self.get_line_number("ADMINS")
        self.settings[line_number + 1] = "    ('%s', '%s')\n" % (admin_name, admin_email)

    def set_database(self, db_name, db_user, db_pass=None):
        line_number = self.get_line_number("DATABASES")
        self.settings[line_number + 3] = "        'NAME': '%s',\n" % db_name
        self.settings[line_number + 4] = "        'USER': '%s',\n" % db_user
        if db_pass:
            self.settings[line_number + 5] = "        'PASSWORD': '%s',\n" % db_pass
        else:
            self.settings[line_number + 5] = "        #'PASSWORD': 'password',\n"

    def save(self, filename):
        print("Writing new settings file...")
        with open(filename, 'w') as f:
            f.writelines(self.settings)
