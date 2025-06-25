import os
from typing import List
from django.core.management.base import BaseCommand, CommandError, CommandParser
from webook.arrangement.models import Person
from webook.users.models import User
from allauth.socialaccount.models import SocialAccount


class Command(BaseCommand):
    help = "Update user emails to match their social account emails"

    def add_arguments(self, parser: CommandParser) -> None:
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Run the command without making any changes",
        )

    def handle(self, *args, **options):
        dry_run = options["dry_run"]
        users: List[User] = User.objects.all()
        people: List[Person] = Person.objects.all()

        for user in users:
            social_accounts: List[SocialAccount] = list(user.socialaccount_set.all())
            if not social_accounts:
                continue

            primary_social_account: SocialAccount = social_accounts[0]

            if not primary_social_account.extra_data:
                print(
                    f"Skipping user {user.username} as no extra data found in social account"
                )
                continue

            social_account_extra_data = primary_social_account.extra_data
            social_account_email = social_account_extra_data.get("mail", None)

            if not social_account_email:
                print(
                    f"Skipping user {user.username} as no email found in social account data"
                )
                continue

            social_account_email = social_account_email.strip().lower()

            if user.email.lower() != social_account_email:
                print(
                    f"Updating email for user {user.id} from {user.email} to {social_account_email}"
                )
                if not dry_run:
                    try:
                        user.email = social_account_email
                        user.save()

                        person = Person.objects.filter(user=user).first()
                        if person:
                            person.personal_email = social_account_email
                            person.social_provider_email = social_account_email
                            person.save()
                    except Exception as e:
                        print(f"Failed to update email for user {user.id}: {str(e)}")

        for person in people:
            user = person.user_set.first()
            if not user:
                print(f"Person {person.id} has no associated user")
                continue

            if person.social_provider_id and person.social_provider_email != user.email:
                person.social_provider_email = user.email
                print(
                    f"Updating social_provider_email for person {person.id} to {user.email}"
                )
                if not dry_run:
                    try:
                        person.save()
                    except Exception as e:
                        print(
                            f"Failed to update social_provider_email for person {person.id}: {str(e)}"
                        )
