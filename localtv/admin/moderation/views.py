# Copyright 2009 - Participatory Culture Foundation
# 
# This file is part of Miro Community.
# 
# Miro Community is free software: you can redistribute it and/or modify it
# under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or (at your
# option) any later version.
# 
# Miro Community is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
# 
# You should have received a copy of the GNU Affero General Public License
# along with Miro Community.  If not, see <http://www.gnu.org/licenses/>.

from django.conf import settings
from django.contrib import comments, messages
from django.contrib.sites.models import Site
from django.core.mail import EmailMessage
from django.template import loader, Context
from django.template.defaultfilters import pluralize
from django.utils.decorators import method_decorator
from django.utils.translation import ugettext_lazy as _

if 'notification' in settings.INSTALLED_APPS:
    from notification import models as notification
else:
    notification = None

from localtv.admin.feeds import generate_secret
from localtv.admin.moderation.forms import (RequestModelFormSet,
                                            CommentModerationForm,
                                            VideoModerationForm,
                                            VideoLimitFormSet)
from localtv.admin.views import MiroCommunityAdminListView
from localtv.decorators import require_site_admin
from localtv.models import Video


class VideoModerationQueueView(MiroCommunityAdminListView):
    form_class = VideoModerationForm
    formset_class = VideoLimitFormSet
    paginate_by = 10
    context_object_name = 'videos'
    template_name = 'localtv/admin/moderation/videos/queue.html'

    @method_decorator(require_site_admin)
    def dispatch(self, *args, **kwargs):
        return super(VideoModerationQueueView, self).dispatch(*args, **kwargs)

    def get_queryset(self):
        return Video.objects.filter(
            status=Video.UNAPPROVED,
            site=Site.objects.get_current()
        ).order_by('when_submitted', 'when_published')

    def get_context_data(self, **kwargs):
        context = super(VideoModerationQueueView, self).get_context_data(**kwargs)
        try:
            current_video = context['object_list'][0]
        except IndexError:
            current_video = None
        
        context.update({
            'feed_secret': generate_secret(),
            'current_video': current_video
        })
        return context

    def formset_valid(self, formset):
        response = super(VideoModerationQueueView, self).formset_valid(formset)

        if formset._approved_count > 0:
            messages.add_message(
                self.request,
                messages.SUCCESS,
                _("Approved %d video%s." % (formset._approved_count,
                                            pluralize(formset._approved_count)))
            )
        if formset._rejected_count > 0:
            messages.add_message(
                self.request,
                messages.SUCCESS,
                _("Rejected %d video%s." % (formset._rejected_count,
                                            pluralize(formset._rejected_count)))
            )
        if formset._featured_count > 0:
            messages.add_message(
                self.request,
                messages.SUCCESS,
                _("Featured %d video%s." % (formset._featured_count,
                                            pluralize(formset._featured_count)))
            )
        if (notification and
            (formset._approved_count > 0 or formset._featured_count > 0)):
            notice_type = notification.NoticeType.objects.get(
                                                        label="video_approved")
            t = loader.get_template(
                        'localtv/submit_video/approval_notification_email.txt')
            for instance in self.object_list:
                if (instance.status == Video.ACTIVE and
                    instance.user is not None and instance.user.email and
                    notification.should_send(instance.user, notice_type, "1")):
                    c = Context({
                        'current_video': instance
                    })
                    subject = '[%s] "%s" was approved!' % (instance.site.name,
                                                           instance.name)
                    body = t.render(c)
                    EmailMessage(subject, body, settings.DEFAULT_FROM_EMAIL,
                                [instance.user.email]).send(fail_silently=True)

        return response


class CommentModerationQueueView(MiroCommunityAdminListView):
    formset_class = RequestModelFormSet
    form_class = CommentModerationForm
    paginate_by = 10
    context_object_name = 'comments'
    template_name = 'localtv/admin/moderation/comments/queue.html'
    queryset = comments.get_model()._default_manager.filter(is_public=False,
                                                            is_removed=False)

    @method_decorator(require_site_admin)
    def dispatch(self, *args, **kwargs):
        return super(CommentModerationQueueView, self).dispatch(*args, **kwargs)

    def get_formset_kwargs(self):
        kwargs = super(CommentModerationQueueView, self).get_formset_kwargs()
        kwargs['request'] = self.request
        return kwargs
