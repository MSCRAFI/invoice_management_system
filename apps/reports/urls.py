from django.urls import path
from . import views

# Note: You would need to create views.py in the reports app
# to serve this data, likely as a TemplateView or JsonResponse.

urlpatterns = [
    # Example: path('summary/', views.ReportSummaryView.as_view(), name='summary'),
]