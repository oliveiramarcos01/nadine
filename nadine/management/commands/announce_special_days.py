from datetime import date, datetime, timedelta
from dateutil.relativedelta import relativedelta

from django.utils.timezone import localtime, now
from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth.models import User

from nadine.models.profile import SpecialDay
from nadine import email


class Command(BaseCommand):
    help = "Send announcement to team of SpecialDays for our members"

    def handle(self, *args, **options):
        today = localtime(now()).date()
        for u in User.helper.active_members():
            for sd in SpecialDay.objects.filter(user=u):
                if sd.month == today.month and sd.day == today.day:
                    email.announce_special_day(u, sd)


# Copyright 2017 Office Nomads LLC (http://officenomads.com/) Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License. You may obtain a copy of the License at http://www.apache.org/licenses/LICENSE-2.0 Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the specific language governing permissions and limitations under the License.
