from django.conf import settings
from allauth.account.adapter import DefaultAccountAdapter
from .models import Exhibitors


""" Hook for overriding the send_mail method of the account adapter """
class CustomPasswordResetAdapter(DefaultAccountAdapter):
	def send_mail(self, template_prefix, email, context):
		if template_prefix == 'account/email/password_reset_key':
			try:
				context['exhibitor'] = Exhibitors.objects.filter(user__email=email)[0]
				context['site_path'] = "%s://%s" % (context['request'].POST['protocol'], context['current_site'].domain)
				msg = self.render_mail('account/email/exhibitors/password_reset_key', email, context)
			except Exhibitors.DoesNotExist:
				msg = self.render_mail(template_prefix, email, context)
		else:
			msg = self.render_mail(template_prefix, email, context)

		msg.send()

