from django.conf import settings
from allauth.account.adapter import DefaultAccountAdapter
from .models import Exhibitors


""" Hook for overriding the send_mail method of the account adapter """
class CustomPasswordResetAdapter(DefaultAccountAdapter):
	def send_mail(self, template_prefix, email, context):
		is_exhibitor = context['user'].groups.filter(name='Exhibitors').exists()
		if is_exhibitor and template_prefix == 'account/email/password_reset_key':
			try:
				protocol = 'https' if self.request.is_secure() else 'http'
				context['exhibitor'] = Exhibitors.objects.filter(user__email=email)[0]
				context['site_path'] = "%s://%s" % (protocol, context['current_site'].domain)
				msg = self.render_mail('account/email/exhibitors/password_reset_key', email, context)
			except Exhibitors.DoesNotExist:
				msg = self.render_mail(template_prefix, email, context)
		else:
			msg = self.render_mail(template_prefix, email, context)

		msg.send()

