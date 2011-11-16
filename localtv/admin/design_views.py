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

from django.shortcuts import render_to_response
from django.template import RequestContext
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect, Http404
from django.views.decorators.csrf import csrf_protect

from localtv.admin import forms
from localtv.decorators import require_site_admin
from localtv.models import SiteLocation, WidgetSettings, NewsletterSettings


@require_site_admin
@csrf_protect
def widget_settings(request):
    sitelocation = SiteLocation.objects.get_current()
    form = forms.WidgetSettingsForm(
        instance=sitelocation.site.widgetsettings,
        initial={'title': 
                 WidgetSettings.objects.get().get_title_or_reasonable_default()})

    if request.method == 'POST':
        form = forms.WidgetSettingsForm(
            request.POST,
            request.FILES,
            instance=sitelocation.site.widgetsettings)
        if form.is_valid():
            widgetsettings = form.save()
            if request.POST.get('delete_icon'):
                if widgetsettings.icon:
                    widgetsettings.icon.delete()
                    widgetsettings.delete_thumbnails()
            if request.POST.get('delete_css'):
                if widgetsettings.css:
                    widgetsettings.css.delete()
            return HttpResponseRedirect(
                reverse('localtv_admin_widget_settings'))
    return render_to_response(
        'localtv/admin/widget_settings.html',
        {'form': form},
        context_instance=RequestContext(request))