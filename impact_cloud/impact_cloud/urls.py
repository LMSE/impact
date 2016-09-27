"""impact_main_site URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.9/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.conf.urls import url, include
    2. Add a URL to urlpatterns:  url(r'^blog/', include('blog.urls'))
"""
from django.conf.urls import url, include

import sys
from . import views

# REST API
from django.contrib.auth.models import User
from rest_framework import routers, serializers, viewsets

# Serializers define the API representation.
class UserSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = User
        fields = ('url', 'username', 'email', 'is_staff')

# ViewSets define the view behavior.
class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer

# Routers provide an easy way of automatically determining the URL conf.
router = routers.DefaultRouter()
router.register(r'users', UserViewSet)

urlpatterns = [
    # REST api
    url(r'^/rest_api$', include(router.urls)),
    url(r'^api-auth/', include('rest_framework.urls', namespace='rest_framework')),

    url(r'^$',views.welcome),

    # url(r'^check_auth$', views.check_auth),
    # url(r'^get_username_auth$', views.get_username_auth),

    # authentication urls
    url(r'^registration/register$',views.register),
    url(r'^createAccount/$',views.index),
    url(r'^login/$',views.login),
    url(r'^login',views.login),
    url(r'^logout',views.logout),

    # experiment_select urls - this should be generalized
    url(r'^experimentSelect/(?P<experiment_id>[0-9]+)$',views.experimentSelect),
    url(r'^experimentSelect_analyze/(?P<experiment_id>[0-9]+)$', views.experimentSelect_analyze),
    url(r'^experimentSelect_input/(?P<experiment_id>[0-9]+)$', views.experiment_select_input),
    url(r'^experimentSelect_export/(?P<experiment_id>[0-9]+)$', views.experimentSelect_export),
    url(r'^export_data/$', views.export_data),

    # input urls
    url(r'^input/inputData$',views.process_input_data),
    url(r'^input/table_input$',views.input),
    url(r'^input/file', views.input_file),

    url(r'^input/$', views.input_initial),
    url(r'^input/new_experiment/$',views.new_experiment),
    url(r'^select_input_format/(?P<input_format>[a-z|A-Z|_]+)$', views.select_input_format),
    url(r'^input/analysis_options$',views.analysis_options),

    # plot urls
    url(r'^plot/$', views.plot),
    url(r'^plot/options/$', views.plot_options),
    url(r'^plot/select_strains/(P<identifier>[a-z|A-Z]+)/(P<identifierName>[a-z|A-Z]+)$', views.selectStrains),
    url(r'^plot/select_strains/$', views.selectStrains),
    url(r'^plot/select_strain_subset/$', views.select_strain_subset),
    url(r'^plot/remove_strains/$', views.removeStrains),
    url(r'^plot/select_titers/$', views.selectTiters),
    url(r'^plot/clear_data/$', views.clear_data),

    # analyze urls
    url(r'^analyze/$', views.analyze),
    url(r'^analyze/replicate_select/(?P<replicate_id>[0-9]+)$', views.analyze_select_replicate),
    url(r'^analyze/delete_experiment/(?P<experiment_id>[0-9]+)$', views.delete_experiment),


    # export urls
    url(r'^export/$', views.export),


    url(r'^iPython/$', views.iPython),


    # other urls
    url(r'^color_scales/$',views.color_scale_examples),
    url(r'^download_plot/$', views.download_plot),

    # url(r'^iPython/auth/$',views.iPython_auth)
]