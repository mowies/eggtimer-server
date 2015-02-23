import datetime

from django.test import TestCase
from mock import ANY, patch

from periods import models as period_models
from periods.management.commands import notify_upcoming_period
from periods.tests.factories import FlowEventFactory


class TestCommand(TestCase):

    def setUp(self):
        self.command = notify_upcoming_period.Command()
        flow_event = FlowEventFactory()
        self.user = flow_event.user
        FlowEventFactory(user=self.user, timestamp=datetime.datetime(2014, 2, 28))

    @patch('django.core.mail.EmailMultiAlternatives.send')
    def test_notify_upcoming_period_no_periods(self, mock_send):
        period_models.FlowEvent.objects.all().delete()

        self.command.handle()

        self.assertFalse(mock_send.called)

    @patch('django.core.mail.EmailMultiAlternatives.send')
    @patch('periods.models._today')
    def test_notify_upcoming_period_send_disabled(self, mock_today, mock_send):
        mock_today.return_value = datetime.date(2014, 3, 14)
        self.user.send_emails = False
        self.user.save()

        self.command.handle()

        self.assertFalse(mock_send.called)

    @patch('periods.email_sender.send')
    @patch('periods.models._today')
    def test_notify_upcoming_period_no_events(self, mock_today, mock_send):
        mock_today.return_value = datetime.date(2014, 3, 13)

        self.command.handle()

        self.assertFalse(mock_send.called)

    @patch('periods.email_sender.send')
    @patch('periods.models._today')
    def test_notify_upcoming_period_ovulation(self, mock_today, mock_send):
        mock_today.return_value = datetime.date(2014, 3, 14)

        self.command.handle()

        mock_send.assert_called_once_with(self.user, 'Ovulation today!', ANY, None)

    @patch('periods.email_sender.send')
    @patch('periods.models._today')
    def test_notify_upcoming_period_expected_soon(self, mock_today, mock_send):
        mock_today.return_value = datetime.date(2014, 3, 25)

        self.command.handle()

        mock_send.assert_called_once_with(self.user, 'Period expected in 3 days',
                                          ANY, None)

    @patch('periods.email_sender.send')
    @patch('periods.models._today')
    def test_notify_upcoming_period_expected_today(self, mock_today, mock_send):
        mock_today.return_value = datetime.date(2014, 3, 28)

        self.command.handle()

        mock_send.assert_called_once_with(self.user, 'Period today!', ANY, None)

    @patch('periods.email_sender.send')
    @patch('periods.models._today')
    def test_notify_upcoming_period_overdue(self, mock_today, mock_send):
        mock_today.return_value = datetime.date(2014, 3, 29)

        self.command.handle()

        mock_send.assert_called_once_with(self.user, 'Period was expected 1 day ago',
                                          ANY, None)
